import datetime

from ycon import load


def _load_value(tmp_path, yaml_value):
    path = tmp_path / "config.yaml"
    path.write_text(f"value: {yaml_value}\n")
    return load(path)["value"]


def test_yes_no_on_off_stay_strings(tmp_path):
    for value in ["yes", "no", "on", "off", "Yes", "NO", "On", "OFF"]:
        assert _load_value(tmp_path, value) == value


def test_true_false_still_resolve_to_bool(tmp_path):
    assert _load_value(tmp_path, "true") is True
    assert _load_value(tmp_path, "True") is True
    assert _load_value(tmp_path, "false") is False
    assert _load_value(tmp_path, "False") is False


def test_leading_zero_digits_stay_strings_not_octal(tmp_path):
    assert _load_value(tmp_path, "017") == "017"
    assert _load_value(tmp_path, "'017'") == "017"


def test_explicit_octal_and_hex_still_resolve_to_int(tmp_path):
    assert _load_value(tmp_path, "0o17") == 15
    assert _load_value(tmp_path, "0x1F") == 31


def test_colon_separated_value_stays_a_string_not_sexagesimal(tmp_path):
    assert _load_value(tmp_path, "'12:34'") == "12:34"


def test_plain_ints_and_floats_still_resolve(tmp_path):
    assert _load_value(tmp_path, "42") == 42
    assert isinstance(_load_value(tmp_path, "42"), int)
    assert _load_value(tmp_path, "-7") == -7
    assert _load_value(tmp_path, "3.14") == 3.14
    assert _load_value(tmp_path, ".5") == 0.5
    assert _load_value(tmp_path, "5.") == 5.0
    assert _load_value(tmp_path, "1e10") == 1e10


def test_special_floats_still_resolve(tmp_path):
    assert _load_value(tmp_path, ".inf") == float("inf")
    assert _load_value(tmp_path, "-.inf") == float("-inf")
    assert _load_value(tmp_path, ".nan") != _load_value(tmp_path, ".nan")


def test_timestamps_and_null_are_unaffected(tmp_path):
    assert _load_value(tmp_path, "2024-01-01") == datetime.date(2024, 1, 1)
    assert _load_value(tmp_path, "null") is None
    assert _load_value(tmp_path, "~") is None
