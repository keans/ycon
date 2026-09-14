"""ycon: YAML config loading with includes, refs, and pydantic validation."""

from importlib.metadata import PackageNotFoundError, version

from ycon.diff import compare_files, diff_configs
from ycon.includes import register_scheme, unregister_scheme, using_scheme
from ycon.loader import load, resolve_to_file
from ycon.validation import load_config

try:
    __version__ = version("ycon")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
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
