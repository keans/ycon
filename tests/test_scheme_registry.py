import pytest

from ycon import load, register_scheme, unregister_scheme, using_scheme
from ycon.includes import resolve_include


def test_register_scheme_handles_matching_uris():
    register_scheme("secret", lambda uri: {"value": f"resolved:{uri}"})
    try:
        assert resolve_include("secret://name") == {
            "value": "resolved:secret://name"
        }
    finally:
        unregister_scheme("secret")


def test_register_scheme_can_override_db(tmp_path):
    register_scheme("db", lambda uri: {"record": uri})
    try:
        path = tmp_path / "config.yaml"
        path.write_text("value: !include db://record1\n")
        assert load(path) == {"value": {"record": "db://record1"}}
    finally:
        unregister_scheme("db")


def test_unregistered_custom_scheme_still_raises():
    with pytest.raises(ValueError, match="Unsupported scheme: nope"):
        resolve_include("nope://x")


def test_unregister_missing_scheme_raises_key_error():
    with pytest.raises(KeyError):
        unregister_scheme("never-registered")


def test_using_scheme_is_scoped_and_restores_on_exit():
    with using_scheme("secret", lambda uri: {"scoped": uri}):
        assert resolve_include("secret://x") == {"scoped": "secret://x"}
    with pytest.raises(ValueError, match="Unsupported scheme: secret"):
        resolve_include("secret://x")


def test_using_scheme_restores_previous_handler_and_survives_error():
    register_scheme("db", lambda uri: {"outer": uri})
    try:
        with (
            pytest.raises(RuntimeError),
            using_scheme("db", lambda uri: {"inner": uri}),
        ):
            assert resolve_include("db://x") == {"inner": "db://x"}
            raise RuntimeError("boom")
        assert resolve_include("db://x") == {"outer": "db://x"}
    finally:
        unregister_scheme("db")
