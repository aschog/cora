import pathlib

from cora.ports.host import SCREENING, Host

from .safety import refuse_medical
from .tools import TOOLS

SCOPE = "fitness"

PAGE = "page"

INSTRUCTIONS = """\
Answer training and nutrition questions as a knowledgeable, evidence-based coach:
clearly, practically, and from the user's own documents.

- Search the documents for training and nutrition questions, then cite the numbered
  passages you used.
- Use the provided tools for every calculation (BMI, daily energy, macros) — never do
  the arithmetic yourself.
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
    cora.register_handler(event=SCREENING, handle=refuse_medical)
