import json

import pytest
import yaml

from ycon.cli import main


def test_show_prints_loaded_config_as_json(tmp_path, capsys):
    path = tmp_path / "config.yaml"
    path.write_text("value: hello\n")

    main(["show", str(path)])

    assert json.loads(capsys.readouterr().out) == {"value": "hello"}


def test_show_accepts_defaults(tmp_path, capsys):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\nport: 5432\n")
    path = tmp_path / "config.yaml"
    path.write_text("port: 6543\n")

    main(["show", str(path), "--defaults", str(defaults)])

    assert json.loads(capsys.readouterr().out) == {
        "host": "localhost",
        "port": 6543,
    }


def test_resolve_writes_output_file(tmp_path, capsys):
    (tmp_path / "child.yaml").write_text("key: hello\n")
    path = tmp_path / "config.yaml"
    path.write_text("child: !include child.yaml\n")
    output = tmp_path / "resolved.yaml"

    main(["resolve", str(path), "-o", str(output)])

    assert yaml.safe_load(output.read_text()) == {"child": {"key": "hello"}}
    assert str(output) in capsys.readouterr().out


def test_resolve_keep_aliases_flag(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("original: {value: hello}\ncopy: !ref original\n")
    output = tmp_path / "resolved.yaml"

    main(["resolve", str(path), "-o", str(output), "--keep-aliases"])

    text = output.read_text()
    assert any(
        isinstance(event, yaml.AliasEvent) for event in yaml.parse(text)
    )


def test_show_strict_flag_rejects_unknown_key(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\n")
    path = tmp_path / "config.yaml"
    path.write_text("typo_host: production\n")

    with pytest.raises(ValueError, match="typo_host"):
        main(["show", str(path), "--defaults", str(defaults), "--strict"])


def test_resolve_strict_flag_rejects_unknown_key(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\n")
    path = tmp_path / "config.yaml"
    path.write_text("typo_host: production\n")
    output = tmp_path / "resolved.yaml"

    with pytest.raises(ValueError, match="typo_host"):
        main(
            [
                "resolve",
                str(path),
                "-o",
                str(output),
                "--defaults",
                str(defaults),
                "--strict",
            ]
        )


def test_show_flags_unrepresentable_values_instead_of_stringifying(
    tmp_path, capsys, monkeypatch
):
    from ycon import register_scheme, unregister_scheme

    register_scheme("weird", lambda uri: {1, 2, 3})
    monkeypatch.chdir(tmp_path)
    try:
        path = tmp_path / "config.yaml"
        path.write_text("value: !include weird://x\n")

        main(["show", str(path)])

        output = json.loads(capsys.readouterr().out)
        assert output["value"]["__unrepresentable__"] == "set"
    finally:
        unregister_scheme("weird")


def test_diff_prints_changed_added_removed(tmp_path, capsys):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("host: localhost\nold: gone\n")
    b.write_text("host: production\nnew: here\n")

    main(["diff", str(a), str(b)])

    out = capsys.readouterr().out
    assert "- old: 'gone'" in out
    assert "+ new: 'here'" in out
    assert "~ host: 'localhost' -> 'production'" in out


def test_diff_reports_no_differences(tmp_path, capsys):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("host: localhost\n")
    b.write_text("host: localhost\n")

    main(["diff", str(a), str(b)])

    assert capsys.readouterr().out.strip() == "no differences"


def test_version_flag_prints_version_and_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.startswith("ycon ")
