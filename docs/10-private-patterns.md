# 10 — Private patterns, public primitives: four honest recipes

The reference setup this template generalizes from runs on a private layer: a hooks and policy
engine that enforces rules deterministically on two harnesses, a dispatch gateway that routes task
classes to governed model lanes, review lanes that guarantee the reviewer is not the author's
vendor, and an orchestration system that runs multi-agent plans in waves with verified, durable
output. **None of that is installable by you.** It lives on private infrastructure, and this
template's anti-goal list is explicit: it is not a reimplementation of the private infrastructure.

What you get instead is this chapter: the four patterns described honestly — the problem each one
solves, the observable failure it prevents, the *shape* of the mechanism, and the smallest useful
version you can build today from public, upstream-verifiable primitives. The recipes are starting
points. They are **not installable as the private system, and they are not equivalents or
implementations of it** — the private layer has properties (cross-harness state attribution,
revert-on-out-of-scope edits, governed lane registries) that no recipe below reproduces, and each
recipe's *Limits* section says so plainly.

Why bother, if none of it is installable? Because the *reasoning* is the transferable part. Each
recipe exists because a cheaper mechanism failed first, and knowing which failure produced which
mechanism is what lets you judge whether you need the mechanism at all. That is the posture of this
whole template: rules you can judge, not rules you copy.

A note on terminology before the recipes: *harness* means the agent program the model runs inside
(pi, or a second agent CLI). *Vendor* means the company that trained the model. *Lane* means a
configured model a task can be routed to. *Role* means a named, reusable agent definition a task
can be delegated to. None of these is a pi concept — pi core has none of them — so each arrives only
through public packages or files you write.

## What this chapter assumes

- You have pi installed and authenticated (`docs/02-install.md`).
- You know what packages are and how the packages CLI works (`docs/04-packages.md`), including the
  execution-authority boundary: pi packages run with full system access and extensions execute
  arbitrary code — which is why the review rule in `docs/04-packages.md` applies to everything
  named here.
- You know that skills fire *probabilistically* — a description decides whether the model reaches
  for it, and "models don't always do this" is upstream's own wording
  (`earendil-works/pi` → `packages/coding-agent/docs/skills.md` § How Skills Work, step 3). Recipe 1 is the
  honest answer to "the model doesn't always load my skill": a behaviour that must always happen
  cannot live only in prose or a skill description.
- You know the instruction-file split rule (`docs/07-instruction-files.md`), because every recipe
  below ends by writing a rule into an instruction file. Where that rule goes is the split rule's
  business, and the chapter owns it.

## Recipe 1 — A unified hooks and policy engine

### Problem

You write a rule in an instruction file — "never force-push `main`", "never commit credentials" —
and it works, for a while. Then a session violates it. You correct the session; it apologizes;
some sessions later it violates it again. Instruction-file prose is *advisory*: the model reads it,
understands it, and can still act against it, because nothing deterministic stands between the
model's decision and the tool that executes it. A rule that has been violated once and matters
gets violated again, and each violation costs a human's attention.

This is the same fact as the probabilistic skill invocation in `docs/05-skills.md`, one level up:
a *must-happen* behaviour encoded as prose is a suggestion with good manners.

### Failure prevented

A repeated correction with no enforcement loop: you explain the rule to the model for the fifth
time, and nothing about the fifth explanation is different from the first. Also, silently disabled
policy: a gate whose script path is mistyped fails by letting everything through, so the first run
of any gate must be watched. And policy drift: the same rule restated in two harnesses' configs
diverges until neither copy matches reality — the duplication failure `docs/07-instruction-files.md`
explains for prose applies with more force to enforcement config.

### Mechanism

The private system's shape, minus every private detail:

1. **One declarative policy file** — not code. Each rule is data: an identifier, the event it
   guards, a matcher narrowing which calls it inspects, a verdict (`block` or `allow`), and a human
   reason string. The reason is part of the rule, not a comment beside it: when a rule fires, the
   *reason* is what the model and the human see, so a rule that cannot explain itself cannot ship.
2. **One thin adapter per harness**, translating the shared file into that harness's native refusal
   shape. Nothing but the translation lives in the adapter; if logic accumulates there, you have
   rebuilt the problem as code.
3. **One entry point** that lists what runs and in what order, explains each rule, and reports
   health — so "why was my command blocked?" has a command that answers it, and a broken gate is
   discoverable instead of silent.

**Failure prevented:** rules that read as data get reviewed, diffed, and explained; rules that
live in adapter code get edited by whoever is debugging the adapter, for reasons that stop being
remembered by the time the diff lands.

Both halves of this are public primitives:

