"""Load a YAML config and validate it against a pydantic model."""

from pydantic import BaseModel

from ycon.loader import load


def load_config[ModelT: BaseModel](
    path: str,
    model: type[ModelT],
    defaults: str | None = None,
    *,
    strict: bool = False,
) -> ModelT:
    """Load `path` (merged over `defaults`, if given) and validate it."""
    return model.model_validate(load(path, defaults=defaults, strict=strict))
