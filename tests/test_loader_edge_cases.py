import pytest
import yaml

from ycon import load


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("", None),
        ("null\n", None),
        ("hello\n", "hello"),
        ("42\n", 42),
        ("false\n", False),
        ("[]\n", []),
        ("{}\n", {}),
        ("- one\n- 2\n- null\n", ["one", 2, None]),
    ],
)
def test_document_shapes(tmp_path, content, expected):
    path = tmp_path / "config.yaml"
    path.write_text(content)
    assert load(path) == expected


def test_refs_inside_lists_and_to_lists(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "value: hello\nitems: [!ref value, {nested: !ref value}]\n"
        "copy: !ref items\n"
    )
    assert load(path) == {
        "value": "hello",
        "items": ["hello", {"nested": "hello"}],
        "copy": ["hello", {"nested": "hello"}],
    }


def test_nested_include_uses_including_directory(tmp_path, monkeypatch):
    directory = tmp_path / "settings"
    directory.mkdir()
    (directory / "child.yaml").write_text("value: !include leaf.yaml\n")
    (directory / "leaf.yaml").write_text("correct\n")
    (tmp_path / "leaf.yaml").write_text("wrong\n")
    (tmp_path / "config.yaml").write_text(
        "child: !include settings/child.yaml\n"
    )
    monkeypatch.chdir(tmp_path)
    assert load("config.yaml") == {"child": {"value": "correct"}}


def test_included_ref_uses_top_level_document(tmp_path):
    (tmp_path / "child.yaml").write_text("message: !ref value\n")
    path = tmp_path / "config.yaml"
    path.write_text(
        "child: !include child.yaml\nvalue: grüße\n", encoding="utf-8"
    )
    assert load(path) == {"child": {"message": "grüße"}, "value": "grüße"}


@pytest.mark.parametrize("style", ["absolute", "localhost", "relative_uri"])
def test_file_include_path_forms(tmp_path, style):
    child = tmp_path / "child.yaml"
    child.write_text("value: ok\n")
    uri = {
        "absolute": str(child),
        "localhost": child.as_uri().replace("file://", "file://localhost"),
        "relative_uri": "file:child.yaml",
    }[style]
    path = tmp_path / "config.yaml"
    path.write_text(f"!include '{uri}'\n")
    assert load(path) == {"value": "ok"}


def test_empty_env_value_is_present(tmp_path, monkeypatch):
    monkeypatch.setenv("YCON_EMPTY", "")
    path = tmp_path / "config.yaml"
    path.write_text("!include env://YCON_EMPTY\n")
    assert load(path) == {"value": ""}


@pytest.mark.parametrize(
    "content",
    [
        "value: [\n",
        "!include [child.yaml]\n",
        "!ref {key: value}\n",
        "!!python/object:builtins.object {}\n",
        "a: 1\n---\nb: 2\n",
    ],
)
def test_invalid_yaml_then_recovery(tmp_path, content):
    path = tmp_path / "config.yaml"
    child = tmp_path / "child.yaml"
    path.write_text("!include child.yaml\n")
    child.write_text(content)
    with pytest.raises(yaml.YAMLError):
        load(path)
    child.write_text("value: recovered\n")
    assert load(path) == {"value": "recovered"}


def test_missing_include_then_recovery(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("!include child.yaml\n")
    with pytest.raises(FileNotFoundError):
        load(path)
    (tmp_path / "child.yaml").write_text("ok\n")
    assert load(path) == "ok"


def test_symlink_include_cycle(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("!include alias.yaml\n")
    (tmp_path / "alias.yaml").symlink_to(path)
    with pytest.raises(ValueError, match="Circular include"):
        load(path)


def test_ref_path_segment_into_a_list_raises_type_error(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("items: [one, two]\nfirst: !ref items.0\n")
    with pytest.raises(TypeError):
        load(path)


def test_mutating_result_does_not_affect_next_load(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("items: [{value: original}]\ncopy: !ref items\n")
    first = load(path)
    first["copy"][0]["value"] = "changed"
    assert load(path) == {
        "items": [{"value": "original"}],
        "copy": [{"value": "original"}],
    }


def test_ref_path_through_alias_to_parent_is_not_a_cycle(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "group:\n  value: hello\n  copy: !ref alias.value\nalias: !ref group\n"
    )
    expected = {"value": "hello", "copy": "hello"}
    assert load(path) == {"group": expected, "alias": expected}
