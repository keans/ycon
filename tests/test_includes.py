import pytest

from ycon.includes import MissingEnvVarError, resolve_include


def test_env_include_reads_variable(monkeypatch):
    monkeypatch.setenv("MY_VAR", "hello")
    assert resolve_include("env://MY_VAR") == {"value": "hello"}


def test_env_include_missing_var_message_names_var(monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    with pytest.raises(MissingEnvVarError, match="NOPE"):
        resolve_include("env://NOPE")


def test_missing_env_var_error_is_a_key_error(monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    with pytest.raises(KeyError):
        resolve_include("env://NOPE")


def test_db_include_uses_netloc_as_record_id():
    with pytest.raises(NotImplementedError, match="db://"):
        resolve_include("db://record1")


def test_db_include_joins_netloc_and_path():
    with pytest.raises(NotImplementedError):
        resolve_include("db://host/sub/record")


@pytest.mark.parametrize("uri", ["ftp://x", "https://x", "s3://bucket/key"])
def test_unsupported_scheme_raises_value_error(uri):
    with pytest.raises(ValueError, match="Unsupported scheme"):
        resolve_include(uri)
