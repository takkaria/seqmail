import tomllib
from dataclasses import dataclass

import typedload
from xdg_base_dirs import xdg_config_home

SETTINGS_PATH = xdg_config_home() / "seqmail.toml"


@dataclass
class JMAPConfig:
    hostname: str
    token: str


@dataclass
class TodoistConfig:
    key: str


@dataclass
class Config:
    jmap: JMAPConfig
    todoist: TodoistConfig


def _load() -> Config:
    with open(SETTINGS_PATH, "rb") as f:
        data = tomllib.load(f)

    return typedload.load(data, Config)


SETTINGS = _load()
