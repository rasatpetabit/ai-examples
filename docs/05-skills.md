# Skills — how pi finds them, and a census you can run

A skill is a self-contained capability package the agent loads **on demand**: a folder with a
`SKILL.md` file (plus optional scripts and reference material) that describes a specialized
workflow, setup procedure, or domain technique. At startup pi scans fixed locations, extracts each
skill's name and description, and puts only those one-line summaries in the system prompt; the full
body is read later, only if a task seems to match. Upstream calls this *progressive disclosure* —
descriptions are always in context, instructions load on demand (`earendil-works/pi` →
`packages/coding-agent/docs/skills.md` § How Skills Work).

That is the exact opposite of an instruction file (see `docs/07-instruction-files.md`), which is
loaded unconditionally on every turn. The distinction is the load-bearing design decision of this
chapter: **a skill is cheap per turn but probabilistic; an instruction file is expensive per turn but
always present.** `docs/01-mental-model.md` explains why the per-turn cost difference matters.

This chapter has two halves. The first is mechanics: where pi looks, what it requires, and the
difference between a skill being *discovered*, *loaded*, *surfaced*, and *invoked* — four states
that look identical from the outside and are the single most common way a skill "mysteriously"
does not work. The second half applies that discipline to the installable world — the public
upstream pack and the skills shipped inside public packages, named so you can install them — and
then hands you the census method for your own machine, organized by where each skill comes from
and labelled by whether you can install it.

## The four discovery locations — and why they do not behave the same

Pi loads skills from four directories, plus three non-directory sources (packages, settings, and
the command line). All rules in this section are quoted from `earendil-works/pi` →
`packages/coding-agent/docs/skills.md` § Locations:

| Location | Scope | Root `.md` files |
|---|---|---|
| `~/.pi/agent/skills/` | user-global | **discovered** as individual skills (with valid frontmatter) |
| `~/.agents/skills/` | user-global | **ignored** |
| `.pi/skills/` | project | **discovered** as individual skills |
| `.agents/skills/` | project, searched in the cwd **and ancestor directories** up to the git repo root (or filesystem root outside a repo) | **ignored** |

The non-directory sources:

- **Packages** — a pi package ships skills via a `skills/` directory or `pi.skills` entries in its
  `package.json` (see `docs/04-packages.md` for the package mechanism).
- **Settings** — a `skills` array in `settings.json`, holding files or directories.
- **CLI** — `pi --skill <path>`, repeatable, which loads even when discovery is off
  (`--no-skills`).

Two rules apply everywhere:

1. **In all skill locations, directories containing a `SKILL.md` are discovered recursively.**
2. Root Markdown files that do not look like skills are ignored silently.

The asymmetry in the root-`.md` column is a trap for anyone coming from another harness. A single
`my-skill.md` file dropped directly in `~/.pi/agent/skills/` works. The same file dropped in
`~/.agents/skills/` is silently ignored — there, a bare `.md` file must sit **one level down** in a
grouping folder to be discovered.

**Failure prevented:** you write a one-file skill, drop it in the wrong global directory, and it
never loads — with no warning, because ignoring non-skill Markdown is the documented behaviour. If
you want a single-file skill, put it in `~/.pi/agent/skills/` or `.pi/skills/`; in `~/.agents/skills/`
give it its own folder with a `SKILL.md`.

Two more load-bearing details from the same section:

- **Project locations are trust-gated.** `.pi/skills/` and project `.agents/skills/` load only
  after the project is trusted; the trust decision is a separate mechanism covered in
  `docs/03-configuration.md`.
- **The `~/.agents/` path is deliberately shared.** The same directory is where other agent tools
  keep skills, which is why its rules differ. Upstream shows how to point pi at another harness's
  skill directory (`§ Using Skills from Other Harnesses`) by listing directories in the settings
  `skills` array:

  ```json
  {
    "skills": ["~/.claude/skills"]
  }
  ```

  **Failure prevented:** maintaining two copies of the same skill because two harnesses use
  different default directories. Point both at one directory instead.

