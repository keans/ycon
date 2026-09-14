# 2. Includes and references

Shows the two custom tags working together:

- `!include db_settings.yaml` pulls in another file.
- `!ref database.host` reaches into that included content — refs are
  resolved after all includes are expanded, so this works even though
  `database` only exists because of an include.
- `!include env://YCON_EXAMPLE_API_KEY` reads an environment variable.

```bash
uv run python examples/02_includes_and_refs/run.py
```

Expected output:

```
{'database': {'host': 'localhost', 'port': 5432}, 'connection_string': 'localhost', 'api_key': {'value': 'demo-key-123'}}
```
