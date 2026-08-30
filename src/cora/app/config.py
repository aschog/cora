"""Every setting a deployment can make, read from the environment and checked once."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from cora.app.log_config import LOG_FILE
from cora.domain.errors import ConfigurationError

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_PLUGINS: tuple[str, ...] = ()
"""A plugin is an extension, so cora starts with none: a scope, a screen or any other
plugin is named by the deployment that wants it."""
DEFAULT_TOP_K = 5
DEFAULT_MAX_TOOL_ROUNDS = 8
DEFAULT_MAX_OUTPUT_TOKENS = 8192
"""A reasoning model bills its thinking to the budget it writes the answer from, so the
cap has to cover both: `gpt-5-mini` spent ~1200 tokens thinking before the first word of
a training plan, and ~3200 in all. The cap is a ceiling, not a reservation — a short
answer costs what it costs."""
DEFAULT_REQUEST_TIMEOUT_SECONDS = 90
"""Long enough that the cap above is what limits an answer, not the clock: the same
`gpt-5-mini` plan took 37-56 seconds to arrive, and a deadline inside that range only
swaps a truncated answer for a timed-out one."""
REASONING_EFFORTS = ("low", "medium", "high")
DEFAULT_REASONING_EFFORT = "low"
"""How much of the budget above the model may spend thinking. Measured on one question,
`gpt-5-mini` answered in 22-25s at `low` against 32-61s at the provider's own `medium`,
searching the documents and citing them either way — and at `high` it spent all 8192
tokens thinking and returned no answer at all. Sent on every request, including to a
model that does not reason: `openai/gpt-4o-mini`, which `DEFAULT_MODEL` still names, was
asked with `low` set and answered normally, so such a model ignores the key rather than
refusing it. No test holds that — only the provider can answer it."""
DEFAULT_HISTORY_TURNS = 20
DEFAULT_DB_PATH = ".cora/chroma"
DEFAULT_MEMORY_PATH = ".cora/memory.sqlite"
DEFAULT_DOCUMENTS_PATH = ".cora/documents.sqlite"
DEFAULT_CONVERSATIONS_PATH = ".cora/conversations.sqlite"
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
    memory_path: str = DEFAULT_MEMORY_PATH
    documents_path: str = DEFAULT_DOCUMENTS_PATH
    conversations_path: str = DEFAULT_CONVERSATIONS_PATH
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
            memory_path=_named(env, "CORA_MEMORY_PATH", DEFAULT_MEMORY_PATH),
            documents_path=_named(env, "CORA_DOCUMENTS_PATH", DEFAULT_DOCUMENTS_PATH),
            conversations_path=_named(
                env, "CORA_CONVERSATIONS_PATH", DEFAULT_CONVERSATIONS_PATH
            ),
            log_path=_named(env, "CORA_LOG_PATH", DEFAULT_LOG_PATH),
            debug=_bool(env, "CORA_DEBUG"),
        )


def _model(env: Mapping[str, str]) -> str:
    """The model to ask, under either name.

    The key and the base URL are named `OPENROUTER_*`, so the model gets guessed that
    way too; `CORA_MODEL` is the documented name and stays the one that wins whenever it
    names a model — blanks are not a name, and would otherwise outrank the alias.
    """
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
    """One setting, or its default. A blank is not a value.

    A variable blanked rather than deleted reads as unset to whoever blanked it:
    `sqlite3.connect("")` opens a private database that dies with the connection, and
    every fact the user asked to keep goes with it.
    """
    return env.get(key, "").strip() or default


def _plugin_modules(env: Mapping[str, str]) -> tuple[str, ...]:
    if "CORA_PLUGINS" not in env:
        return DEFAULT_PLUGINS
    named = env["CORA_PLUGINS"].split(",")
    return tuple(module.strip() for module in named if module.strip())


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


def plugin_settings(
    modules: tuple[str, ...], env: Mapping[str, str] | None = None
) -> dict[str, dict[str, str]]:
    """What each plugin may read as its own settings, keyed by module path.

    A plugin's variables are the ones named for it — `CORA_FITNESS_UNITS` reaches the
    module whose last segment is `fitness`, as `units`. Named for the plugin so a
    deployment can see whose setting it is setting, and read here rather than by the
    plugin so that reading the environment stays the composition root's job.

    Args:
        modules: The plugin modules a deployment named.
        env: Where to read from. The process environment unless a caller says otherwise.
    """
    environ = os.environ if env is None else env
    found: dict[str, dict[str, str]] = {}
    for module in modules:
        prefix = f"CORA_{module.rsplit('.', 1)[-1].upper()}_"
        found[module] = {
            key[len(prefix) :].lower(): value
            for key, value in environ.items()
            if key.startswith(prefix)
        }
    return found
