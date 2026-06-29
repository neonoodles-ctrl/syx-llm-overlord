"""Configuration loader for the bridge service."""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

import yaml

from .personalities import DEFAULT_PERSONALITY, normalize_personality_id

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://10.0.10.151:11434/v1")
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1"


def normalize_model_id(provider: str, model: str) -> str:
    """Fix duplicated OpenRouter prefixes from dashboard display."""
    model = (model or "").strip()
    if provider == "openrouter":
        while model.startswith("openrouter/openrouter/"):
            model = model[len("openrouter/") :]
    return model


@dataclass
class LLMConfig:
    provider: str = "openai"  # openai, anthropic, ollama, together, groq, openrouter, api
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str | None = None
    max_tokens: int = 2048
    temperature: float = 0.7

    # Provider presets: maps provider name -> (base_url, default_model)
    PROVIDER_PRESETS: dict = field(default_factory=lambda: {
        "openai":      (None, "gpt-4o"),
        "anthropic":   (None, "claude-sonnet-4-20250514"),
        "ollama":      ("http://localhost:11434/v1", "llama3"),
        "together":    ("https://api.together.xyz/v1", "meta-llama/Llama-3-70b-chat-hf"),
        "groq":        ("https://api.groq.com/openai/v1", "llama3-70b-8192"),
        "openrouter":  ("https://openrouter.ai/api/v1", "meta-llama/llama-3-70b-instruct"),
        "deepseek":    ("https://api.deepseek.com/v1", "deepseek-chat"),
        "fireworks":   ("https://api.fireworks.ai/inference/v1", "accounts/fireworks/models/llama-v3-70b-instruct"),
        "api":         (None, "gpt-4o"),  # generic -- user provides base_url + api_key
    })

    def resolve(self) -> tuple[str | None, str]:
        """Return (base_url, api_key) after applying provider presets."""
        preset = self.PROVIDER_PRESETS.get(self.provider)
        url = self.base_url
        key = self.api_key

        if preset and not url:
            url = preset[0]

        # Ollama doesn't need a real key
        if self.provider == "ollama" and not key:
            key = "ollama"

        if self.provider == "openrouter" and not key:
            key = openrouter_api_key()

        return url, key


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
class OverlordConfig:
    personality: str = DEFAULT_PERSONALITY


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    game: GameConfig = field(default_factory=GameConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    overlord: OverlordConfig = field(default_factory=OverlordConfig)


def load_config(path: str | Path = "config.yaml") -> Config:
    """Load configuration from YAML file with env var substitution."""
    config_path = Path(path)
    if path == "config.yaml" and CONFIG_PATH.exists():
        config_path = CONFIG_PATH
    elif not config_path.is_absolute() and not config_path.exists():
        config_path = CONFIG_PATH if CONFIG_PATH.exists() else Path(__file__).parent.parent / "config.example.yaml"

    data = load_config_file(config_path) if config_path.exists() else {}

    llm_data = data.get("llm", {})
    game_data = data.get("game", {})
    dash_data = data.get("dashboard", {})
    overlord_data = data.get("overlord", {})
    provider = llm_data.get("provider", "openai")
    model = normalize_model_id(provider, llm_data.get("model", "gpt-4o"))
    if provider == "openrouter":
        api_key = llm_data.get("api_key") or os.environ.get("OPENROUTER_API_KEY", "")
    elif provider == "ollama":
        api_key = llm_data.get("api_key", "")
    else:
        api_key = llm_data.get("api_key") or os.environ.get("OPENAI_API_KEY", "")

    return Config(
        llm=LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
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
        overlord=OverlordConfig(
            personality=normalize_personality_id(
                overlord_data.get("personality", DEFAULT_PERSONALITY)
            ),
        ),
    )


def openrouter_api_key() -> str:
    return os.environ.get("OPENROUTER_API_KEY", "")


def ollama_request_timeout() -> float:
    return 180.0


def ollama_native_url(base_url: str | None = None) -> str:
    """Ollama REST root (no /v1) for /api/tags etc."""
    url = (base_url or DEFAULT_OLLAMA_URL).rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    return url.rstrip("/")


def ollama_v1_url_from_config(cfg: "Config | None" = None) -> str | None:
    """Ollama OpenAI-compatible base URL — only when Ollama is the active provider."""
    if not cfg or cfg.llm.provider != "ollama":
        return None
    if cfg.llm.base_url:
        return cfg.llm.base_url.rstrip("/")
    return DEFAULT_OLLAMA_URL.rstrip("/")


def ollama_host_for_display(cfg: "Config | None" = None) -> str:
    """Configured Ollama host for settings display (no API call)."""
    if cfg and cfg.llm.provider == "ollama" and cfg.llm.base_url:
        return ollama_native_url(cfg.llm.base_url)
    return ollama_native_url(DEFAULT_OLLAMA_URL)


def load_config_file(path: Path | None = None) -> dict[str, Any]:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config.example.yaml"
    if not config_path.exists():
        return {}
    raw = config_path.read_text()
    for key, value in os.environ.items():
        raw = raw.replace(f"${{{key}}}", value)
    return yaml.safe_load(raw) or {}


def save_llm_settings(
    *,
    provider: str,
    model: str,
    base_url: str | None = None,
    path: Path | None = None,
) -> None:
    config_path = path or CONFIG_PATH
    data = load_config_file(config_path) if config_path.exists() else {}
    llm = data.setdefault("llm", {})
    llm["provider"] = provider
    llm["model"] = normalize_model_id(provider, model)
    if base_url is not None:
        llm["base_url"] = base_url
    if provider == "ollama":
        llm.pop("api_key", None)
    elif provider == "openrouter":
        llm.pop("api_key", None)  # key lives in OPENROUTER_API_KEY env only
        if base_url is None:
            llm["base_url"] = DEFAULT_OPENROUTER_URL
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def save_personality_settings(*, personality: str, path: Path | None = None) -> None:
    config_path = path or CONFIG_PATH
    data = load_config_file(config_path) if config_path.exists() else {}
    overlord = data.setdefault("overlord", {})
    overlord["personality"] = normalize_personality_id(personality)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
