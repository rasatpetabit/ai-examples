# Instruction files: the split rule and the hierarchy

This is the chapter readers arrive at when the question is no longer "how do I make pi work"
but "where does **this line** belong, and who owns it once written?" It is the single authority
for one rule: **which file a line of instruction belongs in, and why a rule must never live in
two files at once.** Every other chapter, template, and example in this repository points here
rather than restating the rule, because a rule that is restated is a rule that drifts —
that failure is the subject of this chapter, so this chapter does not commit it.

The rule answers three questions a reader will face the first week they run agents in
parallel on real work:

1. **Scope** — is this line true everywhere, true of this repo, or true of many repos at once?
2. **Vendor** — is this line true of every agent that will ever read it, or only of one harness?
3. **Ownership** — did a human write this line, or does a machine refresh it?

## The three tiers

Instruction files are loaded *every session, from the top*, so their content is the one
control surface that is fully yours: no model vendor ships your rules, no package overrides
them, and you can diff them like any other source file. That leverage is why this chapter
exists and why it comes before the harness-specific chapters.

The tiers are distinguished by **what question they answer**, not by file format. Global and
repo files are Markdown **loaded at session start**. The handbook is Markdown **linked from**
those files; it does not load automatically (see tier 3).

### Tier 1 — global (`~`)

**Holds.** Policy that is true of *you* on every project: how you want agents to behave
regardless of what the code is — working rules, failure modes to avoid, delegation habits,
review discipline, documentation conventions. Nothing that names a repository or a machine
you own, because the file must survive moving to a new laptop and being read while you work
in someone else's checkout.

**Loads.** Once, at session start, in every session — *provided your harness is actually wired to
it*. A global file is only global if the loader reaches it from wherever you work: that is why the
per-harness wiring below matters, and why a session in a checkout outside your home tree may not
see it at all.

**Cost.** **Recurring.** The full text is part of the system prompt every single turn — length
is a cost you pay every session, forever, not a one-time write. A global file therefore earns
each line: it must be a rule you would otherwise re-explain every session.

**Failure prevented:** an agent that behaves one way on Monday in one repo and a different
way on Tuesday in the next, because policy lived in the repo you happened to be standing in —
and the same conversation being spent re-teaching rules you already wrote down.

### Tier 2 — per-repo

**Holds.** What is true of *this repository and no other*: project context (what it is, why
it exists, what it is not), hard rules with the failure each prevents, quirks and gotchas
(the ones that cost you hours to discover), domain conventions, and the commands a new
contributor needs on day one. This tier also owns the repository's handover notes — the file a
future session reads at the start and appends to at the end, so the next session does not
start from zero. When the repo root carries a one-file statement of why the repository exists
and its top invariant, that file sits at this tier. Who may change it, and what an agent must
do when a change and the intent conflict, are carried by the repository's own
consultation-rule block in its `AGENTS.md` — this chapter does not restate that policy.

**Loads.** At session start, concatenated **after** the global tier, so repo-specific policy
refines global policy rather than fighting it from a position of ambiguity.

**Cost.** Recurring for every session run in this repo. Same rule as tier 1: the line earns
its place by changing what the agent does, and nothing else.

**Failure prevented:** an agent re-deriving your project's invariants from the source tree —
which produces work that is locally fluent and structurally wrong, the most expensive class
of agent mistake. Also prevented: two contributors' agents behaving differently in one repo
because the knowledge was never written down.

### Tier 3 — cross-cutting handbook

**Holds.** What is true of *many repos at once* and belongs to none of them individually:
domain-wide boundaries, naming conventions, ownership of shared services, navigation that
points from any repo into the handbook, and runbooks that would otherwise be copy-pasted into
every sibling repo. It lives in its own repository, not inside any implementation repo.

**Loads.** Not automatically — that is the point. A handbook is linked **into** repos through a
pointer block (see "Managed blocks and sentinels" below), so a repo's instructions stay short
while still saying "the authority on domain X lives at this path".

**Cost.** One pointer block per repo, and the discipline to keep the block machine-refreshed.
The handbook itself costs nothing per session until a reader follows the link.

