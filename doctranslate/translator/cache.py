import hashlib
import json
import logging
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import peewee
from peewee import SQL
from peewee import AutoField
from peewee import BigIntegerField
from peewee import BlobField
from peewee import CharField
from peewee import IntegerField
from peewee import Model
from peewee import SqliteDatabase
from peewee import TextField
from peewee import fn

from doctranslate.const import CACHE_FOLDER
from doctranslate.translator.tm_migration import migrate_legacy_sqlite_into_tm
from doctranslate.translator.tm_normalize import normalize_for_tm
from doctranslate.translator.tm_normalize import placeholder_signature
from doctranslate.translator.tm_normalize import stable_hash
from doctranslate.translator.tm_policy import TMMode
from doctranslate.translator.tm_policy import TMRuntimeConfig
from doctranslate.translator.tm_policy import TMScope
from doctranslate.translator.tm_safety import glossary_compatible
from doctranslate.translator.tm_safety import placeholders_compatible
from doctranslate.translator.tm_safety import segment_long_enough
from doctranslate.translator.tm_vector import cosine_similarity
from doctranslate.translator.tm_vector import deserialize_embedding_f32
from doctranslate.translator.tm_vector import serialize_embedding_f32
from doctranslate.translator.tm_vector import try_create_semantic_backend

logger = logging.getLogger(__name__)

# Exact-match cache + translation memory (TM) share one SQLite file (WAL).
db = SqliteDatabase(None)

# Legacy cleanup
CLEAN_PROBABILITY = 0.001
MAX_CACHE_ROWS = 50_000
_cleanup_lock = threading.Lock()

# TM writes + trim share one RLock: set() holds across upsert+cleanup so rows
# cannot race past max_tm_rows; _tm_cleanup re-enters the same lock from set().
_tm_cleanup_lock = threading.RLock()
_tm_write_counter = 0
_tm_write_counter_lock = threading.Lock()

LEGACY_DB_FILENAME = "cache.v2.db"


class _TranslationCache(Model):
    id = AutoField()
    translate_engine = CharField(max_length=128)
    translate_engine_params = TextField()
    original_text = TextField()
    translation = TextField()

    class Meta:
        database = db
        constraints = [
            SQL(
                """
            UNIQUE (
                translate_engine,
                translate_engine_params,
                original_text
                )
            ON CONFLICT REPLACE
            """,
            ),
        ]


class _TmMigration(Model):
    """Applied migration markers for TM DB."""

    name = CharField(primary_key=True, max_length=64)
    applied_at = BigIntegerField()

    class Meta:
        database = db


class _TmEntry(Model):
    """Translation memory row (L1b/L2/L3)."""

    id = AutoField()
    translate_engine = CharField(max_length=128)
    translate_engine_params = TextField()
    lang_in = CharField(max_length=32, default="")
    lang_out = CharField(max_length=32, default="")
    source_text_raw = TextField()
    source_text_norm = TextField()
    target_text = TextField()
    source_hash_raw = CharField(max_length=64)
    source_hash_norm = CharField(max_length=64)
    placeholder_signature = CharField(max_length=64, default="")
    glossary_signature = CharField(max_length=64, default="")
    project_scope = CharField(max_length=512, default="")
    document_scope = CharField(max_length=512, default="")
    origin_mode = CharField(max_length=32, default="live")
    hit_count = IntegerField(default=0)
    last_used_at = BigIntegerField(default=0)
    created_at = BigIntegerField(default=0)
    embedding = BlobField(null=True)

    class Meta:
        database = db
        indexes = (
            (
                (
                    "translate_engine",
                    "translate_engine_params",
                    "source_hash_norm",
                    "glossary_signature",
                ),
                False,
            ),
            (
                (
                    "translate_engine",
                    "translate_engine_params",
                    "document_scope",
                    "project_scope",
                ),
                False,
            ),
        )
        constraints = [
            SQL(
                """
            UNIQUE (
                translate_engine,
                translate_engine_params,
                source_hash_raw,
                glossary_signature,
                project_scope,
                document_scope
                )
            ON CONFLICT REPLACE
            """
            ),
        ]


@dataclass
class TmLookupResult:
    translation: str | None
    layer: str  # legacy_exact | normalized | fuzzy | semantic | miss


