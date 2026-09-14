"""Level 3: layering config over defaults, then validating with pydantic."""

from pathlib import Path

from pydantic import BaseModel

from ycon import load_config

HERE = Path(__file__).parent


class App(BaseModel):
    name: str
    retries: int


class Database(BaseModel):
    host: str
    port: int


class Config(BaseModel):
    app: App
    database: Database


config = load_config(
    HERE / "config.yaml", Config, defaults=HERE / "defaults.yaml"
)
print(config)
