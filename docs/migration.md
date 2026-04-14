# Migration and compatibility

## TOML configuration section

The CLI and nested translator configuration use the **`[doctranslate]`** table in TOML files.

**Legacy:** configs that used **`[babeldoc]`** (same schema) are still read for nested router/local settings when **`[doctranslate]`** is absent. Prefer `[doctranslate]` for new files.

CLI flags loaded from a config file merge sections in this order: **`babeldoc` first, then `doctranslate`** (later keys win). Use only one section to avoid surprises.

## Cache directory

Runtime cache defaults to `~/.cache/doctranslate`. There is no automatic migration from other tool cache folders; clear or ignore old directories if you are switching machines.

## Console entry points

The primary CLI is **`doctranslate`**. An additional kebab-case alias **`doc-translate`** may be installed for the same entry point (see `pyproject.toml` `[project.scripts]`).

## Upstream

This repository is a fork of [funstory-ai/DocTranslate](https://github.com/funstory-ai/DocTranslate). Issue links in older docs may still reference upstream; use [miguelenes/doctranslate issues](https://github.com/miguelenes/doctranslate/issues) for this fork.
