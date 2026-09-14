import yaml

from ycon import resolve_to_file
from ycon.dump import dump_yaml


def test_resolve_to_file_writes_plain_yaml(tmp_path):
    (tmp_path / "child.yaml").write_text("key: hello\n")
    path = tmp_path / "config.yaml"
    path.write_text("child: !include child.yaml\ncopy: !ref child.key\n")
    output = tmp_path / "resolved.yaml"

    resolve_to_file(path, output)

    text = output.read_text()
    assert "!include" not in text
    assert "!ref" not in text
    assert yaml.safe_load(text) == {
        "child": {"key": "hello"},
        "copy": "hello",
    }


def test_resolve_to_file_merges_defaults(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\nport: 5432\n")
    path = tmp_path / "config.yaml"
    path.write_text("port: 6543\n")
    output = tmp_path / "resolved.yaml"

    resolve_to_file(path, output, defaults=defaults)

    assert yaml.safe_load(output.read_text()) == {
        "host": "localhost",
        "port": 6543,
    }


def test_resolve_to_file_output_can_be_reloaded(tmp_path):
    (tmp_path / "child.yaml").write_text("key: hello\n")
    path = tmp_path / "config.yaml"
    path.write_text("child: !include child.yaml\n")
    output = tmp_path / "resolved.yaml"

    resolve_to_file(path, output)

    from ycon import load

    assert load(output) == {"child": {"key": "hello"}}


def test_resolved_containers_are_written_without_aliases(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("original: {value: hello}\ncopy: !ref original\n")
    output = tmp_path / "resolved.yaml"
    resolve_to_file(path, output)
    text = output.read_text()
    assert not any(
        isinstance(event, yaml.AliasEvent) for event in yaml.parse(text)
    )
    assert yaml.safe_load(text) == {
        "original": {"value": "hello"},
        "copy": {"value": "hello"},
    }


def test_dump_yaml_can_keep_aliases_when_requested(tmp_path):
    shared = {"value": "hello"}
    data = {"original": shared, "copy": shared}
    output = tmp_path / "resolved.yaml"

    dump_yaml(data, output, ignore_aliases=False)

    text = output.read_text()
    assert any(
        isinstance(event, yaml.AliasEvent) for event in yaml.parse(text)
    )
    assert yaml.safe_load(text) == data


def test_resolve_to_file_can_keep_aliases_when_requested(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("original: {value: hello}\ncopy: !ref original\n")
    output = tmp_path / "resolved.yaml"

    resolve_to_file(path, output, ignore_aliases=False)

    text = output.read_text()
    assert any(
        isinstance(event, yaml.AliasEvent) for event in yaml.parse(text)
    )