- **pi:** extensions subscribe to lifecycle events. The `tool_call` event fires before a tool
  executes, can inspect the tool name and its arguments, and can block by returning
  `{ block: true, reason: "..." }` — this is upstream's own first example, blocking
  `rm -rf`, in `earendil-works/pi` → `packages/coding-agent/docs/extensions.md` § Events → Tool
  Events. Handlers can also mutate arguments in place before execution. A command registered with
  `pi.registerCommand(name, { handler })` becomes your entry point. Extensions are plain
  TypeScript files auto-discovered from `~/.pi/agent/extensions/` (global) or `.pi/extensions/`
  (project-local, after the project is trusted).
- **The other harness:** Claude Code runs user-defined hooks at lifecycle points; a `PreToolUse`
  hook receives the tool call as JSON on stdin and can return
  `hookSpecificOutput.permissionDecision: "deny"` with a `permissionDecisionReason`, configured in
  `~/.claude/settings.json` or a project `.claude/settings.json`. Upstream's own first example is
  the same `rm -rf` block. Public reference: `code.claude.com/docs/en/hooks` (§ Hook lifecycle,
  § How a hook resolves). What differs between the harnesses lives in `docs/09-claude-code.md`.

The two refusal shapes are different (`{ block: true, reason }` vs `permissionDecision: "deny"`),
which is exactly why the policy file is data and the adapters are thin: one rule, two
translations, zero duplication.

### Smallest useful version

Build it in three rungs. Each rung is independently useful, and each one is the smallest honest
step toward the next — do not skip to the policy file before you have watched one refusal fire.

**Rung 1 — log every tool call.** One extension, no policy, no refusal:

```typescript
// ~/.pi/agent/extensions/audit-log.ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { appendFile } from "node:fs/promises";
import { homedir } from "node:os";

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, _ctx) => {
    // append-only; a log you never read is still evidence for "what did it try?"
    await appendFile(
      homedir() + "/.pi/agent/audit-log.jsonl",
      JSON.stringify({ ts: new Date().toISOString(), tool: event.toolName, input: event.input }) + "\n",
    );
  });
}
```

Read a day of it before adding anything. The log tells you which rules you actually need — writing
policy from imagination is how you get rules that never fire.

**Rung 2 — refuse one named dangerous thing.** Same file, one hardcoded refusal, no config yet.
`pi` exists only as the parameter of the default-exported function from Rung 1 — put this
registration **inside that function**, next to the log handler. Do not paste it at module scope.
Use upstream's own narrowing helper rather than ad-hoc casts:

```typescript
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // ... Rung 1 log handler still here ...
  pi.on("tool_call", async (event, _ctx) => {
    if (isToolCallEventType("bash", event) && event.input.command.includes("rm -rf")) {
      return { block: true, reason: "Refused: recursive force-delete. Ask if you really mean it." };
    }
  });
}
```

The narrowing helper is upstream's documented pattern for typed built-in tool inputs (`packages/coding-agent/docs/extensions.md` § Events → Tool Events): `isToolCallEventType("bash", event)` gives `event.input` as `{ command: string; timeout?: number }` without casting.

Watch the first refusal. **Failure prevented:** a gate that has never fired is indistinguishable
from a broken gate; the first live denial is the only proof the wiring works.

**Rung 3 — read the refusals from a policy file.** Move the rule into data, e.g.
`~/.pi/agent/policy.json`:

```json
[
  {
    "id": "no-force-delete",
    "event": "tool_call",
    "tool": "bash",
    "pattern": "rm -rf",
    "verdict": "block",
    "reason": "Recursive force-delete is never routine. Ask the human."
  }
]
```

and make the extension load and iterate it at startup, plus one command that prints each rule with
its reason:

```typescript
pi.registerCommand("policy", {
  description: "List the loaded guard rules and their reasons",
  handler: async (_args, ctx) => {
    const rules = await loadPolicy(); // read the same JSON the guard loop uses
    for (const r of rules) ctx.ui.notify(`${r.verdict}: ${r.id} — ${r.reason}`, "info");
  },
});
```

