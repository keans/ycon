"""Level 1: the plain `load()` function, no tags involved."""

from pathlib import Path

from ycon import load

config = load(Path(__file__).parent / "config.yaml")
print(config)
