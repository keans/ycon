# 3. Defaults and pydantic validation

`config.yaml` only overrides `database.host`; everything else comes
from `defaults.yaml` via deep-merge. The merged result is then
validated against a pydantic model with `load_config()`.

```bash
uv run python examples/03_defaults_and_validation/run.py
```

Expected output:

```
app=App(name='demo-service', retries=3) database=Database(host='production-db.internal', port=5432)
```

Try breaking it: remove `database.port` from `defaults.yaml` and rerun
— `load_config()` raises `pydantic.ValidationError` because `Database`
requires a `port`.