Now the Claude Code side needs only a hook *script* that reads the same `policy.json` and, for a
matching `PreToolUse` input (read as JSON on stdin), prints the deny envelope on stdout and exits 0:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Recursive force-delete is never routine. Ask the human."
  }
}
```

Exit 0 printing nothing means "no decision — the normal permission flow applies", the exit-code
contract [`09-claude-code.md`](09-claude-code.md) owns. A dozen lines of any scripting language,
because the file carries the semantics. One policy file, two harnesses, one command that
explains the rules: that is the whole shape of the private system, at a fraction of the size and
with none of its guarantees.

### Limits

- **This is not a sandbox.** Upstream is explicit that pi has no built-in permission system and
  runs with the full authority of the user and process that launched it
  (`earendil-works/pi` → `README.md` § Permissions & Containerization, monorepo root). A refusal
  gate makes specific named mistakes *loud*; it does not contain a model that is creative about
  which tool it uses. Containment is containerization — upstream names the Gondolin extension,
  plain Docker, and OpenShell in `packages/coding-agent/docs/containerization.md`, and this
  template points at them rather than teaching them (see `docs/02-install.md`).
- **Preflight sees only what the event payload shows.** A `bash` preflight inspects the command
  string; it cannot see what a script the command invokes will do. A write-path check sees the
  path argument, not what an interpreter later writes. Treat these gates as tripwires, not walls.
- **A broken gate fails open.** A mistyped path or a syntax error in the adapter means no
  enforcement, not an error. Listing loaded policy JSON proves the file parsed; it does not prove
  the adapter is wired. Confirm a dead gate with a harmless matching tool call through each
  harness that you expect to deny.
- **Order and attribution are unsolved here.** The private engine runs an ordered rule set with
  per-session attribution so a delegation's calls are attributable to the delegation. The smallest
  version has neither; pi's `tool_call` gives you the event and the input, and that is all.
- **No rule survives contact with a second author unless it carries its reason.** If the reason
  string is empty, the rule will be deleted by the next person who finds it annoying, correctly.

## Recipe 2 — A model-dispatch gateway

### Problem

You have more than one model available — different providers, different price points, different
blind spots — and the naive way to use that is to hardcode a model name into every prompt, or to
let every task inherit whatever model the session happens to be on. Both fail: the hardcoded name
rots the moment you switch providers, and the inherited default sends a 12-lane parallel
reconnaissance fan-out to whatever model was convenient, which is how a Tuesday afternoon becomes a
surprising invoice. Routing should be *policy* — decided once, in configuration, in terms of task
classes — not a name typed into each prompt.

### Failure prevented

Unbounded spend: a wide fan-out on an expensive model with no ceiling, where the cost is only
visible on the provider's invoice. And silent vendor monoculture: every task, including every
review, resolving to the same vendor's models without anyone deciding that, which quietly forfeits
the diversity that `docs/01-mental-model.md` describes as a mitigation.

### Mechanism

The private gateway's shape is a three-level mapping: **task class → role → lane**. A task class
is what the *work* needs (reconnaissance, implementation, review, judgement). A role is a named
definition that says what an agent of that class does and how it behaves. A lane is a configured
model the role resolves to. Nobody downstream of the mapping names a model; the policy resolves
classes to roles, and roles to lanes, and the lanes are a configuration seam you can re-point
without touching a single task prompt.

The public primitives, all source-verified:

- **pi core has no sub-agents** — upstream says so and names the alternatives ("build your own
  with extensions, or install a package that does it your way",
  `earendil-works/pi` → `packages/coding-agent/README.md` § Philosophy). So roles arrive as a
  package or as your own extension. The public package this recipe uses is `pi-subagents`
  (npm, MIT, `github.com/nicobailon/pi-subagents`) — subject to the review rule in
  `docs/04-packages.md`.
- **Named, reusable roles are public.** `pi-subagents` ships role definitions you can use
  immediately — a scout for codebase recon, a worker for implementation, a reviewer for code
  review, an oracle for second opinions before acting, and more — and lets you define your own
  (its `docs/agents.md`). A role is invoked by name; the parent model decides *whether* to
  delegate, which is the same probabilistic caveat as skills: a must-delegate rule belongs in an
  instruction file or behind a guard, not only in a hope.
- **Role-to-lane pinning is public configuration, not code.** In `~/.pi/agent/settings.json` (or a
  project `.pi/settings.json`), the package reads `subagents.defaultModel` (a default for every
  role that does not set its own), `subagents.defaultProvider` (which provider a bare model id
  resolves against), and `subagents.agentOverrides.<role>.model` to pin one role — plus
  per-provider variants so one role definition serves two providers. Precedence is documented in
  its `docs/models.md`: per-run override → provider-scoped role override → role override → role
  frontmatter → package default → parent session model.
- **A spawn budget is public.** The package bounds cumulative child spawns per run
  (`maxSubagentSpawnsPerRun`, separate from active concurrency — see its `docs/configuration.md`
  for the current default), and a recursion depth guard bounds nesting
  (`maxSubagentDepth` / `PI_SUBAGENT_MAX_DEPTH`; read the upstream doc for the current default). The tiering *concept* — route
  by task shape: a cheap fast lane for recon and mechanical edits, a mid lane for routine
  implementation, a deep reasoning lane only for bounded hard tasks, a taste lane for ambiguous
  judgement — is documented in its `docs/models.md`; the *model names* in its examples are its
  examples, not this template's recommendations. Find your own lanes with the authoritative
  lookups: `pi --list-models`, `/model` in the picker, and `pi update --models` to refresh
  catalogs (`earendil-works/pi` → `packages/coding-agent/README.md` § Providers & Models).

### Smallest useful version

1. Install the package: `pi install npm:pi-subagents`.
2. In `~/.pi/agent/settings.json`, set `subagents.defaultModel` to your workhorse lane and
   `subagents.defaultProvider` so bare ids resolve against the provider you intend. Do not type a
   model name into any task prompt, ever.
3. Pin one role to a different lane than the default — for example the review role to your deep
   lane — with `subagents.agentOverrides.<role>.model`, and give roles that might hit external
   services a different one.
4. Write the budget rule into your canonical `AGENTS.md`, with its reason, e.g.:
   *"A fan-out wider than four children needs an explicit budget: number of children, and which
   lane each runs on. **Failure prevented:** a delegation ceiling stated nowhere is discovered on
   the invoice."*
5. Reconcile the tiering *concepts* to your own lanes by lookup, never by copying the package's
   example model names.

That is the mapping, the seam, and the discipline — the private gateway's three levels in four
settings keys and one written rule.

### Limits

- **No cost accounting.** The public primitive bounds *counts* of children, not money. A budget
  rule that names a lane and a child count is discipline you enforce by review; nothing in this
  recipe measures spend.
- **The parent model decides whether to delegate.** Roles are probabilistic targets like skills;
  the deterministic version of "always dispatch review to a role" is a guard (Recipe 1) that
  rejects a noncompliant operation. An always-loaded instruction-file rule is guidance: the
  parent can still skip it. Do not call an instruction a deterministic enforcement path.
- **Vendor diversity is not automatic.** If every lane resolves to one provider, the mapping is
  spend policy, not diversity policy — see Recipe 3 for the diversity half.
- **This is one public package, not the canonical answer.** pi's core stance is that sub-agents
  arrive from extensions or packages you choose; if `pi-subagents` is unsuitable, the same recipe
  applies to any role-bearing package, or to roles you define in your own extension.
- **Not the private gateway.** The private layer resolves lanes through a governed registry with
  per-class fail-closed behaviour (an unavailable required lane is an error, never a silent
  substitute). The smallest version silently substitutes: a missing role override falls back to the
  default lane with no complaint. If silent fallback would hurt you, guard it.

## Recipe 3 — Cross-vendor review lanes

### Problem

You finish a change and ask your agent to review it. The reviewer — the same model, from the same
vendor, trained on the same data, possibly sharing the same blind spots and the same training-time
inclination to be agreeable — says it looks good. It is a real review, and it can find real
defects; it is simply a *correlated* one, so its agreement is weaker evidence than an independent
reviewer's would be. The trap is that it *feels* like decorrelated verification, so you ship on it.

### Failure prevented

A same-vendor "yes" read as if it were a decorrelated one: a reviewer that shares the author's
vendor is likelier to share the author's blind spots, so its agreement is weaker evidence than it
appears. It is not zero evidence — an independent same-vendor reviewer still reads the work
under review and can find defects. What it is *less* able to supply is decorrelation, and decorrelation is what
this recipe is reaching for: a reviewer trained elsewhere is less likely to share the author's
particular blind spots. It is one plausible way to reduce correlation, not the only one — a fresh
context, a different method, or a different model within one vendor can reduce it too, and two
vendors can still share training sources and failure modes. That is why
`docs/01-mental-model.md` treats diversity as a mitigation rather than a proof: a cross-vendor
review can still be wrong.

### Mechanism

One rule, one configuration seam, honest bookkeeping:

- **The rule:** a completion claim on substantive work must be reviewed by a model from a different
  vendor than the one that wrote the work. "Different vendor" means the company that trained the
  model, not a different model from the same company, and not the same open weights behind two
  API facades. The rule belongs in your canonical `AGENTS.md` (per the split rule in
  `docs/07-instruction-files.md`), with the reason beside it.
- **The seam:** pi supports multiple providers simultaneously. Authenticate more than one
  (`/login`, or per-provider API-key environment variables — see `docs/02-install.md`), and every
  provider's models become selectable via `/model`, listable via `pi --list-models`, and
  pinnable per role as in Recipe 2. With Recipe 2's `subagents.agentOverrides`, the *review* role
  can be pinned to a different vendor's lane than the *implementation* lane **as a default**.
  That default is not a guarantee: if you later point the implementation lane at the same vendor,
  the pin still matches. Compare the author and reviewer vendors **at the moment of the review**;
  a match means the diversity requirement is unmet, not that the pin failed silently.
- **Custom and local models count too.** pi reads custom providers from `~/.pi/agent/models.json`
  (OpenAI-, Anthropic- and Google-compatible APIs; local runtimes like Ollama or vLLM work —
  `earendil-works/pi` → `packages/coding-agent/docs/models.md`), and extensions can register
  providers outright (`docs/custom-provider.md`). A locally served open-weights model is a
  legitimate review lane, with the caveat above about facades over identical weights.
- **The bookkeeping:** which vendor reviewed must be recorded *from the dispatch at the moment of
  use* — the receipt, the run artifact, or the session log naming the lane actually used — never
  typed in by hand. A provenance line written from memory is a claim, not evidence, and it goes
  stale the moment you re-point a lane. The private system's receipts record reviewer and author
  *family* derived from the actual dispatch; your smallest version derives it the same way or
  doesn't claim it.

### Smallest useful version

1. Authenticate a second provider in pi (`/login`, or the provider's API-key environment variable).
2. Put the rule in your canonical `AGENTS.md`: *"Completion claims on substantive work are
   reviewed by a model from a different vendor than the author. Record which vendor reviewed, from
   the run's own artifacts. **Failure prevented:** a same-vendor review is mistaken for a
   decorrelated one."*
3. With Recipe 2 installed, pin the review role to the second vendor's lane, so that when a review
   *is* invoked it resolves to the second vendor by default. That is a default, not an
   enforcement: nothing here makes the review happen. Only a completion gate that refuses an
   unreviewed claim does that, and this recipe does not ship one — step 4 is how you cover the gap
   by hand.
4. On substantive work, before accepting a completion claim, ask for the review and read the
   provenance line — the one the run wrote, not the one the author typed.

### Limits

- **Cross-vendor is a mitigation, not a proof.** Two vendors can share a blind spot, and a
  cross-vendor reviewer can be sycophantic in its own way. What it buys you is *decorrelation*:
  a model trained on different data is less likely to share the author's specific blind spots,
  so it is likelier to catch a class of error the author cannot see. It is not strictly better in
  every case, and it does not replace your own reading of the diff.
- **Diversity is necessary but nowhere near sufficient.** A different vendor with the wrong work
  to review, no stated criteria, or no authority to block will produce a review that reads well
  and clears nothing. What makes a review load-bearing is the work it received, the criteria it
  was given, and whether its refusal would actually stop the work. A reviewer that can only advise
  is a commenter.
- **The other harness's subagent lanes are constrained differently.** Whether its delegations can
  carry a non-Anthropic model at all is a property of that harness, covered in
  `docs/09-claude-code.md`; do not assume the recipe transfers unchanged across harnesses.
- **Vendor identity is not always obvious.** The same weights behind two API facades, or fine-tunes
  of one vendor's base, are not diversity. The rule is about training lineage; when you cannot
  establish lineage, say so rather than pretending the box is ticked.
- **Not the private review-lane system.** The private layer makes vendor provenance a
  mechanically checked field on a receipt and fails closed on a missing one. The smallest version
  is a written rule plus your own eyes on the run artifacts.

## Recipe 4 — Deterministic orchestration

### Problem

You discover that a task decomposes — six read-only reconnaissance lanes, or four independent
files, or a plan with waves of dependencies — and you fan out. The children research; the tokens
burn; the turn ends. Some children ran out of context mid-investigation, some stalled, some
"finished" by describing work instead of doing it — and the durable output of the whole exercise
is one conversation, plus nothing on disk. Nothing survived to be resumed, verified, or committed.

This failure is not hypothetical. While this template was being produced, a six-lane parallel
reconnaissance fan-out was dispatched and produced **zero durable output** — not one file
written. The cause, recorded honestly in
`docs/11-verification.md`, was the conjunction of over-scoped briefs, undersized execution
context, high concurrency, and no write-early contract. A fan-out whose children cannot write
incrementally returns exactly nothing when a child stalls, and the orchestrator could neither stop
nor steer it. The reader deserves to know this is a real and common failure, not a scare story.

### Failure prevented

The burning of tokens with no durable residue — and, its mirror image, the *silent partial
result*: half the lanes finished, and nobody can tell which half. Both come from the same absence:
no durable state between the orchestrator and the children, so "progress" exists only in
transcripts that die with the context window.

### Mechanism

Four disciplines, each one converting a hope into a checkable fact:

1. **Waves with explicit dependencies.** Tasks that share no state run in parallel; tasks that
   consume another task's output wait for it. The dependency order lives in a plan file on disk,
   not in the orchestrator's context — an orchestrator that holds the plan only in its window
   loses the plan to compaction exactly when the run gets long.
2. **Disjoint file scopes.** Each task names the files it may write, and nothing else. One writer
   per file; parallel writers get isolated checkouts (see below). **Failure prevented:** two
   sessions legitimately sharing a repo on disjoint subtrees still collide when a scope line is
   fuzzy — "the docs directory" is a scope; "whatever seems related" is a race.
3. **Durable incremental output — write early.** For a child assigned a **new** output artifact,
   the first write is a heading skeleton with honest `TODO:` markers, then fill it section by
   section. Check that the file does not already exist with content — do not overwrite user work
   with a skeleton. Existing files get incremental edits. Read-only reconnaissance writes a
   parent-owned receipt or a named report path, not a fake product file. A skeleton on disk is
   resumable; research in a child's head is not. **Failure prevented:** the zero-output fan-out
   above, where every child researched until its context was gone and the wave had nothing to show.
4. **Per-task verification.** Each task carries the exact commands that prove *its* work, and runs
   them before reporting done — the orchestrator re-runs them at the barrier. A keyword grep
   proves a surface exists; it cannot prove prose is correct, so a task's own verify commands are
   the floor, not the ceiling. **Failure prevented:** the wave that "completed" on children's
   self-reported success, which `docs/01-mental-model.md` explains as hallucinated completion —
   the failure mode where an agent asserts success without evidence.

The public primitives:

- **Delegation and parallel children:** the same `pi-subagents` package as Recipe 2 — foreground
  children stream into the conversation, background children keep working after control returns,
  and a live fleet view shows what is running (its README § Where running work shows up).
- **Isolated writers:** workflow children can be run in isolated worktrees (`worktree: true`),
  branch-managed and cleaned up by the package, so parallel writers get parallel checkouts instead
  of a shared dirty tree — one writer per worktree unless isolation makes concurrency safe (its
  `docs/workflows.md` § Worktree isolation).
- **Bounded recursion:** children do not get the delegation tool by default, and nesting depth is
  guarded (`docs/workflows.md` § Recursion guard) — the private lesson "an orchestrator's
  orchestrator is how you get exponential spawn" is enforced, not merely advised.
- **Durable state:** pi sessions are append-only JSONL on disk, auto-saved under
  `~/.pi/agent/sessions/` organized by working directory (`packages/coding-agent/README.md` §
  Sessions); the package adds per-run status and receipt artifacts (its `docs/observability.md`).
  Plan files, scopes, and verify commands belong in the repository, where they outlive every
  session.

### Smallest useful version

No tooling is required for the smallest version — it is four lines of contract in a plan file,
enforced by your own review at the wave barrier:

1. Write the plan as a file in the repo: for each task, a one-line goal, the **files in scope**
   (explicit list), the **verify commands**, and the tasks it depends on.
2. In the canonical `AGENTS.md`, write the wave rule: *"Multi-agent work runs in waves of
   file-disjoint tasks. A child assigned a NEW output artifact creates it as a skeleton first and
   fills it incrementally; a child working in an existing file edits it in place and never
   replaces it wholesale. A task that reports done has run its verify commands and pasted real
   output.
   **Failure prevented:** research that lives only in a child's context window dies there — the
   write-early contract is why a stalled child costs one task, not the wave."*
3. Run the first wave: delegate with scopes and verify commands in the brief, or run the tasks
   yourself — the contract is the mechanism; `pi-subagents` (with worktree isolation when writers
   are parallel) is the convenience, not the requirement.
4. At the barrier: re-run each task's verify commands yourself, read the diffs, and only then
   start the next wave. A barrier that trusts self-reports is not a barrier.

That is waves, scopes, durable incremental output, and per-task verification — the four properties
the private orchestration system exists to guarantee — in a plan file, one rule, and your own eyes.

### Limits

- **The public primitive does not enforce file scopes.** The private wave dispatcher reverts
  out-of-scope edits mechanically. In the smallest version the scope is a promise the child reads;
  enforcement is your review of the diff at the barrier (a `git status` per worktree shows exactly
  what each child touched), or a guard you build with Recipe 1. Assume company: several agents may
  legitimately share a repo on disjoint subtrees, so check before landing into shared ground.
- **Concurrency discipline is prompt-authored.** How many children run at once, and on what size
  of brief, is your judgement, backed by Recipe 2's budget rule. The failed fan-out above failed
  partly because six over-scoped children ran concurrently with no ceiling; the guard that would
  have flagged it is one you write.
- **Background runs still need a barrier.** Durable state makes a stalled run *inspectable*, not
  *finished*; "the fleet is still running" is a status, not a completion claim.
- **Not the private orchestration system.** The private layer runs the plan as typed waves with
  mechanical scope enforcement, per-task verify receipts, and post-barrier cleanup that reverts
  out-of-scope writes. The smallest version reproduces the contract and leaves the enforcement to
  you — which is exactly the honest gap between a starting point and the system it sketches.

## What this chapter deliberately does not do

- **No reimplementation.** The four recipes are starting points, not equivalents; the private
  system's guarantees (mechanical scope enforcement, governed lane registries, fail-closed
  attribution, receipt-bound provenance) are named as gaps in each *Limits* section, not hidden.
- **No security claims.** Refusal gates are tripwires, not containment; for the boundary, see
  `docs/02-install.md` and the upstream containerization doc it points at.
- **No pinned model identities, versions, or package versions in the recipes**, per the
  anti-pinning rule owned by [README.md](../README.md) ("Lookup over literal"). Lanes are chosen
  by lookup (`pi --list-models`, `/model`), and every version-sensitive fact carries its lookup
  command in the verification notes, per this template's unmaintained-but-corrections-welcome
  posture (`docs/11-verification.md`).
- **No private identities.** The private layer is described as shapes and properties, never as
  names, paths, or entry points you could grep for.

## Related chapters

- `docs/01-mental-model.md` — hallucinated completion, context rot, unbounded spend, and
  sycophantic review: the four failures the four recipes prevent, explained from first principles.
- `docs/04-packages.md` — the packages CLI, the authority boundary that makes you review any
  package named here, and the private classes in the inventory this chapter is the honest map of.
- `docs/05-skills.md` — probabilistic invocation, the fact that makes Recipe 1 necessary.
- `docs/07-instruction-files.md` — the split rule every written rule in these recipes obeys.
- `docs/09-claude-code.md` — what differs on the second harness, including its subagent lanes.
- `docs/11-verification.md` — the claim-to-source matrix consolidated, and the honest record of
  the failed fan-out Recipe 4 generalizes from.

## Verification notes

Claims were verified live during writing against pristine upstream sources — not from memory, not
from the installed (nonstandard, forked) pi, and not from the private planning bundle. Citations
name the repo, package-relative path, and section; never a fork-relative line number. Facts below
are point-in-time; each row names how to re-check it. Upstream `earendil-works/pi` `main` resolved
to commit `71dca871bc80` (2026-09-11) and `nicobailon/pi-subagents` `main` to `47bae7f78d4a`
(2026-09-14) at verification time.

| Claim in this chapter | Where | Verified by (command) | Result at verification | Public source |
|---|---|---|---|---|
| Extensions are TypeScript modules subscribing to lifecycle events; custom tools, commands, UI, persistence listed | Recipe 1 § Mechanism | fetched `packages/coding-agent/docs/extensions.md` § (intro, Key capabilities) | present as cited | `earendil-works/pi` |
| `tool_call` fires before execution, can block via `{ block: true, reason?, terminate? }`; `event.input` mutable; upstream's own example blocks `rm -rf` | Recipe 1 § Mechanism, Rung 2 | same doc § Events → Tool Events | present as cited, verbatim example | `earendil-works/pi` |
| `pi.registerCommand(name, { description, handler })` registers a slash command | Recipe 1 § Rung 3 | same doc § ExtensionAPI Methods → `pi.registerCommand` | present as cited | `earendil-works/pi` |
| Extension auto-discovery locations: `~/.pi/agent/extensions/` global, `.pi/extensions/` project-local after trust; extensions run with full system permissions | Recipe 1 § Mechanism | same doc § Extension Locations | present as cited, security note verbatim in substance | `earendil-works/pi` |
| pi has no built-in permission system; runs with user/process authority; containment via container; three patterns listed | Recipe 1 § Limits | fetched monorepo-root `README.md` § Permissions & Containerization | present as cited | `earendil-works/pi` |
| Claude Code hooks: `PreToolUse` fires before a tool call and can block; handler reads JSON on stdin, returns `hookSpecificOutput.permissionDecision: "deny"`; upstream's example blocks `rm -rf`; configured in `~/.claude/settings.json` / project `.claude/settings.json`; broken gates fail open with a non-blocking notice | Recipe 1 § Mechanism | fetched `https://code.claude.com/docs/en/hooks` (§ Hook Events table, § How a hook resolves, § settings paths, failure notices) | present as cited (living reference page; no revision pin exists for it) | code.claude.com |
| "No sub-agents" is a stated pi-core absence, with extension/package alternatives | Recipe 2 § Mechanism | fetched `packages/coding-agent/README.md` § Philosophy | present, verbatim alternatives | `earendil-works/pi` |
| `pi-subagents` is public, MIT, installs via `pi install npm:pi-subagents`, ships builtin roles incl. scout/worker/reviewer/oracle; foreground vs background children; `maxSubagentSpawnsPerRun` bounds cumulative spawns; FleetView observability | Recipe 2 § Mechanism, Recipe 4 § Mechanism | `npm view pi-subagents name license repository.url description --json`; fetched upstream `README.md` (§ Install, § Builtin agents, § Where running work shows up) | `"license": "MIT"`, `github.com/nicobailon/pi-subagents`; roles and budget key present as cited | registry.npmjs.org, `github.com/nicobailon/pi-subagents` |
| Role→lane pinning keys: `subagents.defaultModel`, `subagents.defaultProvider`, `subagents.agentOverrides.<name>.model`, per-provider variants; documented precedence; recommended tiering by task shape | Recipe 2 § Mechanism | fetched upstream `docs/models.md` | all keys present as cited; model *names* in its examples deliberately not reproduced (lookup-over-literal) | `github.com/nicobailon/pi-subagents` |
| Model/provider discovery: `/model` picker, `pi --list-models`, `pi update --models`; multiple providers authenticated via `/login` or per-provider API keys | Recipe 2, Recipe 3 | fetched `packages/coding-agent/README.md` § Providers & Models, § CLI Reference | present as cited | `earendil-works/pi` |
| Custom providers/models via `~/.pi/agent/models.json` (OpenAI/Anthropic/Google-compatible; Ollama/vLLM/LM Studio); `pi.registerProvider()` for full custom providers | Recipe 3 § Mechanism | fetched `packages/coding-agent/docs/models.md`, `docs/custom-provider.md` | present as cited | `earendil-works/pi` |
| Worktree isolation for workflow children (`worktree: true`, branch-managed, one writer per worktree); recursion guard with depth default and config; child sessions do not get the delegation tool by default | Recipe 4 § Mechanism | fetched upstream `docs/workflows.md` (§ Worktree isolation, § Recursion guard, § Recommended orchestration pattern) | present as cited; depth *default number* deliberately not reproduced — see its doc | `github.com/nicobailon/pi-subagents` |
| pi sessions are append-only JSONL, auto-saved under `~/.pi/agent/sessions/` organized by working directory | Recipe 4 § Mechanism | fetched `packages/coding-agent/README.md` § Sessions | present as cited | `earendil-works/pi` |
| Skills fire probabilistically; "models don't always do this" is upstream wording | § What this chapter assumes | fetched `packages/coding-agent/docs/skills.md` § How Skills Work, step 3 | present, quoted | `earendil-works/pi` |
| Upstream doc revisions at verification | this table | `GET /repos/earendil-works/pi/commits/main`, `GET /repos/nicobailon/pi-subagents/commits/main` | `71dca871bc80` (2026-09-11); `47bae7f78d4a` (2026-09-14) | api.github.com |

