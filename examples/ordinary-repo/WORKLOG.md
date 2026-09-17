# WORKLOG.md — ordinary-repo

The durable handoff surface for this repository. Sessions read this file at
the start of substantive work and append an entry before ending it — scope,
key decisions and why, not a replay of the diff (the diff shows what; the
entry records why). Entries are newest-first. History is never rewritten:
a correction is a new entry that supersedes the old one, never an edit of
it — a rewritten entry destroys the record of what was actually believed
at the time, which is exactly what a future decision-maker needs to see.

A good entry answers three questions: what was decided, why, and what
someone continuing the work needs to know that the diff cannot say.

**Failure prevented:** a future session reversing a deliberate decision
because the reason it was made survived nowhere but the author's head —
the single most expensive way work gets undone around AI agents, because
it looks like ordinary progress.

## 2026-09-14 — pointer block kept to one link; consultation rule names INTENT sections

- What: Instruction files only; no behaviour change in `src/example.py`.
- Decided: The bytes between the handbook-pointer sentinels are a single relative link to
  `../handbook/docs/boundaries/index.md`, and the "do not hand-edit" explanation sits
  *outside* the sentinels so a later stamper refresh cannot erase it. The consultation
  block names the `INTENT.md` sections explicitly and names no private skill. `README.md`
  no longer points at a cross-cutting chapter that does not ship with this repository.
- Open: none.

## 2026-09-14 — initial tree: tally program and instruction files

- What: Initial example tree — `src/example.py` (the `tally` program), `AGENTS.md`,
  `CLAUDE.md`, `INTENT.md`, `WORKLOG.md`, `README.md`.
- Decided: The record format is strictly `<count> TAB <label>`, first-tab split, chosen
  so labels may contain tabs without escaping and the format has exactly one separator
  — no platform text conventions involved. Supporting decisions:
  - Leading-zero counts and blank labels are rejected on purpose: one
  canonical textual form per count keeps the format round-trippable, and
  rejecting junk input early beats guessing intent.
  - Line splitting is LF-only, so CR is ordinary label content. Deliberate:
  the same input file must summarize identically on every machine.
  - Sort order is descending count, then ascending label **by Unicode code
  point**, not locale. Locale collation would make output machine- and
  environment-dependent, breaking the top invariant.
  - Errors are per-line on stderr, but processing continues: one bad record
  must not hide another. The run then exits 1, so callers still see a
  hard failure.
  - No dependencies, no configuration, no flags beyond `--help`: an
  example whose selling point is "runs with zero setup" must not acquire
  setup. A bare run processes a built-in demo input so the tool never
  fails from being invoked empty.
  - No test suite. The project is small enough that running it is the
  verification, and the README records how; a test framework here would be
  ceremony, not coverage.

- Open: The interface (CLI, record format, exit codes) is specified in the module
  docstring and is treated as frozen; everything else is internal. Any behavioural change
  updates this worklog and the docstring together. `CLAUDE.md` is intentionally nearly
  empty: what belongs in it versus `AGENTS.md` is the split rule owned by
  `docs/07-instruction-files.md`.
