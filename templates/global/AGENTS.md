# Global policy (canonical)

```text
TEMPLATE — canonical global policy skeleton
Copy to:      ~/AGENTS.md
Adjust:       every <placeholder> becomes your own content; links in this skeleton
              are relative to the template repository — replace or remove them
              once the file is copied. Delete this fenced block after copying.
Reasoning:     the split rule that decides what belongs here — and the per-line
              test for it — is stated once in ../../docs/07-instruction-files.md.
              This skeleton points at it and never restates it.
Convention:   every rule you add carries a "Failure prevented:" line naming the
              failure it exists to prevent. The shipped sections demonstrate the
              convention; keep it when you replace them.
```

This is the canonical, vendor-neutral policy file: the rules that are true of
your work with any coding agent. It does not restate where a line belongs —
that test, and the destinations, are owned by
[07-instruction-files.md](../../docs/07-instruction-files.md), which also says
why duplicating it fails.

**Failure prevented:** a rule written into one harness's file is invisible to
every other harness, so the behaviour it demands appears only *sometimes* — and
when the same rule is later written into a second harness's file, the two copies
drift into disagreeing with no way to tell which is stale.

## Scope and authority

One paragraph: what this file binds (every agent session you start, on any
machine you configure), and its precedence — repository-level instruction files
narrow or override it, and never silently contradict it.
<!-- Placeholder: name the scope — machines, projects, people. -->
**Failure prevented:** without an explicit precedence order, a repository file
and this file can both load and disagree, and the agent resolves the conflict by
whichever it read last — an accident, not a decision.

## How this file reaches each harness

Orientation only; the mechanisms live in
[07-instruction-files.md](../../docs/07-instruction-files.md) and in each
harness's overlay.

- pi loads `AGENTS.md` files — its global one, plus one per ancestor directory
  of the working directory. It has no import syntax inside these files, so
  wiring this file to pi is a placement question: put a prose pointer
  where pi will load it. The options, and which one survives a working
  directory outside your home tree, are in the pi overlay.
- Claude Code reads `CLAUDE.md`, not `AGENTS.md`. Your global
  `~/.claude/CLAUDE.md` imports this file with a single `@`-import line and adds
  only Claude-specific mechanics below it.

**Failure prevented:** a harness's loading behaviour described in that harness's
own overlay is unreadable by every other harness — the description belongs here,
where all of them load it.

## Ranked invariants

List the outcomes you will not tolerate, worst first, each with the failure it
prevents. The ranking is the content: when two rules conflict, the agent breaks
the one you ranked lower.
<!-- Placeholder: two to five invariants, worst first. -->
**Failure prevented:** an unranked rule list leaves a genuine conflict between
two rules to be resolved by the agent's guess.

## Environment and tools

Stable facts about the tools you use — editors, package managers, language
runtimes — and any operating-system or hardware quirk that makes a generic
default wrong for you. Describe the *quirk*, not the inventory.
<!-- Placeholder: your tooling and any nonstandard environment trait. -->
**Failure prevented:** an agent applies generic defaults to a nonstandard
environment and reports success while doing the wrong thing for it.

What belongs at this tier, and why, are owned by
[07-instruction-files.md](../../docs/07-instruction-files.md).

## Working discipline

How the agent must work: verify before claiming, quote the output that drove a
decision, leave unrelated changes alone, and finish what the task actually
required rather than what was easiest to finish.
<!-- Placeholder: your working rules, each with its Failure prevented line. -->
**Failure prevented:** an unverified "done" — a change reported complete from
inspection, a decision attributed to output nobody quoted, or unrelated files
swept into the diff — each of which costs the reviewer the work of discovering
what actually happened.

## Probabilistic capability

Skills, plugins and similar capability bundles load probabilistically: the model
may not reach for one on the turn that mattered. What follows from that — where a
behaviour you cannot afford to miss must live instead — is stated once in
`docs/05-skills.md` (the skills chapter) and pointed at from here rather than
restated.
<!-- Placeholder: any behaviour here that must never be skipped. -->
**Failure prevented:** a rule entrusted to a skill fires only on the sessions
where the model happens to load it, with no error and no trace that the behaviour
was ever expected.

## Decision points

When to ask you and when to decide: settle discoverable, reversible details
yourself and state the choice; bring back only genuine forks — irreversible
acts, outward-facing changes, real ambiguity in the goal. Say plainly that
silence is never consent.
<!-- Placeholder: your escalation rules. -->
**Failure prevented:** every implementation detail handed back as a question
spends your time on sub-steps you already delegated — and every detail the
agent settles that was actually a fork is a decision made by the wrong party.

## Authority and verification

What outranks the agent's own derivation: authoritative sources, live device or
config state, prior records, and anything you name explicitly. When a derivation
disagrees with any of them, the derivation is wrong.
<!-- Placeholder: your authority order and any named-source rules. -->
**Failure prevented:** a confident model conclusion silently overriding the very
document, machine, or output that held the answer — and the agent reporting the
override as success.

## Concurrency and shared work

Only if your setup runs more than one agent at a time: how to check what else is
in flight before writing, what to do on a genuine overlap, and what one agent
owes another agent's uncommitted work.
<!-- Placeholder: your concurrency rules, or delete this section. -->
**Failure prevented:** concurrent agents writing one worktree produce interleaved
edits that look like progress and merge as garbage — and reverting "stray"
changes destroys another agent's work in progress.

## Completion and evidence

What proves work done: match the evidence to the surface where the result is
consumed — a receipt (the command ran) never proves an outcome (it worked) — and
required execution that did not happen stays explicit instead of dissolving into
a limitations paragraph.
<!-- Placeholder: your completion bar. -->
**Failure prevented:** "the tests passed" without the run, or a passing keyword
check standing in for the real requirement — a completion claim downstream
readers act on but cannot verify.

## Credentials and sensitive material

Where secrets live, what must never be echoed into files or transcripts, and
your posture once a credential has appeared somewhere it should not. State your
actual policy; do not write a security guide.
<!-- Placeholder: your credential rules. -->
**Failure prevented:** a credential pasted into a shared or published file
because no rule said where the line was — and a panic response (rotate
everything) that costs a day and fixes nothing.

## Durable state

Where decisions, blockers, and surprises persist beyond a session — a worklog, a
memory system, a plan file — and what must be written there before a turn ends.
<!-- Placeholder: your persistence surfaces. -->
**Failure prevented:** the next session, or the next person, restarts from zero
because the one decision that would have saved them existed only in a
conversation that has scrolled away.

## Editing this file

How policy itself changes: small reviewable diffs, one dated note for anything
non-obvious, nothing added without the failure it prevents.
<!-- Placeholder: your policy-editing convention, if any. -->
**Failure prevented:** a silent bulk rewrite of policy changes every agent's
behaviour at once, with no diff to review and no way back.
