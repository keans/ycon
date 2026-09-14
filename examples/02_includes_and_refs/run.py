"""Level 2: `!include` (file and env) and `!ref` into included content."""

import os
from pathlib import Path

from ycon import load

os.environ.setdefault("YCON_EXAMPLE_API_KEY", "demo-key-123")

config = load(Path(__file__).parent / "config.yaml")
print(config)
