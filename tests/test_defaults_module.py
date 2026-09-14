from ycon.defaults import load_with_defaults


def test_load_with_defaults_merges_files(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\nport: 5432\n")
    path = tmp_path / "config.yaml"
    path.write_text("port: 6543\n")

    assert load_with_defaults(path, defaults) == {
        "host": "localhost",
        "port": 6543,
    }
