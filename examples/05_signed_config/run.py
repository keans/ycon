"""Level 5: signing a validated config and verifying it on load.

Requires the optional `signing` extra: `uv sync --extra signing`.
"""

from pathlib import Path

from nacl.signing import SigningKey

from ycon import load_config
from ycon.signing import SignableModel

HERE = Path(__file__).parent


class Config(SignableModel):
    name: str
    retries: int


# In a real deployment the signing key lives with whoever publishes
# config, and only its public verify key travels with the app that
# reads it.
signing_key = SigningKey.generate()

config = load_config(HERE / "config.yaml", Config)
bundle = config.to_signed_bundle(signing_key)

# ... bundle["payload"] + bundle["signature"] ship together; the
# reader only needs signing_key.verify_key.encode().hex() to check it.
verified = Config.from_signed_bundle(bundle, signing_key.verify_key)
print(verified)

# Tampering with the payload after signing is detected on load.
bundle["payload"]["retries"] = 99
try:
    Config.from_signed_bundle(bundle, signing_key.verify_key)
except ValueError as exc:
    print(f"tampered bundle rejected: {exc}")
