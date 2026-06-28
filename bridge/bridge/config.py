"""Configuration loader for the bridge service."""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str | None = None
    max_tokens: int = 2048
    temperature: float = 0.7


@dataclass
class GameConfig:
    mod_url: str = "http://localhost:47823"
    poll_interval_seconds: int = 5
    command_rate_limit: int = 3


@dataclass
class DashboardConfig:
    port: int = 3847
    ws_enabled: bool = True


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    game: GameConfig = field(default_factory=GameConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)


def load_config(path: str | Path = "config.yaml") -> Config:
    """Load configuration from YAML file with env var substitution."""
    config_path = Path(path)
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config.example.yaml"

    if config_path.exists():
        with open(config_path) as f:
            raw = f.read()

        # Substitute ${ENV_VAR} patterns
        for key, value in os.environ.items():
            raw = raw.replace(f"${{{key}}}", value)

        data = yaml.safe_load(raw) or {}
    else:
        data = {}

    llm_data = data.get("llm", {})
    game_data = data.get("game", {})
    dash_data = data.get("dashboard", {})

    return Config(
        llm=LLMConfig(
            provider=llm_data.get("provider", "openai"),
            model=llm_data.get("model", "gpt-4o"),
            api_key=llm_data.get("api_key", os.environ.get("OPENAI_API_KEY", "")),
            base_url=llm_data.get("base_url"),
            max_tokens=llm_data.get("max_tokens", 2048),
            temperature=llm_data.get("temperature", 0.7),
        ),
        game=GameConfig(
            mod_url=game_data.get("mod_url", "http://localhost:47823"),
            poll_interval_seconds=game_data.get("poll_interval_seconds", 5),
            command_rate_limit=game_data.get("command_rate_limit", 3),
        ),
        dashboard=DashboardConfig(
            port=dash_data.get("port", 3847),
            ws_enabled=dash_data.get("ws_enabled", True),
        ),
    )
