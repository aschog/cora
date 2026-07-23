from docchat_plugins.fitness import SYSTEM_PROMPT


def test_system_prompt_sets_persona_and_load_bearing_instructions() -> None:
    prompt = SYSTEM_PROMPT.lower()

    assert prompt.strip()
    assert "coach" in prompt
    assert "cite" in prompt or "source" in prompt
    assert "tool" in prompt
    assert "medical" in prompt
