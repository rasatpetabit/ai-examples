# 6 — Durable memory, MCP, and context management

Three capabilities arrive together in this chapter because they answer the same question from
different sides: **the context window is finite, and every session starts empty.** Durable memory
moves knowledge *across* sessions so you stop paying the re-learning cost. MCP connects the agent
to external tools and data without drowning the window in tool definitions. Context management
keeps a *single* session alive when raw data threatens to eat it. Each is a package you install
on the minimal core — none is a pi default — and each fails in a specific, preventable way that
this chapter names beside the mechanism.

## The problem each subsystem solves

A coding agent has no memory of you, your project, or yesterday. Every session starts amnesiac:
the same instruction is given again, the same correction is re-derived, the same mistake is
repeated. That is not a nuisance, it is a cost curve — and a specific compounding one:

**The repeated-correction problem.** If the model misuses a naming convention on Monday and you
correct it, the correction lives only in that session. Tuesday it makes the same mistake again,
because nothing carried the correction across. You will correct it every day forever, or until
the correction moves into a surface the agent loads automatically — an instruction file, or a
memory system. A correction that has been given more than once is a signal, not an annoyance:
prose reminders have failed, and the fix is a *deterministic* surface, not a louder reminder.
Memory systems can carry corrections across sessions, and instruction files carry rules the agent
must load — but a rule that keeps being violated needs enforcement, which is the subject of
[docs/10-private-patterns.md](10-private-patterns.md) on hooks and guards.

**The tool-integration problem.** An agent can only call what it can see. Every MCP server you
connect has historically meant injecting its full tool schema into the window — the adapter this
chapter documents exists because a single server can burn tens of thousands of tokens before the
conversation starts (see its own "Why This Exists" section). The cost is paid whether or not the
tools are used, and it is paid *again* on every turn, because the system prompt and tool
definitions are re-sent each time (see [docs/01-mental-model.md](01-mental-model.md) on recurring
system-prompt cost).

**The raw-data problem.** A single command can dump hundreds of kilobytes into the window — a
test suite's full output, a directory listing, a JSON blob. After a few of those, compaction
fires and irrecoverably summarizes away the details you needed. The mitigation is not "be
careful"; it is a discipline: process data where it is produced and let only the derived answer
into the window. This chapter names that discipline and the package that mechanizes it.

## Durable memory — the concept

Cross-session memory is a store the agent reads before acting and writes after learning
something. The primitive pair is:

- **Recall before work** — inject relevant memories into the context before the agent acts, so
  it arrives already knowing your conventions, decisions, and prior corrections.
- **Retain after work** — write durable memories after a session completes, so the next session
  starts with what this one learned.

Without the pair, every session rebuilds the same context from scratch, and the correction loop
above never closes. With it, a correction given once becomes *available* for later automatic
recall — subject to retrieval relevance. Similarity search can miss a must-follow rule on any
turn. That is the point at which memory and instruction files start to overlap, and the
boundary matters:

