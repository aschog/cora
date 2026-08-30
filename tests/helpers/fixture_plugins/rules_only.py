from cora.domain.errors import InputRejectedError
from fixture_plugins import make_plugin


class _Refuses:
    def apply(self, user_input: str) -> None:
        raise InputRejectedError("not on my watch")


extend = make_plugin(instructions="", tools=(), validation_rules=(_Refuses(),)).extend
