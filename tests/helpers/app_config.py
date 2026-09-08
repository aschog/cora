"""The shipped configuration pointed at a directory of a test's own.

Here rather than in a suite because more than one needs it, and a test module is not
importable from another under importlib mode.
"""

from pathlib import Path

from cora.app.config import Config


def store_config(
    root: Path,
    *,
    debug: bool = False,
    plugin_modules: tuple[str, ...] = (),
) -> Config:
    return Config(
        api_key="k",
        model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        plugin_modules=plugin_modules,
        top_k=3,
        max_tool_rounds=4,
        history_turns=6,
        max_output_tokens=1024,
        request_timeout_seconds=30,
        reasoning_effort="low",
        db_path=str(root / "cora.sqlite"),
        documents_path=str(root / "documents"),
        log_path=str(root / "logs" / "cora.log"),
        plugins_path=str(root / "plugins"),
        debug=debug,
    )