**Failure prevented:** N hand-maintained copies of the same domain rule in N sibling repos —
the failure mode that has already taught this industry about documentation drift, at the
scale of instruction files. When copy 3 of 5 disagrees with copy 5 of 5, an agent that loads
both cannot tell which is stale, and neither can you.

> The tier split is by reader task, not by directory tree. If you cannot say which question a
> line answers — everywhere / this repo / many repos — you cannot say which tier owns it, and
> an agent loading all three gets three answers that do not compose.

## The split rule

Within a tier, the second axis is **vendor**. The rule:

> **`AGENTS.md` is canonical.** It holds everything vendor-neutral: policy, invariants,
> workflow, repo conventions, and anything true of more than one harness. It also holds a
> *description* of another harness's behaviour when that description is useful to every
> agent ("Claude Code has no `@AGENTS.md` unless you import it"). Exclusive *mechanics*
> of one harness (tool names, hook events, slash commands) do **not** belong here.
>
> **`CLAUDE.md` holds Claude-Code-specific mechanics only**: the names of Claude's own tools,
> its hooks and their triggers, its slash commands, its plugin and skill mechanics — and it
> is a thin shim: one `@`-import of `AGENTS.md`, then Claude-only mechanics beneath it.
>
> **pi reads `AGENTS.md` directly.** Most repositories have no separate pi overlay: put
> pi-only *repository* instructions in that repo's `AGENTS.md` (pi loads it; a
> Claude session ignores pi-only lines via the per-line test). A **user-global** pi overlay
> (`~/.pi/agent/AGENTS.md` as a mechanics appendix) is optional, and it is not a second
> canonical file.

The reason this split exists is mechanical, not aesthetic:

- **pi** concatenates `AGENTS.md` (or `CLAUDE.md`) from the global agent directory, every
  parent directory above your working directory, and the current directory, at startup. Where
  both exist in one directory, pi's candidate order is `AGENTS.override.md`, then `AGENTS.md`,
  then `CLAUDE.md` — so a repo that ships both canonical and shim gives pi the canonical file
  directly.
- **Claude Code** reads `CLAUDE.md`, not `AGENTS.md`. Its documented bridge is exactly the
  shim: create a `CLAUDE.md` containing `@AGENTS.md` and add Claude-specific instructions
  below the import; Claude loads the imported file at session start, then appends the rest.
  A symlink is the zero-mechanics alternative when there is no Claude-only content.

So the split is not a preference about file naming. It is the only arrangement in which the
vendor-neutral policy is **written once** and every harness reads **the same copy**: pi reads
it natively; Claude Code expands it into its own memory file through an import; any future
harness that reads `AGENTS.md` (now a widely-shared convention) gets it for free. Any other
arrangement forces you to maintain two copies of your policy — the failure described in
"Why duplication fails", below.

### What "vendor-neutral" does not mean

`AGENTS.md` is not "generic advice for some hypothetical agent". It is the real, complete
policy file — every rule you would otherwise write twice. The vendor-neutral test is about
**which agent a sentence is *useful to***, not about watering it down to the lowest common
denominator. Concretely:

- **"Run tests before reporting done"** — true of every agent that can run commands →
  `AGENTS.md`.
- **"The `/review` command maps to the team's code-review skill."** — names a harness
  slash command, meaningless to a harness without it → `CLAUDE.md`.
- **"When Claude Code spawns a subagent, the child's tool-call events reach a parent-side
  observer with the parent's session identifiers"** — a sentence *about* Claude Code, but
  true and useful to any agent that must reason about attribution, and loadable in every
  harness → `AGENTS.md`. Describing another
  harness's behaviour is the canonical file's job, **never** the overlay's, because the
  overlay is the one file the other harnesses never load.

## The per-line decision test

The canonical statement of the test — apply it to **every line before you write it**, in
whichever file you were about to write it in:

> *would this sentence still be true and useful for an agent that is not Claude Code?*

- **Yes** → it belongs in `AGENTS.md`.
- **No — it names a Claude Code tool, hook, or command and would be meaningless elsewhere** →
  it belongs in `CLAUDE.md`.
