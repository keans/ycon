# 1. Basic loading

The simplest possible use of ycon: a plain YAML file, no `!include`,
no `!ref`, no defaults.

```bash
uv run python examples/01_basic_loading/run.py
```

Expected output:

```
{'app_name': 'demo-service', 'debug': False, 'port': 8080}
```
