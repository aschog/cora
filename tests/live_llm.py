from collections.abc import Mapping

import pytest

from cora.adapters.openrouter_chat_model import OPENROUTER_BASE_URL


def live_credentials(env: Mapping[str, str]) -> tuple[str, str]:
    api_key = env.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY is not set; the llm tier needs a real key")
    return OPENROUTER_BASE_URL, api_key