- **It is true of pi mechanics only** — a pi flag, a pi extension, a pi config key — →
  **repository:** that repo's `AGENTS.md` (pi loads it; Claude does not act on it).
  **User-global optional overlay:** `~/.pi/agent/AGENTS.md` *appended after* the canonical
  global policy, never as a replacement. A pi-only sentence in the Claude overlay is a
  sentence the only reader that could use it never loads.

Two corollaries the test produces, which readers otherwise get wrong:

1. **The test is per-line, not per-file.** A file is not "Claude's file" or "pi's file"; each
   sentence inside it is classified individually. This is why the canonical file can
   legitimately contain a sentence *about* Claude Code (corollary above) while the Claude
   overlay contains only Claude mechanics.
2. **The test classifies by usefulness, and the answer can change.** When a harness-specific
   mechanism gains a vendor-neutral equivalent — when "run it" becomes a rule any agent can
   follow — the sentence moves from the overlay to the canonical file. Re-run the test when
   the fact changes, not on a schedule.

## How each harness actually loads these files

The rule above is only worth following because the mechanics underneath it are what they are.
Every fact in this section was verified against the live upstream sources cited in
"Verification notes".

### pi (the worked example, and the recommendation)

- Context files: `~/.pi/agent/AGENTS.md` (global), then **every parent directory** walking up
  from the working directory, then the current directory. All matching files are concatenated,
  in that order, with duplicates suppressed by path.
- Per directory, pi tries `AGENTS.override.md`, then `AGENTS.md`, then `CLAUDE.md`, and loads
  the first that exists — an override **replaces** that directory's file; other directories
  still contribute theirs.
- A linked git worktree's own copy of the file shadows the main repository's copy (both would
  occupy the same logical repository scope, so loading both would apply that context twice);
  normal ancestor inheritance is untouched.
- Disable all of it for one run with `--no-context-files` / `-nc`.
- The global system prompt can be replaced entirely with `.pi/SYSTEM.md` (project) or
  `~/.pi/agent/SYSTEM.md` (global), and appended to without replacing via `APPEND_SYSTEM.md`
  — a mechanism the handbook tier can use to add load-bearing text without owning the whole
  prompt.
- **pi strips a UTF-8 BOM from context files and nothing else.** HTML comments are not
  removed: a `<!-- ... -->` comment in a pi context file is sent to the model, token for
  token. (Verified: pi's context loader reads the file, strips the BOM, and hands the raw
  content to the prompt; there is no comment stripping anywhere on that path.) Budget
  comments in pi context files accordingly — they are not free, and a comment that is only
  meaningful to a human maintainer costs every session.
- pi has **no `@`-import syntax for context files**. The concatenation is the mechanism. To
  point a pi context file at another document, write the path in prose — the model follows it
  with `read` when the pointer is actionable, and a reader sees the same pointer.
- pi has **no built-in permission system** and no plan-mode or subagent primitives; those are
  extension-supplied. Name that fact in canonical `AGENTS.md` so every harness sees it; put
  the extension's own tool names and events in the optional pi overlay (or, at repo scope, in
  that repo's `AGENTS.md`).

### Claude Code (the companion track)

- Memory files: managed policy locations (IT-controlled), user `~/.claude/CLAUDE.md`, project
  `./CLAUDE.md` or `./.claude/CLAUDE.md`, plus `CLAUDE.local.md` beside any of them, loaded in
  that broad-to-specific order and concatenated, not overridden.
- `@path/to/file` imports are expanded at launch. How a path resolves, how deep imports
  recurse, and how to mention a path without importing it are the import syntax, owned by
  [docs/09-claude-code.md](09-claude-code.md).
- External imports (a project-level memory file importing something outside the working
  directory, like the canonical global policy from your home directory) trigger a one-time
  approval dialog the first time; user-scope memory files import without the dialog.
- Claude Code **does** strip block-level HTML comments from memory files before injecting
  them into context — comments are for maintainers and cost no tokens there, though they are
  visible when the file is read directly.
- What Claude Code does *not* do: read `AGENTS.md` natively. The `@AGENTS.md` shim is the
  documented bridge, and it is why the canonical file can be one file instead of two.