Pi implements the open [Agent Skills standard](https://agentskills.io/specification), warning
about most violations but staying lenient — notably, pi does *not* require a skill's `name` to match
its parent directory, because that requirement is a poor fit for shared skill directories.

## The frontmatter contract: `name` + `description`

Every discovered `SKILL.md` needs YAML frontmatter with two required fields
(`packages/coding-agent/docs/skills.md` § Frontmatter):

```markdown
---
name: my-skill
description: What this skill does and when to use it. Be specific.
---
```

| Field | Required | Notes |
|---|---|---|
| `name` | yes | ≤64 chars, lowercase `a-z 0-9 -`, no leading/trailing/consecutive hyphens; need not match the directory |
| `description` | yes | ≤1024 chars; what the skill does and when to use it |
| `license` | no | license name or reference to a bundled file |
| `compatibility` | no | ≤500 chars of environment requirements |
| `metadata` | no | arbitrary key-value mapping |
| `allowed-tools` | no | space-delimited pre-approved tools (experimental) |
| `disable-model-invocation` | no | when `true`, hides the skill from the model (see below) |

The validation rules (`§ Validation`) are not symmetric, and the asymmetry matters:

- **Most issues warn but still load** — a name that is too long or has invalid characters, or a
  description over 1024 characters. These produce a warning; the skill still loads.
- **A declared skill with a missing description is NOT loaded.** A malformed `SKILL.md`, or a
  `SKILL.md` with no description, warns and is **not loaded**.
- Unknown frontmatter fields are ignored.
- **Name collisions (the same `name` from different locations) warn and keep the first skill
  found.**

**Failure prevented:** an empty or absent `description` silently drops the skill. It is the one
frontmatter defect that removes the skill entirely rather than degrading it — and since `description`
is also the invocation trigger (next section), a skill that survives with a weak description is
only half-alive.

## Discovered ≠ loaded ≠ surfaced ≠ invoked

These four states are the whole diagnostic story. A skill can be correctly installed, correctly
formed, and still never appear to the model — for reasons that look identical from the outside.

1. **Discovered** — pi's startup scan found it: a directory with a `SKILL.md` (recursively, in any
   location), a root `.md` where root files count, or a nested `.md` in a grouping folder. Not being
   discovered means the file is in the wrong place, or the project is not trusted.
2. **Loaded** — frontmatter satisfied: `name` plus a non-empty `description`. Otherwise: warn
   (or stay silent, for non-skill Markdown) and drop.
3. **Surfaced** — loaded, *and* not hidden by `disable-model-invocation: true`, *and* not
   shadowed by a same-`name` skill in a location the loader reaches first. Only surfaced skills
   appear in the system prompt's skills block.
4. **Invoked** — the model reads the full `SKILL.md` because a task matched the description. This
   happens per turn and is probabilistic (next section).

`disable-model-invocation: true` is not a defect state — it is the documented opt-out for skills a
human should trigger (`/skill:name`), such as a heavyweight review process you do not want the
model auto-starting mid-task.

**Failure prevented:** "my skill is broken" has four different causes, and guessing wastes hours.
Run the ladder in order:

```bash
ls <skill-dir>/SKILL.md        # 1. discovered at all? (right location? project trusted?)
# 2. non-empty YAML description? this grep is a rough text check, not the loader:
#    `description: ""` and some block scalars still match. Trust --verbose load warnings.
grep -c 'description:' <skill-dir>/SKILL.md
grep 'disable-model-invocation' <skill-dir>/SKILL.md  # 3. hidden by design?
grep -r '^name:' ~/.pi/agent/skills/ ~/.agents/skills/  # 4. same name shadowing?
```

Then start pi with `--verbose` and watch for load warnings, which name dropped skills and
collisions explicitly.

## Probabilistic invocation — the single most important design lesson

Upstream's own text (`§ How Skills Work`, step 3): when a task matches, the agent uses `read` to
load the full `SKILL.md` — "**models don't always do this**; use prompting or `/skill:name` to
force it".

Sit with that sentence. The entire skill mechanism — discovery, frontmatter, descriptions — ends in
a coin-flip-shaped step you do not control. A well-formed skill with a perfect description is still
only *available*; whether the model reaches for it on any given turn is a model-behaviour
probability, not a guarantee.

So the design rule follows directly:

> **A behaviour you cannot afford to miss belongs in an always-loaded instruction file
> (`docs/07-instruction-files.md`) or behind a deterministic guard (`docs/10-private-patterns.md`) —
> never only in a skill description.**

**Failure prevented:** the highest-cost failure mode in this whole area — a mandatory process step
(forced review, a security check, a completion-evidence rule) lives in a skill, the model does not
invoke it on the turn that mattered, and the step is skipped at the worst possible moment. Skills
earn their keep for *capability* (teaching how). Instruction files earn theirs for *policy
availability* — the rule is always in context — but presence is not adherence: the model can
still act against a rule it can see. Only a guard that inspects an action enforces anything, and
only for the actions its check actually covers.

## Writing a skill that actually fires

Because the `description` decides when the model loads the skill, upstream gives a concrete
good/bad contrast (`§ Description Best Practices`):

```yaml
# Good — names the artefacts and the trigger
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple
  PDFs. Use when working with PDF documents.

# Poor — does not reliably fire
description: Helps with PDFs.
```

**Failure prevented:** the vague description loads when the model happens to think of it and not
when the task calls for it. Name concrete triggers and artefacts.

The rest of the craft, briefly:

- A skill folder holds `SKILL.md` plus any helper scripts and reference files; the instructions
  reference them by relative path.
- Skills also register as `/skill:name` commands (`§ Skill Commands`), toggleable with the
  `enableSkillCommands` setting; `/skill:name` is also the way to *force* a load the model did not
  choose on its own.
- Upstream's opening line is worth taking literally: *pi can create skills — ask it to build one
  for your use case.*
- **Security boundary, stated once, from upstream's own Locations section:** skills can instruct
  the model to perform any action and may include executable code the model invokes — review skill
  content before use. The package-level version of this warning is in `docs/04-packages.md`; skills
  are not a softer case, they are the same case.

## The inventory, by provenance — and the census method behind it

The reference setup — the working setup this template generalizes from — carries a working
skills installation. Rather than describe it impressionistically, this section states the
discipline it follows: skills you can install are listed by name and source, so you can
install them yourself; everything else a working setup carries — private packs, host-local
and workflow-bound skills — is accounted for as a class, not published as a census, because
a census of one private machine would rot. The method below is the transferable part. Compare
a planned inventory against a live scan of your own, and record any drift between the two
rather than papering over it.

Why this matters enough to spend a chapter section on: an earlier draft of this project's own
planning asserted that "missing descriptions" explained a gap between the number of installed skill
directories and the number a session offered the model. When the census was actually run, **every
directory had valid frontmatter** — the hypothesis was simply wrong, and the real causes were
`disable-model-invocation` (hidden by design) and one name collision. Recording your own census
complete, with each row's actual state, is what prevents that class of confident error.

**Census method.** For each of the four directory locations plus package-declared skill sources:
list directories, check for `SKILL.md`, parse frontmatter, record `name`, `description` length,
`disable-model-invocation`, and `license`; resolve symlinks to their targets to identify
provenance; cross-tab hidden vs surfaced. Nothing is inferred from absence: where an outcome was not
measured, it is recorded as unmeasured. You can run the equivalent over **your own** install with:

```bash
# Partial scan of the four *directory* locations only. It does not cover
# package-declared skill sources (pi.skills / settings skills[]), and GNU find
# does not descend into symlinked skill dirs unless you add -L.
for d in ~/.pi/agent/skills ~/.agents/skills .pi/skills .agents/skills; do
  find -L "$d" -name SKILL.md -print 2>/dev/null
done
# Then also inspect each installed package's package.json `pi.skills` (or `pi.skill`)
# entries and any paths listed in settings `skills`.
```

and read each hit's frontmatter. A complete census matches the method above, not this
partial find.

The census is organized by **provenance tier** — where the skill comes from and whether an outsider
can install it — which is a different axis from the discovery locations above: a discovery location
tells you where pi looks; a provenance tier tells you whether you can have the skill too.

### Provenance tier A — public upstream: superpowers (14 skills, installable)

