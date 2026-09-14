# ycon

Load YAML configuration with file and environment includes, shared
defaults, and references between values. Validate the result with Pydantic
or export the effective configuration as plain YAML.

Requires **Python 3.12 or newer**.

## Getting started

From a checkout of this repository, install the dependencies:

```bash
uv sync
```

Create `config.yaml`:

```yaml
app:
  name: example
  retries: 3
```

Load it in Python with `uv run python`:

```python
from ycon import load

config = load("config.yaml")
assert config["app"]["retries"] == 3
```

File arguments accept strings or `pathlib.Path` objects. Each call reads
files and environment variables again, so subsequent loads reflect changes.
Without defaults, the result can be any supported YAML value, including a
mapping, list, scalar, or `None` for an empty document.

See the [runnable examples](examples/README.md) for complete configurations.

## Scalar type resolution

Unquoted scalars resolve to Python types using **YAML 1.2's Core Schema**,
not PyYAML's YAML 1.1 defaults. This avoids well-known YAML 1.1 surprises:

| Value | YAML 1.1 (PyYAML default) | ycon (YAML 1.2 Core Schema) |
| --- | --- | --- |
| `yes`, `no`, `on`, `off` | `bool` | `str` |
| `017` | `15` (octal) | `str` (`"017"`) |
| `12:34` | `754` (sexagesimal) | `str` (`"12:34"`) |
| `true`, `false` | `bool` | `bool` (unchanged) |
| `0o17`, `0x1F` | `bool`/`int` variants | `int` (explicit-prefix octal/hex only) |
| `42`, `3.14`, `.inf`, `.nan` | resolved as usual | unchanged |
| `2024-01-01` | `datetime.date` | unchanged (timestamps aren't restricted) |

Quote a value (`"yes"`) if you want the literal string under either
scheme; explicit-prefix octal/hex (`0o17`, `0x1F`) still resolve as
integers. This applies everywhere YAML is parsed — `!include`d files,
`defaults=`, and top-level configs alike.

## Include files and environment variables

```yaml
# db_settings.yaml
host: localhost
port: 5432
```

```yaml
# config.yaml
database: !include db_settings.yaml
credentials: !include env://API_KEY
```

File includes are relative to the directory of the file containing the
`!include`, including when files include other files.

| Include form | Behavior |
| --- | --- |
| `!include settings.yaml` | Load a relative file. Absolute paths also work. |
| `!include file:///etc/app/settings.yaml` | Load a local file URI; percent-encoded characters are decoded. |
| `!include env://API_KEY` | Read the environment variable as `{"value": "<contents>"}`. |
| `!include db://record-id` | Raises `NotImplementedError` unless a `db` handler is registered (see [Custom include schemes](#custom-include-schemes)). |

For example, when `API_KEY=demo`, `config["credentials"]` is
`{"value": "demo"}`. An empty environment value is valid; an unset variable
raises `ycon.includes.MissingEnvVarError`, a subclass of `KeyError`.

Plain filenames preserve literal `#` and `%` characters. File URIs accept
an empty host or `localhost`; remote hosts, queries, and fragments are
rejected. Environment URIs must contain only the variable name, without a
path, query, or fragment.

### Custom include schemes

Register a handler to support `db://` (or any other scheme) without
forking the package:

```python
from ycon import register_scheme


def load_from_db(uri: str) -> dict:
    record_id = uri.removeprefix("db://")
    return {"id": record_id, "name": "..."}  # look it up for real


register_scheme("db", load_from_db)
```

`register_scheme(scheme, handler)` registers a callable. The handler
receives the full URI string and returns the resolved value. Registering
a handler under `env` overrides the built-in environment handler,
taking priority over the built-in handling; `file`/relative-path includes
are resolved before scheme handlers run and cannot be overridden this way.
Registration is process-global and takes effect for every `load()` call
afterward, until removed with `unregister_scheme(scheme)`.

For a temporary registration — in a test, or to scope a handler to one
call — use `using_scheme` as a context manager. It restores whatever was
registered before (or removes the entry entirely) on exit, even if the
block raises:

```python
from ycon import using_scheme

with using_scheme("db", load_from_db):
    config = load("config.yaml")
# the "db" handler (if any) reverts here
```

## Reference other values

Use `!ref` with a dot-separated mapping path:

```yaml
database:
  host: localhost
  port: 5432
app:
  db_host: !ref database.host
  db_port: !ref database.port
```

References preserve the target's type: `app.db_port` above is an integer.
They can target other references, entire mappings or lists, and values
introduced by includes or defaults. A reference inside an included file
uses the final top-level document as its root.

Paths address string mapping keys. List indexing and keys containing a
literal dot are not supported. Missing keys raise `KeyError`; invalid
indexing raises `TypeError`. Error messages identify the reference path and
the segment that failed.

Repeated includes and shared YAML aliases are allowed. Circular includes,
references, and recursive YAML aliases raise `ValueError`.

## Layer configuration over defaults

```yaml
# defaults.yaml
database:
  host: localhost
  port: 5432
  options:
    timeout: 30
    retries: 3
```

```yaml
# config.yaml
database:
  port: 6543
  options:
    retries: 5
```

```python
from ycon import load

config = load("config.yaml", defaults="defaults.yaml")
assert config == {
    "database": {
        "host": "localhost",
        "port": 6543,
        "options": {"timeout": 30, "retries": 5},
    }
}
```

Nested mappings merge key by key; the configuration wins wherever it
supplies a replacement value.

| Override value | Effect on the default |
| --- | --- |
| Mapping | Merge recursively when the default is also a mapping; otherwise replace it. |
| List, including `[]` | Replace the entire default value. |
| Scalar, including `null`, `false`, `0`, or `""` | Replace the default value. |
| Empty mapping `{}` | Preserve an existing default mapping. |
| Omitted key | Keep the default value. |

When `defaults=` is supplied, both documents must be mappings. Empty or
top-level `null` documents contribute an empty mapping; other document
types raise `TypeError`. Use `defaults=None` to omit defaults. An empty
path string is still treated as a path and raises an I/O error.

Pass `strict=True` to catch typos: any key in the configuration that
doesn't exist in `defaults` at the same nesting level raises `ValueError`
naming the full dotted path to the key (e.g. `"database.hots"`), instead
of silently being added.

```python
load("config.yaml", defaults="defaults.yaml", strict=True)
```

`strict` is ignored when `defaults` is not given, and is also accepted by
`load_config()`, `resolve_to_file()`, and `ycon.merge.deep_merge()`.

Loading happens in this order:

1. Load defaults and configuration, expanding their includes.
2. Merge configuration over defaults.
3. Resolve references against the merged document.
4. Validate, when using `load_config()`.

This means a reference defined in defaults sees overridden values. To
merge dictionaries directly, use `ycon.merge.deep_merge(base, override)`.

## Validate with Pydantic

```python
from pydantic import BaseModel
from ycon import load_config


class Database(BaseModel):
    host: str
    port: int


class Config(BaseModel):
    database: Database


config = load_config("config.yaml", Config, defaults="defaults.yaml")
assert config.database.port == 6543
```

`load_config()` returns an instance of the supplied model, using
`model.model_validate(...)`. Pydantic controls coercion, extra-field
handling, and validation rules. Invalid or missing required values raise
`pydantic.ValidationError`; loading errors propagate unchanged.

## Export resolved YAML

```python
from ycon import resolve_to_file

resolve_to_file("config.yaml", "resolved.yaml", defaults="defaults.yaml")
```

The output preserves the configuration's nested structure and, by default,
contains no `!include`, `!ref`, or YAML aliases — values shared via aliases
are written out in full at each location. Pass `ignore_aliases=False` to
keep them as YAML anchors/aliases instead. The output includes resolved
environment values and can be loaded by a standard YAML reader. The output
file is created or overwritten; source comments and formatting are not
preserved.

### Gzip support

Paths ending in `.gz` are automatically read or written as gzip, including
configuration files, defaults, includes, and exported output:

```python
from ycon import load, resolve_to_file

config = load("config.yaml.gz", defaults="defaults.yaml.gz")
resolve_to_file("config.yaml", "resolved.yaml.gz")
```

```yaml
data: !include dataset.yaml.gz
```

To write an already-resolved Python value, use
`ycon.dump.dump_yaml(data, path, ignore_aliases=True)`.

## Compare two configs

```python
from ycon import compare_files

result = compare_files("a.yaml", "b.yaml", defaults="defaults.yaml")
```

Loads and fully resolves both files (`defaults=`, if given, applies to
both) and returns how the second differs from the first, as a dict with
three keys, each keyed by dotted path:

- `added` — present only in the second file: `{"new_key": value}`
- `removed` — present only in the first file: `{"old_key": value}`
- `changed` — present in both with different values: `{"path": (old, new)}`

Nested mappings are compared key by key recursively; any other differing
value, including a whole list, is reported as one entry in `changed`
rather than diffed further. To compare two already-loaded values instead
of files, use `ycon.diff.diff_configs(a, b)` directly. Type changes such as
`true` to `1` are reported, including inside lists and in mapping keys.
Matching YAML `.nan` values are treated as unchanged. Paths use brackets for
literal dotted keys, empty keys, and non-string keys: `['a.b']` differs
from nested `a.b`, and `[1]` differs from the string-key path `1`.

## Sign a config

Install the optional `signing` extra (adds a dependency on
[PyNaCl](https://pynacl.readthedocs.io/) for Ed25519 signatures):

```bash
uv sync --extra signing
```

Subclass `SignableModel` instead of `BaseModel` to sign and verify a
validated config with an Ed25519 key:

```python
from nacl.signing import SigningKey
from ycon import load_config
from ycon.signing import SignableModel


class Config(SignableModel):
    name: str
    retries: int


signing_key = SigningKey.generate()  # keep this with the config publisher

config = load_config("config.yaml", Config)
bundle = config.to_signed_bundle(signing_key)
# bundle == {"payload": {...}, "signature": "<hex>", "signer_pubkey": "<hex>"}

# Only the verify key needs to travel with the app that reads the config.
verified = Config.from_signed_bundle(bundle, signing_key.verify_key)
```

`to_signed_bundle()` signs `model_dump(mode="json")` serialized as sorted,
separator-minimal JSON (`canonical_bytes()`) and returns a JSON-serializable
dict with the payload, hex-encoded signature, and signer public key.
`from_signed_bundle()` checks the received payload signature and signer
against the supplied trusted verify key before validating the model. It raises
`ValueError` if the signature doesn't match — use it to reject a tampered
or misattributed config before trusting it. `sign()`/`verify()` are also
available directly for lower-level use, without the bundle wrapper.
`ycon.signing` is a separate module, not imported by `ycon/__init__.py`,
so the core package has no hard dependency on PyNaCl. See
[`examples/05_signed_config`](examples/05_signed_config/) for a runnable
version, including the tampering-detection path.

## Command line

Installing the package provides a `ycon` command:

```bash
uv run ycon show config.yaml --defaults defaults.yaml --strict
uv run ycon resolve config.yaml -o resolved.yaml --defaults defaults.yaml
uv run ycon resolve config.yaml -o resolved.yaml --keep-aliases
uv run ycon diff a.yaml b.yaml --defaults defaults.yaml
uv run ycon --version
```

`--defaults`, `--strict`, and `--keep-aliases` are optional.

`show` loads and resolves a config the same way `load()` does and prints
it as JSON; a value a custom scheme handler returns that JSON can't
represent (e.g. a `set`) is flagged as
`{"__unrepresentable__": "<type>", "repr": "<repr>"}` rather than being
silently stringified. `resolve` is the CLI form of `resolve_to_file()`,
useful for resolving a config once at build/deploy time so the runtime
only ever loads the resolved YAML. `diff` is the CLI form of
`compare_files()`, printing `- removed`, `+ added`, and `~ changed`
lines. Run `uv run ycon --help` or `uv run ycon <command> --help` for
details.

## Development

Run these commands from the repository root:

```bash
uv sync
uv run pytest
uv run pytest --cov=ycon --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
```

Apply formatting with `uv run ruff format .`. Start exploring with
`uv run python examples/01_basic_loading/run.py`, or choose another
[example](examples/README.md).

The package is fully type-hinted and ships a `py.typed` marker, so
`mypy`/`pyright` type-check against it directly. `ycon.__version__`
(and `ycon --version`) reports the installed package version.

## Related projects

- [PyYAML](https://pyyaml.org/) — the underlying YAML parser; no includes,
  references, or defaults-merging on its own.
- [OmegaConf](https://omegaconf.readthedocs.io/) — hierarchical config with
  variable interpolation and merging; part of the larger Hydra ecosystem.
- [Dynaconf](https://www.dynaconf.com/) — layered settings across
  files/env/secrets, oriented around app settings rather than YAML tags.
- [Hydra](https://hydra.cc/) — configuration composition for applications,
  built on OmegaConf, with a CLI and multi-run support.
- [python-anyconfig](https://github.com/ssato/python-anyconfig) — loads and
  merges config in many formats (YAML, JSON, TOML, ...) behind one API.
- [confuse](https://confuse.readthedocs.io/) — YAML settings with defaults
  and validation, from the beets project.
- [pyaml-env](https://github.com/mkaranasou/pyaml_env) — minimal YAML
  loader that expands `${ENV_VAR}` references, no includes or refs.