### The asymmetry worth planning around

Because pi loads context files by concatenation and Claude Code loads memory files by
expansion of imports, a comment costs tokens in one and not the other, an import is a
directive in one and prose in the other, and a file that is "one `@`-import plus a paragraph"
in Claude Code is simply "a paragraph that says see `AGENTS.md`" in pi. The split rule keeps
the policy identical across harnesses while leaving each harness its own mechanics for
pointing at it — that is the intended outcome, not a wart.

## Why duplication fails: drift

The failure the split rule prevents is not "wasted tokens", though duplication wastes those
too. It is that **two copies of a rule drift, and a drifting copy is worse than no copy**:

- You update the rule in the copy you were looking at. The other copy now says something
  different — often something that used to be true, which is the most misleading category of
  instruction a model can load.
- No reader, human or model, can tell which copy is authoritative. A human sees two rules and
  picks the one they agree with; a model loading both sees a contradiction, and
  **contradiction produces arbitrary behaviour**: Claude Code's own documentation states that
  when two rules conflict, the model may pick one arbitrarily — which means the rule you did
  not intend becomes as load-bearing as the one you did.
- Drift compounds silently. The two copies disagree by one line, then by a paragraph, then
  one of them describes a harness feature the other never had.

**Failure prevented:** a future maintainer — or a future model — following a stale copy of a
rule that contradicts the live one, with no way to tell which is which. The repair is
structural, not diligent: **a rule never lives in both.** The overlay points at the
canonical file rather than repeating it, and every other document in this guide follows
the same discipline — this chapter links to the templates and examples rather than
duplicating their contents.

This is also the reason the handbook tier uses a **pointer block** instead of copy-paste:
when the shared rule changes, one edit in the handbook refreshes every repo that points at
it, and no repo's copy can silently disagree with the authority it cites.

## Pointer mechanisms

There are exactly three legitimate ways for one instruction file to refer to another without
duplicating it:

| Mechanism | Where it works | Rule |
|---|---|---|
| `@path/to/file` import | Claude Code memory files | One per file, pointing at the canonical `AGENTS.md`. The import syntax — how a path resolves, how deep imports recurse, and how to mention a path without importing it — is owned by [docs/09-claude-code.md](09-claude-code.md). |
| Prose pointer | Every harness, including pi | A sentence that names the path and what it answers. The model follows it with `read` when actionable. This is the only mechanism pi has, so the canonical file's pointer is prose in pi and an import in Claude Code — same rule, two syntaxes. |
| Symlink | Anywhere the filesystem permits | The zero-mechanics shim: `CLAUDE.md` → `AGENTS.md` when there is no Claude-only content. Note the costs: it needs privileges on some platforms, and Claude Code treats a symlinked user-scope memory file pointing outside the working directory as external, skipping it in some session types rather than loading it silently. |

Rules that make pointers safe to follow:

- A pointer is a promise that the target answers a question. Never point at a file that does
  not exist — verify every pointer after moving any file. **Failure prevented:** a dead
  pointer, which is worse than no pointer — a model still follows it, wastes a turn, and
  learns your instructions rot.
- Pointer-only shims stay pointer-only. A shim that grows real policy re-creates the
  duplication the shim exists to prevent. **Failure prevented:** two diverging copies of the
  same rule, indistinguishable in authority — the drift failure, smuggled back in through
  the file that was supposed to prevent it.
- A pointer block that is machine-refreshed is **not** yours to hand-edit; see the next
  section.

## Managed blocks and sentinels

Some regions of an instruction file are **machine-owned**: a script writes and refreshes
them, so the information is identical across many repos and stays identical as the source
changes. The convention is a pair of HTML comments marking the region:

```markdown
<!-- handbook-pointer:start -->
... content a stamping script owns ...
<!-- handbook-pointer:end -->
```

- **Everything between the sentinels belongs to the machine.** A hand edit inside them is
  silently overwritten by the next refresh. If the block is wrong, the fix is in the
  **source** the script stamps from — never in the stamped copy, because your edit has a
  short lifetime and no one will know it was yours.
