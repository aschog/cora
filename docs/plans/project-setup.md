# Feature: Project setup (Phase 0)

Bootstrap the repo per `docs/workflow.md` Phase 0 so every later feature branch
starts on tested, gated ground. Stack is fixed by `docs/plans/webapp-overview.md` §7:
Python 3.12 + uv, ruff, ty, pytest; runtime dependencies (LangChain, Chroma,
sentence-transformers, Streamlit) arrive with their own feature branches, not here.

## Checklist

- [ ] Scaffold uv project (src layout, package `docchat`), driven by a red→green
      smoke test proving the test runner and package wiring work
- [ ] Configure toolchain in `pyproject.toml`: ruff (format + lint), ty, pytest;
      all four gates run clean
- [ ] Add test watch mode (fast unit tier reruns on every save)
- [ ] Write `README.md` (what the project is, how to set up and run the gates)
- [ ] Install git hooks: pre-commit (format check, lint, types, unit tests),
      commit-msg (Conventional Commits)
- [ ] Set up CI mirroring the hooks (format check, lint, type check, tests)
- [ ] Write `CLAUDE.md`: commands + architecture rules (dependency rule, ports &
      adapters, TDD workflow pointers)
- [ ] Define AI subagents in `.claude/agents/`: `ai-architect`, `ai-code-reviewer`,
      `ai-researcher`
- [ ] AI skills for the stack available (astral uv/ruff/ty + Streamlit skills)

## Acceptance

`uv sync` from a clean clone; format, lint, type check and tests all pass; a
malformed commit message is rejected; a commit with failing tests is rejected;
CI runs the same gates on push.
