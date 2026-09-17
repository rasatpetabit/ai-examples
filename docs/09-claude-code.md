# Claude Code — the secondary harness track

This template recommends pi as the worked example, and pi's chapters stand on their own. Claude
Code is covered here because the reference setup this template generalizes from runs both
harnesses — and because the instruction-file split only earns its keep when two harnesses
actually read the same files. This is not even-handedness: it is the second half of a real
dual-harness setup, documented to the same verified bar as the pi track.

What this chapter is **not**: a restatement of anything vendor-neutral. The split rule — which
file a line belongs in, and why duplication is the failure — lives in
[`07-instruction-files.md`](07-instruction-files.md) and is never repeated here. If you are
designing your instruction hierarchy, read that chapter first; this one tells you only what is
mechanically different on the Claude side.

Everything below is verified against Claude Code's official documentation (live pages under
`code.claude.com/docs/en/`) and the npm registry; the exact commands, results, and sources are in
[Verification notes](#verification-notes) at the end. No Claude Code session was executed during
verification — every fact here is source-verified, and the chapter says so where it matters.

## Install and first run

Claude Code is installed by one of several official paths. The current authoritative list is on
the official setup page (see [Verification notes](#verification-notes) for the URL); the ones that
matter for a reader of this template:

- **Native installer (recommended by upstream):**
  `curl -fsSL https://claude.ai/install.sh | bash` on macOS, Linux, and WSL. Native
  installations update themselves in the background.
- **Package managers:** Homebrew (`brew install --cask claude-code`), WinGet on Windows, and
  the apt/dnf/apk Linux family — each documented on the same setup page. Package-manager
  installs do not auto-update; you upgrade deliberately.
- **npm:** `npm install -g @anthropic-ai/claude-code`. The package requires a recent Node.js —
  the floor is a moving target that upstream raises, so do not copy a number from any document,
  including this one. Look it up:

  ```console
  $ npm view @anthropic-ai/claude-code engines
  ```

  The npm package installs the same native binary as the standalone installer, pulled in through
  per-platform optional dependencies.

This chapter records no Claude Code version as the current one, per the anti-pinning rule owned
by [README.md](../README.md) ("Lookup over literal"). You **may** record the version you actually
tested, dated, next to a verification result or a bug report — that number is evidence, not a
recommendation, and it does not become false when upstream ships another release.

**Failure prevented:** a copied "current version" becomes a lie the day upstream ships. The
lookup command stays true forever; a recommendation-as-number does not. A dated observation is
not that failure.

Verify the install the way upstream documents it, not by inference:

```console
$ claude --version
$ claude doctor
```

`claude --version` prints the running version. `claude doctor` prints read-only installation and
settings diagnostics — install health, settings-file validation errors, and warnings with
suggested fixes — without starting a session. Start a session with `claude` in a project
directory.

## Authentication

Claude Code requires a Claude subscription or Console account (Pro, Max, Team, Enterprise, or
Console tiers — the free claude.ai plan does not include Claude Code). After installing, run
`claude` and follow the browser login prompts. The alternative path is an API key in the
`ANTHROPIC_API_KEY` environment variable; if it is set, Claude Code asks once to approve the key
instead of opening a browser.

Third-party deployment providers (Amazon Bedrock, Google Cloud's Agent Platform, Microsoft
Foundry) are supported for serving Claude models through your cloud account. This matters for the
rest of the chapter: **every documented deployment path serves Claude models** — there is no
supported configuration in which Claude Code runs a different vendor's model. Hold that thought
for
[Subagents and the model constraint](#subagents-and-the-model-constraint).

**Failure prevented:** planning to "just use the free account" hits a wall on first launch; and
assuming a third-party provider escapes the single-vendor property does not — it does not.

## Instruction files: `~/.claude/CLAUDE.md`, imports, and the repo shim

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. That single fact is why the split rule from
[`07-instruction-files.md`](07-instruction-files.md) has a Claude-specific half at all: your
canonical `AGENTS.md` is invisible to this harness unless you wire it in. Claude Code's own
documentation recommends exactly the wiring this template teaches — create a `CLAUDE.md` that
`@`-imports `AGENTS.md`, then add Claude-specific lines below the import:

```markdown
@AGENTS.md

## Claude Code

Use plan mode for changes under `src/billing/`.
```

(The body of that example is upstream's own illustration; the import line is the mechanism.)

### Where Claude Code looks

| Scope | Location | Notes |
|---|---|---|
| User | `~/.claude/CLAUDE.md` | Your preferences across all projects |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared, committed to version control |
| Local | `./CLAUDE.local.md` | Personal, machine-specific; add to `.gitignore` |
| Managed policy | OS-level paths (e.g. `/etc/claude-code/CLAUDE.md` on Linux) | Organization-wide, admin-controlled |

All discovered files **concatenate** — from the filesystem root down to your working directory —
rather than overriding each other. `CLAUDE.md` files in directories *above* your working directory
load at launch; files in subdirectories load on demand when Claude reads files there.

**Failure prevented:** committing `CLAUDE.local.md` publishes your personal sandbox paths and
test data to everyone who clones the repo. Add it to `.gitignore` before writing anything into
it.

### The `@`-import mechanism

- Syntax: `@path/to/file` anywhere in a `CLAUDE.md`.
- Relative paths resolve **relative to the file containing the import**, not the working
  directory.
- Paths beginning with `~` resolve from your **home directory** — the form the shipped global
  overlay uses for its `@~/AGENTS.md` import; upstream's own example is
  `@~/.claude/my-project-instructions.md`, for sharing preferences across git worktrees.
- Imports recurse, to a **maximum depth of four hops**.
- Backticks make a path literal: `` `@README` `` mentions; `@README` (bare) imports. Use the
  backtick form when you want to *name* a file without loading it.

An import in a **project-level** file whose path resolves outside the working directory (for
example, a home-directory import) is *external*: the first time Claude Code encounters it, it
shows an approval dialog, because a file someone else committed should not silently pull your
home directory into context. Decline once and the import stays disabled. **User-scope** files
(`~/.claude/CLAUDE.md`, `~/.claude/rules/`) are files you wrote yourself and their imports load
without the dialog.

**Failure prevented:** importing a personal file from a project `CLAUDE.md` and finding it
silently not loaded — the external-import dialog was declined once, and it does not appear again.

### Recurring cost, and the size discipline

`CLAUDE.md` files are loaded into the context window at the **start of every session**, so their
length is a recurring cost, not a one-time one — the same economics as pi's context files (see
[`01-mental-model.md`](01-mental-model.md) for the principle). Upstream's own guidance: target
**under 200 lines** per file, and keep rules specific and well-structured, because adherence
falls as files grow. Splitting content into `@`-imports helps organization but **does not reduce
context**, since imported files also load at launch. For large rule sets, upstream offers
`.claude/rules/` with path-scoped rules that load only when Claude works with matching files.

**Failure prevented:** a bloated overlay that is loaded (and paid for) every turn of every
session, and that the model follows less reliably precisely because it is long.

### The repo shim, concretely

The pattern this template ships in `templates/repo/` is a two-line-plus-mechanics file:

```markdown
@AGENTS.md

<!-- Claude Code-specific mechanics only. The per-line decision test for what
     belongs here is in docs/07 of this template, not restated in this file. -->
```

The upstream documentation also offers a symlink alternative (`ln -s AGENTS.md CLAUDE.md`).
Prefer the import: a symlink makes `CLAUDE.md` byte-identical to `AGENTS.md`, which leaves
nowhere to put Claude-specific mechanics below it, and creating symlinks on Windows requires
Administrator privileges or Developer Mode. **Failure prevented:** the symlink form is
unusable on Windows and structurally cannot carry the overlay's mechanics; the import form does
both.

`/init` generates a starting project `CLAUDE.md` by analyzing the codebase (`/init` suggests
improvements if one exists rather than overwriting). `/memory` lists and opens your memory-file
locations across scopes. `/context` shows what actually loaded this session — **use it to
verify the shim works**: `@AGENTS.md` must appear under Memory files. A rule that is not loaded
is not a rule.

**Failure prevented:** editing the wrong file for an hour — `AGENTS.md` edits that never reach
Claude Code because the shim is missing, mis-typed, or its external import was declined.

## Hooks and their trigger points

Hooks are user-defined commands (and HTTP endpoints, MCP tool calls, LLM prompts, or subagents)
that execute automatically at specific lifecycle points. They are the mechanism that turns
advice into enforcement, which is why the policy-engine pattern in
[`10-private-patterns.md`](10-private-patterns.md) is built on them; this section covers only the
mechanics, not the pattern.

### Where hooks are configured

| Location | Scope | Shareable |
|---|---|---|
| `~/.claude/settings.json` | All your projects | No |
| `.claude/settings.json` | Single project | Yes, committed |
| `.claude/settings.local.json` | Single project | No, gitignored |
| Managed policy settings | Organization-wide | Admin-controlled |
| Plugin `hooks/hooks.json` | Where plugin is enabled | Bundled with plugin |
| Skill and subagent frontmatter | Session / that subagent | Defined in the file |

Hook entries **merge** across settings levels rather than replacing each other.

### The trigger points

Hooks are configured in JSON: an event name, a matcher group filtering when it fires, and one or
more handlers. The load-bearing events:

- `PreToolUse` / `PostToolUse` — before and after any tool call; the matcher filters on tool
  name (`"Bash"`, `"Edit|Write"`, or a pattern).
- `UserPromptSubmit` — when a prompt is submitted.
- `Stop` / `SubagentStop` — when the model tries to end its turn (a `Stop` hook can prevent it,
  forcing continued work).
- `SessionStart` / `SessionEnd` — session lifecycle.
- `PreCompact` / `PostCompact` — around compaction.
- `Notification`, `SubagentStart`, `PreModelSwitch`, and others — see the official hooks
  reference for the full, current list; do not enumerate it from memory.

Hooks from settings files, managed policy, and plugins **also run inside subagents**: a
subagent's own tool calls fire `PreToolUse` and friends, with `agent_id` and `agent_type` fields
in the hook input identifying the subagent. A guard you configure covers dispatched work, not
just the main loop.

### Exit codes and the silent-gate trap

The exit code of a command hook is its verdict:

- **0** — proceed (or act on JSON printed to stdout).
- **2** — **block**. On events that can block, exit 2 blocks even if the hook also prints JSON
  saying otherwise; on `PreToolUse` it blocks the tool call, on `UserPromptSubmit` it rejects the
  prompt, on `Stop` it prevents the model from stopping. Events that cannot block (`PostToolUse`
  — the tool already ran — and others) show stderr instead.
- **any other code** — a *non-blocking error*: the action proceeds, and the transcript shows a
  hook-error notice.

The trap that turns a guard into decoration: **a hook that cannot start is a non-blocking
error.** A mistyped script path in `settings.json` — the file doesn't exist, or isn't executable —
fails with something like exit 127, the notice goes to the transcript, and **for most hook
events the action proceeds**. The gate you believe you installed is silently disabled.

**Failure prevented:** trusting an enforcement rule that has never actually fired. Watch the
first run of every hook you install; if the gate is load-bearing, verify a denial end-to-end.
This is the same lesson as pi's skill-invocation gap in [`05-skills.md`](05-skills.md) — a rule
the model merely *reads* is advisory; only a mechanism you have *seen fire* is enforcement.

`"disableAllHooks": true` in settings disables every hook without removing them — useful when
debugging, and a reason to keep enforcement out of files a casual edit can flip.

## Plugins and skills

### Skills

Claude Code skills are `SKILL.md` files (Markdown body plus YAML frontmatter between `---`
markers) in named directories, following the open **Agent Skills** standard that several AI
tools now share. Locations, in the order the official docs list them: personal
(`~/.claude/skills/<name>/SKILL.md`, all your projects), project (`.claude/skills/<name>/SKILL.md`,
committed and team-shared), enterprise (managed-settings directory), plugin
(`<plugin>/skills/<name>/SKILL.md`, namespaced), and claude.ai account skills that sync into
Cowork and cloud sessions. `.claude/commands/` is the older flat-Markdown format; it still works,
but skills are preferred for new work.

The frontmatter contract mirrors pi's: a `name` and, above all, a `description` — the
description is what the model reads to decide *whether* to load the skill. The rest of that
contract — the probabilistic-invocation consequence and what belongs in an always-loaded
instruction file instead — is identical on both harnesses and lives in one place:
[`05-skills.md`](05-skills.md). Read it there; this chapter adds nothing to it.
`disable-model-invocation: true` opts a skill out of automatic loading for manual `/name`
invocation only.

**Failure prevented:** shipping a must-have rule as a skill description and losing work on the
days the model doesn't reach for it — the failure `05-skills.md` documents with the evidence.

### Plugins

A plugin is a self-contained directory that bundles skills, subagents, hooks, commands, and MCP
server configs, identified by a `.claude-plugin/plugin.json` manifest. The manifest carries the
plugin's name, description, and version; components sit in conventional subdirectories
(`skills/`, `agents/`, `hooks/`, `commands/`, `.mcp.json`) at the plugin root. Distribution is
through **marketplaces**: a `marketplace.json` catalog users register with
`/plugin marketplace add <source>` and install from with
`/plugin install <plugin>@<marketplace>`. Test a plugin in progress by pointing a session at its
directory with `--plugin-dir`; a local copy takes precedence over an installed one for that
session, which is the sanctioned way to iterate.

**Failure prevented:** hand-copying configuration files between machines and projects — the
plugin is the unit of sharing, versioning, and updates; ad-hoc copies drift and are never
updated.

### MCP servers

MCP is built in on this harness where pi deliberately has none: a Claude Code session adds MCP
servers with `claude mcp add` or a committed `.mcp.json`, and the full current command surface is
on the official MCP page (see [Verification notes](#verification-notes)). The contrast with pi is
the reason this subsection exists: pi's core ships no MCP by design, and the adapter package
taught in [`06-memory-mcp-context.md`](06-memory-mcp-context.md) is how a pi install gains the
same capability. The capability crosses harnesses; the wiring does not.

## Subagents and the model constraint

Claude Code has **built-in** subagents — upstream pi, by contrast, has none (`earendil-works/pi`
→ `packages/coding-agent/README.md` § Philosophy lists "No sub-agents" as a deliberate absence;
pi-side subagents arrive via packages, per [`04-packages.md`](04-packages.md)). Each Claude Code
subagent runs in its own context window with its own system prompt, tool set, and permissions,
which is the same context-preservation win as any subagent anywhere.

Subagents are Markdown files in `.claude/agents/` (project scope, discovered by walking up
toward the repository root) or `~/.claude/agents/` (personal, all projects), or plugin
`agents/` directories. The frontmatter fields that matter here: `name` (identifier; hooks see it
as `agent_type`), `description` (**the delegation trigger** — Claude reads descriptions to
decide when to dispatch, so keep them short; the docs warn past ~15,000 combined tokens of
subagent descriptions), `tools`/`disallowedTools`, and `model`.

### The constraint

The `model` field accepts: a **Claude model family alias** (`sonnet`, `opus`, `haiku`,
`fable`), a **full Claude model ID**, or `inherit`. Nothing else. The resolution order —
per-invocation parameter, then the subagent's frontmatter, then `CLAUDE_CODE_SUBAGENT_MODEL`,
then the main conversation's model — is documented on the subagents page; what every value in
that chain shares is the closed enum. And as established in
[Authentication](#authentication), every documented deployment path serves Claude models.

**The harness difference that matters most:** on the **documented Claude-provider surface**,
subagent model IDs are a closed Anthropic-family enum — first party, Bedrock, Agent Platform,
Foundry, or an LLM gateway *proxying the Anthropic API*. (What a family alias currently
resolves to is a runtime fact — check it with `/model`, never from a document.)

One honest edge: the official model-configuration page states that behind a custom base URL or
gateway, Claude Code passes any model-ID string through **without checking it** — the gateway
defines the names. That is a documented pass-through, not a loophole and not a claim that
non-Claude subagents cannot be configured. Compatibility of a non-Claude backend behind that
pass-through was **not established** here. Do not treat it as a supported lane, and do not
treat it as structurally impossible.

**Verification result for this claim:** this template's planning spec asserted the enum was
Anthropic-only; it was re-checked against the live official documentation while writing this
chapter. The claim **holds for the documented Claude-provider surface**, with the pass-through
recorded as documented-but-unverified-for-other-vendors. The re-check is recorded in
[Verification notes](#verification-notes).

### Why it is load-bearing

The review-diversity requirement is owned by
[`10-private-patterns.md`](10-private-patterns.md); what this chapter owns is its Claude Code
consequence. A Claude Code session reviewing Claude Code work does not meet that requirement:
on the documented surface the model family cannot be varied. That is not the definition of a second opinion —
independent same-vendor review can still find defects — and it is not proof that no review
occurred. It is an unmet diversity requirement. The pattern that meets the bar is in
[`10-private-patterns.md`](10-private-patterns.md).

**Failure prevented:** asking Claude Code to audit its own output and treating its agreement as
*diversity-satisfying* validation. Same-vendor review is still review; it does not satisfy this
template's cross-vendor bar.

## What does not differ

Everything vendor-neutral — policy, invariants, workflow, repo conventions, the mental model —
is exactly the same on both harnesses, because pi reads the canonical `AGENTS.md` directly and
Claude Code reads it through the import shim. The split rule, the three tiers, and the per-line
decision test: [`07-instruction-files.md`](07-instruction-files.md). Cross-vendor review lanes:
[`10-private-patterns.md`](10-private-patterns.md). The finite-window economics that make
instruction files the highest-leverage control: [`01-mental-model.md`](01-mental-model.md).
Copy-and-edit starting files for both halves of the split:
[`../templates/global/`](../templates/global/) and [`../templates/repo/`](../templates/repo/),
with a filled-in ordinary-repo example in
[`../examples/ordinary-repo/`](../examples/ordinary-repo/). The adoption sequence that puts
those files in place is [`ADOPTING.md`](../ADOPTING.md).

## Verification notes

Method: every fact above was **source-verified** — fetched from Claude Code's official live
documentation (`https://code.claude.com/docs/en/...`) or the public npm registry — on
**2026-09-14**. **No Claude Code runtime session was executed** (no install, no `claude` launch,
no hook fired) and no claim above depends on one; anything a reader wants runtime-confirmed is
given the upstream command that confirms it (`claude --version`, `claude doctor`, `/context`,
`/model`). Live web docs carry no stable revision hash, so provenance is page + section + fetch
date; re-verify anything with the same fetches, or discover the current page set from the
official index at `https://code.claude.com/docs/llms.txt` (verified present, 356 lines).

| Claim (where in this chapter) | Check performed | Result | Source (page § section) |
|---|---|---|---|
| Native install `curl -fsSL https://claude.ai/install.sh \| bash`; background auto-update | fetched setup page | verbatim | `en/setup` § Install Claude Code / Native installation |
| npm form `npm install -g @anthropic-ai/claude-code`; npm installs the same native binary via per-platform optional deps | fetched setup page | verbatim | `en/setup` § Install with npm |
| npm package engines floor is a lookup, not a literal | `npm view @anthropic-ai/claude-code engines` | `{"node": ">=22.0.0"}` recorded as provenance only | npm registry |
| `claude --version`, `claude doctor` diagnostics | fetched setup page | verbatim | `en/setup` § Verify your installation |
| Account requirement (Pro/Max/Team/Enterprise/Console; free plan excluded); `ANTHROPIC_API_KEY` once-approve path | fetched setup page | verbatim | `en/setup` § Authenticate |
| Third-party providers (Bedrock, Google Cloud's Agent Platform, Microsoft Foundry) serve Claude models | fetched setup + model-config pages | verbatim | `en/setup` § Authenticate; `en/model-config` § Available models |
| Claude Code reads `CLAUDE.md` not `AGENTS.md`; `@AGENTS.md` import pattern is upstream's own recommendation; symlink alternative; Windows admin caveat | fetched memory page | verbatim | `en/memory` § AGENTS.md |
| Memory locations table (user/project/local/managed); concatenation root-down; on-demand subdirectory loads | fetched memory page | verbatim | `en/memory` § Choose where to put CLAUDE.md files |
| `@`-import: relative to containing file; `~` resolves from the home directory (upstream example `@~/.claude/my-project-instructions.md`); max 4 hops; backtick escape | fetched memory page | verbatim | `en/memory` § Import additional files |
| External-import approval dialog; user-scope trusted without dialog | fetched memory page | verbatim | `en/memory` (external-import discussion) |
| Loaded every session; <200-line target; imports do not reduce context; `.claude/rules/` path scoping | fetched memory page | verbatim | `en/memory` § Write effective instructions |
| `/init`, `/memory`, `/context` | fetched memory page | verbatim | `en/memory` § Set up a project CLAUDE.md; § /memory; § /context |
| Hook locations table; entries merge across levels; `disableAllHooks` | fetched hooks page | verbatim | `en/hooks` § Hook locations |
| Hook events (PreToolUse/PostToolUse/UserPromptSubmit/Stop/SubagentStop/SessionStart/SessionEnd/PreCompact/…); matcher mechanics | fetched hooks page | verbatim | `en/hooks` § Hook events; § Matcher patterns |
| Exit 0 / exit 2 blocks (JSON cannot override) / other codes non-blocking; per-event block table | fetched hooks page | verbatim | `en/hooks` § Exit code 0; § Exit code 2; § Exit code 2 behavior per event |
| A hook that can't start is a non-blocking error (mistyped path ⇒ silently disabled gate) | fetched hooks page | verbatim | `en/hooks` (non-blocking error discussion) |
| Hooks run inside subagents; `agent_id`/`agent_type` input fields | fetched hooks page | verbatim | `en/hooks` § Hook locations |
| Skills: `SKILL.md` + frontmatter; Agent Skills open standard; location tiers; `.claude/commands` legacy; `disable-model-invocation` | fetched skills page | verbatim | `en/skills` § Create your first skill; § Choose where skills load; frontmatter table |
| Plugins: `.claude-plugin/plugin.json` manifest; conventional component dirs; `/plugin marketplace add`; `/plugin install name@marketplace`; `--plugin-dir` precedence | fetched plugins + plugin-marketplaces pages | verbatim | `en/plugins` § Plugin structure overview; `en/plugin-marketplaces` § Walkthrough |
| Subagents built-in (contrast with pi's "No sub-agents") | fetched sub-agents page; pi upstream README | verbatim both | `en/sub-agents` § Built-in subagents; `earendil-works/pi` → `packages/coding-agent/README.md` § Philosophy |
| Subagent locations (`.claude/agents/`, `~/.claude/agents/`, plugin `agents/`, `--agents` flag, managed settings); walk-up discovery; description-driven delegation; ~15k-token description warning | fetched sub-agents page | verbatim | `en/sub-agents` § Choose the subagent scope; § Understand automatic delegation |
| `model` field enum: Claude aliases / full Claude model IDs / `inherit`; resolution order (invocation → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → main model) | fetched sub-agents page | verbatim | `en/sub-agents` § Supported frontmatter fields; § Choose a model |
| Spec's model-enum claim re-checked; holds for supported surface; custom-base-URL pass-through edge recorded in-chapter | cross-read of `en/sub-agents` + `en/model-config`; the `fable` alias re-fetched from `en/sub-agents` § Choose a model | confirmed, edge case surfaced; `fable` present verbatim ("`sonnet`, `opus`, `haiku`, or `fable`"), so the four-alias enum is upstream's, not a transcription error | both pages |
| MCP is built-in on Claude Code (`claude mcp add`, `.mcp.json`) — a genuine pi contrast (pi: no MCP by design, adapter package instead) | fetched mcp page | verbatim | `en/mcp` § Installing MCP servers; cf. [`06-memory-mcp-context.md`](06-memory-mcp-context.md) |
| npm package identity: `@anthropic-ai/claude-code`, homepage `github.com/anthropics/claude-code`, license field `SEE LICENSE IN README.md` | `npm view @anthropic-ai/claude-code` (+`--json`) | recorded as provenance | npm registry |

**Not verified at write time (deliberately):** current resolved versions of the family aliases
(runtime facts — `/model`); feature-by-feature availability across Claude Code releases (the
docs pages carry version-gated notes and are the authority); behaviour of any managed-policy or
enterprise deployment mode (no such environment was available, so none is described beyond what
the docs state); star counts or any popularity metric (excluded by this template's
lookup-over-literal rule). The full evidence matrix for the whole template is consolidated in
[`11-verification.md`](11-verification.md).