**Instruction files hold rules; memory holds facts.** A rule ("never commit generated files")
belongs in an instruction file because it is deliberate, versioned, reviewable policy the agent
must load — see [docs/07-instruction-files.md](07-instruction-files.md). A fact ("the deploy
script lives in `scripts/deploy.sh` and needs `ENV=staging`") belongs in memory because it is
discovered, contextual, and numerous. When a *fact* is really a rule the model keeps violating,
the memory system is not the fix — deterministic enforcement is, and the honest statement is that
memory recall is probabilistic too: a recalled memory is injected text, not a guarantee of
behaviour, exactly as a skill description only *probabilistically* triggers the model to load
the skill (see [docs/05-skills.md](05-skills.md)).

**Failure prevented:** treating memory as a rules store, or instruction files as a fact store.
The failure each way is real: rules in memory are recalled only when similarity search surfaces
them, so the model can miss a must-follow rule on any given turn; facts in instruction files
bloat the recurring prompt cost with detail the agent rarely needs.

## Durable memory — the real install path (Hindsight)

The memory system in the reference setup — the working setup this template generalizes from —
is [Hindsight](https://hindsight.vectorize.io/), and it is the one this template documents
because its distribution structure teaches the exact lesson this chapter most needs: **the
project name, the server distribution, the client packages, and the pi extension are four
different artifacts, and installing the wrong one is the single most likely mistake in this
chapter.**

### The four artifacts, disambiguated

| Layer | Correct artifact | Notes |
|---|---|---|
| The project | `github.com/vectorize-io/hindsight`, MIT | The memory server and its official clients. |
| The **server** (pip, full) | `pip install hindsight-api` | Standalone API server, works out of the box. |
| The **server** (pip, slim) | `pip install hindsight-api-slim` | Requires external embeddings/reranking/database. |
| The **server** (embedded in Python) | `pip install hindsight-all` | In-process server for Python programs. |
| The **server** (Docker) | `ghcr.io/vectorize-io/hindsight:latest` | One container, embedded PostgreSQL (`slim` tag available). |
| The **server** (Helm) | `oci://ghcr.io/vectorize-io/charts/hindsight` | Production/Kubernetes deployments. |
| The **TypeScript client** | npm `@vectorize-io/hindsight-client` | What a TS integration programs against. |
| The **Python client** | pip `hindsight-client` | Same role, for Python. |
| The **pi extension** | npm `@luxusai/pi-hindsight` | `pi install npm:@luxusai/pi-hindsight` — third-party, targets the TS client. |
| The **control-plane UI** | npm `@vectorize-io/hindsight-control-plane` | Web UI; run via `npx`. |

**Failure prevented:** `pip install hindsight` (and to a lesser degree conflating the layers).
PyPI hosts an unrelated distribution literally named `hindsight` — a small, old package
("Python tools for Hindsight Software", by an unrelated author) with nothing to do with this
project. It installs without error. The correct server install is `pip install hindsight-api`;
`hindsight-client` is the Python client, not the server. This was verified live against the
public PyPI registry while writing (see the verification notes): the unrelated `hindsight`
distribution resolves, and nothing about its name warns you.

### Running a server and the control plane

The official installation guide's bare-metal path (verify current commands against the live
guide — the URL is in the verification notes):

```bash
pip install hindsight-api
export HINDSIGHT_API_LLM_PROVIDER=<provider>      # required
export HINDSIGHT_API_LLM_API_KEY=<key>            # required
hindsight-api                                     # listens on http://localhost:8888
```

The server needs an LLM provider key for fact extraction and answer generation — that is a
property of how it works, not a configuration detail you can skip. For development it can run
with an embedded PostgreSQL; production deployments use an external PostgreSQL (14+, with a
vector extension) via `HINDSIGHT_API_DATABASE_URL`. The control-plane web UI runs against the
API:

```bash
npx @vectorize-io/hindsight-control-plane --api-url http://localhost:8888
```

which serves on port 9999 by default. Both ports (8888 API, 9999 UI) are the distributions'
documented defaults, not private values; the installation guide is the authority for current
behaviour.

**Failure prevented:** skipping the LLM-key requirement and concluding the server is broken.
The official guide states the key is required for the server's core functions; a first-run
without one fails for a reason the guide predicts, not for a mysterious one.

### The pi extension

```bash
pi install npm:@luxusai/pi-hindsight
```

The extension recalls relevant memory before provider calls and retains structured session
deltas after completed agent runs, and exposes explicit memory tools for direct
retain/recall/reflect operations. Setup is through its `/hindsight` interactive hub: choose a
Hindsight server (self-hosted at the default local URL, or Hindsight Cloud), pick a memory
profile (shared coding bank, isolated per-repo bank, user bank, or recall-only), and it writes
its own configuration. Its server compatibility floor is a lookup, not a copied number — the
extension's own compatibility matrix states the supported Hindsight server range and the
required client version, and `/hindsight:doctor` reports the live server's fitness; the commands
to re-check are in the verification notes.

The extension ships its own skill (discovered through pi's normal package skill discovery — see
[docs/05-skills.md](05-skills.md)), which is how the model learns the tools exist. That is worth
noticing as a pattern: **packages can ship skills, and those skills are the model-facing
documentation layer** — the extension registers the tools, the skill teaches the model when to
reach for them, and neither guarantees the model will, for the same probabilistic-invocation
reason the skills chapter documents.

**Failure prevented:** assuming "memory is on" means "memory is used". The extension gates
automatic recall and retain behind completed setup (an explicit bank ID for the default
profile); before that, tools refuse rather than silently no-op. A session that looks amnesiac
should be checked with the status command, not debugged from memory.

### A second, first-party pi route

Hindsight's own project now ships a first-party multi-agent integration —
`npx @vectorize-io/hindsight-coding-agents install pi` — which installs an extension entry into
pi settings plus a companion skill, with native tools and no MCP involved. That command is the
project's only supported route for pi. It exists because both hosts reading the same `pi` key
in a shared `package.json` cannot name two entry points; the install command points each host
at its own bundle. A reader choosing between the third-party extension above and the
first-party integration should check both projects' current guidance — they are different
artifacts by different maintainers, with different feature surfaces, and this template
documents both rather than pretending only one exists.

## Durable memory — configuration shape, keys only

The extension reads a configuration file it owns — `~/.pi/agent/hindsight.json` (global) or
`.pi/hindsight.json` (project), `.jsonc` variants also read — with environment variables
overriding file values. The **shape** is the transferable knowledge; the **values** are yours
and include a base URL and an API-key reference, which is exactly why this chapter documents
keys and never values.

The key structure (from the extension's public reference; read out of the live reference
configuration during verification, values redacted, and cross-checked against the public
documentation — see the verification notes for exactly how far that cross-check went):

```json
{
  "setupComplete": "...",
  "scope":   { "mode": "...", "projectIdStrategy": "..." },
  "hindsight": {
    "baseUrl": "...",
    "timeoutMs": "...",
    "apiKey": { "source": "env", "name": "<ENV-VAR-NAME>" }
  },
  "banks": {
    "project": { "enabled": "...", "derive": "...", "bankId": "..." },
    "user":    { "enabled": "...", "bankId": "..." }
  },
  "userRetain": { "mode": "..." },
  "recall": {
    "enabled": "...", "injectionPosition": "...",
    "storeLastRecall": "...", "storeLastRecallFailures": "..."
  },
  "retain": {
    "enabled": "...", "flushIntervalMs": "...",
    "periodicFlushMaxJobs": "...", "periodicFlushTimeoutMs": "..."
  }
}
```

Points that matter more than the list:

- **`hindsight.apiKey` is a reference, not a secret.** `source: "env"` plus a variable *name* —
  the raw key never lives in the config file. Copying a friend's config file is safe precisely
  because the secret is one indirection away.
- **`banks` selects identity; missions do not live here.** Bank missions, mental models, and
  templates are bank settings managed in the Hindsight control-plane UI, not pi JSON — the pi
  file selects banks and configures extension behaviour, and the server owns the memory content.
- **The full key list is a lookup, not a copy.** The extension's public reference documents every
  field with defaults; `/hindsight` status shows each setting's effective value and its source
  (`project`, `global`, `env`, or `default`), which is how you diagnose precedence without
  reading a document at all.

**Failure prevented:** pasting a config file from a working setup into a new one and expecting
memory to work. `setupComplete` and bank IDs in that JSON *are* the gate fields — a copied file
that already has them set will look complete while pointing at someone else's banks. Reset
`setupComplete` and choose your own bank identity; do not assume `/hindsight` status will
detect a copied configuration. Silent reuse of another installation's banks is the failure.

## MCP — the concept, and why it is an adapter

MCP (Model Context Protocol) is a standard way for an agent to call external tools and data
sources: a *server* exposes named tools; a *client* (the agent) discovers and calls them. Its
appeal to a newcomer is obvious — connect a server, get tools. Its cost is less obvious and is
the reason for this chapter's framing:

**pi has no MCP support in its core — as a deliberate design decision.** Upstream states it in
the same breath as "No sub-agents" and "No permission popups": *No MCP. Build CLI tools with
READMEs (see Skills), or build an extension that adds MCP support.* The philosophy is that tool
definitions are expensive and mostly unused, and simple CLI tools behind a skill often do the job
without the protocol. See [docs/01-mental-model.md](01-mental-model.md) for the recurring-cost
mechanic that makes this a rational choice, and
[docs/04-packages.md](04-packages.md) for what "an extension adds it" means.

The extension that adds it is `pi-mcp-adapter` (MIT), installed like any package:

```bash
pi install npm:pi-mcp-adapter
```

It presents **one proxy tool** (roughly a couple of hundred tokens, by the adapter's own
account) instead of injecting every server's tool schema. The model discovers tools on demand:
`mcp({ search: "..." })` to find a tool by keyword, `mcp({ describe: "tool" })` for its schema,
`mcp({ tool: "name", args: {...} })` to call it. Servers are lazy — they do not connect until
a tool is actually called — and idle servers disconnect after a timeout. Tool metadata is
cached, so search works without a live connection.

**Failure prevented:** connecting MCP servers the way other harnesses let you and burning the
window on schemas. The proxy pattern is the whole point of this adapter: the reference setup
this template generalizes from ran many servers, and the naive form would have paid every
server's definition cost on every turn. The adapter's own "Why This Exists" section states the
problem it solves in those terms.

### The configuration shape

The adapter reads standard MCP config files, by precedence (later wins):

1. `~/.config/mcp/mcp.json` (user-global shared)
2. `~/.agents/mcp.json`, `~/.agents/mcp/mcp.json` (tool-agnostic shared)
3. `~/.pi/agent/mcp.json` (Pi global override)
4. `.mcp.json` (project shared)
5. `.pi/mcp.json` (Pi project override)

The per-server shape, from the adapter's own README (which is the authority — pi core does not
read these files):

