from fixture_plugins import make_plugin


def _refuses(question: str) -> str:
    return "not on my watch"


extend = make_plugin(instructions="", tools=(), screens=(_refuses,)).extend
