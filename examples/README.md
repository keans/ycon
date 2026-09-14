# ycon examples

Runnable examples ordered by increasing difficulty. Each subfolder
has its own README with details and expected output.

| # | Folder | Covers |
|---|--------|--------|
| 1 | [`01_basic_loading`](01_basic_loading/) | Plain `load()`, no tags |
| 2 | [`02_includes_and_refs`](02_includes_and_refs/) | `!include` (file, env) and `!ref` |
| 3 | [`03_defaults_and_validation`](03_defaults_and_validation/) | `defaults=` merging and `load_config()` with pydantic |
| 4 | [`04_advanced_gzip_and_resolve`](04_advanced_gzip_and_resolve/) | `.yaml.gz` includes and `resolve_to_file()` |
| 5 | [`05_signed_config`](05_signed_config/) | Signing/verifying a validated config with `ycon.signing` (optional extra) |

Run any example from the repository root with:

```bash
uv run python examples/<folder>/run.py
```
