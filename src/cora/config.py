import os
from collections.abc import Mapping
from dataclasses import dataclass

from core.errors import ConfigurationError
from core.openrouter_chat_model import OPENROUTER_BASE_URL

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_PLUGIN = "plugins.fitness"
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
            top_k=int(env.get("CORA_TOP_K", str(DEFAULT_TOP_K))),
            max_tool_rounds=int(
                env.get("CORA_MAX_TOOL_ROUNDS", str(DEFAULT_MAX_TOOL_ROUNDS))
            ),
        )