- **Everything outside the sentinels belongs to humans.** A well-behaved stamper replaces
  only the bytes between an ordered marker pair and leaves the surrounding file untouched,
  so hand-written policy and the machine block coexist in one file without fighting.
- Sentinels are the mechanism that makes the handbook tier affordable: one script, run when
  the handbook changes, stamps the current navigation into every sibling repo. Without them,
  keeping N repos' pointers current is N manual edits, and the first skipped edit is the
  first drifting copy.
- Marker discipline: a missing, duplicated, or reversed pair is a defect, and a stamper
  must reject it rather than "fix" it. The complete placement and validation contract — which
  is stricter than "anywhere in the file", and why — is owned by
  [docs/08-cross-cutting-docs.md](08-cross-cutting-docs.md).

**Failure prevented:** a human edit inside a machine-owned region being silently lost on the
next refresh — the contributor concludes their change was "ignored", re-applies it by hand
into a copy that will be refreshed again, and the loop repeats; or worse, they stop trusting
the block entirely and hand-maintain a parallel copy that drifts.

Where sentinels cost tokens: in pi context files the marker comments are **sent to the
model** (pi does not strip HTML comments), so keep the machine block's marker lines short and
do not use the marker pair as a place to write prose for humans. In Claude Code memory files
block-level comments are stripped before injection, so the same markers cost nothing. See
"How each harness actually loads these files".

## Copy destinations and path adjustment

The templates and examples in this repository are starting points, not finished policy — they
are skeletons with section guidance and neutral placeholder names, and the value you add is
your own content. Where each shipped file goes:

| Shipped file | Destination | What must be adjusted after copying |
|---|---|---|
| `templates/global/AGENTS.md` | **Multi-harness:** `~/AGENTS.md`. **Pi-only home:** you may put it at `~/.pi/agent/AGENTS.md` *if that is your only global file*. | Fill in your own policy per section; delete section guidance you do not use. Do not copy this guide's chapters into it — link, don't duplicate. |
| `templates/global/CLAUDE.md` | `~/CLAUDE.md` — the **home-root pointer**, not the global instructions file. It deliberately contains no import; it exists only to stop a policy copy landing there by accident. | Delete its fenced template block after copying (the file says so), and drop its repo-relative links — they do not resolve outside this repository. |
| `templates/global/claude-overlay.md` | `~/.claude/CLAUDE.md` — **this** is the global instructions file, and it carries the `@`-import of the canonical policy. | Confirm the `@`-import resolves to the canonical file's actual location after copying. How import paths resolve is owned by [docs/09-claude-code.md](09-claude-code.md). Claude mechanics only. |
| `templates/global/pi-overlay.md` | **Do not copy over the canonical file.** If you keep canonical policy at `~/AGENTS.md`, point pi at the canonical via a one-line `~/.pi/agent/AGENTS.md` that tells the model to treat `~/AGENTS.md` as policy (a prose pointer; pi has no `@`-import), with this overlay's mechanics underneath it. Do **not** keep a hand-concatenated second copy of the canonical at that path: it is the duplication this chapter exists to prevent, and where both paths load you get the same policy twice in context. | pi mechanics only. |
| `templates/repo/AGENTS.md` | Per-repo `AGENTS.md` at the repo root | Replace placeholders with your project's real context, rules, and conventions. |
| `templates/repo/CLAUDE.md` | Per-repo `CLAUDE.md` beside it | Keep the `@AGENTS.md` import; add repo-specific Claude mechanics beneath it, or nothing at all. |
| `templates/repo/INTENT.md` | Per-repo root | Your why / top invariant / non-goals / direction / posture. Who may change it, and what an agent does on a conflict, are owned by the repository's own consultation-rule block. |
| `templates/repo/WORKLOG.md` | Per-repo root | This file owns the convention; keep it as shipped and add your first entry. |
| `examples/ordinary-repo/AGENTS.md` | Copyable reference, not a direct copy | The pointer block between its sentinels is stamped for the example's sibling-handbook layout — if your handbook lives elsewhere, re-stamp rather than hand-edit. |
| `examples/handbook/` | Copyable reference | See `docs/08-cross-cutting-docs.md` for the stamping mechanism it demonstrates. |

