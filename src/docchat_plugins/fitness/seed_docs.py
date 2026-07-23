_PROTEIN_NOTE = """\
# Protein for muscle growth

For building and maintaining muscle, aim for roughly 1.6-2.2 g of protein per
kg of bodyweight per day (ISSN position stand; Morton et al. 2018 found a
breakpoint near 1.62 g/kg). Spread intake across 3-4 meals of 0.3-0.4 g/kg each.
Whole-food sources — poultry, fish, eggs, dairy, legumes — cover most needs;
supplements are convenience, not magic.
"""

_ENERGY_NOTE = """\
# Calories, TDEE, and body-weight change

Total Daily Energy Expenditure (TDEE) is your basal metabolic rate multiplied by
an activity factor (sedentary 1.2 up to extra-active 1.9). Eating at TDEE
maintains weight; a deficit of ~500 kcal/day loses roughly 0.45 kg/week, and a
similar surplus supports lean gains. Adjust from real-world trends over 2-3
weeks rather than day-to-day scale noise.
"""

SEED_DOCS: tuple[tuple[str, bytes], ...] = (
    ("protein.md", _PROTEIN_NOTE.encode("utf-8")),
    ("energy_balance.md", _ENERGY_NOTE.encode("utf-8")),
)