def _tm_insert_replace(**kwargs) -> None:
    """Insert or replace a TM row (SQLite UNIQUE ... ON CONFLICT REPLACE)."""
    _TmEntry.insert(**kwargs).on_conflict_replace().execute()


class TranslationCache:
    @staticmethod
    def _sort_dict_recursively(obj):
        if isinstance(obj, dict):
            return {
                k: TranslationCache._sort_dict_recursively(v)
                for k in sorted(obj.keys())
                for v in [obj[k]]
            }
        elif isinstance(obj, list):
            return [TranslationCache._sort_dict_recursively(item) for item in obj]
        return obj

    def __init__(self, translate_engine: str, translate_engine_params: dict = None):
        self.translate_engine = translate_engine
        self.replace_params(translate_engine_params)
        self.tm_runtime = TMRuntimeConfig()
        self._document_scope = ""
        self._project_scope = ""
        self._glossary_signature = ""
        self._glossary_pairs: list[tuple[str, str]] = []
        self._semantic_backend = None  # lazy

    def configure_tm_runtime(
        self,
        *,
        tm_runtime: TMRuntimeConfig,
        document_scope: str,
        project_scope: str,
        glossary_signature: str,
        glossary_pairs: list[tuple[str, str]],
    ) -> None:
        self.tm_runtime = tm_runtime
        self._document_scope = document_scope or ""
        self._project_scope = project_scope or ""
        self._glossary_signature = glossary_signature or ""
        self._glossary_pairs = list(glossary_pairs or [])
        # Segregate legacy exact cache when glossary set changes.
        self.add_params("tm_glossary_signature", self._glossary_signature)
        if tm_runtime.mode == TMMode.SEMANTIC and self._semantic_backend is None:
            self._semantic_backend = try_create_semantic_backend(
                tm_runtime.embedding_model,
            )
        elif tm_runtime.mode != TMMode.SEMANTIC:
            self._semantic_backend = None

    def replace_params(self, params: dict = None):
        if params is None:
            params = {}
        self.params = params
        params = self._sort_dict_recursively(params)
        self.translate_engine_params = json.dumps(params)

    def update_params(self, params: dict = None):
        if params is None:
            params = {}
        self.params.update(params)
        self.replace_params(self.params)

    def add_params(self, k: str, v):
        self.params[k] = v
        self.replace_params(self.params)

    def _langs(self) -> tuple[str, str]:
        li = str(self.params.get("lang_in", ""))
        lo = str(self.params.get("lang_out", ""))
        return li, lo

    def _scope_where(self, query):
        """Restrict TM rows by reuse scope."""
        scope = self.tm_runtime.scope
        doc = self._document_scope
        proj = self._project_scope
        if scope == TMScope.DOCUMENT:
            return query.where(_TmEntry.document_scope == doc)
        if scope == TMScope.PROJECT:
            return query.where(
                (_TmEntry.document_scope == doc)
                | (_TmEntry.project_scope == proj)
                | ((_TmEntry.document_scope == "") & (_TmEntry.project_scope == "")),
            )
        return query

    def get(self, original_text: str) -> str | None:
        res = self.lookup(original_text)
        return res.translation

    def lookup(self, original_text: str) -> TmLookupResult:
        """Layered TM lookup; legacy exact first."""
        # L1 legacy exact
        try:
            result = _TranslationCache.get_or_none(
                translate_engine=self.translate_engine,
                translate_engine_params=self.translate_engine_params,
                original_text=original_text,
            )
            if result:
                if self.tm_runtime.mode != TMMode.OFF:
                    self._touch_tm_by_raw_hash(stable_hash(original_text))
                if random.random() < CLEAN_PROBABILITY:  # noqa: S311
                    self._cleanup()
                return TmLookupResult(result.translation, "legacy_exact")

            if self.tm_runtime.mode == TMMode.OFF:
                if random.random() < CLEAN_PROBABILITY:  # noqa: S311
                    self._cleanup()
                return TmLookupResult(None, "miss")

            li, lo = self._langs()
            norm = normalize_for_tm(original_text, lang_in=li)
            h_norm = stable_hash(norm)
            h_raw = stable_hash(original_text)

            # L1b normalized exact (stored row may differ in raw whitespace)
            q = _TmEntry.select().where(
                (_TmEntry.translate_engine == self.translate_engine)
                & (_TmEntry.translate_engine_params == self.translate_engine_params)
                & (_TmEntry.source_hash_norm == h_norm)
                & (_TmEntry.glossary_signature == self._glossary_signature)
            )
            q = self._scope_where(q)
            row = q.order_by(_TmEntry.last_used_at.desc()).first()
            if row:
                if self._safe_to_reuse(
                    original_text,
                    row.source_text_raw,
                    row.target_text,
                    layer="normalized",
                ):
                    self._bump_tm_hit(row)
                    self._maybe_tm_cleanup()
                    return TmLookupResult(row.target_text, "normalized")

            if self.tm_runtime.mode not in (TMMode.FUZZY, TMMode.SEMANTIC):
                self._maybe_tm_cleanup()
                return TmLookupResult(None, "miss")

            if not segment_long_enough(
                original_text,
                self.tm_runtime.min_segment_chars,
            ):
                return TmLookupResult(None, "miss")

            # L2 fuzzy
            fuzzy_hit = self._fuzzy_lookup(original_text, norm)
            if fuzzy_hit:
                self._maybe_tm_cleanup()
                return fuzzy_hit

            # L3 semantic
            if (
                self.tm_runtime.mode == TMMode.SEMANTIC
                and self._semantic_backend
                and self._semantic_backend.available
            ):
                sem = self._semantic_lookup(original_text)
                if sem:
                    self._maybe_tm_cleanup()
                    return sem

            self._maybe_tm_cleanup()
            return TmLookupResult(None, "miss")
        except peewee.OperationalError as e:
            if "database is locked" in str(e):
                logger.debug("Cache is locked")
                return TmLookupResult(None, "miss")
            raise

    def _safe_to_reuse(
        self,
        query_raw: str,
        cand_raw: str,
        cand_tgt: str,
        *,
        layer: str,
    ) -> bool:
        if not placeholders_compatible(query_raw, cand_raw, cand_tgt):
            return False
        if not glossary_compatible(query_raw, cand_tgt, self._glossary_pairs):
            return False
        _ = layer
        return True

    def _fuzzy_lookup(self, original_text: str, norm: str) -> TmLookupResult | None:
        try:
            from rapidfuzz import fuzz
            from rapidfuzz import process
        except ImportError:
            logger.debug("rapidfuzz not installed; fuzzy TM disabled")
            return None

        q = _TmEntry.select().where(
            (_TmEntry.translate_engine == self.translate_engine)
            & (_TmEntry.translate_engine_params == self.translate_engine_params)
            & (_TmEntry.glossary_signature == self._glossary_signature)
        )
        q = self._scope_where(q)
        rows = list(
            q.order_by(_TmEntry.last_used_at.desc()).limit(
                self.tm_runtime.fuzzy_candidate_limit,
            ),
        )
        if not rows:
            return None

        choices = [(r.source_text_norm, r) for r in rows]
        proc_norm = norm
        best = process.extractOne(
            proc_norm,
            [c[0] for c in choices],
            scorer=fuzz.WRatio,
            score_cutoff=self.tm_runtime.fuzzy_min_score,
        )
        if not best:
            return None
        _match_s, score, idx = best
        row = rows[idx]
        if not self._safe_to_reuse(
            original_text, row.source_text_raw, row.target_text, layer="fuzzy"
        ):
            return None
        logger.debug("TM fuzzy hit score=%s id=%s", score, row.id)
        self._bump_tm_hit(row)
        return TmLookupResult(row.target_text, "fuzzy")

    def _semantic_lookup(self, original_text: str) -> TmLookupResult | None:
        be = self._semantic_backend
        if not be or not be.available:
            return None
        q_emb = be.encode([original_text])
        if q_emb.size == 0:
            return None
        qv = q_emb[0]

        q = _TmEntry.select().where(
            (_TmEntry.translate_engine == self.translate_engine)
            & (_TmEntry.translate_engine_params == self.translate_engine_params)
            & (_TmEntry.glossary_signature == self._glossary_signature)
            & (_TmEntry.embedding.is_null(False))
        )
        q = self._scope_where(q)
        rows = list(q.order_by(_TmEntry.last_used_at.desc()).limit(400))
        best_row = None
        best_sim = -1.0
        for row in rows:
            try:
                vec = deserialize_embedding_f32(bytes(row.embedding))
            except Exception:
                continue
            if vec.shape[0] != qv.shape[0]:
                continue
            sim = cosine_similarity(qv, vec)
            if sim > best_sim:
                best_sim = sim
                best_row = row
        if best_row is None or best_sim < self.tm_runtime.semantic_min_similarity:
            return None
        if not self._safe_to_reuse(
            original_text,
            best_row.source_text_raw,
            best_row.target_text,
            layer="semantic",
        ):
            return None
        logger.debug("TM semantic hit sim=%s id=%s", best_sim, best_row.id)
        self._bump_tm_hit(best_row)
        return TmLookupResult(best_row.target_text, "semantic")

    def _touch_tm_by_raw_hash(self, raw_hash: str) -> None:
        try:
            q = _TmEntry.update(
                hit_count=_TmEntry.hit_count + 1,
                last_used_at=_now_ms(),
            ).where(
                (_TmEntry.translate_engine == self.translate_engine)
                & (_TmEntry.translate_engine_params == self.translate_engine_params)
                & (_TmEntry.source_hash_raw == raw_hash)
                & (_TmEntry.glossary_signature == self._glossary_signature),
            )
            q.execute()
        except peewee.OperationalError as e:
            if "database is locked" not in str(e):
                raise

    def _bump_tm_hit(self, row: _TmEntry) -> None:
        try:
            _TmEntry.update(
                hit_count=_TmEntry.hit_count + 1,
                last_used_at=_now_ms(),
            ).where(_TmEntry.id == row.id).execute()
        except peewee.OperationalError as e:
            if "database is locked" not in str(e):
                raise

    def promote_to_legacy_exact(self, original_text: str, translation: str) -> None:
        """Persist an L1 exact row when reuse came from TM (fuzzy/normalized/semantic)."""
        try:
            _TranslationCache.create(
                translate_engine=self.translate_engine,
                translate_engine_params=self.translate_engine_params,
                original_text=original_text,
                translation=translation,
            )
        except peewee.OperationalError as e:
            if "database is locked" not in str(e):
                raise

    def set(self, original_text: str, translation: str):
        try:
            _TranslationCache.create(
                translate_engine=self.translate_engine,
                translate_engine_params=self.translate_engine_params,
                original_text=original_text,
                translation=translation,
            )
            if self.tm_runtime.mode != TMMode.OFF:
                with _tm_cleanup_lock:
                    self._tm_upsert(
                        original_text,
                        translation,
                        origin_mode="live",
                        store_embedding=self.tm_runtime.mode == TMMode.SEMANTIC,
                    )
                    if random.random() < CLEAN_PROBABILITY:  # noqa: S311
                        self._cleanup()
                    self._bump_tm_write_and_cleanup()
            else:
                if random.random() < CLEAN_PROBABILITY:  # noqa: S311
                    self._cleanup()
                self._bump_tm_write_and_cleanup()
        except peewee.OperationalError as e:
            if "database is locked" in str(e):
                logger.debug("Cache is locked")
            else:
                raise

    def _tm_upsert(
        self,
        original_text: str,
        translation: str,
        *,
        origin_mode: str,
        store_embedding: bool = False,
    ) -> None:
        li, lo = self._langs()
        norm = normalize_for_tm(original_text, lang_in=li)
        ph = placeholder_signature(original_text)[:64]
        now = _now_ms()
        emb_blob = None
        if (
            store_embedding
            and self._semantic_backend
            and self._semantic_backend.available
        ):
            try:
                vec = self._semantic_backend.encode([original_text])[0]
                emb_blob = serialize_embedding_f32(vec)
            except Exception:
                logger.debug("TM embedding encode failed", exc_info=True)

        try:
            _tm_insert_replace(
                translate_engine=self.translate_engine,
                translate_engine_params=self.translate_engine_params,
                lang_in=li,
                lang_out=lo,
                source_text_raw=original_text,
                source_text_norm=norm,
                target_text=translation,
                source_hash_raw=stable_hash(original_text),
                source_hash_norm=stable_hash(norm),
                placeholder_signature=ph,
                glossary_signature=self._glossary_signature,
                project_scope=self._project_scope,
                document_scope=self._document_scope,
                origin_mode=origin_mode,
                hit_count=0,
                last_used_at=now,
                created_at=now,
                embedding=emb_blob,
            )
        except peewee.OperationalError as e:
            if "database is locked" in str(e):
                logger.debug("TM DB is locked on upsert")
            else:
                raise

    def _maybe_tm_cleanup(self) -> None:
        self._bump_tm_write_and_cleanup()

    def _bump_tm_write_and_cleanup(self) -> None:
        global _tm_write_counter
        if self.tm_runtime.mode == TMMode.OFF:
            return
        with _tm_write_counter_lock:
            _tm_write_counter += 1
            n = _tm_write_counter
        every = max(1, self.tm_runtime.cleanup_every_n_writes)
        if n % every != 0:
            return
        self._tm_cleanup()

    def _tm_cleanup(self) -> None:
        with _tm_cleanup_lock:
            max_id = _TmEntry.select(fn.MAX(_TmEntry.id)).scalar()
            cap = self.tm_runtime.max_tm_rows
            if not max_id or max_id <= cap:
                return
            threshold = max_id - cap
            logger.info("Cleaning up translation memory (trim ids <= %s)", threshold)
            _TmEntry.delete().where(_TmEntry.id <= threshold).execute()

    def _cleanup(self) -> None:
        if not _cleanup_lock.acquire(blocking=False):
            return
        try:
            logger.info("Cleaning up translation cache...")
            max_id = _TranslationCache.select(fn.MAX(_TranslationCache.id)).scalar()
            if not max_id or max_id <= MAX_CACHE_ROWS:
                return
            threshold = max_id - MAX_CACHE_ROWS
            _TranslationCache.delete().where(
                _TranslationCache.id <= threshold,
            ).execute()
        finally:
            _cleanup_lock.release()

    def export_tm_ndjson(self, path: Path) -> int:
        """Export TM rows for this engine+fingerprint to NDJSON."""
        n = 0
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for row in _TmEntry.select().where(
                (_TmEntry.translate_engine == self.translate_engine)
                & (_TmEntry.translate_engine_params == self.translate_engine_params),
            ):
                rec = {
                    "translate_engine": row.translate_engine,
                    "translate_engine_params": row.translate_engine_params,
                    "lang_in": row.lang_in,
                    "lang_out": row.lang_out,
                    "source_text_raw": row.source_text_raw,
                    "source_text_norm": row.source_text_norm,
                    "target_text": row.target_text,
                    "placeholder_signature": row.placeholder_signature,
                    "glossary_signature": row.glossary_signature,
                    "project_scope": row.project_scope,
                    "document_scope": row.document_scope,
                    "origin_mode": row.origin_mode,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
        logger.info("Exported %s TM rows to %s", n, path)
        return n

    def import_tm_ndjson(self, path: Path) -> int:
        """Import NDJSON lines into TM (respects unique constraint)."""
        path = Path(path)
        if not path.is_file():
            return 0
        n = 0
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                li = rec.get("lang_in", "")
                lo = rec.get("lang_out", "")
                raw = rec["source_text_raw"]
                tgt = rec["target_text"]
                norm = rec.get("source_text_norm") or normalize_for_tm(raw, lang_in=li)
                now = _now_ms()
                try:
                    _tm_insert_replace(
                        translate_engine=rec.get(
                            "translate_engine",
                            self.translate_engine,
                        ),
                        translate_engine_params=rec.get(
                            "translate_engine_params",
                            self.translate_engine_params,
                        ),
                        lang_in=li,
                        lang_out=lo,
                        source_text_raw=raw,
                        source_text_norm=norm,
                        target_text=tgt,
                        source_hash_raw=stable_hash(raw),
                        source_hash_norm=stable_hash(norm),
                        placeholder_signature=str(rec.get("placeholder_signature", ""))[
                            :64
                        ],
                        glossary_signature=str(rec.get("glossary_signature", ""))[:64],
                        project_scope=str(rec.get("project_scope", ""))[:512],
                        document_scope=str(rec.get("document_scope", ""))[:512],
                        origin_mode=str(rec.get("origin_mode", "import"))[:32],
                        hit_count=0,
                        last_used_at=now,
                        created_at=now,
                        embedding=None,
                    )
                    n += 1
                except peewee.OperationalError as e:
                    if "database is locked" in str(e):
                        logger.debug("TM import locked, stopping")
                        break
                    raise
        logger.info("Imported %s TM rows from %s", n, path)
        return n


def _now_ms() -> int:
    return int(time.time() * 1000)


def _run_legacy_migration_if_needed() -> None:
    """One-time import from ``cache.v1.db`` if present (separate legacy file only)."""
    marker = "legacy_cache_v1_import"
    if _TmMigration.get_or_none(_TmMigration.name == marker):
        return

    v1 = CACHE_FOLDER / "cache.v1.db"
    if not v1.is_file():
        return

    def _insert(
        engine,
        params_json,
        raw,
        norm,
        raw_h,
        norm_h,
        tgt,
        ph_sig,
        gloss_sig,
        project_scope,
        document_scope,
        origin_mode,
    ):
        now = _now_ms()
        try:
            pobj = json.loads(params_json)
            li = str(pobj.get("lang_in", ""))
            lo = str(pobj.get("lang_out", ""))
        except Exception:
            li, lo = "", ""
        try:
            _tm_insert_replace(
                translate_engine=engine,
                translate_engine_params=params_json,
                lang_in=li,
                lang_out=lo,
                source_text_raw=raw,
                source_text_norm=norm,
                target_text=tgt,
                source_hash_raw=raw_h,
                source_hash_norm=norm_h,
                placeholder_signature=ph_sig[:64] if ph_sig else "",
                glossary_signature=gloss_sig[:64] if gloss_sig else "",
                project_scope=project_scope[:512] if project_scope else "",
                document_scope=document_scope[:512] if document_scope else "",
                origin_mode=origin_mode[:32],
                hit_count=0,
                last_used_at=now,
                created_at=now,
                embedding=None,
            )
        except peewee.OperationalError:
            logger.debug("TM migration row insert skipped", exc_info=True)

    migrate_legacy_sqlite_into_tm(v1, _insert, mark="legacy_v1")
    _TmMigration.insert(
        name=marker,
        applied_at=_now_ms(),
    ).on_conflict_replace().execute()


def init_db(remove_exists=False):
    CACHE_FOLDER.mkdir(parents=True, exist_ok=True)
    cache_db_path = CACHE_FOLDER / LEGACY_DB_FILENAME
    logger.info("Initializing cache database at %s", cache_db_path)
    if remove_exists and cache_db_path.exists():
        cache_db_path.unlink()
    db.init(
        cache_db_path,
        pragmas={
            "journal_mode": "wal",
            "busy_timeout": 2000,
        },
    )
    db.create_tables([_TranslationCache, _TmEntry, _TmMigration], safe=True)


def init_test_db():
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    cache_db_path = temp_file.name
    temp_file.close()

    test_db = SqliteDatabase(
        cache_db_path,
        pragmas={
            "journal_mode": "wal",
            "busy_timeout": 1000,
        },
    )
    test_db.bind(
        [_TranslationCache, _TmEntry, _TmMigration],
        bind_refs=False,
        bind_backrefs=False,
    )
    test_db.connect()
    test_db.create_tables([_TranslationCache, _TmEntry, _TmMigration], safe=True)
    return test_db


def clean_test_db(test_db):
    test_db.drop_tables([_TranslationCache, _TmEntry, _TmMigration])
    test_db.close()
    db_path = Path(test_db.database)
    if db_path.exists():
        db_path.unlink()
    for suf in ("-wal", "-shm"):
        wp = Path(str(db_path) + suf)
        if wp.exists():
            wp.unlink()


# Module init: production DBs
init_db()


def glossary_signature_from_pairs(pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        return ""
    norm = sorted({(a.strip(), b.strip()) for a, b in pairs if a and b})
    payload = json.dumps(norm, ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def flatten_glossary_entries_from_config(cfg) -> list[tuple[str, str]]:
    """Collect (source, target) pairs from translation config glossaries."""
    out: list[tuple[str, str]] = []
    sc = getattr(cfg, "shared_context_cross_split_part", None)
    if not sc:
        return out
    for g in sc.get_glossaries():
        for e in getattr(g, "entries", []) or []:
            out.append((e.source, e.target))
    return out