**Not verified (explicit gaps):**

- **No code was run.** Nothing in this chapter was executed: the extension snippets in Recipe 1
  are written against upstream's documented API shape but were not loaded into a pi session, and
  `pi-subagents` was not installed or exercised. The verification is source-level, per this
  template's distinction between source verification and an executed runtime check. Treat the
  snippets as reviewed-against-the-docs, not tested — and run Rung 1 yourself before extending it.
- **The two-harness policy-file recipe is a design, not a shipped implementation.** No such shared
  policy file exists upstream; the shape is this chapter's synthesis of two independently verified
  refusal mechanisms (pi `tool_call` blocking, Claude Code `PreToolUse` deny).
- **`pi-subagents`' deeper surface** (scripted `workflowScript`, missions, watchdog, extension API)
  is linked but not exhaustively documented here; its own docs are the authority, and it is a
  third-party package with no maintenance relationship to this template.
- **Exact config defaults** (spawn budget value, recursion depth value) are deliberately not
  reproduced — they are version-sensitive and belong to the package's configuration doc, which
  each claim above links to.
- **Whether the Claude Code harness can carry non-Anthropic subagent lanes** is not asserted here;
  it is a harness property covered by `docs/09-claude-code.md`, which owns that verification.
- **The private layer is described by shape, from this author's context, not from public
  sources.** Typed waves, mechanical scope, per-task receipts, and out-of-scope revert (above)
  are contextual descriptions of that layer, not independently verified public APIs. What you can
  build from public primitives is what is written in the recipes; the rest is named as a limit.
