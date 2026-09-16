from cora.domain.errors import PluginLoadError
from cora.ports.host import SCREENING, Host

from .guard import refuse_misuse
from .prompts import DEFAULT_STYLE, STYLES
from .tools import interview_tools, report_tool

CONTRACT = 1

SCOPE = "interview"

STYLE = "style"


def extend(cora: Host) -> None:
    """One style of coaching, a misuse screen, and up to three tools, all under
    interview and none outside it.

    The two interview tools answer with what a delegated loop wrote, so both are
    declared untrusted. Saving the report changes something outside cora and says so,
    so a call of it waits for the user — and it is offered only where the deployment
    configured somewhere to write, the way cora offers no `remember` without a memory.

    Raises:
        PluginLoadError: The style setting names none of the five, so the deployment
            is refused at load with the setting and the stray value named, rather than
            a typo quietly becoming the default.
    """
    style = cora.settings.get(STYLE, DEFAULT_STYLE)
    if style not in STYLES:
        raise PluginLoadError(
            __name__,
            f"{STYLE} must be one of {', '.join(sorted(STYLES))}, but got {style!r}",
        )
    cora.register_instructions(STYLES[style], scope=SCOPE)
    cora.register_handler(event=SCREENING, handle=refuse_misuse, scope=SCOPE)
    for tool in interview_tools(cora):
        cora.register_tool(
            name=tool.name,
            description=tool.description,
            parameter_schema=tool.parameter_schema,
            run=tool.run,
            scope=SCOPE,
            untrusted=tool.untrusted,
            asks=tool.asks,
        )
    if cora.output is None:
        return
    saving = report_tool(cora.output, cora)
    cora.register_tool(
        name=saving.name,
        description=saving.description,
        parameter_schema=saving.parameter_schema,
        run=saving.run,
        scope=SCOPE,
        effect=saving.effect,
    )