A note on "the home root": the canonical global policy file lives at the root of your home
directory (`~/AGENTS.md`) when you run harnesses that load from the home root, and at
`~/.pi/agent/AGENTS.md` when pi is your harness — pi loads the global context file from its
agent directory. The **rule** is the same either way: one canonical file, one overlay per
harness, pointers from every other surface. Do not maintain a home-root `AGENTS.md` and a
separate pi-global `AGENTS.md` as two independent policies; that is the duplication failure
in its most common real-world form. If both locations must exist (for harnesses with
different discovery roots), one should be a pointer to — or a link of — the other, and only
one is ever edited.

## Worked examples of the test

Lines, classified. The value of these is the boundary cases.

| Line under test | Verdict | Why |
|---|---|---|
| "Fix failing pre-commit hooks rather than committing around them." | `AGENTS.md` | True of any agent that can run `git commit`. Nothing Claude-specific about it. |
| "Use the `/model` command to switch providers." | pi overlay | A pi slash command; Claude Code has its own distinct model-selection UI. |
| "When Claude Code spawns a subagent, the child's tool-call events reach a parent-side observer with the parent's session identifiers — a rule about attribution must not be written assuming each agent sees only its own events." | `AGENTS.md` | It is *about* Claude Code, but it is true and useful to every agent reasoning about attribution across harnesses. The canonical file describes other harnesses' behaviour; overlays never do. |
| "The adversarial-review subagent role is dispatched before a confident completion claim." | `AGENTS.md` | Vendor-neutral: a role definition, not a harness tool name. Which harness supplies subagent mechanics is a separate, overlay-level fact. |
| "A pre-tool hook named for plan review fires on `ExitPlanMode`." | `CLAUDE.md` | Names a Claude Code hook (`PreToolUse`) and its Claude-specific trigger tool (`ExitPlanMode`, which presents a plan for approval and exits plan mode). Both are documented Claude Code mechanics; meaningless to pi. |
| "Ask before editing any harness `settings.json`." | `AGENTS.md` | True of every agent that can edit files — Claude Code's settings, pi's settings, any future harness's settings. |
| "Use the extension's context-management tool for long raw outputs, so large command output does not flood the window." | pi overlay | Names a tool that exists only when a specific pi extension supplies it; another harness has different context-management mechanics. |
| "A completed claim needs a second set of eyes from a governed review route." | `AGENTS.md` | Vendor-neutral policy. *How* to invoke the reviewer is overlay mechanics; *that* it must happen is canonical. |
| "The `Skill` tool bootstrap loads `SKILL.md` files." | `CLAUDE.md` | Names Claude Code's `Skill` tool. pi loads skills by a different mechanism, described in the pi overlay and the skills chapter. |

The two rows worth staring at are rows 3 and 8. Row 3 is the corollary that surprises
readers: **describing another harness's behaviour is `AGENTS.md`'s job, not the overlay's** —
because the overlay is the one file the other harnesses never load, so a sentence about
Claude Code that lives in the Claude overlay is a sentence whose only possible readers
already know it. Row 8 is the other side: a *policy* (review before confidence) is canonical
even when the *mechanism* that implements it (which tool to call) is overlay-specific. Policy
belongs to the thing being protected, not to the tool that happens to enforce it today.

## Verification notes

Every version-sensitive claim in this chapter was checked against live sources during
writing. This is the claim-to-source record; re-run the commands to
re-verify anything here. Where a claim could not be verified from a source, it is stated as
such rather than smoothed over.

