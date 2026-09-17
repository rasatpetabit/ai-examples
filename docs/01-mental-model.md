# 1 — The mental model: what a coding agent actually is

You are an expert in systems. You have run terminals, package managers, and version control for
decades, and this guide will never explain any of them. What you do not have yet is the model of
*the machine on the other side of the prompt* — and every property of a coding-agent setup that
looks arbitrary, superstitious, or paranoid becomes obvious once you have it. This chapter builds
that model from first principles, with no assumed AI vocabulary, in the register of systems
documentation rather than a tutorial. It is not a pitfalls chapter. It is the orientation that
makes the rest of this template's rules legible as consequences rather than commandments: after
reading it you should be able to derive most of the later rules yourself, and judge any rule you
choose to drop.

Four properties of the machine do almost all the explanatory work:

1. The model consumes text ("tokens") through a **finite window**, and has no memory outside it.
2. The system prompt is **re-sent every turn**, so its length is a recurring cost and the
   instruction files riding inside it are the highest-leverage control you fully own.
3. The model itself can do nothing — an agent is the model **driving tools** through a loop, so
   capability is a property of the tool surface you give it.
4. When the window fills, **compaction** summarizes it away: the running session no longer sees the discarded turns unless something retrieves them.

From those four follow the four expensive failure modes this setup exists to prevent —
hallucinated completion, context rot, unbounded spend, and sycophantic review — each covered
below with its mitigation, so the rules shipped in `templates/` read as engineering consequences
rather than taste.

## The model, the tokens, and the finite window

The model reads and emits **tokens**: chunks of text, roughly a word or a fraction of one. Tokens
are the unit of both what it can attend to and what the provider bills. Nothing about the
terminal, the filesystem, or your repository reaches the model except as tokens.

The window is the model's **working memory**: the maximum number of tokens — your instruction
files, the conversation so far, every file the agent has read, and every command output it has
seen, concatenated — that one request can carry. It is finite by construction, and the number is
a property of the model, not of the agent harness: the harness can be configured to any model,
so any concrete number printed here would be wrong the moment the guide is read. Ask the harness
what it currently is — the command that reports the live value belongs to the configuration
chapter.

Because the window is the *whole* of the model's memory, anything outside it does not exist for
the purposes of the current turn. The model does not "remember" the early part of a long session
in some other place; if it fell out of the window or was summarized away, it is gone from the
model's point of view, and it can only be brought back by putting the tokens back into the
window — re-reading a file, re-running a command, or finding the fact where it was durably
stored. This one property explains a large fraction of agent misbehaviour that looks, from the
outside, like carelessness.

A coding agent is therefore a loop: send the model the current window (instructions, files,
conversation, recent tool results), receive tool calls, execute them, append the results, send
the window again. The next chapter ([docs/02-install.md](02-install.md)) walks your first
session; the point of seeing the loop now is that everything below is about what happens inside
one iteration of it.

## The system prompt is a recurring cost, not a one-time one

The first thing in the window, every turn, is the **system prompt**: the standing instructions
the harness prepends to everything else. It is not sent once at session start. It is re-sent on
every request — so a 2,000-token system prompt occupies 2,000 tokens of the window on every
turn, not once at session start. Occupancy is not the same as billed cost: some providers cache
unchanged prefixes, which can change price and latency without shrinking the window. The same
is true of the instruction files you write:
pi, like its peers, loads `AGENTS.md` from your home directory, from parent directories, and
from the current directory, and concatenates all matching files into the context the model sees
on every turn. (The full loading rules, the `AGENTS.md`/`CLAUDE.md` split, and the per-line
decision test live in [docs/07-instruction-files.md](07-instruction-files.md).)

That recurring cost cuts both ways, and both directions are load-bearing:

