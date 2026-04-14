# DocTranslate Fork Implementation Guide

This guide walks you through verifying the forked package, applying architectural improvements, ensuring legal compliance, and initializing a clean Git repository.

---

## Table of Contents
1. [Step 1: Verify package and CLI](#step-1-verify-package-and-cli)
2. [Step 2: Architecture Improvements](#step-2-architecture-improvements)
3. [Step 3: AGPL Compliance](#step-3-agpl-compliance)
4. [Step 4: Clean Git Initialization (Option B)](#step-4-clean-git-initialization-option-b)
5. [Verification Checklist](#verification-checklist)

---

## Step 1: Safe Rebranding

### Overview
The `rebrand.py` script safely replaces all "DocTranslate"/"doctranslate" references with "DocTranslate"/"doctranslate" while preserving code functionality.

### Execute Rebranding

**1.1 Preview changes (dry-run)**
```bash
cd /home/menes/Projects/DocTranslate
python rebrand.py --dry-run
```

Output will show:
- All files that will be modified
- Directory renames (doctranslate/ → doctranslate/)
- Count of replacements per file

**1.2 Apply changes**
```bash
python rebrand.py --apply
```

This will:
- Replace all "DocTranslate" → "DocTranslate" in code/docs
- Replace all "doctranslate" → "doctranslate" in code/imports/paths
- Rename `doctranslate/` → `doctranslate/`
- Rename `babeldoc_exception/` → `doctranslate_exception/`
- Update `pyproject.toml` script entry point

**1.3 Verify rebranding**
```bash
# Check for remaining old names (should be minimal — only in .git history)
grep -r "doctranslate" . --include="*.py" --include="*.toml" --include="*.md" 2>/dev/null | grep -v ".git" | head -20

# Verify package is importable
python -c "import doctranslate; print(f'✓ Version: {doctranslate.__version__}')"

# Verify CLI works
pip install -e .
doctranslate --help
doctranslate --version
```

Expected output:
```
✓ Version: 0.5.24
usage: doctranslate [-h] [-v] [--config CONFIG_FILE] ...
```

---

## Step 2: Architecture Improvements

### New Multi-Translator Router

**2.1 File created:** `doctranslate/translator/router.py`

This adds:
- `TranslatorRouter`: Main routing orchestrator
- `RouterStrategy` enum: FAILOVER, ROUND_ROBIN, LEAST_LOADED, COST_AWARE
- `TranslatorMetrics`: Per-backend monitoring
- `QualityScorer` & `SimpleBackTranslationScorer`: Translation quality evaluation

**2.2 Integration example**

In your translation code, use the router instead of a single translator:

```python
from doctranslate.translator.router import TranslatorRouter, RouterStrategy
from doctranslate.translator import OpenAITranslator

# Create router with multiple backends
router = TranslatorRouter([
    OpenAITranslator(model="gpt-4", api_key="sk-..."),
    # Add more translators here (Anthropic, local Ollama, etc.)
])

# Set strategy
router.set_strategy(RouterStrategy.FAILOVER)  # Try first, fallback on error

# Use it like a normal translator
config = TranslationConfig(
    translator=router,  # Pass router instead of single translator
    # ... other config
)
```

**2.3 Configuration in TOML**

To enable multi-translator routing in config:

```toml
[doctranslate]
translator = "router"  # Signals to use multi-translator mode
strategy = "failover"  # or: round_robin, least_loaded, cost_aware

# Backend 1: OpenAI (primary)
openai_api_key = "sk-..."
openai_model = "gpt-4"

# Backend 2: Anthropic (fallback)
anthropic_api_key = "sk-ant-..."
anthropic_model = "claude-3-opus"
```

**2.4 Test the router**

```python
from doctranslate.translator.router import TranslatorRouter
from doctranslate.translator import OpenAITranslator
import asyncio

async def test_router():
    router = TranslatorRouter([
        OpenAITranslator(api_key="sk-...", model="gpt-4"),
    ])
    
    result = await router.translate("Hello", "en", "es")
    print(f"Translation: {result}")
    print(router.print_metrics())

asyncio.run(test_router())
```

---

## Step 3: AGPL Compliance

### Files already created:
- ✅ `LICENSE` (original, unchanged)
- ✅ `LICENSE.ADDITIONS` (new, documents modifications)
- ✅ `NOTICE` (new, formal attribution)
- ✅ `README_TEMPLATE.md` (new, with attribution section)

### 3.1 Update README.md

Replace the current `README.md` with content based on `README_TEMPLATE.md`:

```bash
# Backup original
cp README.md README_BABELDOC.md

# Use template as starting point (you'll customize it)
cp README_TEMPLATE.md README.md

# Edit and customize for your needs
nano README.md  # Add your own sections, examples, etc.
```

Key sections to maintain in your README:
- Attribution to DocTranslate (with link to original)
- Link to `LICENSE.ADDITIONS`
- List of what's new vs. original
- Compliance note about AGPL network use clause

### 3.2 Verify legal files

Check that all legal files exist and are in root:

```bash
ls -la LICENSE* NOTICE README.md

# Expected output:
# -rw-r--r-- LICENSE
# -rw-r--r-- LICENSE.ADDITIONS
# -rw-r--r-- NOTICE
# -rw-r--r-- README.md
```

### 3.3 Copyright headers in modified files

For files you significantly modified, add copyright headers:

```python
# Copyright (C) 2024 funstory-ai Limited
# Copyright (C) 2025 Miguel Enes — Modified: Multi-translator router, docs
# License: GNU Affero General Public License v3.0 (see LICENSE)
```

Example: Top of `doctranslate/translator/router.py` already includes this.

### 3.4 AGPL Compliance Checklist

- ✅ Original LICENSE file preserved (funstory-ai copyright)
- ✅ New LICENSE.ADDITIONS file created
- ✅ NOTICE file created with attribution
- ✅ README includes attribution section
- ✅ Copyright headers on modified files
- ✅ Link to original repository
- ✅ If service: promise to provide source to users

---

## Step 4: Clean Git Initialization (Option B)

This creates a fresh Git history while maintaining legal compliance.

### 4.1 Verify all changes are applied

Before proceeding, confirm:
- Rebranding script has run (`--apply`)
- All documentation updated
- Legal files in place

```bash
# Double-check
ls -la LICENSE* NOTICE doctranslate/ README.md
```

### 4.2 Create orphan branch

```bash
# From your current main branch (after all changes are committed locally)
git checkout --orphan fresh-main
```

This creates a new branch with no history.

### 4.3 Stage all files

```bash
git add -A
```

### 4.4 Create initial commit

```bash
git commit -m "Initial commit: DocTranslate based on DocTranslate v0.5.24

This is a customized fork of DocTranslate (https://github.com/funstory-ai/DocTranslate)
created by Miguel Enes.

Key additions:
- Multi-translator orchestration engine (doctranslate/translator/router.py)
- Rebranding (user-facing CLI, documentation)

DocTranslate is licensed under AGPL-3.0. This derivative maintains the same license.
See LICENSE, LICENSE.ADDITIONS, and NOTICE for full attribution.
"
```

### 4.5 Delete old branch and rename new one

```bash
# Delete the old history
git branch -D main

# Rename the orphan branch to main
git branch -m fresh-main main
```

Verify:
```bash
git log --oneline
# Output: Should show only your new initial commit
```

### 4.6 Add your remote

```bash
# Update remote URL to your GitHub repo
git remote set-url origin git@github.com:YOUR_USERNAME/doctranslate.git

# Verify remote
git remote -v
# Output:
# origin	git@github.com:YOUR_USERNAME/doctranslate.git (fetch)
# origin	git@github.com:YOUR_USERNAME/doctranslate.git (push)
```

### 4.7 Push to GitHub

```bash
# Force push (necessary for orphan branch)
git push -u origin main --force
```

### 4.8 Verify on GitHub

- Visit: `https://github.com/YOUR_USERNAME/doctranslate`
- Check:
  - Repository shows as "1 commit"
  - Initial commit message includes DocTranslate attribution
  - All files present (LICENSE, LICENSE.ADDITIONS, NOTICE, etc.)
  - README shows your custom content with attribution section

---

## Verification Checklist

### Code Quality
- [ ] `python -c "import doctranslate; print(doctranslate.__version__)"` ✓
- [ ] `doctranslate --help` runs without errors ✓
- [ ] `pip install -e .` succeeds ✓
- [ ] `pytest tests/` passes (if tests exist) ✓

### Rebranding
- [ ] All "DocTranslate" references changed to "DocTranslate" ✓
- [ ] All "doctranslate" references changed to "doctranslate" ✓
- [ ] CLI command is `doctranslate` (not `doctranslate`) ✓
- [ ] Package imports work: `from doctranslate import ...` ✓
- [ ] Cache folder is `~/.cache/doctranslate` (not `doctranslate`) ✓

### Architecture
- [ ] `doctranslate/translator/router.py` exists ✓
- [ ] `TranslatorRouter` class can be imported ✓
- [ ] Router strategies are available ✓
- [ ] Multi-translator routing example runs ✓

### Legal Compliance
- [ ] `LICENSE` file exists (original funstory-ai copyright) ✓
- [ ] `LICENSE.ADDITIONS` file exists ✓
- [ ] `NOTICE` file exists ✓
- [ ] `README.md` includes attribution section ✓
- [ ] Link to original DocTranslate repo in docs ✓
- [ ] Copyright headers on modified files ✓

### Git/Repository
- [ ] `git log --oneline` shows only 1 initial commit ✓
- [ ] Remote URL points to your GitHub ✓
- [ ] Repository is accessible on GitHub ✓
- [ ] All files pushed successfully ✓
- [ ] No `.git` history from DocTranslate remains ✓

### Documentation
- [ ] `README.md` describes DocTranslate (not DocTranslate) ✓
- [ ] Documentation includes multi-translator setup ✓
- [ ] `docs/` folder updated with new branding ✓
- [ ] `mkdocs.yml` has correct site_name ✓

---

## Troubleshooting

### Issue: "Module named 'doctranslate' not found"
**Solution:** Rerun `python rebrand.py --apply` and ensure all import paths updated:
```bash
grep -r "from doctranslate import" . --include="*.py" | grep -v ".git"
# Should return nothing
```

### Issue: `pytest` fails with import errors
**Solution:** Reinstall in development mode:
```bash
pip install -e .
pytest tests/ --tb=short
```

### Issue: Git push fails with "updates were rejected"
**Solution:** Use force push (this is expected for orphan branch):
```bash
git push -u origin main --force
```

### Issue: Old DocTranslate commits still visible
**Solution:** Verify orphan branch was used correctly:
```bash
git log --oneline --all
# Should show only your fresh-main (now main) commit

# If old commits still exist, ensure you deleted the old branch:
git branch -D main   # (if main still exists)
```

---

## Next Steps

1. **Add contributors:** Set up GitHub teams/permissions for your repo
2. **Setup CI/CD:** Add GitHub Actions workflows for testing and documentation
3. **Release:** Create v0.1.0 release with proper changelog
4. **Marketing:** Announce your fork with blog post/social media
5. **Community:** Set up issues/discussions for users

---

## Getting Help

- **GitHub Issues:** Post questions/bugs on your repo
- **License Questions:** See AGPL-3.0 FAQ at https://www.gnu.org/licenses/agpl-3.0.html
- **DocTranslate Original:** https://github.com/funstory-ai/DocTranslate

---

**Guide Version:** 1.0  
**Created:** 2025-04-14  
**For:** DocTranslate (fork of DocTranslate)
