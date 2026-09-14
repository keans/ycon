import pytest

from ycon import load
from ycon.includes import resolve_include
from ycon.merge import deep_merge


def test_env_include_rejects_path_component():
    with pytest.raises(ValueError, match="Unsupported env://"):
        resolve_include("env://VAR/extra")


def test_env_include_rejects_query_component():
    with pytest.raises(ValueError, match="Unsupported env://"):
        resolve_include("env://VAR?default=1")


def test_file_uri_rejects_query_component(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("value: !include file:child.yaml?x=1\n")
    with pytest.raises(ValueError, match="Unsupported file URI"):
        load(path)


def test_deep_merge_type_error_names_the_offending_types():
    with pytest.raises(TypeError, match="list and dict"):
        deep_merge([1, 2], {"a": 1})
    with pytest.raises(TypeError, match="dict and str"):
        deep_merge({"a": 1}, "not-a-mapping")


def test_ref_error_message_names_path_and_failing_segment(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("a:\n  b: 1\nbroken: !ref a.b.c\n")
    with pytest.raises(TypeError, match=r"!ref 'a\.b\.c' failed at 'a\.b\.c'"):
        load(path)


def test_ref_missing_key_error_names_path_and_failing_segment(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("a:\n  b: 1\nbroken: !ref a.missing.c\n")
    with pytest.raises(
        KeyError, match=r"!ref 'a\.missing\.c' failed at 'a\.missing'"
    ):
        load(path)
