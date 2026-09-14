from ycon import compare_files
from ycon.diff import diff_configs


def test_no_differences():
    a = {"host": "localhost", "port": 5432}
    assert diff_configs(a, dict(a)) == {
        "added": {},
        "removed": {},
        "changed": {},
    }


def test_added_and_removed_top_level_keys():
    a = {"host": "localhost"}
    b = {"port": 5432}
    assert diff_configs(a, b) == {
        "added": {"port": 5432},
        "removed": {"host": "localhost"},
        "changed": {},
    }


def test_changed_scalar_value():
    a = {"port": 5432}
    b = {"port": 6543}
    assert diff_configs(a, b) == {
        "added": {},
        "removed": {},
        "changed": {"port": (5432, 6543)},
    }


def test_nested_dict_diff_uses_dotted_paths():
    a = {"database": {"host": "localhost", "port": 5432}}
    b = {"database": {"host": "production", "port": 5432}}
    assert diff_configs(a, b) == {
        "added": {},
        "removed": {},
        "changed": {"database.host": ("localhost", "production")},
    }


def test_added_and_removed_nested_keys():
    a = {"database": {"host": "localhost"}}
    b = {"database": {"port": 5432}}
    assert diff_configs(a, b) == {
        "added": {"database.port": 5432},
        "removed": {"database.host": "localhost"},
        "changed": {},
    }


def test_list_value_change_is_a_single_change_not_a_recursive_diff():
    a = {"items": [1, 2, 3]}
    b = {"items": [1, 2]}
    assert diff_configs(a, b) == {
        "added": {},
        "removed": {},
        "changed": {"items": ([1, 2, 3], [1, 2])},
    }


def test_non_dict_top_level_values():
    assert diff_configs("a", "b") == {
        "added": {},
        "removed": {},
        "changed": {".": ("a", "b")},
    }
    assert diff_configs("a", "a") == {
        "added": {},
        "removed": {},
        "changed": {},
    }


def test_compare_files_loads_and_diffs(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("host: localhost\nport: 5432\n")
    b.write_text("host: production\nport: 5432\n")

    assert compare_files(a, b) == {
        "added": {},
        "removed": {},
        "changed": {"host": ("localhost", "production")},
    }


def test_compare_files_applies_defaults_to_both(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\nport: 5432\n")
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("port: 6543\n")
    b.write_text("port: 6544\n")

    result = compare_files(a, b, defaults=defaults)
    assert result["changed"] == {"port": (6543, 6544)}


def test_type_changes_are_reported_inside_lists_and_mappings():
    for before, after in [
        (True, 1),
        (1, 1.0),
        ([True], [1]),
        ([{"value": False}], [{"value": 0}]),
    ]:
        assert diff_configs({"value": before}, {"value": after}) == {
            "added": {},
            "removed": {},
            "changed": {"value": (before, after)},
        }


def test_literal_dotted_keys_do_not_overwrite_nested_changes():
    before = {"a.b": 1, "a": {"b": 2}, "": 3, "1": 4, 1: 5}
    after = {"a.b": 6, "a": {"b": 7}, "": 8, "1": 9, 1: 10}
    assert diff_configs(before, after)["changed"] == {
        "['a.b']": (1, 6),
        "a.b": (2, 7),
        "['']": (3, 8),
        "1": (4, 9),
        "[1]": (5, 10),
    }


def test_mapping_key_type_changes_are_not_hidden_by_python_equality():
    assert diff_configs({True: "value"}, {1: "value"}) == {
        "added": {"[1]": "value"},
        "removed": {"[True]": "value"},
        "changed": {},
    }
    assert diff_configs({1: "value"}, {1.0: "value"}) == {
        "added": {"[1.0]": "value"},
        "removed": {"[1]": "value"},
        "changed": {},
    }


def test_mapping_key_type_changes_inside_lists():
    before, after = [{True: "value"}], [{1: "value"}]
    assert diff_configs(before, after)["changed"] == {".": (before, after)}


def test_identical_yaml_nan_values_are_not_changes(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    content = "value: .nan\nitems: [.nan]\n"
    a.write_text(content)
    b.write_text(content)
    assert compare_files(a, b) == {"added": {}, "removed": {}, "changed": {}}