[Superpowers](https://github.com/obra/superpowers) is a public, MIT-licensed repository of agent
process skills — brainstorming, planning, TDD, debugging, code review, worktrees — shipped as a pi
package (`pi-package` keyword plus a `pi` block declaring its extension and skills). The reference
install carries all 14:

| Skill | Purpose |
|---|---|
| `brainstorming` | explore a problem before designing |
| `dispatching-parallel-agents` | fan out independent work safely |
| `executing-plans` | work through a written plan step by step |
| `finishing-a-development-branch` | land a branch cleanly |
| `receiving-code-review` | process incoming review findings |
| `requesting-code-review` | ask for a review with the right context |
| `subagent-driven-development` | drive implementation through subagents |
| `systematic-debugging` | root-cause a defect instead of patching symptoms |
| `test-driven-development` | red-green-refactor discipline |
| `using-git-worktrees` | isolate parallel work in separate checkouts |
| `using-superpowers` | bootstrap the skill set for a session |
| `verification-before-completion` | prove done-ness before claiming it |
| `writing-plans` | write executable implementation plans |
| `writing-skills` | author new skills that follow the contract above |

Install:

```bash
pi install git:github.com/obra/superpowers
```

(`earendil-works/pi` → `packages/coding-agent/README.md` § Pi Packages documents the `git:` install
form.)

**One honest caveat about the copy this was measured against.** The reference setup does not
install superpowers straight from GitHub; it enables a local-path package entry pointing at a
privately managed read-only snapshot of the upstream repository with a small private overlay.
A live diff of the snapshot against upstream found the *set* of 14 skill directories
identical, but at least one skill's *content* diverges (the copy this was measured against
routes its design step through a private review-gate skill; the upstream copy does not). What
you install from upstream is the upstream content — which is the point of installing from
upstream. The count is stable at 14 today; recount yours with the GitHub contents API
command in the verification notes.

### Provenance tier B — skills shipped inside public npm packages (10, installable with their packages)

These arrive automatically when you install the package that carries them — no separate skill
install exists or is needed. The `pi.skills` declaration in each package's `package.json` was read
from the installed packages, and every skill's `SKILL.md` was parsed.

| Package (install) | Ships | Skills | Notes |
|---|---|---|---|
| `pi install npm:context-mode` | context-window management tooling | 8: `context-mode`, `ctx-doctor`, `ctx-index`, `ctx-insight`, `ctx-purge`, `ctx-search`, `ctx-stats`, `ctx-upgrade` | **Elastic-2.0** — source-available, not open source; the full license caution is in `docs/04-packages.md` |
| `pi install npm:@luxusai/pi-hindsight` | durable-memory extension | 1: `hindsight-memory-doctor` | MIT; the memory system itself is `docs/06-memory-mcp-context.md`'s subject |
| `pi install npm:pi-mcp-adapter` | MCP adapter | 1: `mcp-scripting` | MIT; ships with `disable-model-invocation: true` **by the package's own design** — it is a human-invoked reference, reachable via `/skill:mcp-scripting` |

That last row is worth pausing on: a hidden skill in a *public* package proves that
`disable-model-invocation` is a deliberate upstream design tool, not a sign something is broken.
If you install these packages and do not see `mcp-scripting` offered to the model, that is the
package working as authored.

### Provenance tiers C and D — the private rows, as classes

A working setup like the one this template generalizes from also carries skills no reader can
install: a privately-authored pack of process and review skills, and skills bound to one host or
to a private workflow engine. Those rows are deliberately not published as a census — they
measure one private machine, and naming them would identify a private toolchain. They are still
accounted for, as classes: an honest inventory includes what you cannot have, labelled as such,
so a reader can tell what they are missing. The smallest public version of each class —
dispatch, orchestration, hooks, review — is `docs/10-private-patterns.md`'s subject.

Run the census method above over your own install and label your own rows the same way:
tier A public upstream, tier B shipped inside a public package, tier C your own private pack,
tier D host-local or workflow-bound. Expect tier C to be where human-triggered process skills
live, and expect a large share of them to be hidden on purpose (`disable-model-invocation`),
so the model cannot auto-start a heavyweight review or interview when a human should decide —
the public `mcp-scripting` row in tier B is the same design choice made by a public package.
To see the list a running session actually surfaces, rather than the one the rules predict,
use the public `pi-context-inspector` package.