```json
{
  "mcpServers": {
    "a-stdio-server": {
      "command": "npx",
      "args": ["-y", "some-mcp-server"]
    },
    "an-http-server": {
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer ${MY_TOKEN}" }
    }
  },
  "imports": ["cursor", "claude-code", "claude-desktop", "opencode"]
}
```

- `mcpServers` — the map of servers. `command`/`args` for stdio servers (a local process);
  `url`/`headers` for HTTP servers. The two transports are mutually exclusive per server.
- `imports` — an optional array of *host-specific compatibility imports* (other tools' config
  formats: `cursor`, `claude-code`, `claude-desktop`, `opencode`, `vscode`, `windsurf`,
  `codex`). Use it only for formats not covered by the standard files above; standard files are
  loaded automatically.

Credential values in `headers` and `env` support `${VAR}` interpolation, so a secret stays in
the environment and the config file references the variable name — the same
reference-not-secret pattern as the memory config. An `mcp({ action: "install", url: ... })`
call can add an endpoint without editing files; `/mcp` opens the interactive panel, and
`/mcp setup` scaffolds a first config.

**Failure prevented:** hand-editing the adapter-owned override files as if they were the
normal config. The shared files (`.mcp.json`, `~/.config/mcp/mcp.json`) are the normal setup
targets; the Pi-owned files hold overrides and compatibility imports, and a reader who treats
them as primary will fight the precedence order instead of using it.

