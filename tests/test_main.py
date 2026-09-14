import ycon


def test_public_api_exports_load_and_load_config():
    assert ycon.__all__ == [
        "__version__",
        "compare_files",
        "diff_configs",
        "load",
        "load_config",
        "register_scheme",
        "resolve_to_file",
        "unregister_scheme",
        "using_scheme",
    ]
    for name in ycon.__all__:
        assert getattr(ycon, name) is not None


def test_version_is_a_non_empty_string():
    assert isinstance(ycon.__version__, str)
    assert ycon.__version__


def test_version_falls_back_when_package_metadata_is_missing(monkeypatch):
    import importlib
    from importlib.metadata import PackageNotFoundError

    def raise_not_found(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr("importlib.metadata.version", raise_not_found)
    reloaded = importlib.reload(ycon)
    try:
        assert reloaded.__version__ == "0.0.0"
    finally:
        importlib.reload(ycon)