- **It is why instruction files are the highest-leverage control you fully own.** The model
  cannot act on what is not in its window, and instruction files are the one channel through
  which you put standing behaviour into every turn — not a tool the vendor ships, not a prompt
  pattern you must re-type, but a file on your disk that you can read, edit, version, and
  diff. Model choice matters, but you do not own the weights; you do own these files. That is
  the argument this whole template rests on: **instruction files are the highest-leverage
  control on agent behaviour — above model choice — that the reader fully owns.**
- **It is also why every line in them must earn its place.** An unpruned instruction file taxes
  every turn forever, in both latency and money, and — worse — in attention: a wall of
  low-value rules competes with a short list of load-bearing ones inside the same finite
  window. The window being finite means your instruction files are spending it.

> **Failure prevented:** an instruction file that grows without pruning — every "add a line for
> this incident" with no deletion, no expiry, and no review — becomes a standing tax on every
> turn, and the model starts ignoring the whole file because the load-bearing rules are buried
> in noise. Prune as deliberately as you add; every line must earn its place by changing what
> the model does.

## An agent is a model driving tools

The model, by itself, can only emit text. It cannot read your disk, run a command, or change a
file. An agent harness is the loop that connects the model's output to **tools** and feeds the
results back in as tokens. Everything the agent can actually *do* is the tool surface you
configured — and that is why capability in this world is mostly *installation*, not prompting.

pi gives the model four tools by default: `read`, `write`, `edit`, and `bash`. That is the
default-enabled surface, and it is deliberately small (the binary carries more built-ins than it
enables by default — see `docs/03-configuration.md` for the inventory). Upstream's design stance is that the
core stays minimal and everything else is built with extensions, skills, or third-party pi
packages — pi names the explicit absences itself, each with the alternative it points to:

- **No MCP.** Build CLI tools with READMEs, or add MCP with an extension.
- **No sub-agents.** Spawn instances via tmux, build your own with extensions, or install a
  package that does it your way.
- **No permission popups.** Run in a container, or build a confirmation flow with extensions.
- **No plan mode.** Write plans to files, or build/install it.
- **No built-in to-dos.** They confuse models; use a TODO file or an extension.
- **No background bash.** Use tmux.

(The upstream source and section for this list is recorded in the verification notes below.)

The practical consequences for you:

- If you arrive from another harness, **do not assume MCP, subagents, plan mode, or permission
  prompts are pi features**. In the harness you are leaving, those may be built in; in pi they
  are opt-in, arriving through packages and extensions — which is precisely what
  [docs/04-packages.md](04-packages.md) covers. Skills are a separate extension
  point with their own authoring rules, in [docs/05-skills.md](05-skills.md); they
  are not how you implement an MCP server or a subagent.
- **There is no built-in permission system.** Upstream states it plainly: pi runs with the
  permissions of the user and process that launched it, and does not restrict filesystem,
  process, network, or credential access. The four tools above are executed with your
  authority. `bash` is your shell. If you need hard boundaries, that is containerization, not
  configuration — upstream points at three containment patterns and this guide stops there,
  because it is not a security guide.
- Because capability is packages, and packages run with full authority, the rule about
  reviewing what you install — and the honest license table that comes with it — is
  [docs/04-packages.md](04-packages.md)'s business.

One more property of the loop matters more than any of the above: **the model sees tool results,
not tool execution.** Output that floods the window (a huge log, a full-directory dump) is
indistinguishable from a large file the model read: it displaces context. The discipline for
that — process in a sandbox, return only the derived answer — belongs to
[docs/06-memory-mcp-context.md](06-memory-mcp-context.md), which also covers the extension
that manages context automatically.

## Compaction and irrecoverable loss

A long session will eventually fill the window. When it does, the harness does not fail; it
**compacts**: it asks the model to write a summary of the conversation so far, discards the
original turns, and continues from the summary plus a tail of recent context. pi compacts
automatically by default — it triggers on context overflow (recovering and retrying) and
proactively as the window approaches its limit.

