import pytest

from cora.adapters.openrouter_chat_model import OPENROUTER_BASE_URL
from live_llm import live_credentials


def test_a_present_key_yields_the_real_openrouter_endpoint() -> None:
    base_url, api_key = live_credentials({"OPENROUTER_API_KEY": "sk-or-live"})

    assert base_url == OPENROUTER_BASE_URL
    assert api_key == "sk-or-live"


def test_a_missing_key_skips_with_a_reason_naming_the_variable() -> None:
    with pytest.raises(pytest.skip.Exception, match="OPENROUTER_API_KEY"):
        live_credentials({})
