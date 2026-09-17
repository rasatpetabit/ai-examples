<!-- handbook-pointer:start -->
- [Boundaries index](../handbook/docs/boundaries/index.md)
<!-- handbook-pointer:end -->

The block at the top of this file is a managed region. What belongs in one, and
what to do when its contents are wrong, are owned by
[`docs/07-instruction-files.md`](../../docs/07-instruction-files.md); this file
does not restate them.

## Project context

This repository holds **one small program and the instructions that describe it**:
`src/example.py`, a dependency-free `tally` that summarizes a line-oriented records
file. It exists so that every instruction surface in this tree — `AGENTS.md`,
`CLAUDE.md`, `INTENT.md`, `WORKLOG.md` — describes something real and runnable rather
than a placeholder. What a fluent newcomer most often gets wrong is assuming there is
more here than there is: there is no package to install, no test framework, no build,
and no dependency to add. The program is the whole product, and the instructions are
the whole point of the example.

**Failure prevented:** an agent that re-derives the project from the source tree alone
rebuilds what the code happens to do today, not what it is for.

## Hard rules

- **No third-party dependencies.** The program runs on a stock Python 3 with only the
  standard library. **Failure prevented:** a one-file example that needs a `pip install`
  before it can be run stops being an example.
- **The documented output shape is a contract.** Its exact form and ordering are
  specified in the module docstring; what belongs here is that consumers parse it, so
  it does not change casually. **Failure prevented:** a cosmetic "pretty-print" that
  silently breaks every consumer of the documented shape.
- **Verification is a real run, not a reading.** What that means operationally, and
  what to record, are owned by the work-conventions section below and by `WORKLOG.md`.
  **Failure prevented:** a change reported as done from inspection, when the run was
  never performed.

## Quirks and gotchas

The program's behavioural contract — the record shape, the 256-digit input bound, how
labels split, how duplicate labels merge, and the output order — is specified in the
module docstring of `src/example.py`, which is the authority for all of it. What
belongs here is only the traps that contract sets for a reader:

- **The count bound constrains INPUT only.** Two rows can sum past it, so an output row
  is legal to print yet rejected if fed back in. **Failure prevented:** treating a
  rejected re-entry as a bug and "fixing" the parser to accept unbounded input.
- **A bare run is not an error** — it processes built-in demo input, so the documented
  first command cannot fail. **Failure prevented:** a copied tree whose documented first
  command is a usage error, which is how an example stops being runnable.

## Domain conventions

- **`die()` is the only exit path** for a reported error: a message on stderr and a
  documented status. **Failure prevented:** error paths that exit with whatever the
  interpreter happened to produce.
- **stdout is written as bytes** and errors as text on stderr, so the output is
  byte-exact on any locale. **Failure prevented:** a run whose output differs between
  machines — locale collation or newline translation changing what a caller compares.

<!-- intent:consultation-rule v1 -->
## Intent consultation rule

Read `INTENT.md` before any substantive change in this repository and judge
the proposed change against the sections named there: **Why this repository
exists**, **Top invariant**, **Non-goals**, **Direction**, **Posture**.
When the verdict is not obvious, stop and ask the owner rather than
reasoning alone. **Failure prevented:** a change that meets its stated
requirements but quietly violates what the repository is *for* — locally
correct, globally wrong.

Amending `INTENT.md` is the owner's call. It is never a way to make a change
fit: rewriting the invariant instead of reconsidering the change is the
exact failure the review would otherwise catch. When the owner and the
proposed change disagree, escalate that disagreement — do not resolve it
silently in either direction.

This block is the repository's marked consultation rule; the marked block
marker names this section wherever it is referenced.
<!-- /intent:consultation-rule -->

## Work conventions

- `WORKLOG.md` is the durable handoff surface for this repository. That file
  states the convention — when to read, when to append, what an entry records,
  and why history is never rewritten. This bullet is a pointer; the rule lives
  there.
- Verification for any change to `src/example.py` is running it:
  `python3 src/example.py` (demo path), plus a piped input through `-`
  covering the changed behaviour. Paste the real output in the entry.
  **Failure prevented:** reporting a behavioural change as done from
  inspection when the run was never performed.
