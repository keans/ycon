from pathlib import Path

import ycon


def test_py_typed_marker_is_present():
    marker = Path(ycon.__file__).parent / "py.typed"
    assert marker.is_file()
