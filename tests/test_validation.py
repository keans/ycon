import pytest
from pydantic import BaseModel, ValidationError

from ycon import load_config


class Nested(BaseModel):
    key: str


class Config(BaseModel):
    nested: Nested


def test_load_config_validates(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("nested:\n  key: hello\n")
    config = load_config(str(path), Config)
    assert isinstance(config, Config)
    assert config.nested.key == "hello"


def test_load_config_raises_on_wrong_type(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("nested:\n  key: [1, 2, 3]\n")
    with pytest.raises(ValidationError):
        load_config(str(path), Config)


def test_load_config_raises_on_missing_field(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("other: value\n")
    with pytest.raises(ValidationError):
        load_config(str(path), Config)


def test_load_config_resolves_includes_and_refs(tmp_path):
    (tmp_path / "child.yaml").write_text("key: !ref message\n")
    path = tmp_path / "config.yaml"
    path.write_text("nested: !include child.yaml\nmessage: hello\n")
    assert load_config(path, Config) == Config(nested=Nested(key="hello"))


def test_load_config_reports_error_in_included_data(tmp_path):
    (tmp_path / "child.yaml").write_text("key: [invalid]\n")
    path = tmp_path / "config.yaml"
    path.write_text("nested: !include child.yaml\n")
    with pytest.raises(ValidationError) as error:
        load_config(path, Config)
    assert error.value.errors()[0]["loc"] == ("nested", "key")


def test_load_config_propagates_reference_error(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("nested: !ref missing\n")
    with pytest.raises(KeyError, match="missing"):
        load_config(path, Config)


def test_load_config_rejects_empty_document(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("")
    with pytest.raises(ValidationError):
        load_config(path, Config)


def test_load_config_merges_over_defaults(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("nested:\n  key: default-key\n")
    path = tmp_path / "config.yaml"
    path.write_text("other: value\n")
    config = load_config(path, Config, defaults=defaults)
    assert config == Config(nested=Nested(key="default-key"))


def test_load_config_strict_rejects_unknown_key(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("nested:\n  key: default-key\n")
    path = tmp_path / "config.yaml"
    path.write_text("typo: value\n")
    with pytest.raises(ValueError, match="typo"):
        load_config(path, Config, defaults=defaults, strict=True)