Four census rules the method above implies, stated once because each one was learned the hard
way:

- **A census is a snapshot with a date.** A skills directory is live configuration. Record the
  count you measured, never silently update it, and when a re-scan differs from the recorded
  number, publish both and name the delta — drift is a finding, not an embarrassment.
- **Deduplicate by resolved real path.** A package's `pi.skills` entry and its default `skills/`
  directory are frequently the same directory; scanning both double-counts.
- **Resolve symlinks before counting collisions.** Two discovery locations can expose the same
  bytes under one name; when they do, which copy the loader keeps is immaterial — the collision
  is an alias, not a lost skill.
- **"Declared" and "on disk" are separate measurements.** A package can declare a skills
  directory that does not exist; a census that only scans directories will silently miss it,
  and a census that only reads manifests will silently invent it. Record both.

What this chapter deliberately does not measure about the private rows: content equality
between a private pack and its public namesakes, the origin of unattributed directories, and
which private skills are hidden. Unmeasured is recorded as unmeasured — a census that guesses
is worse than a hole.

## Verification notes (claim-to-source)

Upstream revision for all `earendil-works/pi` citations: `main` at `71dca871bc80b6bc97be37f0ca3189399d651fff`,
the commit the documents were fetched from for this chapter. Re-fetch and re-run anything below;
`docs/11-verification.md` consolidates the full matrix for the whole guide.

| Claim | Command (run for this chapter) | Result | Source |
|---|---|---|---|
| Four locations; root-`.md` rules; recursive `SKILL.md`; ancestor search; trust gate; other-harness skills array | `curl -s -o /tmp/skills.md https://raw.githubusercontent.com/earendil-works/pi/71dca871bc80b6bc97be37f0ca3189399d651fff/packages/coding-agent/docs/skills.md` | 232 lines at that commit; every rule in this chapter's mechanics sections is quoted from it. Fetch `main` separately if you want a current-upstream drift check. | `earendil-works/pi` → `packages/coding-agent/docs/skills.md` § Locations |
| Frontmatter contract and field table | same fetch | § Frontmatter, table reproduced by field | same file § Frontmatter |
| Missing description ⇒ not loaded; collisions keep first; over-length warns but loads | same fetch | § Validation, quoted | same file § Validation |
| "models don't always do this"; progressive disclosure | same fetch | § How Skills Work, quoted | same file § How Skills Work |
| `/skill:name` commands and `enableSkillCommands` | same fetch | § Skill Commands | same file § Skill Commands |
| superpowers ships 14 skills, today | `curl --fail --silent --show-error https://api.github.com/repos/obra/superpowers/contents/skills` | HTTP 200; 14 directories, names listed in tier A | `github.com/obra/superpowers` contents API |
| superpowers is MIT-licensed | GitHub API `license.spdx_id` on the same repo | `MIT` | same repo |
| superpowers is a pi package | `curl` its `package.json` from the repo | `pi-package` keyword; `pi` block with `skills: ["./skills"]` | repo `package.json` |
| `git:` install form exists | upstream README fetch | `pi install git:github.com/user/repo[@ref]` documented | `earendil-works/pi` → `packages/coding-agent/README.md` § Pi Packages |
| Package-shipped skills (8 + 1 + 1) and their frontmatter | parse each installed package's `package.json` `pi.skills` and `SKILL.md` files | counts and fields as listed in tier B | the public packages' own shipped files |
| `mcp-scripting` hidden by design | parse its `SKILL.md` | `disable-model-invocation: true` present in the public package | `pi-mcp-adapter`'s shipped skill |
| Census method and drift rules | the `find` snippet above plus each installed package's `package.json` `pi.skills` (or `pi.skill`) and settings `skills` | your own per-directory census, deduplicated by resolved real path, drift recorded | this chapter's census method |
| A local snapshot of a public pack can drift from upstream (the caveat above) | diff your snapshot's `SKILL.md` files against upstream `main` | your own divergence list — upstream is the source of truth | `github.com/obra/superpowers` |

No claim above is sourced from the private paths, private repositories, or (non-upstream)
installed fork of the machine this was measured on; where a fact could only be measured on
that machine, it is labelled as such and the row tells you how to recount it where you are.
