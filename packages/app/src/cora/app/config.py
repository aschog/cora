import os
from collections.abc import Mapping
from dataclasses import dataclass

from cora.app.retrieval import DEFAULT_RETRIEVAL, RETRIEVAL_MODES
from cora.domain.errors import ConfigurationError

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_PLUGINS = ("cora.plugins.security",)
DEFAULT_TOP_K = 5
DEFAULT_MAX_TOOL_ROUNDS = 8
DEFAULT_HISTORY_TURNS = 20
DEFAULT_DB_PATH = ".cora/chroma"
DEFAULT_MEMORY_PATH = ".cora/memory.sqlite"
DEFAULT_FUSION_QUERIES = 4


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    base_url: str
    plugin_modules: tuple[str, ...]
    top_k: int
    max_tool_rounds: int
    history_turns: int
    db_path: str
    memory_path: str = DEFAULT_MEMORY_PATH
    retrieval: str = DEFAULT_RETRIEVAL
    fusion_queries: int = DEFAULT_FUSION_QUERIES
    debug: bool = False

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
            base_url=env.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
            plugin_modules=_plugin_modules(env),
            top_k=_int(env, "CORA_TOP_K", DEFAULT_TOP_K, minimum=1),
            max_tool_rounds=_int(
                env, "CORA_MAX_TOOL_ROUNDS", DEFAULT_MAX_TOOL_ROUNDS, minimum=1
            ),
            history_turns=_int(
                env, "CORA_HISTORY_TURNS", DEFAULT_HISTORY_TURNS, minimum=0
            ),
            db_path=env.get("CORA_DB_PATH", DEFAULT_DB_PATH),
            memory_path=env.get("CORA_MEMORY_PATH", DEFAULT_MEMORY_PATH),
            retrieval=_retrieval_mode(env),
            fusion_queries=_int(
                env, "CORA_FUSION_QUERIES", DEFAULT_FUSION_QUERIES, minimum=1
            ),
            debug=_bool(env, "CORA_DEBUG"),
        )


def _plugin_modules(env: Mapping[str, str]) -> tuple[str, ...]:
    """Unset takes the default set; set and empty asks for none. Distinguishing the
    two is what makes bare cora something a deployment can choose."""
    if "CORA_PLUGINS" not in env:
        return DEFAULT_PLUGINS
    named = env["CORA_PLUGINS"].split(",")
    return tuple(module.strip() for module in named if module.strip())


def _retrieval_mode(env: Mapping[str, str]) -> str:
    mode = env.get("CORA_RETRIEVAL", DEFAULT_RETRIEVAL)
    if mode not in RETRIEVAL_MODES:
        allowed = ", ".join(RETRIEVAL_MODES)
        raise ConfigurationError(
            f"CORA_RETRIEVAL must be one of {allowed}, but got {mode!r}."
        )
    return mode


def _bool(env: Mapping[str, str], key: str) -> bool:
    return env.get(key, "").strip().lower() in {"1", "true"}


def _int(env: Mapping[str, str], key: str, default: int, *, minimum: int) -> int:
    """`minimum` is 0 only where the feature reads it as off, as history turns do."""
    raw = env.get(key, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be an integer, but got {raw!r}.") from exc
    if value < minimum:
        raise ConfigurationError(f"{key} must be {minimum} or more, but got {value}.")
    return value
