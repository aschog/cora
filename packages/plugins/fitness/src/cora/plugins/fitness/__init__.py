from cora.plugins.fitness.safety import MedicalSafetyRule
from cora.plugins.fitness.tools import TOOLS
from cora.ports.plugin import Plugin

INSTRUCTIONS = """\
Answer training and nutrition questions as a knowledgeable, evidence-based coach:
clearly, practically, and from the user's own documents.

- Search the documents for training and nutrition questions, then cite the numbered
  passages you used.
- Use the provided tools for every calculation (BMI, daily energy, macros) — never do
  the arithmetic yourself.
- You are not a doctor. Do not give medical advice, diagnoses, or medication
  guidance; direct those questions to a qualified healthcare professional.
"""

SCOPE = "training and nutrition"

PLUGIN = Plugin(
    name="Fitness coaching",
    instructions=INSTRUCTIONS,
    scope=SCOPE,
    tools=TOOLS,
    validation_rules=(MedicalSafetyRule(),),
)
