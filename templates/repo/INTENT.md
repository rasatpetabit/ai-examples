# INTENT.md — <project-name>

<!--
Copy to: your repository root, as `INTENT.md`.
Template skeleton — templates/repo/INTENT.md: the repository owner's statement of why the
repository exists. It is not a README — it does not answer "what is this and how do I use
it"; it answers "why does this exist at all, and what must never happen to it."

Ownership: this file is written by the repository's owner and records the owner's decisions.
Who may change it, and what happens when a change and the intent conflict, are owned by the
consultation-rule block in `AGENTS.md`; this file does not restate that policy.

Fill in each section; delete guidance you do not want to keep. A section left as TODO is a
real gap: the top invariant below is what decides hard cases in this repository, so it
cannot stay a placeholder.
-->

## Why this repository exists

<one paragraph in the owner's words: the problem it solves, for whom, and what the world looks like without it — the reason this code exists rather than the features it happens to contain>

## Top invariant

<the one thing that must never happen here, stated as a single rule. If several rank, name
them worst-first and say which wins when two collide. This line decides hard cases; the
sections below explain, but this one binds>

**Failure prevented:** every agent and reviewer who judges a change here measures against the
invariant in force today, rather than against what they assume the project cares about —
without it, a change is judged by local fluency alone, and the most expensive violations look
like good work in the diff.

## Non-goals

<what this repository deliberately is not and will not become, so that "it would be nice if…" stops at the boundary instead of arriving as a pull request>
- <not-thing>
- <not-thing>

**Failure prevented:** scope creep arrives dressed as obvious improvement — a stated non-goal
is what makes "this is out of scope" a defensible answer rather than laziness.

## Direction

<where this is going — what a well-informed maintainer would build next, and what this repository is drifting toward even when nobody is steering>

**Failure prevented:** a change that moves the repository against its grain looks locally
reasonable; the direction line is what lets an agent (or a reviewer) see the drift while it is
still one commit.

## Posture

<how the repository holds itself — e.g. "capability first, with the way it goes wrong and the rule that prevents it beside the thing that causes it" or "correctness before features, always". The style that applies to every future change here>

**Failure prevented:** every contributor writes in the shape of the last change they liked;
posture is what makes one of those shapes the repository's, so the file reads like one author
rather than a committee of eras.