| # | Claim in this chapter | How verified | Result | Public source | Section | Revision |
|---|---|---|---|---|---|---|
| 1 | pi loads `AGENTS.md` (or `CLAUDE.md`) from the global agent dir, parents, and cwd; concatenates all; `AGENTS.override.md` replaces that directory's file; `--no-context-files` disables | Fetched `packages/coding-agent/README.md` from pristine upstream; read § Context Files | Confirmed, text quoted in the source row | https://github.com/earendil-works/pi → `packages/coding-agent/README.md` | § Context Files | repo commit `71dca871bc80b6bc97be37f0ca3189399d651fff` (main, 2026-09-11) |
| 2 | Per-directory candidate order is `AGENTS.override.md`, `AGENTS.md`, `AGENTS.MD`, `CLAUDE.md`, `CLAUDE.MD` — pi reads the canonical file where both exist | Read the loader source at that revision: `loadContextFileFromDir` candidate list | Confirmed — upstream's README does not state the precedence, so this claim is sourced from code, and that is recorded here | https://github.com/earendil-works/pi → `packages/coding-agent/src/core/resource-loader.ts` | `loadContextFileFromDir` | `71dca871bc80b6bc97be37f0ca3189399d651fff` |
| 3 | Linked-worktree copy shadows the main repo's copy for the same logical scope | Same source file, `findShadowedContextFile` + call site | Confirmed | same file | `findShadowedContextFile` | `71dca871bc80b6bc97be37f0ca3189399d651fff` |
| 4 | pi strips a UTF-8 BOM and does **not** strip HTML comments from context files | Grepped the context-loading path in source at that revision for comment handling: only `stripBom` is applied | Confirmed — no comment stripping exists on the context-file path | `packages/coding-agent/src/core/resource-loader.ts` + `src/utils/text.ts` (`stripBom`) | `loadContextFileFromDir` | `71dca871bc80b6bc97be37f0ca3189399d651fff` |
| 5 | pi has no `@`-import syntax for context files | Searched the upstream README and `docs/` (25 files) for any import directive for context files; none exists | Confirmed as an absence, by exhaustive search of the shipped docs | https://github.com/earendil-works/pi → `packages/coding-agent/README.md` § Context Files + `docs/` directory listing | — | `71dca871bc80b6bc97be37f0ca3189399d651fff` |
| 6 | pi has no built-in permission system; no MCP/subagents/plan-mode/to-dos in core; those come from extensions/packages | Fetched `packages/coding-agent/README.md` § Philosophy and monorepo root `README.md` § Permissions & Containerization | Confirmed; upstream states each absence explicitly with a named alternative | https://github.com/earendil-works/pi → `packages/coding-agent/README.md` § Philosophy; root `README.md` § Permissions & Containerization | as named | `71dca871bc80b6bc97be37f0ca3189399d651fff` |
| 7 | Claude Code reads `CLAUDE.md`, not `AGENTS.md`; the documented bridge is a `CLAUDE.md` containing `@AGENTS.md` plus Claude-specific content below, with a symlink alternative. The import syntax itself (path resolution, recursion depth, mention-versus-import) is stated in [`09-claude-code.md`](09-claude-code.md) rather than enumerated here | Fetched the live documentation page and read § AGENTS.md, § Import additional files, § How CLAUDE.md files load | Confirmed; all quoted from the page | https://code.claude.com/docs/en/memory | § AGENTS.md, § Import additional files, § How CLAUDE.md files load | live page, fetched 2026-09-14; docs carry no in-page version |
| 8 | Claude Code strips block-level HTML comments from memory files before injection; comments inside code blocks are preserved | Same page, the note on maintainer comments | Confirmed | same page | "Block-level HTML comments … are stripped" | fetched 2026-09-14 |
| 9 | Two contradictory instructions may be resolved arbitrarily by the model | Same page, § Best practices for writing CLAUDE.md (consistency) | Confirmed — this grounds the drift-failure section | same page | § Best practices → Consistency | fetched 2026-09-14 |
| 10 | Claude Code external-import approval dialog; user-scope memory imports without dialog; symlinked user-scope memory files pointing outside the working directory are skipped in some session types | Same page, § Import additional files → Warning, and the symlink note | Confirmed | same page | as named | fetched 2026-09-14 |
| 11 | pi's context files cost tokens every turn because they are part of the system prompt; skills' `SKILL.md` bodies are loaded on demand and "models don't always do this" | Fetched `packages/coding-agent/docs/skills.md` § How Skills Work; the system-prompt/per-turn cost is a first-principles consequence stated in the mental-model chapter, not a quoted upstream claim | Partially verified — the quote is upstream; the token-cost framing is derived, not quoted. The derivation is in `docs/01-mental-model.md`, which owns it | https://github.com/earendil-works/pi → `packages/coding-agent/docs/skills.md` | § How Skills Work | `71dca871bc80b6bc97be37f0ca3189399d651fff` |
| 12 | Sentinel comments `<!-- handbook-pointer:start -->` / `<!-- handbook-pointer:end -->` and the machine-owned-region convention | This is a **convention defined by this template's handbook example and its stamping script**, not an upstream pi or Claude Code feature | Verified as a convention of this template: the markers are defined by `examples/handbook/`'s stamping script, which validates and replaces exactly the bytes between one ordered pair. Upstream's HTML-comment stripping (claims 4 and 8) is what makes the convention viable in Claude Code and is why pi context files must keep marker lines short | this template → `examples/handbook/` (see `docs/08-cross-cutting-docs.md` for the mechanism) | — | re-run the handbook stamping self-test |
| 13 | `/model` is a pi slash command for switching models (used as a worked example of a pi-mechanics line) | Fetched `packages/coding-agent/README.md` § CLI Reference (slash-command table) | Confirmed: `/model` listed as "Switch models; Ctrl+S in the picker saves the startup default" | https://github.com/earendil-works/pi → `packages/coding-agent/README.md` | § CLI Reference | `71dca871bc80b6bc97be37f0ca3189399d651fff` |
| 14 | Claude Code has a `PreToolUse` hook and an `ExitPlanMode` tool ("presents a plan for approval and exits plan mode"), both usable as worked examples of Claude-mechanics lines | Fetched the live hooks and tools reference pages | Confirmed: `PreToolUse` runs before every tool call; `ExitPlanMode` is a listed built-in tool | https://code.claude.com/docs/en/hooks and https://code.claude.com/docs/en/tools-reference | hooks lifecycle; tools table | live pages, fetched 2026-09-14 |
| 15 | Claude Code has a `Skill` tool (used as a worked example of a Claude-mechanics line) | Fetched the live skills page | Confirmed: skills are invoked through the `Skill` tool; `disable-model-invocation` hides one from it | https://code.claude.com/docs/en/skills | § Skill invocation | fetched 2026-09-14 |

