# Adopting this template

You cloned it. This file is the answer to "now what?"

Two different things get called "using this template", and they need different
instructions. Pick one:

| You want to | Do this |
|---|---|
| Instruction files for your own machine and repositories | [Mode 1](#mode-1--use-the-templates) — copy files out and leave this clone alone as a reference |
| Your own version of this guide, for your team or your harness mix | [Mode 2](#mode-2--fork-the-guide) — edit in place and keep the suite green |

Mode 1 is where almost everyone starts, and it does not require reading the
eleven chapters first. The chapters explain *why* the templates have the shape
they do; you can adopt the shape now and read the reasoning when a decision
actually bites.

Or hand the work to an agent: [the brief](#handing-this-to-an-ai-agent) at the
bottom is self-contained and copy-pasteable.

## Mode 1 — use the templates

### The three layers, and the order to adopt them

The templates cover three independent layers. Adopt any subset. Each is useful
on its own and none of them requires the next:

1. **Per-repository** — [`templates/repo/`](templates/repo/). One repository's
   context, rules, and conventions. Cheapest, most contained, fastest to pay for
   itself. **Start here.**
2. **Global** — [`templates/global/`](templates/global/). Policy that follows
   you into every session on your machine. Adopt it once two or more
   repositories would otherwise repeat the same rules.
3. **Cross-cutting handbook** — [`examples/handbook/`](examples/handbook/).
   Policy shared by several repositories that each stay independent. Adopt it
   only when layer 2 has stopped being enough. It is the only layer that needs a
   tool to stay honest, because its pointers are derived rather than
   hand-written.

Which shipped file goes where, and what to adjust after copying it, is one
table: [`docs/07-instruction-files.md`](docs/07-instruction-files.md) § *Copy
destinations and path adjustment*. That table is the authority for destinations.
This file sequences the work and deliberately does not restate it — a second
copy of a destination table is a second thing to drift.

**Failure prevented:** copying a template to a plausible-looking path, and then
wondering why nothing changed. One of the destinations is a pointer file that
must contain no policy, and one overlay must *not* be copied over the canonical
file at all; the table says which, and guessing gets both wrong silently.

### Step 1 — one repository

Copy into the root of the repository you are working on:

- `templates/repo/AGENTS.md` → `AGENTS.md`
- `templates/repo/CLAUDE.md` → `CLAUDE.md` (only if you use Claude Code)
- `templates/repo/INTENT.md` → `INTENT.md` (optional; see below)
- `templates/repo/WORKLOG.md` → `WORKLOG.md` (optional; see below)

Then, in each file you copied:

- Replace every `<angle-bracket placeholder>` with your project's real content.
- Delete the sections you do not use. A skeleton section you left empty is noise
  the model reads on every session.
- Delete the template's own header comment — the `Copy to:` / `Adjust:` block,
  or the `<!-- ... -->` block. It is instructions for you, not for the model.
  In a pi context file an HTML comment is **sent to the model and billed as
  tokens**; pi strips a byte-order mark and nothing else.
- Repoint or delete the template's relative links. They resolve inside this
  clone and will not resolve inside your repository.

Before committing, check that no `<angle-bracket placeholder>` from the skeleton
survived. HTML comments — including the `intent:consultation-rule` sentinels —
are not placeholders; they are markers a tool looks for.

`INTENT.md` is worth its file when a repository has a reason to exist that a
reader cannot infer from the code, and when you want an agent to judge a
proposed change against that reason rather than against the diff alone.
`WORKLOG.md` is worth its file when more than one session — or more than one
agent — will work in the repository, because it is the cheapest handover that
exists. Skip either one without guilt; neither is load-bearing for the other
two files.

### Step 2 — your machine

Only once step 1 has worked in a real session. Copy the four global files to the
destinations the table in `docs/07` names, then:

- Fill in your own policy in the canonical file. Delete the section guidance you
  do not use.
- Confirm the overlay's import line resolves to wherever your canonical file
  actually landed. How import paths resolve is owned by
  [`docs/09-claude-code.md`](docs/09-claude-code.md) § *The `@`-import
  mechanism*.
- Keep harness mechanics in the overlay for that harness and policy in the
  canonical file. The per-line test that decides which file a line belongs in is
  [`docs/07-instruction-files.md`](docs/07-instruction-files.md)'s subject, and
  it is the one idea in this tree worth reading before you write policy rather
  than after.

If pi is your only harness, the table gives you a choice about where the
canonical file lives. Take it deliberately: two independent global policy files
that both load is the duplication failure in its most common real form.

### Step 3 — a handbook (only if you need one)

Read [`docs/08-cross-cutting-docs.md`](docs/08-cross-cutting-docs.md) first; it
owns the pattern and the stamping mechanism.
[`examples/handbook/`](examples/handbook/) is a runnable demonstration and
[`examples/ordinary-repo/`](examples/ordinary-repo/) is the repository that
points at it. Copy both, or neither — the pattern does not work half-applied,
because the pointer block between the sentinels is *derived*. Hand-editing
inside the sentinels is exactly what the next stamping run overwrites.

### Step 4 — prove it loaded

A file you wrote is not a file the harness read. Check it, because the failure
is silent: an instruction file at the wrong path loads nothing and reports
nothing.

- **Claude Code:** run `/context` in a session started in your repository and
  confirm your `AGENTS.md` content appears under Memory files — that is the shim
  working. `/memory` lists the locations across scopes. Both commands and what
  they show are documented in
  [`docs/09-claude-code.md`](docs/09-claude-code.md).
- **pi:** put a short unique marker line in the file you copied, start a session
  in that directory, and ask the model to repeat the marker. Then re-run with
  `--no-context-files` and confirm it cannot. The difference is your evidence
  that the file loads, and that the marker came from the file rather than from
  your prompt.

**Failure prevented:** believing a rule is in force because you wrote it down,
and debugging agent behaviour for an hour before suspecting that the file was
never read.

### What to do with this clone afterwards

Nothing. Leave it. It is a reference you consulted, not a dependency you
maintain — no file in your home directory or repository points back at it once
you have repointed the links in step 1. Keeping the clone costs you nothing and
re-reading a chapter later costs less than re-deriving it.

## Mode 2 — fork the guide

If you are making your own version of this document set — for a team, a
different harness mix, or your own conventions — the tree is built to be
modified, and it ships the machinery that keeps a modified copy honest.

Three files carry the machinery:

- [`MANIFEST.txt`](MANIFEST.txt) — the exact list of files that constitute the
  tree, one relative path per line. It is the publication boundary: what is
  listed is public, what is not listed does not ship.
- [`tools/leak-scan.sh`](tools/leak-scan.sh) — scans a tree for private
  material: credentials, absolute paths, internal hosts, configuration
  identifiers. Run it before you publish anything derived from a private
  workspace. `bash tools/leak-scan.sh --self-test` proves the detector can still
  fail.
- [`docs/11-verification.md`](docs/11-verification.md) — carries the integrated
  suite inside a fenced block, and the per-chapter claim-to-source tables.
  `bash tools/leak-scan.sh --verify-document docs/11-verification.md` extracts
  that block and runs it.

### Re-certifying your fork

Run the suite after any edit that touches structure, and before any publish:

```bash
bash tools/leak-scan.sh --verify-document docs/11-verification.md
python3 scripts/rule-dup-gate.py
```

The suite ends with `SUITE_RESULT=PASS` or it exits non-zero and tells you what
failed. It builds its own copy of the tree in a temporary directory, checks the
copy, and deletes it — so it proves the tree without leaving anything behind,
and a pass is a statement about the bytes, not about your intentions.

What it will reject in your fork, so you are not surprised:

- A file in the tree that `MANIFEST.txt` does not list, and a manifest entry
  that does not exist. Both directions, because an omission is how private
  material rides alongside a clean manifest.
- A manifest path with a dotted component, an absolute path, a `..`, a glob, a
  directory, or a duplicate. This is why there is no `.gitignore` in this tree:
  hidden paths are structurally unmanifestable, and the manifest is the
  publication boundary.
- A file that is not valid UTF-8, that contains a NUL byte, or that does not end
  with exactly one newline.
- A chapter that has a verification section with no claim-to-source table, or a
  recorded citation URL that is not public `https`.
- A rule stated in two files. `scripts/rule-dup-gate.py` searches for the
  *concept*, not the wording, via the topic patterns in
  [`scripts/rule-registry.json`](scripts/rule-registry.json) — because the same
  defect reworded is still the same defect, and a wording search misses it every
  time.
- An installer. There is no `setup.sh` here and the suite fails if one appears.

### The discipline you inherit

Two rules make a fork survivable, and both are already load-bearing in the
chapters:

- **Lookup over literal.** Where a fact can go stale, the chapter gives the
  command that produces the current value instead of the value. This is why a
  fork of this tree can sit for a year and still be usable: it does not assert
  what upstream looked like on a particular day. [`README.md`](README.md) owns
  this rule.
- **One rule, one owner.** A rule is stated in exactly one file and pointed at
  from everywhere else. [`docs/07-instruction-files.md`](docs/07-instruction-files.md)
  owns the version of this that applies to instruction files, and the gate above
  enforces the version that applies to this tree.

Keep both and your fork stays editable by someone who was not there when it was
written — including you, later.

## Handing this to an AI agent

Copy the block below into a session running in *your* environment, fill in the
angle brackets, and let the agent do the copying. It is written to be
self-contained: the agent does not need this conversation, and it is told where
the authority for each decision lives rather than being given a summary that
could drift from it.

```text
You are setting up AI-agent instruction files for my environment, using the
template repository at <path to your clone of this repository>.

Read these in full, in this order, before writing anything:
1. ADOPTING.md at that path — it sequences this work and names the layers.
2. docs/07-instruction-files.md § "Copy destinations and path adjustment" —
   the authoritative table of which shipped file goes where and what to adjust
   after copying. Do not guess a destination; if the table does not cover your
   case, stop and ask me.
3. Each template file you are about to copy.

Scope for this run:
- Layers to set up:            <per-repo | global | handbook>
- Target repositories:         <paths>
- Harnesses I actually use:    <pi | Claude Code | both>

For each layer in scope: copy every shipped template to the destination the
table names, then in the copy replace every <angle-bracket placeholder> with
content you derived from my real environment, delete the sections I do not use,
delete the template's own header comment block, and repoint or delete the
template's relative links (they resolve inside the clone, not inside my
repository).

Constraints:
- Ask me before inventing policy I have not stated. Deriving content from my
  repository, my existing configuration, and my answers is the job; writing
  rules you think I should have is not.
- Show me the destination path and the file content before writing anything
  into my home directory or into a harness configuration path.
- Keep policy in the canonical file for its scope and mechanics in the overlay
  for one harness. Where a second surface needs the same policy, it points at
  the canonical file instead of copying it. Apply the per-line test in
  docs/07-instruction-files.md rather than your own judgement about which file
  a line belongs in.
- Do not hand-edit inside a sentinel pair; those bytes are derived.

Then verify the files actually load, and show me the evidence:
- Claude Code: run /context in a session started in the target repository and
  confirm the AGENTS.md content appears under Memory files.
- pi: confirm a unique marker line you placed in the copied file can be
  repeated by the model in a normal session and cannot with --no-context-files.
A file that was written but never loaded is not finished.

Report: every destination path you wrote, what you changed in each, which
placeholders you could not fill and why, and the verification output.
```

**Failure prevented:** an agent that copies templates to plausible paths, fills
placeholders with invented policy, and reports success without ever confirming
that a harness read the result.

## Where each claim in this file comes from

This file sequences work and points at owners; it asserts very little of its
own. The load-bearing facts behind it, and their sources, live in the chapters
that own them: destinations and the per-line test in
[`docs/07-instruction-files.md`](docs/07-instruction-files.md), the import
mechanism and `/context` and `/memory` in
[`docs/09-claude-code.md`](docs/09-claude-code.md), pi's context-file loading
and `--no-context-files` in
[`docs/07-instruction-files.md`](docs/07-instruction-files.md), the handbook
pattern and stamping in
[`docs/08-cross-cutting-docs.md`](docs/08-cross-cutting-docs.md), the export
contract and the detector in [`README.md`](README.md) and
[`docs/11-verification.md`](docs/11-verification.md). Each of those chapters
carries its own claim-to-source table. Re-run the lookups rather than trusting
any of them, including this one.
