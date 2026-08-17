import os
from collections.abc import Mapping
from dataclasses import dataclass

from cora.domain.errors import ConfigurationError

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_PLUGINS: tuple[str, ...] = ()
"""A plugin is an extension, so cora starts with none: a domain, a guard or any other
bundle is named by the deployment that wants it."""
DEFAULT_TOP_K = 5
DEFAULT_MAX_TOOL_ROUNDS = 8
DEFAULT_HISTORY_TURNS = 20
DEFAULT_DB_PATH = ".cora/chroma"
DEFAULT_MEMORY_PATH = ".cora/memory.sqlite"
DEFAULT_DOCUMENTS_PATH = ".cora/documents.sqlite"


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
    documents_path: str = DEFAULT_DOCUMENTS_PATH
    debug: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Config":
        env = os.environ if env is None else env
        api_key = _named(env, "OPENROUTER_API_KEY", "")
        if not api_key:
            raise ConfigurationError(
                "OPENROUTER_API_KEY is not set. Add it to your environment."
            )
        return cls(
            api_key=api_key,
            model=_model(env),
            base_url=_named(env, "OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
            plugin_modules=_plugin_modules(env),
            top_k=_int(env, "CORA_TOP_K", DEFAULT_TOP_K, minimum=1),
            max_tool_rounds=_int(
                env, "CORA_MAX_TOOL_ROUNDS", DEFAULT_MAX_TOOL_ROUNDS, minimum=1
            ),
            history_turns=_int(
                env, "CORA_HISTORY_TURNS", DEFAULT_HISTORY_TURNS, minimum=0
            ),
            db_path=_named(env, "CORA_DB_PATH", DEFAULT_DB_PATH),
            memory_path=_named(env, "CORA_MEMORY_PATH", DEFAULT_MEMORY_PATH),
            documents_path=_named(env, "CORA_DOCUMENTS_PATH", DEFAULT_DOCUMENTS_PATH),
            debug=_bool(env, "CORA_DEBUG"),
        )


def _model(env: Mapping[str, str]) -> str:
    """The key and the base URL are named `OPENROUTER_*`, so the model gets guessed that
    way too; `CORA_MODEL` is the documented name and stays the one that wins whenever it
    names a model — blanks are not a name, and would otherwise outrank the alias."""
    return _named(env, "CORA_MODEL", _named(env, "OPENROUTER_MODEL", DEFAULT_MODEL))


def _named(env: Mapping[str, str], key: str, default: str) -> str:
    """A variable blanked rather than deleted reads as unset to whoever blanked it, so a
    blank is never a value: `sqlite3.connect("")` opens a private database that dies
    with the connection, and every fact the user asked to keep goes with it."""
    return env.get(key, "").strip() or default


def _plugin_modules(env: Mapping[str, str]) -> tuple[str, ...]:
    if "CORA_PLUGINS" not in env:
        return DEFAULT_PLUGINS
    named = env["CORA_PLUGINS"].split(",")
    return tuple(module.strip() for module in named if module.strip())


def _bool(env: Mapping[str, str], key: str) -> bool:
    return env.get(key, "").strip().lower() in {"1", "true"}


def _int(env: Mapping[str, str], key: str, default: int, *, minimum: int) -> int:
    """`minimum` is 0 only where the feature reads it as off, as history turns do."""
    raw = _named(env, key, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be an integer, but got {raw!r}.") from exc
    if value < minimum:
        raise ConfigurationError(f"{key} must be {minimum} or more, but got {value}.")
    return value