## MCP — a worked example against a genuinely public server

The rest of this chapter could be prose claims. Instead, here is the worked example the
template's verification chapter replays: a real MCP server, really public, really
account-free, called live while this guide was being written.

The chosen server is **`@modelcontextprotocol/server-everything`** — the MCP steering group's
own reference server, whose stated purpose is to exercise the protocol's features. It needs no
account, no API key, no filesystem path, and no network access at call time; its `echo` tool
returns its input. It is the right example *because* it is useless: nothing about the
interaction depends on credentials or private values, so the capture below is exactly
reproducible by any reader.

Config (project `.mcp.json`):

```json
{
  "mcpServers": {
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

**What actually happened when it was called live** (JSON-RPC over stdio, exactly as the MCP
specification defines; commands and raw capture in the verification notes):

1. `initialize` — the server answered with its identity and capabilities:
   `serverInfo` `{"name": "mcp-servers/everything", "title": "Everything Reference Server",
   "version": "2.0.0"}`, `protocolVersion` `2025-03-26`, capabilities including `completions`,
   `logging`, `prompts`, `resources`, `tasks`, `tools`.
2. `tools/list` — the server listed **13 tools** (among them `echo`, `get-env`,
   `get-sum`, `get-structured-content`, `trigger-long-running-operation`, and others).
3. `tools/call` on `echo` with `{"message": "verify"}` — the server returned content
   `Echo: verify`, `isError: false`.

No authentication was requested at any step. The full transcript of the exchange is reproducible
with the commands recorded in the verification notes at the end of this chapter, which is the
template's whole standard of proof: an interaction claim is captured, not narrated.

**Why this matters more than it looks.** The example is deliberately minimal, and the discipline
it demonstrates is the one this template applies to itself: a claim about an interaction with an
external system is only as good as the captured result. A reader who runs the same three
JSON-RPC messages gets the same result, or the chapter is wrong and should be corrected. The
same standard governs the memory and compaction claims above; see
[docs/11-verification.md](11-verification.md) for the consolidated matrix.

**Failure prevented:** the "it should work" example. A worked example with an imaginary
endpoint, or one that was never actually called, teaches the reader to trust prose over
captured output — the exact failure mode (hallucinated completion) this template exists to
prevent, applied to the document itself.

## Context management — the problem and the mitigation pattern

Back to the finite window. The recurring-cost mechanic from the mental-model chapter has a
second face: it is not only the system prompt that costs on every turn — everything the session
has accumulated costs too, and raw tool output accumulates fast. A single command can return
tens of kilobytes; a few can consume the budget the conversation needed.

The **derived-answer discipline** is the pattern to internalize before installing anything:

> When a tool produces raw data, process it where it lands and return only the derived answer
> to the conversation.

Not "read the log and summarize it" (the log entered the window first, and compaction may have
already eaten it) but "run a script that reads the log and prints the answer". The window
receives the answer; the raw data never enters it. This is a discipline you can apply with
plain `bash` — the built-in tool is enough to write the processing script — and it is the
single highest-leverage context habit in this chapter.

**Failure prevented:** raw output flooding the window and triggering compaction at the moment
the session was most valuable. Compaction is lossy and fires automatically (below); the
cheapest place to prevent the loss is before the bytes enter, not after compaction has
summarized them away.

### The package that mechanizes the discipline

`context-mode` (**Elastic-2.0 throughout** — source-available, not OSI-open; the license
caution is in [docs/04-packages.md](04-packages.md)) exists to make the derived-answer
discipline the default rather than the exception. Its own description: sandboxed code
execution, an FTS5 knowledge base, and intent-driven search — the model writes a script, the
sandbox runs it, only the result returns to the window. Its tools include sandboxed code-execution tools (`ctx_execute`, `ctx_batch_execute`,
`ctx_execute_file`), search/index tools (`ctx_index`, `ctx_search`, `ctx_fetch_and_index`), and
meta-tools (`ctx_stats`, `ctx_doctor`).

Install (pi, per its upstream README's pi section):

```bash
npm install -g context-mode
pi install npm:context-mode
```

then add the MCP server to the **normal** shared config (`.mcp.json` in the project, or
`~/.config/mcp/mcp.json` globally) — the same files the previous section named as setup
targets, not the adapter-owned `~/.pi/agent/mcp.json` / `.pi/mcp.json` overrides:

```json
{
  "mcpServers": {
    "context-mode": { "command": "context-mode" }
  }
}
```

and restart pi. In a session, `ctx stats` reports the tools are live.

Its extension registers pi lifecycle hooks for session continuity and routing enforcement —
session events (file edits, git operations, errors, decisions) are indexed into its database
so a compacted session can retrieve what it was doing rather than losing it to the summary.
The **license** is the one thing to check before adopting: the npm package carries
Elastic-2.0, which is source-available with usage restrictions (notably the managed-service
restriction), not open source — and a reader must never meet that fact for the first time
after depending on it.

**Failure prevented:** adopting a context-saver without checking its license, and discovering
after the fact that its terms differ from every other package in the stack. The lookup is one
command (`npm view context-mode license --json`), and the license caution belongs in the
adoption step, not a footnote.

## Context management — pi's own compaction

Compaction is pi's built-in answer to a window that has filled: summarize the older parts of
the session and continue with the summary plus the recent messages. It is **automatic by
default**, triggering when the session crosses a threshold, and it is **lossy by design** — the
summary replaces the original messages, and what the summary dropped does not come back. The
full history remains in the session file on disk (a JSONL with a tree structure), and `/tree`
can revisit it, but the *conversation* now runs on the summary.

How the threshold is computed (from pi's own compaction documentation, upstream
`packages/coding-agent/docs/compaction.md`):

```
contextTokens > contextWindow - reserveTokens
```

with the cut point chosen by walking back until `keepRecentTokens` of recent material is
preserved unsummarized. The three core keys, with their defaults from the upstream settings
reference:

| Key | Default | What it does |
|---|---|---|
| `compaction.enabled` | `true` | Auto-compaction on/off. Disabling it means the session fails when the window fills instead of summarizing. |
| `compaction.reserveTokens` | `16384` | Tokens reserved for the model's response; the trigger fires before they are consumed. |
| `compaction.keepRecentTokens` | `20000` | Recent tokens kept verbatim rather than summarized. |

These are pi **core** settings — in `~/.pi/agent/settings.json` or `.pi/settings.json`, not
contributed by any extension. That distinction is load-bearing in the configuration chapter
([docs/03-configuration.md](03-configuration.md)) because its opposite is the trap: an
extension-contributed key pasted into a bare install is silently ignored, and an
extension-provided compaction alternative (the reference setup pins a smart-compact extension)
is a *package*, with its own compatibility and its own failure surface, not a pi setting.

The defaults are snapshots of the upstream documentation from when this guide was verified,
recorded in the verification notes; the durable form is the lookup (`/settings` in a session,
or the upstream settings doc) and the table above is the behaviour, which is stable even as
the numbers may move.

**Failure prevented:** treating compaction as a safety net that preserves what matters. What
compaction preserves is chosen by token count (`keepRecentTokens`), not by value — a critical
fact stated ten turns ago can be summarized into a sentence that loses it. The mitigations are
the derived-answer discipline above (never let raw data in), instruction files (rules re-load
every session regardless of compaction), and durable memory (facts re-recall after compaction).

## Related chapters

- [docs/01-mental-model.md](01-mental-model.md) — the token, window, and recurring-cost
  mechanics this chapter's mitigations answer.
- [docs/03-configuration.md](03-configuration.md) — where the compaction keys live, and the
  core-versus-extension key distinction.
- [docs/04-packages.md](04-packages.md) — how packages are installed, pinned, and licensed;
  the Elastic-2.0 caution for `context-mode` lives there.
- [docs/05-skills.md](05-skills.md) — probabilistic invocation, which is why a memory tool
  being available does not mean the model uses it.
- [docs/07-instruction-files.md](07-instruction-files.md) — where an instruction file lives,
  how the harness loads it, and who owns which part of it. (The rules-versus-facts boundary
  itself is stated in this chapter, under "Instruction files hold rules; memory holds
  facts.")
- [docs/10-private-patterns.md](10-private-patterns.md) — deterministic enforcement, the
  answer when a correction has been given twice.
- [docs/11-verification.md](11-verification.md) — the consolidated claim-to-source matrix,
  including every command in the notes below.

## Verification notes

Claims in this chapter were verified live during writing, each against its cited public source:
registry lookups against the public npm and PyPI registries, upstream documentation fetches
over HTTPS, and one executed runtime MCP check, distinguished below. Citations name the
repository and section — never fork-relative line numbers, and never a private path. Upstream
revisions are provenance, not version pins: re-resolve them with the commands shown before
relying on a citation.

### Claim-to-source table

| Claim in this chapter | Where | Verified by (command) | Result at verification | Public source |
|---|---|---|---|---|
| Hindsight **server** install is `pip install hindsight-api` (full) or `hindsight-api-slim`; embedded `hindsight-all`; Docker image and Helm chart as listed; server command `hindsight-api`, default port 8888, `--port` to change | § real install path | fetched `hindsight.vectorize.io/developer/installation` (bare-metal, Docker, Helm sections) | all present as cited; `hindsight-api --port 9000` documented with default 8888 | Hindsight docs § Installation / Bare Metal (pip) |
| Control-plane UI via `npx @vectorize-io/hindsight-control-plane --api-url http://localhost:8888`, port 9999 | § running a server | same fetch (Control Plane section) | present as cited; `-p/--port` default 9999, `HINDSIGHT_CP_ACCESS_KEY` optional | Hindsight docs § Installation / Control Plane |
| Required env `HINDSIGHT_API_LLM_PROVIDER`, `HINDSIGHT_API_LLM_API_KEY`; optional `HINDSIGHT_API_DATABASE_URL` for external PostgreSQL 14+ with vector extension | § running a server | same fetch (Prerequisites, Bare Metal sections) | present as cited; pgvector default, alternatives pgvectorscale/vchord/scann | Hindsight docs § Installation / Prerequisites |
| **Wrong-distribution trap**: PyPI `hindsight` is an unrelated project | § real install path | `curl -s https://pypi.org/pypi/hindsight/json` (parsed locally) | version 0.1.7, summary "Python tools for Hindsight Software", different author from the memory project | pypi.org |
| `hindsight-api` and `hindsight-client` on PyPI are the real project's server and Python client | § install table | `curl -s https://pypi.org/pypi/hindsight-api/json`; same for `hindsight-client` | both at 0.9.x line, summaries name the agent-memory project | pypi.org |
| pi extension is npm `@luxusai/pi-hindsight`, MIT; compatible TS client `@vectorize-io/hindsight-client` | § pi extension; § install table | `npm view @luxusai/pi-hindsight repository.url license dependencies --json`; `npm view @vectorize-io/hindsight-client repository.url license --json` | extension MIT, repo `github.com/luxus/pi-hindsight`, dependency `@vectorize-io/hindsight-client ^0.9.0`; client MIT, repo `github.com/vectorize-io/hindsight` | registry.npmjs.org |
| MCP adapter is npm `pi-mcp-adapter`, MIT | § MCP | `npm view pi-mcp-adapter repository.url license --json` | `"license": "MIT"`, `git+https://github.com/nicobailon/pi-mcp-adapter.git` | registry.npmjs.org |
| pi core has no MCP — "No MCP" with CLI-tools alternative, in § Philosophy | § MCP concept | fetched `earendil-works/pi` → `packages/coding-agent/README.md`, § Philosophy | "**No MCP.** Build CLI tools with READMEs (see Skills), or build an extension that adds MCP support." present verbatim | `earendil-works/pi` → `packages/coding-agent/README.md` § Philosophy |
| Adapter config: `mcpServers` with `command`/`args` (stdio) or `url`/`headers` (HTTP, mutually exclusive per server); `imports` array for host-specific compatibility; the five precedence levels listed in § configuration shape (`~/.config/mcp/mcp.json`; `~/.agents/mcp.json` and `~/.agents/mcp/mcp.json`; `~/.pi/agent/mcp.json`; `.mcp.json`; `.pi/mcp.json`); `${VAR}` interpolation in headers/env; lazy servers, one proxy tool, metadata cache | § configuration shape | fetched `github.com/nicobailon/pi-mcp-adapter` README (§ What happens on first run, § Quick Start, § Config, § Server Options, § Import Existing Configs, § Usage, § How It Works) | all present as cited; `command` documented "mutually exclusive with `url` and `socket`"; supported imports `cursor`, `claude-code`, `claude-desktop`, `opencode`, `vscode`, `windsurf`, `codex` | `nicobailon/pi-mcp-adapter` README |
| **Worked MCP example**: `@modelcontextprotocol/server-everything` initialize + tools/list + one harmless call, account-free | § worked example | executed live: JSON-RPC over stdio via `npx -y @modelcontextprotocol/server-everything`, isolated temp cwd, no home-config writes — `initialize` → `tools/list` → `tools/call echo` | **executed runtime check** (not source-only): `serverInfo` `mcp-servers/everything` v2.0.0, `protocolVersion` 2025-03-26, capabilities incl. tools/prompts/resources; 13 tools listed; `echo` returned `Echo: verify`, `isError: false`; no auth requested at any step | `modelcontextprotocol/servers` → `src/everything` (reference/test server; its README states "not intended to be a useful server") |
| First-party pi route: `npx @vectorize-io/hindsight-coding-agents install pi` writes an extension entry + companion skill, no MCP; `pi install npm:@vectorize-io/hindsight-coding-agents` deliberately not wired | § a second, first-party route | fetched `hindsight.vectorize.io/sdks/integrations/coding-agents` (pi row); `npm view @vectorize-io/hindsight-coding-agents version repository.url --json` | present as cited; package repo `github.com/vectorize-io/hindsight`, subdirectory `hindsight-integrations/coding-agents` | Hindsight docs § Coding Agents |
| Extension config file `~/.pi/agent/hindsight.json` / `.pi/hindsight.json` (+ `.jsonc`), env override, unknown fields ignored; key structure as documented; `apiKey` is source+name reference; missions/banks boundary | § configuration shape, keys only | fetched `luxus.github.io/pi-hindsight/reference/configuration/` (§ Precedence, § Advanced project config example) and `…/reference/surface-reference/` (§ `hindsight_config`); read the live reference config's **keys** (values redacted, never read into this chapter) | file paths, precedence, and the `banks`/`recall`/`retain`/`hindsight` shapes verified on the public config page; `setupComplete`, `baseUrl`, `projectIdStrategy`, `timeoutMs`, `apiKey` confirmed on the generated surface reference's `hindsight_config` allowlist; one key in the live file (`userRetain`) is **not documented** on either public page checked — recorded in the gaps below, not silently asserted | `luxus/pi-hindsight` docs § Reference / Configuration, § Reference / Surface reference |
| Extension server floor: Hindsight 0.8+ with append `update_mode`; TS client `^0.9.0`; Node >= 20 | § pi extension (compatibility floor as lookup) | fetched `luxus.github.io/pi-hindsight/reference/compatibility/` (§ Supported runtime matrix, § Required Hindsight capabilities) | matrix present as cited; "If append retain is unavailable, live automatic retain is not considered supported"; `/hindsight:doctor` reports the live server floor | `luxus/pi-hindsight` docs § Reference / Compatibility matrix |
| Extension memory tools `hindsight_recall`, `hindsight_retain`, `hindsight_retain_global`, `hindsight_reflect`, `hindsight_status`, plus control-plane tools; `/hindsight` and `/hindsight:next-opt-out` commands; setup gate | § pi extension; § configuration | fetched `luxus.github.io/pi-hindsight/reference/tools-and-commands/` | all present as cited; setup gate requires explicit bank ID for domain-tagged auto memory | `luxus/pi-hindsight` docs § Reference / Tools and commands |
| `context-mode` adds sandboxed execution (`ctx_execute` family), search/index (`ctx_index`, `ctx_search`, `ctx_fetch_and_index`), meta-tools (`ctx_stats`, `ctx_doctor`); pi install via global npm + `pi install npm:context-mode` + `mcpServers` entry; extension registers lifecycle hooks | § the package that mechanizes | fetched `github.com/mksglu/context-mode` README (Pi Coding Agent section); `npm view context-mode license repository.url --json` | present as cited; 11 MCP tools (6 sandbox + 5 meta) plus hooks registered on pi lifecycle events | `mksglu/context-mode` README |
| `context-mode` npm license is Elastic-2.0 | § context management | `npm view context-mode license repository.url --json` | `"license": "Elastic-2.0"`; license caution cross-linked to docs/04, not duplicated here | registry.npmjs.org; `mksglu/context-mode` |
| Compaction: automatic by default, threshold `contextTokens > contextWindow - reserveTokens`, cut point via `keepRecentTokens`, lossy, full history in session file, `/tree` revisit | § pi's own compaction | fetched `earendil-works/pi` → `packages/coding-agent/docs/compaction.md` (§ Compaction / When It Triggers, § How It Works); `packages/coding-agent/README.md` § Sessions | all present as cited; trigger inequality verbatim; split-turn handling documented | `earendil-works/pi` → `packages/coding-agent/docs/compaction.md` |
| Compaction core keys with defaults `compaction.enabled` `true`, `reserveTokens` `16384`, `keepRecentTokens` `20000`; `compaction.modelOverrides` per-model object; `enabled` not model-specific | § compaction key table | fetched `earendil-works/pi` → `packages/coding-agent/docs/settings.md` § Compaction | table rows present with those defaults; resolution order documented (override → ordinary → built-in default) | `earendil-works/pi` → `packages/coding-agent/docs/settings.md` § Compaction |

