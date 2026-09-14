import pytest

nacl = pytest.importorskip("nacl")

from nacl.signing import SigningKey

from ycon.signing import SignableModel


class Config(SignableModel):
    name: str
    retries: int


def test_sign_and_verify_round_trip():
    key = SigningKey.generate()
    config = Config(name="demo", retries=3)
    sig = config.sign(key)
    assert config.verify(key.verify_key, sig)


def test_verify_rejects_mismatched_data():
    key = SigningKey.generate()
    config = Config(name="demo", retries=3)
    sig = config.sign(key)
    tampered = Config(name="demo", retries=4)
    assert not tampered.verify(key.verify_key, sig)


def test_verify_rejects_wrong_key():
    key = SigningKey.generate()
    other_key = SigningKey.generate()
    config = Config(name="demo", retries=3)
    sig = config.sign(key)
    assert not config.verify(other_key.verify_key, sig)


def test_to_signed_bundle_and_from_signed_bundle_round_trip():
    key = SigningKey.generate()
    config = Config(name="demo", retries=3)
    bundle = config.to_signed_bundle(key)
    restored = Config.from_signed_bundle(bundle, key.verify_key)
    assert restored.model_dump() == config.model_dump()


def test_from_signed_bundle_rejects_tampered_payload():
    key = SigningKey.generate()
    config = Config(name="demo", retries=3)
    bundle = config.to_signed_bundle(key)
    bundle["payload"]["retries"] = 999
    with pytest.raises(ValueError, match="tampered"):
        Config.from_signed_bundle(bundle, key.verify_key)


def test_canonical_bytes_is_deterministic():
    config = Config(name="demo", retries=3)
    assert config.canonical_bytes() == config.canonical_bytes()


@pytest.mark.parametrize("change", ["coercion", "extra", "missing"])
def test_bundle_rejects_payload_changes_hidden_by_validation(change):
    class Defaults(SignableModel):
        retries: int = 3

    key = SigningKey.generate()
    bundle = Defaults().to_signed_bundle(key)
    if change == "coercion":
        bundle["payload"]["retries"] = "3"
    elif change == "extra":
        bundle["payload"]["injected"] = True
    else:
        del bundle["payload"]["retries"]
    with pytest.raises(ValueError, match="tampered"):
        Defaults.from_signed_bundle(bundle, key.verify_key)


def test_bundle_rejects_wrong_trusted_key():
    key = SigningKey.generate()
    bundle = Config(name="demo", retries=3).to_signed_bundle(key)
    with pytest.raises(ValueError):
        Config.from_signed_bundle(bundle, SigningKey.generate().verify_key)


def test_bundle_rejects_replaced_signer_metadata():
    key = SigningKey.generate()
    bundle = Config(name="demo", retries=3).to_signed_bundle(key)
    bundle["signer_pubkey"] = SigningKey.generate().verify_key.encode().hex()
    with pytest.raises(ValueError):
        Config.from_signed_bundle(bundle, key.verify_key)


@pytest.mark.parametrize("signature", [b"", b"short", b"x" * 65, None, "bad"])
def test_verify_returns_false_for_malformed_signatures(signature):
    key = SigningKey.generate()
    assert not Config(name="demo", retries=3).verify(key.verify_key, signature)


@pytest.mark.parametrize("field", ["payload", "signature", "signer_pubkey"])
def test_bundle_rejects_missing_fields(field):
    key = SigningKey.generate()
    bundle = Config(name="demo", retries=3).to_signed_bundle(key)
    del bundle[field]
    with pytest.raises(ValueError):
        Config.from_signed_bundle(bundle, key.verify_key)


@pytest.mark.parametrize("signature", ["not-hex", "00", None, 123])
def test_bundle_rejects_malformed_signatures(signature):
    key = SigningKey.generate()
    bundle = Config(name="demo", retries=3).to_signed_bundle(key)
    bundle["signature"] = signature
    with pytest.raises(ValueError):
        Config.from_signed_bundle(bundle, key.verify_key)


def test_bundle_signs_exactly_the_payload_it_returns():
    from pydantic import model_serializer

    calls = []

    class Dynamic(SignableModel):
        @model_serializer
        def serialize(self):
            calls.append(1)
            return {"counter": len(calls)}

    key = SigningKey.generate()
    bundle = Dynamic().to_signed_bundle(key)
    import json

    encoded = json.dumps(
        bundle["payload"], sort_keys=True, separators=(",", ":")
    ).encode()
    key.verify_key.verify(encoded, bytes.fromhex(bundle["signature"]))
    assert len(calls) == 1


def test_canonical_bytes_sorts_nested_keys_and_survives_json_round_trip():
    import json

    class Nested(SignableModel):
        values: dict[str, int]
        name: str

    key = SigningKey.generate()
    first = Nested(values={"b": 2, "a": 1}, name="grüße")
    second = Nested(values={"a": 1, "b": 2}, name="grüße")
    assert first.canonical_bytes() == second.canonical_bytes()
    bundle = json.loads(json.dumps(first.to_signed_bundle(key)))
    assert Nested.from_signed_bundle(bundle, key.verify_key).model_dump() == (
        second.model_dump()
    )


def test_tampered_bundle_is_rejected_before_model_validators_run():
    from pydantic import model_validator

    calls = []

    class Observed(Config):
        @model_validator(mode="before")
        @classmethod
        def observe(cls, value):
            calls.append(value)
            return value

    key = SigningKey.generate()
    bundle = Config(name="demo", retries=3).to_signed_bundle(key)
    bundle["payload"]["retries"] = 4
    with pytest.raises(ValueError, match="tampered"):
        Observed.from_signed_bundle(bundle, key.verify_key)
    assert calls == []


def test_authentic_bundle_still_requires_valid_model_data():
    from pydantic import ValidationError

    class Other(SignableModel):
        name: str
        retries: str

    key = SigningKey.generate()
    bundle = Other(name="demo", retries="invalid").to_signed_bundle(key)
    with pytest.raises(ValidationError):
        Config.from_signed_bundle(bundle, key.verify_key)


@pytest.mark.parametrize("bundle", [None, [], {}, {"payload": {}}])
def test_malformed_bundle_raises_value_error(bundle):
    with pytest.raises(ValueError, match="verification failed"):
        Config.from_signed_bundle(bundle, SigningKey.generate().verify_key)


def test_signed_config_loaded_with_defaults(tmp_path):
    from ycon import load_config

    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("name: demo\nretries: 3\n")
    path = tmp_path / "config.yaml"
    path.write_text("retries: 5\n")
    config = load_config(path, Config, defaults=defaults)
    key = SigningKey.generate()
    bundle = config.to_signed_bundle(key)
    assert Config.from_signed_bundle(bundle, key.verify_key).model_dump() == {
        "name": "demo",
        "retries": 5,
    }
