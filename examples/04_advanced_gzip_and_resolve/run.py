"""Level 4: gzip-compressed includes and resolving a config to a file.

Generates `large_dataset.yaml.gz` on the fly so the example doesn't
need to ship a binary file, then:
1. loads config.yaml, which !includes both a plain file and the
   gzip-compressed dataset, with !refs resolved throughout,
2. writes the fully-resolved result to resolved.yaml.gz.
"""

from pathlib import Path

from ycon import load, resolve_to_file
from ycon.dump import dump_yaml

HERE = Path(__file__).parent
DATASET = HERE / "large_dataset.yaml.gz"

dump_yaml({"rows": [{"id": i, "value": i * i} for i in range(5)]}, DATASET)

config = load(HERE / "config.yaml")
print(config)

output = HERE / "resolved.yaml.gz"
resolve_to_file(HERE / "config.yaml", output)
print(f"wrote fully-resolved config to {output}")
print(load(output) == config)
