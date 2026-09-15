"""Every setting a deployment can make, read from the environment and checked once."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from cora.app.log_config import LOG_FILE
from cora.domain.errors import ConfigurationError
from cora.ports.host import name_of

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_PLUGINS: tuple[str, ...] = ()
DEFAULT_SCOPES: tuple[str, ...] = ()
DEFAULT_PLUGINS_PATH = ".cora/plugins"
DEFAULT_TOP_K = 5
DEFAULT_MAX_TOOL_ROUNDS = 8
DEFAULT_MAX_OUTPUT_TOKENS = 8192
DEFAULT_REQUEST_TIMEOUT_SECONDS = 90
REASONING_EFFORTS = ("low", "medium", "high")
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_HISTORY_TURNS = 20
DEFAULT_DB_PATH = ".cora/cora.sqlite"
DEFAULT_DOCUMENTS_PATH = ".cora/documents"
DEFAULT_OUTPUT_PATH = "cora-output"
DEFAULT_LOG_PATH = LOG_FILE


@dataclass(frozen=True)
class Config:
    """What a deployment decided. Read once at startup and never re-read.

    Every path is where cora keeps something of the user's, and each is separate so one
    can be moved without moving the others.
    """

    api_key: str
    model: str
    base_url: str
    plugin_modules: tuple[str, ...]
    top_k: int
    max_tool_rounds: int
    history_turns: int
    max_output_tokens: int
    request_timeout_seconds: int
    reasoning_effort: str
    db_path: str
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    plugins_path: str = DEFAULT_PLUGINS_PATH
    documents_path: str = DEFAULT_DOCUMENTS_PATH
    output_path: str = DEFAULT_OUTPUT_PATH
    log_path: str = DEFAULT_LOG_PATH
    debug: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Config":
        """Read the configuration, refusing anything unusable rather than guessing.

        Args:
            env: The environment to read. A mapping of a test's own, or the real one.

        Raises:
            ConfigurationError: A required setting is missing, or one is set to
                something it cannot be. Raised at startup, so a misconfigured
                deployment never reaches a question.
        """
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
            plugins_path=_named(env, "CORA_PLUGINS_PATH", DEFAULT_PLUGINS_PATH),
            scopes=_named_list(env, "CORA_SCOPES", DEFAULT_SCOPES),
            top_k=int_setting(env, "CORA_TOP_K", DEFAULT_TOP_K, minimum=1),
            max_tool_rounds=int_setting(
                env, "CORA_MAX_TOOL_ROUNDS", DEFAULT_MAX_TOOL_ROUNDS, minimum=1
            ),
            history_turns=int_setting(
                env, "CORA_HISTORY_TURNS", DEFAULT_HISTORY_TURNS, minimum=0
            ),
            max_output_tokens=int_setting(
                env, "CORA_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS, minimum=1
            ),
            request_timeout_seconds=int_setting(
                env,
                "CORA_REQUEST_TIMEOUT",
                DEFAULT_REQUEST_TIMEOUT_SECONDS,
                minimum=1,
            ),
            reasoning_effort=_effort(env),
            db_path=_named(env, "CORA_DB_PATH", DEFAULT_DB_PATH),
            documents_path=_named(env, "CORA_DOCUMENTS_PATH", DEFAULT_DOCUMENTS_PATH),
            output_path=_named(env, "CORA_OUTPUT_PATH", DEFAULT_OUTPUT_PATH),
            log_path=_named(env, "CORA_LOG_PATH", DEFAULT_LOG_PATH),
            debug=_bool(env, "CORA_DEBUG"),
        )


def _model(env: Mapping[str, str]) -> str:
    return _named(env, "CORA_MODEL", _named(env, "OPENROUTER_MODEL", DEFAULT_MODEL))


def _effort(env: Mapping[str, str]) -> str:
    effort = _named(env, "CORA_REASONING_EFFORT", DEFAULT_REASONING_EFFORT)
    if effort not in REASONING_EFFORTS:
        raise ConfigurationError(
            f"CORA_REASONING_EFFORT must be one of {', '.join(REASONING_EFFORTS)}, "
            f"but got {effort!r}."
        )
    return effort


def _named(env: Mapping[str, str], key: str, default: str) -> str:
    return env.get(key, "").strip() or default


def _plugin_modules(env: Mapping[str, str]) -> tuple[str, ...]:
    return _named_list(env, "CORA_PLUGINS", DEFAULT_PLUGINS)


def _named_list(
    env: Mapping[str, str], key: str, default: tuple[str, ...]
) -> tuple[str, ...]:
    if key not in env:
        return default
    return tuple(named.strip() for named in env[key].split(",") if named.strip())


def _bool(env: Mapping[str, str], key: str) -> bool:
    return env.get(key, "").strip().lower() in {"1", "true"}


def int_setting(env: Mapping[str, str], key: str, default: int, *, minimum: int) -> int:
    """One reading of a number from the environment, for every setting that is one.

    Named rather than private because a frontend has settings of its own to read the
    same way.

    Args:
        key: The variable's name, quoted back in any refusal.
        default: What the setting is when the variable is unset or blank.
        minimum: The lowest value that means anything. 0 only where the feature reads
            zero as off, as history turns do.

    Raises:
        ConfigurationError: The value is not a whole number, or is below `minimum`.
    """
    raw = _named(env, key, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{key} must be an integer, but got {raw!r}.") from exc
    if value < minimum:
        raise ConfigurationError(f"{key} must be {minimum} or more, but got {value}.")
    return value


PLUGIN_PREFIX = "CORA_PLUGIN_"


def plugin_settings(
    modules: tuple[str, ...], env: Mapping[str, str] | None = None
) -> dict[str, dict[str, str]]:
    """What each plugin may read as its own settings, keyed by module path.

    A plugin's variables are the ones named for it — `CORA_PLUGIN_BIRDS_UNITS` reaches
    the module whose last segment is `birds`, as `units`. Named for the plugin so a
    deployment can see whose setting it is setting, and read here rather than by the
    plugin so that reading the environment stays the composition root's job.

    Args:
        modules: The plugin modules a deployment named.
        env: Where to read from. The process environment unless a caller says otherwise.

    A plugin whose name is the tail of another's prefix can be handed a variable meant
    for that one — `CORA_PLUGIN_BIRDS_UNITS_X` reaches both `birds` and
    `birds_units`, as `units_x` and as `x`. Loading refuses two plugins named *alike*,
    which is not this: these are two names, and one is a prefix of the other. Left as it
    is because both are plugins the same deployment named, so nothing of cora's leaks
    and nothing crosses a trust boundary — a plugin reads a setting meant for its
    neighbour, which is the deployment's own business to sort out by renaming.
    """
    environ = os.environ if env is None else env
    found: dict[str, dict[str, str]] = {}
    for module in modules:
        prefix = f"{PLUGIN_PREFIX}{name_of(module).upper()}_"
        found[module] = {
            key[len(prefix) :].lower(): value
            for key, value in environ.items()
            if key.startswith(prefix)
        }
    return found