Compaction is **lossy**, and the loss is real in both directions:

- **The live window cannot see it unless something retrieves it.** The full history is
  preserved on disk in the session file — pi sessions are JSONL files with a tree structure,
  and `/tree` lets you revisit any point — but *the model in the running session does not see
  that history unless a later turn reads it back in.* After compaction it sees the summary.
  A detail dropped by the summary is missing from subsequent turns until you (or a tool)
  fetch it; the model has no way to notice the omission on its own. Retrieval is work, not
  automatic recovery.
- **Summaries are lossy exactly where agents are weak.** Compaction happens when you have been
  working longest — deep in a session, with many files read and decisions made — which is
  precisely when the state that matters is too detailed to survive a summary: exact file
  paths, an edge case you reasoned through and dismissed, the reason a change was deliberately
  *not* made. The model after compaction confidently continues from what it can see, with no
  introspective access to what was lost.

The consequence is not "avoid long sessions" (they are often unavoidable); it is that
**load-bearing state must live outside the window** — in always-loaded instruction files, in
durable memory, in the repository itself (tests, comments, a worklog) — so that a compaction
event cannot silently destroy it. That is why this setup treats durable memory and written
records as core infrastructure rather than conveniences
([docs/06-memory-mcp-context.md](06-memory-mcp-context.md)), and why a session that carries its
working state only in conversation is a session one compaction away from confident nonsense.

The core knobs — `compaction.enabled`, `compaction.reserveTokens`,
`compaction.keepRecentTokens` — are real pi settings, verified in the notes below, and
belong to [docs/03-configuration.md](03-configuration.md).

## The four expensive failure modes

These four account for most of the money and time an agent setup loses, and every rule in this
template traces to one of them. They are presented as orientation, not a pitfalls appendix: you
cannot judge a rule you do not understand the failure of, which is the cargo-culting this
chapter exists to prevent. Each is stated as mechanism → what it looks like → the mitigation
that later chapters implement.

### Hallucinated completion

**Mechanism.** A language model emits the most plausible next token. Generation does not
intrinsically verify that the work it is describing was performed. Tool results in the window
can be execution evidence — they can also be incomplete, lost to compaction, or ignored by the
next tokens. If the window contains your request and fragments of a plan, the most plausible
continuation includes success narration. Nothing in the loop's design checks narration against
reality before you read it.

**What it looks like.** The agent reports "done — all tests pass, the config was updated", and
some or none of it happened: the test command was never run, the file edit did not apply, or
the failure is still there. It is most common when the model cannot afford to do the work
(weak tool access, missing tool results, context near exhaustion) — and most dangerous because
it arrives in the same confident register as genuine completion. The expensive part is not the
failed work; it is your hours, because you believed a completion claim, made decisions on top
of it, and discovered the truth several steps downstream.

**Mitigations implemented in this template.** Completion claims must carry the evidence that
proves them — receipts, not assertions: real command output quoted or summarised, exit codes,
file paths and line numbers. Every rule in this template that demands "concrete evidence" or
"paste the real output" exists for exactly this reason. Where the claim matters, it is checked
by something other than the model's narration: a test suite, a deterministic check, or an
independent reviewer. See [docs/10-private-patterns.md](10-private-patterns.md) on review
lanes, and the verification chapter for the discipline this template holds itself to.

> **Failure prevented:** a reader trusts "done", builds on unfinished work, and discovers it
> several steps downstream — or worse, ships it. The rule "no completion claim without the
> output that proves it" converts narration into evidence.

### Context rot

**Mechanism.** Two forces degrade a long session simultaneously. First, attention weakens over
long contexts — the model's ability to use a fact degrades with its distance from the "now" of
the turn. Second, compaction (above) drops details from the summary whenever it fires, and
both degrade the *same* fact: early instructions, subtle constraints, and decisions made
pages ago carry less and less weight as the session grows.

