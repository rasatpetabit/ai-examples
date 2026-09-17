# INTENT.md — ordinary-repo

This file is the repository's **intent**: why it exists, the invariant that
ranks above convenience, what it explicitly does not try to be, and the
direction its owner is taking it. Agents consult it (see the marked
`intent:consultation-rule` block in `AGENTS.md`) before substantive changes;
humans read it to decide whether to invest. Who may amend this file, and when, is stated
in the marked consultation rule in `AGENTS.md`.

## Why this repository exists

This repository exists to hold `tally`, a small, dependency-free command-line
summary tool with a stable, specified wire format. It exists because the
instruction files that surround it need something real to describe: rules,
conventions and quirks that answer to actual code rather than to invented
snippets. The value is in the whole working unit — a program whose
behaviour is specified, observable from a single command, and small enough
to hold in one's head.

## Top invariant

**The output is a deterministic function of the input bytes.** The same
input produces the same output bytes and the same exit code on any machine,
at any time, under any locale. Every change must preserve this. Where
convenience conflicts with determinism — a "nicer" locale-aware sort, a
friendlier parser — determinism wins.

## Non-goals

- Not a general data-processing toolkit: it summarizes `<count> TAB
  <label>` records, nothing else. Features are added reluctantly, and
  only with a stated use.
- Not performance-competitive: it processes what fits through standard
  input in a single pass. Streaming to a constant-memory implementation is
  a redesign, not a tweak, and is out of scope unless the owner says
  otherwise.
- Not a formatting library: output is the fixed summary format plus the
  `TOTAL` footer. JSON, CSV and table modes are explicitly not wanted.
- Not configurable: there are no options, flags beyond `--help`, or
  environment knobs. The format and the contract are the interface; the
  absence of configuration *is* the design.

## Direction

Small and stable, with correctness proven by running it. Growth means
clarifying the specification, not adding features. If this repository
ever needs a dependency, a build step, or a second source module, that is
a signal the scope has drifted, and it should raise the top invariant
conversation rather than be absorbed silently.

## Posture

Changes land in small, verifiable steps: run the program, record the real
output in the worklog, keep the entry honest. An unverified behavioural
claim about this program is treated as false until a run shows otherwise.
How a disagreement about direction is handled is owned by this repository's
consultation-rule block in `AGENTS.md`, not restated here.
