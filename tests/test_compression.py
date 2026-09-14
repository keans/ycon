import gzip

from ycon import load, resolve_to_file
from ycon.dump import dump_yaml


def test_load_reads_gzip_compressed_file(tmp_path):
    path = tmp_path / "config.yaml.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("value: hello\n")
    assert load(path) == {"value": "hello"}


def test_load_include_reads_gzip_compressed_child(tmp_path):
    child = tmp_path / "child.yaml.gz"
    with gzip.open(child, "wt", encoding="utf-8") as f:
        f.write("value: hello\n")
    path = tmp_path / "config.yaml"
    path.write_text("child: !include child.yaml.gz\n")
    assert load(path) == {"child": {"value": "hello"}}


def test_dump_yaml_writes_gzip_compressed_file(tmp_path):
    path = tmp_path / "resolved.yaml.gz"
    dump_yaml({"value": "hello"}, path)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        assert f.read() == "value: hello\n"


def test_resolve_to_file_round_trips_through_gzip(tmp_path):
    (tmp_path / "child.yaml").write_text("key: hello\n")
    path = tmp_path / "config.yaml"
    path.write_text("child: !include child.yaml\n")
    output = tmp_path / "resolved.yaml.gz"

    resolve_to_file(path, output)

    assert load(output) == {"child": {"key": "hello"}}


def test_plain_yaml_is_not_gzip_compressed(tmp_path):
    path = tmp_path / "resolved.yaml"
    dump_yaml({"value": "hello"}, path)
    assert path.read_text() == "value: hello\n"