### Upstream revisions at verification (provenance, not pins)

Resolved during this chapter's verification by
`curl -fsSL https://api.github.com/repos/<owner>/<repo>/commits/<default-branch>`:

| Repository | Branch | Resolved commit | Committed |
|---|---|---|---|
| `earendil-works/pi` | `main` | `71dca871bc80` | 2026-09-11 |
| `nicobailon/pi-mcp-adapter` | `main` | `b8fbc9cdc871` | 2026-09-14 |
| `luxus/pi-hindsight` | `main` | `8ab02c423b40` | 2026-08-13 |
| `vectorize-io/hindsight` | `main` | `e3efe5dd8b07` | 2026-09-13 |
| `modelcontextprotocol/servers` | `main` | `d73f99efbfd4` | 2026-09-03 |
| `mksglu/context-mode` | `main` | `ba5f5dfd1a0c` | 2026-09-13 |

Registry values (`npm view … version`, PyPI JSON API) are point-in-time and re-runnable; the
table records what the lookups returned so a reader can re-run them and reconcile drift against
this chapter's recorded results rather than trusting this snapshot.

### The worked-example runtime check, in full

Executed in an isolated temporary working directory (no writes to the operator's real pi
configuration, no global installs), with the driver above:

```bash
npx -y @modelcontextprotocol/server-everything   # stdio JSON-RPC, driven by a small Python driver
```

