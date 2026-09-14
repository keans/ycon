import pytest

from ycon.merge import deep_merge


def test_override_wins_on_scalars():
    assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}


def test_new_keys_are_added():
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_nested_dicts_are_merged_recursively():
    base = {"db": {"host": "localhost", "port": 5432}}
    override = {"db": {"port": 6543}}
    assert deep_merge(base, override) == {
        "db": {"host": "localhost", "port": 6543}
    }


def test_lists_are_replaced_not_merged():
    assert deep_merge({"a": [1, 2]}, {"a": [3]}) == {"a": [3]}


def test_dict_replaces_non_dict_and_vice_versa():
    assert deep_merge({"a": 1}, {"a": {"b": 2}}) == {"a": {"b": 2}}
    assert deep_merge({"a": {"b": 2}}, {"a": 1}) == {"a": 1}


def test_base_is_not_mutated():
    base = {"a": {"b": 1}}
    deep_merge(base, {"a": {"b": 2}})
    assert base == {"a": {"b": 1}}


def test_shared_aliases_can_be_merged_more_than_once():
    base_child = {"host": "localhost", "port": 5432}
    override_child = {"port": 6543}
    base = {"a": base_child, "b": base_child}
    override = {"a": override_child, "b": override_child}
    expected = {"host": "localhost", "port": 6543}
    assert deep_merge(base, override) == {"a": expected, "b": expected}
    assert base_child == {"host": "localhost", "port": 5432}
    assert override_child == {"port": 6543}


def test_strict_raises_on_unknown_key():
    with pytest.raises(ValueError, match="b"):
        deep_merge({"a": 1}, {"b": 2}, strict=True)


def test_strict_allows_existing_keys():
    assert deep_merge({"a": 1}, {"a": 2}, strict=True) == {"a": 2}


def test_non_strict_still_allows_unknown_keys():
    assert deep_merge({"a": 1}, {"b": 2}, strict=False) == {"a": 1, "b": 2}
