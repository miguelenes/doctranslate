"""CLI entry and backward-compatible helpers."""

from __future__ import annotations

import logging
import multiprocessing as mp
import queue
import sys

import doctranslate.format.pdf.high_level
from doctranslate.cli.dispatch import main_dispatch
from doctranslate.cli.legacy_parser import create_legacy_parser
from doctranslate.cli.translate_run import run_legacy_translate_pipeline

__version__ = "0.5.24"

logger = logging.getLogger(__name__)

# Tests and external callers expect this symbol on ``main``.
create_parser = create_legacy_parser


async def main() -> None:
    """Legacy entry: flat ``configargparse`` CLI."""
    parser = create_parser()
    args = parser.parse_args()
    await run_legacy_translate_pipeline(parser, args)


class EvictQueue(queue.Queue):
    def __init__(self, maxsize):
        self.discarded = 0
        super().__init__(maxsize)

    def put(self, item, block=False, timeout=None):
        while True:
            try:
                super().put(item, block=False)
                break
            except queue.Full:
                try:
                    self.get_nowait()
                    self.discarded += 1
                except queue.Empty:
                    pass


def speed_up_logs():
    import logging.handlers

    root_logger = logging.getLogger()
    log_que = EvictQueue(1000)
    queue_handler = logging.handlers.QueueHandler(log_que)
    queue_listener = logging.handlers.QueueListener(log_que, *root_logger.handlers)
    queue_listener.start()
    root_logger.handlers = [queue_handler]


def cli():
    """Command line interface entry point."""
    from rich.logging import RichHandler

    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])

    logging.getLogger("httpx").setLevel("CRITICAL")
    logging.getLogger("httpx").propagate = False
    logging.getLogger("openai").setLevel("CRITICAL")
    logging.getLogger("openai").propagate = False
    logging.getLogger("httpcore").setLevel("CRITICAL")
    logging.getLogger("httpcore").propagate = False
    logging.getLogger("http11").setLevel("CRITICAL")
    logging.getLogger("http11").propagate = False
    for v in logging.Logger.manager.loggerDict.values():
        if getattr(v, "name", None) is None:
            continue
        if (
            v.name.startswith("pdfminer")
            or v.name.startswith("peewee")
            or v.name.startswith("httpx")
            or "http11" in v.name
            or "openai" in v.name
            or "pdfminer" in v.name
        ):
            v.disabled = True
            v.propagate = False

    speed_up_logs()
    doctranslate.format.pdf.high_level.init()
    sys.exit(main_dispatch())


# for backward compatibility
def create_cache_folder():
    return doctranslate.format.pdf.high_level.create_cache_folder()


# for backward compatibility
def download_font_assets():
    return doctranslate.format.pdf.high_level.download_font_assets()


if __name__ == "__main__":
    if sys.platform == "darwin" or sys.platform == "win32":
        mp.set_start_method("spawn")
    else:
        mp.set_start_method("forkserver")
    cli()
