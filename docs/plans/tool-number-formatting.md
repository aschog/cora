# Readable tool numbers

The fitness calculators return raw floats, so a tool result reads `23.13424523…`
where a coach would say `23.1`. Round each metric to a fitting precision.

## Acceptance criteria

- BMI → 1 decimal place (`23.1`).
- BMR and TDEE → whole kcal (integers).
- Protein, fat, carbs → whole grams (integers).
- Rounding happens at the **tool boundary** (`tools.py`), so both the model and
  the UI receive the clean number. The calculators stay exact and exactly tested.

## Design

- `calculators.py` unchanged — pure, exact math.
- In `tools.py`, wrap each calculator before it is wired as a `Tool.run`:
  - `_to_one_dp(x)` → BMI to 1 dp.
  - `_to_whole(mapping)` → round every value of a result dict to `int`.
  Wire `BMI_TOOL` through `_to_one_dp`, the two dict tools through `_to_whole`.

## TDD checklist

- [x] `BMI_TOOL.run(weight_kg=75, height_m=1.8)` → `23.1` (exact is `23.148…`).
- [ ] `DAILY_ENERGY_TOOL.run(...)` returns whole-kcal ints for `bmr` and `tdee`.
- [ ] `MACROS_TOOL.run(...)` returns whole-gram ints for `protein_g`, `fat_g`, `carbs_g`.

## Fallout

None expected — calculator unit tests keep asserting exact values; only the tool
outputs change. Confirm the plugin bundle still validates.