**What it looks like.** A session that started strong starts to drift: the agent re-reads
files it already saw, re-asks questions, contradicts a convention it followed perfectly an
hour ago, or loses a constraint it had been respecting. Long-session drift is a property of
the mechanism, not a lapse that more scolding will fix.

**Mitigations implemented in this template.** Keep load-bearing instructions in
always-loaded files so they are re-sent fresh every turn instead of being buried in history;
prune those files so the load-bearing rules are not competing with noise. Keep durable state
outside the window (memory, repository, worklog) rather than trusting conversation to carry it.
When output is large, do not paste it into the window — process it and return the derived
answer only ([docs/06-memory-mcp-context.md](06-memory-mcp-context.md)). For work that matters,
prefer a fresh session with a well-written file over a long session carrying everything in
conversation: a new session costs almost nothing in context, and reads your instruction files
whole.

> **Failure prevented:** treating long-session drift as a model-quality problem and responding
> with in-conversation repetition ("as I already told you...") — which adds tokens to a window
> that is already rotting. Move the rule to a file; end the session and start a new one.

### Unbounded spend

**Mechanism.** Every turn re-sends the whole window (see "recurring cost"), so cost scales
with context length × turn count. Then multi-agent patterns multiply it: a fan-out that
launches many sub-agents runs many windows in parallel, each re-sending its own instructions
and its own brief, and every additional lane adds more turns. A task delegated to a fan-out
that does not converge costs real money and returns nothing — and stalled children can still
spend, because producing tokens is the model's only behaviour. **This failure is not
hypothetical for this template:** during its own production, a parallel reconnaissance fan-out
burned significant token volume and produced zero durable output — the cause and the lesson
are recorded in [docs/11-verification.md](11-verification.md), because a reader deserves to
know the failure is real and common.

**What it looks like.** A one-question task balloons into a dozen parallel investigations that
each research more than the answer needs; a delegation that could have been one session runs
eight; costs arrive with no output that survives them. The mechanism is indifferent to whether
the agent is clever: spend happens by emitting tokens, so any loop that keeps emitting is
spending whether or not it is converging.

**Mitigations implemented in this template.** Budgets declared before the fan-out (scope,
turn limits, and a cap on lanes); write-early contracts so a lane produces durable output
incrementally instead of researching until its context is exhausted; per-task verification so
each lane proves its own work before the parent integrates it; and dispatch that routes
task *classes* to governed roles rather than defaulting every prompt to the strongest
available model — which is also the honest way to say "the expensive model is not for every
turn". See [docs/10-private-patterns.md](10-private-patterns.md) on the dispatch pattern.

> **Failure prevented:** a fan-out that spends tokens for zero output — the exact failure this
> template recorded on itself. The rules "declare a budget before you fan out", "write early,
> durably, incrementally", and "verify per task" are what stops the recon fan-out failure
> from being a rite of passage.

### Sycophantic review

**Mechanism.** Ask a model from vendor V to review a proposal written by a model from vendor
V, and the reviewer shares the author's training data, priors, and — most importantly — its
*blind spots*. Shared training and framing raise the chance of correlated misses; they do not
make agreement automatic, and a same-vendor reviewer can still find errors. Two models from
the same vendor agreeing is still a weaker instrument than two independent opinions. The
degenerate case is worse: a reviewer invoked *inside the author's own conversation* inherits
the author's framing, including its errors, and is poorly placed to notice them.

**What it looks like.** You ask "is this correct?" in the same session, and it says yes. You
ask a same-vendor model in a new session, and it agrees with the author's approach,
terminology, and conclusions. Both feel like verification — the second one even produces a
receipt — but the review is correlated with the work in a way that makes it a poor instrument
for finding what the author could not.

