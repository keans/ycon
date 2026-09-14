"""Ed25519-sign and verify a validated config model.

Requires the optional `signing` extra (`pynacl`): install with
`pip install ycon[signing]` or `uv add ycon[signing]`. Not imported by
`ycon/__init__.py`, so the core package has no hard dependency on it.
"""

import json
from typing import Self

from pydantic import BaseModel

try:
    from nacl.exceptions import BadSignatureError
    from nacl.signing import SigningKey, VerifyKey
except ImportError as exc:
    raise ImportError(
        "ycon.signing requires the optional 'signing' extra: install "
        "with `pip install ycon[signing]` (or `uv add ycon[signing]`)"
    ) from exc


def _canonical_bytes(data) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


class SignableModel(BaseModel):
    """Pydantic model with canonical serialization and Ed25519 signing.

    Subclass this like any `BaseModel` (e.g. as the model passed to
    `ycon.load_config()`) to sign or verify a validated configuration.
    """

    def canonical_bytes(self) -> bytes:
        """Serialize to sorted, separator-minimal JSON for signing."""
        return _canonical_bytes(self.model_dump(mode="json"))

    def sign(self, signing_key: SigningKey) -> bytes:
        """Sign the canonical serialization and return the signature."""
        return signing_key.sign(self.canonical_bytes()).signature

    def verify(self, verify_key: VerifyKey, signature: bytes) -> bool:
        """Return whether `signature` matches the canonical serialization."""
        if not isinstance(signature, bytes) or len(signature) != 64:
            return False
        try:
            verify_key.verify(self.canonical_bytes(), signature)
            return True
        except BadSignatureError:
            return False

    def to_signed_bundle(self, signing_key: SigningKey) -> dict:
        """Sign this model and return a JSON-serializable signed bundle."""
        # Serialize once so custom serializers cannot change the payload.
        payload = self.model_dump(mode="json")
        sig = signing_key.sign(_canonical_bytes(payload)).signature
        return {
            "payload": payload,
            "signature": sig.hex(),
            "signer_pubkey": signing_key.verify_key.encode().hex(),
        }

    @classmethod
    def from_signed_bundle(cls, bundle: dict, verify_key: VerifyKey) -> Self:
        """Verify the received payload before validating it as this model."""
        try:
            payload = bundle["payload"]
            sig = bytes.fromhex(bundle["signature"])
            signer = bytes.fromhex(bundle["signer_pubkey"])
            if len(sig) != 64 or signer != verify_key.encode():
                raise ValueError("Invalid signature or signer")
            # Pydantic coercion and defaults must not hide payload changes.
            verify_key.verify(_canonical_bytes(payload), sig)
        except (KeyError, TypeError, ValueError, BadSignatureError) as exc:
            raise ValueError(
                "Signature verification failed — config may be tampered"
            ) from exc
        return cls.model_validate(payload)
