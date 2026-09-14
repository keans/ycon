# 5. Signed config

Loads and validates `config.yaml` with `load_config()`, then signs the
validated model with an Ed25519 key via `ycon.signing.SignableModel`
and verifies it back. Tampering with the signed payload is detected
on `from_signed_bundle()`.

Requires the optional `signing` extra:

```bash
uv sync --extra signing
uv run python examples/05_signed_config/run.py
```

Expected output:

```
name='demo-service' retries=3
tampered bundle rejected: Signature verification failed — config may be tampered
```

In a real deployment the signing key stays with whoever publishes
config; only the corresponding public verify key needs to travel with
the application that loads it.
