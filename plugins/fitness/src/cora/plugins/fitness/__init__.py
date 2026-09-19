import pathlib
from functools import partial

from cora.ports.host import SCREENING, Host

from .safety import refuse_medical
from .tools import TOOLS
from .workouts import list_workouts

SCOPE = "fitness"

PAGE = "page"

INSTRUCTIONS = """\
Answer training and nutrition questions as a knowledgeable, evidence-based coach:
clearly, practically, and from the user's own documents.

- Search the documents for training and nutrition questions, then cite the numbered
  passages you used.
- Use the provided tools for every calculation (BMI, daily energy, macros) — never do
  the arithmetic yourself.
- For what was trained — which days, which lifts, how the load and the reps moved —
  call `list_workouts` and show its text as it is: the names as the log spells them,
  never translated, and no table of your own. It names the days and the exercises;
  ask it with `detail` only when the reader asks for the numbers. It lists every
  session, where a search finds only the ones worded like the question. Search the
  documents for what a guide or a plan says.
- You are not a doctor. Do not give medical advice, diagnoses, or medication
  guidance; direct those questions to a qualified healthcare professional.
- When someone names a health condition, answer their training or nutrition question
  anyway, adapted to what they told you, and say plainly that they should clear the
  plan with their doctor. Do not refuse the question, and do not treat the condition.
"""


def extend(cora: Host) -> None:
    """Coaching under its own scope, a trainer to work in, and one refusal that holds
    outside it too. The page is a directory shipped beside this module."""
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
    cora.register_page(pathlib.Path(__file__).parent / PAGE, scope=SCOPE)
    for tool in TOOLS:
        cora.register_tool(
            name=tool.name,
            description=tool.description,
            parameter_schema=tool.parameter_schema,
            run=tool.run,
            scope=SCOPE,
        )
    cora.register_tool(
        name="list_workouts",
        description=(
            "Every workout logged in this field, as text to show: one line per day "
            "naming the exercises worked, oldest first. With detail, each movement's "
            "load, sets, reps, volume and whether it rose on the last time. Narrow "
            "to one exercise, or to the days since one."
        ),
        parameter_schema={
            "type": "object",
            "properties": {
                "exercise": {
                    "type": "string",
                    "description": "Only this exercise, as the log names it.",
                },
                "since": {
                    "type": "string",
                    "description": "Only sessions on or after this day, YYYY-MM-DD.",
                },
                "detail": {
                    "type": "boolean",
                    "description": "Each movement with its numbers, when asked for.",
                },
            },
        },
        run=partial(list_workouts, cora),
        scope=SCOPE,
    )
    cora.register_handler(event=SCREENING, handle=refuse_medical)