Driver shape (JSON-RPC 2.0, LF-delimited, per the MCP specification): send `initialize` with
client info, read the result; send `notifications/initialized`; send `tools/list`, read the
result; send `tools/call` with `name: "echo"` and `{"message": "verify"}`, read the result.

The exact driver, replayable. **Prerequisites:** Python 3 *and* Node/npm (`npx -y` can download
the server and write npm cache/logs outside the temporary cwd). It does not write Pi
configuration. Isolate npm as well if you need write isolation (`npm_config_cache` under the
temp dir).

```python
import subprocess, json, threading, queue, time, os

proc = subprocess.Popen(
    ["npx", "-y", "@modelcontextprotocol/server-everything"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    text=True, bufsize=1,
)
lines = queue.Queue()
threading.Thread(target=lambda: [lines.put(l) for l in iter(proc.stdout.readline, "")] or lines.put(None),
                 daemon=True).start()

def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n"); proc.stdin.flush()

def read_until_id(want_id, timeout_s=20):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty:
            proc.terminate()
            raise SystemExit("FAIL: timed out waiting for MCP response id=%s" % want_id)
        if line is None:
            proc.terminate()
            raise SystemExit("FAIL: MCP server closed stdout before id=%s" % want_id)
        line = line.strip()
        if not line:
            continue
        try:
            m = json.loads(line)
        except ValueError:
            continue
        if m.get("id") == want_id:
            return m
    proc.terminate()
    raise SystemExit("FAIL: timed out waiting for MCP response id=%s" % want_id)

send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-03-26", "capabilities": {},
    "clientInfo": {"name": "doc-verify", "version": "0.0.1"}}})
r = read_until_id(1)
print("INIT serverInfo:", json.dumps(r["result"]["serverInfo"]))
print("INIT protocolVersion:", r["result"]["protocolVersion"])

send({"jsonrpc": "2.0", "method": "notifications/initialized"})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
r2 = read_until_id(2)
tools = [t["name"] for t in r2["result"]["tools"]]
print(f"TOOLS/LIST: {len(tools)} tools returned")

send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
    "name": "echo", "arguments": {"message": "verify"}}})
r3 = read_until_id(3)
print("CALL echo isError:", r3["result"].get("isError", False))
print("CALL echo content:", r3["result"]["content"][0]["text"])

proc.stdin.close(); proc.terminate()
```

