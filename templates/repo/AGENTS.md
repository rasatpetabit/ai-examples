# AGENTS.md — <project-name>

<!--
Copy to: your repository root, as `AGENTS.md`.
Template skeleton — templates/repo/AGENTS.md: the canonical instruction file for ONE repository.

How to use it: replace every <angle-bracket placeholder> with this project's real content,
delete the sections you do not use, then delete this comment. A shipped file that still
contains a placeholder is a shipped placeholder — before committing, check that no
<angle-bracket placeholder> from this skeleton remains. HTML comments, including the
intent:consultation-rule sentinels, are not placeholders.

This file holds the context, rules and conventions of THIS repository. Which
line belongs in which file — including where harness-specific mechanics go at
repository scope — is decided by one test, owned by this guide's
instruction-files chapter: ../../docs/07-instruction-files.md. It is not
restated here. Links in this skeleton resolve inside this repository; after
copying into your repository they will not — repoint or delete them.
-->

## Project context

<what-this-repository-is — one paragraph: what it is, why it exists, what it deliberately is not, and the one thing a fluent newcomer most often gets wrong about it>

**Failure prevented:** an agent that re-derives the project from the source tree alone rebuilds
what the code happens to do today, not what it is for — this paragraph is what makes the
difference visible before the first edit.

## Intent

<!-- intent:consultation-rule v1 -->
`INTENT.md` at this repository's root states why the repository exists, what must never happen
in it, what it is deliberately not, and where it is going. Before any substantive change, read
it and judge the change against it: state in one line which of *serves* / *neutral* / *fights* /
*unavailable* the change is. `fights` — or a verdict you cannot reach — stops and goes to the
owner before code is written. INTENT.md is the owner's statement; it is amended through the
owner, never edited to make a change fit.
<!-- /intent:consultation-rule -->

**Failure prevented:** a change that contradicts the repository's reason looks exactly like good
work in the diff — the `fights` verdict is what makes the contradiction visible *before*
anything is written, and an owner's stated reason cannot be silently overruled by an agent
that never read it.

## Hard rules

Rules that must not be broken here. Each states the failure it prevents beside it, so a future
maintainer can judge the rule rather than obey it blindly — and delete it when the failure it
prevents no longer occurs. Keep only what is specific to <project-name>: the tier test that
splits this-repo rules from everywhere-rules is ../../docs/07-instruction-files.md.

- <rule> — **Failure prevented:** <what goes wrong without it>

## Quirks and gotchas

<the traps that cost real time to discover and cannot be seen from the code — each with what it breaks when missed>

**Failure prevented:** the next session pays again for a trap this file could have named — a
known dead end is re-investigated from scratch, which is pure waste.

## Domain conventions

<naming, layout, and idiom conventions that a fluent newcomer to the language or framework would still get wrong here — this project's local exceptions to general practice>

**Failure prevented:** work that follows the ecosystem's general conventions instead of this
project's — every choice locally defensible, the whole structurally foreign.

## First-day commands

The commands a new contributor runs first: build, run, test. For each, name where its
authoritative definition lives (the build file, the script, the README) rather than restating
the command in a second place — the definition moves, the copy does not, and the stale copy
wins the argument.

- <entry command> — <what it does; defined authoritatively in <where>>

**Failure prevented:** an agent runs a command copied here after the real definition changed —
the document and the build disagree, and the agent trusts the document.

## Handover notes

`WORKLOG.md` at the repository root owns this repository's session handover. Read it before
you start work here; it states the convention — when to read, when to append, how entries are
ordered, and what history may not be touched. Nothing about that convention is repeated here.

**Failure prevented:** nothing else a session loads names `WORKLOG.md`, so without this line
the handover happens only when a human remembers to open the file — the rule that must fire
every session has to live in the file that loads every session.