### Claims intentionally **not** made

- **Not verified:** that every other agent harness now reads `AGENTS.md`. The claim made is
  narrower and safe: pi reads it natively, Claude Code reaches it through a documented
  `@`-import, and the file is a widely-shared convention. A census of which harnesses read
  `AGENTS.md` natively was not performed for this chapter, so no such claim appears in the
  guidance.
- **Not claimed:** that comment stripping or import depth on either side is stable across
  versions. Both are behaviour that can change; the per-line split rule does not depend on
  them, which is why the rule is stated independently of the mechanics that ground it.
- **No pinned versions anywhere**, per the anti-pinning rule owned by
  [README.md](../README.md) ("Lookup over literal"). pi's current version is reported by
  `npm view @earendil-works/pi-coding-agent version`, and the revision cited in the table is
  citation provenance — the state of upstream at fetch time — not a pin your install should
  reproduce. `docs/11-verification.md` owns the re-verification commands for every
  version-sensitive claim in this template.

### What this chapter deliberately does not cover

The templates (`templates/global/`, `templates/repo/`) apply this rule — they do not restate
it; their section lists point back here. The handbook example (`examples/handbook/`) and the
`docs/08-cross-cutting-docs.md` demonstrate the stamping mechanism this chapter names; the
Claude-Code-specific mechanics (hooks, their triggers, plugin mechanics, subagent model
constraints) live in `docs/09-claude-code.md`, which is the overlay chapter to this one and
covers only what differs there.

The per-line test, the tier definitions, and the drift-failure statement are the three things
to take away; everything else in this chapter is grounding or consequence. If you remember
only one line, remember the test:

> *would this sentence still be true and useful for an agent that is not Claude Code?*
>
> Yes → `AGENTS.md`. No → the overlay for the harness it names.