**Mitigations implemented in this template.** A review meant to catch correlated blind spots
wants a reviewer from a different vendor than the author, configured as a second provider so it
is a policy rather than a mood. Two properties of that idea are worth internalizing before you
configure it, and they are the part this chapter owns: **cross-vendor diversity is a mitigation,
not proof of correctness** — a different vendor reduces some correlations without guaranteeing
the flaw was found — and **the value of a review is bounded by what the reviewer checks**, so a
reviewer needs a checklist naming what to look for and the work under review itself rather than
the author's reasoning.

The rule itself, and how to implement it, are owned by
[docs/10-private-patterns.md](10-private-patterns.md); the harness difference that makes "same
lane" different from "second lane" is owned by [docs/09-claude-code.md](09-claude-code.md).

> **Failure prevented:** treating a same-vendor "yes" as if it were a decorrelated review.
> It is still a review, and it can still find defects; what it cannot do is rule out the class
> of blind spot the author and reviewer share.

## Where the mitigations live

| Failure mode | Mitigation | Where it is implemented |
|---|---|---|
| Hallucinated completion | Evidence-bearing completion claims; verification by execution and independent review | [docs/10-private-patterns.md](10-private-patterns.md); the discipline this template records in [docs/11-verification.md](11-verification.md) |
| Context rot | Always-loaded instruction files, pruned; durable state outside the window; derived answers, not raw dumps | [docs/06-memory-mcp-context.md](06-memory-mcp-context.md); the file craft in [docs/07-instruction-files.md](07-instruction-files.md) |
| Unbounded spend | Budgets before fan-out; write-early, incremental, durable output; per-task verification; class-to-role dispatch | [docs/10-private-patterns.md](10-private-patterns.md) |
| Sycophantic review | Reviewer from a different vendor, given the work under review not the author's reasoning; explicit diversity caveat | [docs/10-private-patterns.md](10-private-patterns.md); [docs/09-claude-code.md](09-claude-code.md) |

Read the rest of this guide in the order your task demands; the fixed paths are:

- [docs/02-install.md](02-install.md) — install pi, authenticate, first session, verify it worked
- [docs/03-configuration.md](03-configuration.md) — settings: core keys vs extension-contributed keys, project trust, model selection by lookup
- [docs/04-packages.md](04-packages.md) — the packages CLI, starter vs advanced sets, license cautions, the dead-fork trap
- [docs/05-skills.md](05-skills.md) — skill mechanics, the installable inventory, and a census method you can run
- [docs/06-memory-mcp-context.md](06-memory-mcp-context.md) — durable memory, MCP as an adapter, context management and compaction
- [docs/07-instruction-files.md](07-instruction-files.md) — the AGENTS.md/CLAUDE.md split rule and the per-line decision test
- [docs/08-cross-cutting-docs.md](08-cross-cutting-docs.md) — the handbook pattern: one index plus leaves, and a machine-stamped pointer block
- [docs/09-claude-code.md](09-claude-code.md) — the secondary harness track and what differs
- [docs/10-private-patterns.md](10-private-patterns.md) — hooks engine, dispatch, review lanes, orchestration as patterns
- [docs/11-verification.md](11-verification.md) — what was verified, how, and how to re-verify anything yourself

The templates and examples ship the consequences of this chapter as starting files:
`templates/global/` and `templates/repo/` (instruction-file skeletons whose every rule carries
the failure it prevents), `examples/ordinary-repo/` and `examples/handbook/` (complete genericized
trees you can copy and edit). The sequence for putting them in place is
[`ADOPTING.md`](../ADOPTING.md).

## Verification notes

Every AI-mechanics claim in this chapter that names a pi behaviour was verified against pristine
upstream source during this template's production, at the upstream revision recorded below. AI
mechanisms (attention degradation, plausibility of narration, vendor correlation) are not pi
facts; they are properties of language models, documented here as mechanism explanations, and
they are marked as such rather than pinned to a source. What follows is the claim-to-source
table this guide's verification chapter consolidates; the commands were run live during
production, and you can re-run every one of them.

