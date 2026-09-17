# ordinary-repo — a small example repository

This directory is a **complete, runnable example of an ordinary single
repository** in the instruction-file shape this template teaches: a real
`AGENTS.md` with project context, hard rules, domain conventions and quirks;
a thin `CLAUDE.md` shim; a populated `INTENT.md`; a `WORKLOG.md`; and a
minimal source tree the instructions describe. The sibling
`templates/repo/` ships the same shape as empty skeletons; this example
shows those skeletons **filled in**, so "populated" has a concrete
referent.

## What each file answers

| File | What it answers |
|---|---|
| `AGENTS.md` | Project context, hard rules, domain conventions, quirks and gotchas, the machine-stamped handbook pointer block, and the marked intent consultation-rule block. This is the canonical instruction file for this repository — the one every other surface routes back to. |
| `CLAUDE.md` | Claude-Code mechanics only: an `@AGENTS.md` import plus nothing that fails the per-line test. |
| `INTENT.md` | Why this repository exists, its top invariant, non-goals, direction and posture. |
| `WORKLOG.md` | The durable session-to-session handoff: decisions and why, newest first. |
| `src/example.py` | `tally` — a small, dependency-free Python 3 program, so the instruction files describe something real. |

## Trying the example

From this directory (Python 3, no dependencies, no setup):

```
python3 src/example.py
```

processes a built-in demo input and prints:

```
4	blue
3	red
2	green
TOTAL	9
```

Feed it your own line-oriented records — one `<count> TAB <label>` per line —
from a file or standard input:

```
printf '5\tlinux\n3\tmacos\n5\tlinux\n' | python3 src/example.py -
```

Duplicate labels merge by summation. Output is ordered by descending count,
then by ascending label compared by Unicode code point, with a `TOTAL`
footer. Invalid records are reported on stderr as `tally: SOURCE:LINE:
message` and the run exits non-zero — nothing is silently dropped. The
record format and exit codes are specified authoritatively in the module
docstring.

## What this example demonstrates that the templates do not

1. A **machine-stamped pointer block** in `AGENTS.md`, between a sentinel
   pair, holding a relative link to `../handbook/docs/boundaries/index.md`,
   which exists in this tree. The ownership rule for that region is owned by
   [`docs/07-instruction-files.md`](../../docs/07-instruction-files.md); this
   README does not restate it.
2. A **marked intent consultation-rule block** binding substantive changes
   to `INTENT.md`.
3. **Populated** rather than skeleton content: real project context, real
   rules each naming the failure it prevents, and a real program to run.

## Where the rules live

Nothing normative is duplicated here. The split rule — which file a line
belongs to and why — is stated once in
[`docs/07-instruction-files.md`](../../docs/07-instruction-files.md). The
per-repo skeletons live in
[`templates/repo/AGENTS.md`](../../templates/repo/AGENTS.md). The handbook
pattern this pointer block anticipates is the sibling `examples/handbook/`
tree, and the pointer resolves inside this template's published layout.

## Verification notes

The claims in this tree are claims about the example itself, and were
verified by **running** it when this example was written, not by inspection alone:

- `python3 src/example.py` → the four lines shown above, exit 0.
- Piping records through `-` → merged, ordered output as described, exit 0.
- A record missing its tab, a leading-zero count, and an empty label each
  produce a `tally: SOURCE:LINE: message` stderr report and exit 1.
- The same input produces identical output bytes on repeated runs, including
  under `PYTHONOPTIMIZE=1`.

No upstream pi or Claude Code capability is claimed anywhere in this tree;
the pointer-block and consultation-rule conventions are defined by this
template, in the chapters linked above.
