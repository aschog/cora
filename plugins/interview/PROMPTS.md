# The five instruction styles

`prompts.py` holds five candidate instruction sets for the same field, one per
prompting technique. They share their first line (what the router reads) and their
ground rules (documents, tools, the live-interview boundary), so a comparison between
them compares the technique and nothing else. `CORA_PLUGIN_INTERVIEW_STYLE` picks the
one that registers.

| Style | Technique | What it bets on |
| --- | --- | --- |
| `zero_shot` | Zero-shot prompting | The model already coaches well when told to be direct and role-specific |
| `few_shot` | Few-shot learning | Two worked examples (STAR, layered technical answers) fix the register better than any description of it |
| `chain_of_thought` | Chain-of-thought | Showing the reasoning — what is probed, what a strong answer contains — is itself the coaching |
| `role_persona` | Role prompting | A concrete persona (a hiring manager) pulls in judgement generic instructions leave out |
| `structured_rubric` | Structured output | Fixed sections (Probing, Strong answer, Pitfalls, Drill) make every answer complete and skimmable |

## How to compare them

Run the same three questions under each style — five runs of cora, changing only the
environment variable — and judge the answers on usefulness, specificity to the role,
and how actionable the advice is:

1. "How should I answer 'tell me about a time you failed'?"
2. "Drill me on Python questions for a senior backend role."
3. Upload a job description into the `interview` field, then: "What should I prepare
   for this position?"

```sh
export CORA_PLUGIN_INTERVIEW_STYLE=zero_shot   # then few_shot, chain_of_thought, …
make run
```

## Result

| Style | Q1 | Q2 | Q3 | Notes |
| --- | --- | --- | --- | --- |
| `zero_shot` | | | | |
| `few_shot` | | | | |
| `chain_of_thought` | | | | |
| `role_persona` | | | | |
| `structured_rubric` | | | | |

The table is blank because the comparison is a live run against OpenRouter, which
costs money and is the deployer's to spend. The shipped default is `few_shot`, chosen
by reasoning rather than measurement: worked examples pin the register and the answer
shape harder than any instruction about them, which is the failure mode coaching
answers actually have. If the live run disagrees, change `DEFAULT_STYLE` in
`prompts.py` and write the numbers in.