| Claim in this chapter | Verified by | Result | Public source |
|---|---|---|---|
| pi gives the model four tools by default: `read`, `write`, `edit`, `bash` | `curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/README.md` (grep "gives the model four tools") | Quote found: "By default, pi gives the model four tools: `read`, `write`, `edit`, and `bash`." | `earendil-works/pi` → `packages/coding-agent/README.md` § Quick Start |
| pi's built-in tools are exactly: `read`, `bash`, `powershell` (Windows), `edit`, `write`, `grep`, `find`, `ls` | same fetch, grep "Available built-in tools" | Quote found: "Available built-in tools: `read`, `bash`, `powershell` (Windows), `edit`, `write`, `grep`, `find`, `ls`" | `earendil-works/pi` → `packages/coding-agent/README.md` § CLI Reference |
| pi's core is deliberately minimal: No MCP, No sub-agents, No permission popups, No plan mode, No built-in to-dos, No background bash — each with a named alternative | same fetch, § Philosophy | All six absences present verbatim with their alternatives | `earendil-works/pi` → `packages/coding-agent/README.md` § Philosophy |
| pi has no built-in permission system and runs with the launching user's permissions | `curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/README.md` (§ Permissions & Containerization) | Quote found: "Pi does not include a built-in permission system for restricting filesystem, process, network, or credential access. By default, it runs with the permissions of the user and process that launched it." | `earendil-works/pi` → `README.md` § Permissions & Containerization (monorepo root) |
| pi loads `AGENTS.md` from global, parent, and current directories and concatenates all matching files | fetch of `packages/coding-agent/README.md` § Context Files | Quote found: "Pi loads `AGENTS.md` (or `CLAUDE.md`) at startup from: `~/.pi/agent/AGENTS.md` (global), parent directories (walking up from cwd), current directory… All matching files are concatenated." | `earendil-works/pi` → `packages/coding-agent/README.md` § Context Files |
| Compaction is automatic by default, triggers on overflow and proactively, and is lossy; full history remains in the session file and `/tree` can revisit it | fetch of `packages/coding-agent/README.md` § Sessions → Compaction | Quote found: "Automatic: Enabled by default. Triggers on context overflow (recovers and retries) or when approaching the limit (proactive)… Compaction is lossy. The full history remains in the JSONL file; use `/tree` to revisit." | `earendil-works/pi` → `packages/coding-agent/README.md` § Sessions → Compaction |
| `compaction.enabled` / `reserveTokens` / `keepRecentTokens` are real pi core settings (with defaults `true` / `16384` / `20000`) | `curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/settings.md` § Compaction | All three keys present in the settings table with those defaults | `earendil-works/pi` → `packages/coding-agent/docs/settings.md` § Compaction |

Upstream revision at verification: `earendil-works/pi` branch `main`, commit `71dca871bc80`
(committed 2026-09-11), resolved by `curl -fsSL https://api.github.com/repos/earendil-works/pi/commits/main`
and recorded as provenance, not as a pinned version. All citations above name the package-relative
path and section — the philosophy and tool claims come from `packages/coding-agent/README.md`,
which is the file that ships to npm; the monorepo root `README.md` has no Philosophy section, so a
citation of the form "pi README § Philosophy" without the package path is a trap, and none appear
here.

**Not verified from a live session for this chapter, by design:** the token mechanics, the
four-failure-mode mechanisms, and the vendor-correlation claim are general properties of
language models, stated as mechanism explanations rather than pi claims; no upstream pi document
asserts them, and none is cited. The fan-out failure recorded as real is documented in
[docs/11-verification.md](11-verification.md) from its own receipts; this chapter states it
exists and points there, rather than restating its private details. This chapter's prose
contains no star counts, model names, provider names, or version numbers; where a current
value is needed (window size, available models), the chapter names the surface that reports
it and the configuration chapter carries the lookup commands.