Captured results, verbatim:

```
INIT serverInfo: {"name": "mcp-servers/everything", "title": "Everything Reference Server", "version": "2.0.0"}
INIT protocolVersion: 2025-03-26
TOOLS/LIST: 13 tools returned
CALL echo isError: False
CALL echo content: Echo: verify
```

### Not verified (explicit gaps)

- **No runtime check of the Hindsight server or the pi extension.** Installing and running the
  memory server requires an LLM provider key and a database decision; this template distinguishes
  source verification from executed runtime checks, and this chapter
  verifies the install path, config shape, and compatibility floor from the projects' own
  documentation, not from a live server session. The MCP worked example above is the executed
  runtime check this chapter *does* carry — chosen precisely because it needs no key.
- **No runtime check that `pi install npm:@luxusai/pi-hindsight` (or `pi-mcp-adapter`, or
  `context-mode`) succeeds on a bare upstream install.** Verified at the registry/source level;
  installation is the reader's step, and the packages chapter
  ([docs/04-packages.md](04-packages.md)) owns the per-package provenance.
- **The extension's complete config surface** (every field and default) is documented by its
  public reference and the live reference file's keys were read (values redacted), but not
  field-by-field against the extension's source code — and one live-file key (`userRetain`)
  was **not found** on either public page checked (the configuration page or the generated
  surface reference). It may be a legacy or migrated field; a reader should treat the
  public reference and `/hindsight` status as authoritative over this chapter's key list.
  The public reference is the authority cited, and `/hindsight` status is the reader's live
  lookup.
- **Which specific memory profile suits a given repo** — that is a user decision the extension's
  guided setup exists to walk through; this chapter documents the mechanism, not the choice.
- **The worked example's tool list beyond the capture.** The reference server exercises protocol
  features that evolve; the captured exchange (initialize, 13 tools listed, `echo` call) is the
  durable, reproducible part, and a reader re-running the three JSON-RPC messages should
  expect the same interaction shape with a possibly-larger tool list as the reference server
  grows.
