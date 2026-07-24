import os
from collections.abc import Mapping
from dataclasses import dataclass

from cora.adapters.openrouter_chat_model import OPENROUTER_BASE_URL
from cora.core.errors import ConfigurationError

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_PLUGIN = "cora.plugins.fitness"
DEFAULT_TOP_K = 5
DEFAULT_MAX_TOOL_ROUNDS = 8


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    base_url: str
    plugin_module: str
    top_k: int
    max_tool_rounds: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Config":
        env = os.environ if env is None else env
        api_key = env.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "OPENROUTER_API_KEY is not set. Add it to your environment."
            )
        return cls(
            api_key=api_key,
            model=env.get("CORA_MODEL", DEFAULT_MODEL),
            base_url=env.get("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
            plugin_module=env.get("CORA_PLUGIN", DEFAULT_PLUGIN),
            top_k=_int(env, "CORA_TOP_K", DEFAULT_TOP_K),
            max_tool_rounds=_int(env, "CORA_MAX_TOOL_ROUNDS", DEFAULT_MAX_TOOL_ROUNDS),
        )


def _int(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be an integer, but got {raw!r}.") from exc
