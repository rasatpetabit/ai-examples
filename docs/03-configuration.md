# 3 — Configuration: settings, trust, and model selection

pi keeps its configuration in two JSON files and one trust decision. This chapter covers all three:
where the files live and which one wins, what the keys are (by category, without transcribing the
whole catalog), how to tell a pi-core key from one an extension contributes, what project trust
actually gates, and how to pick a model and provider by lookup instead of by copying a name.

This is the chapter to read after [installing](02-install.md) and before [choosing packages](04-packages.md).
It assumes you have never configured an agent before; it assumes you have configured many systems
in general. Related surfaces are covered elsewhere and only pointed at here: package installation
and pinning semantics live in [chapter 4](04-packages.md), skill discovery and its locations in
[chapter 5](05-skills.md), compaction keys in depth in [chapter 6](06-memory-mcp-context.md), and
the `AGENTS.md`/`CLAUDE.md` instruction hierarchy in [chapter 7](07-instruction-files.md).

One framing before anything else, because the reference setup — the working setup this template
generalizes from — is often the first place a reader meets it: **pi's core is deliberately minimal.**
Upstream states the philosophy plainly — features that other tools bake in are reached through
extensions, skills, or installable packages, keeping the core minimal
(`earendil-works/pi` → `packages/coding-agent/README.md` § Philosophy). If you arrive from another
agent harness, you may expect MCP, subagents, plan mode, or permission prompts to be core features;
in pi none of them are. And the reference configuration carries keys pi itself has never heard of,
contributed by extensions. A reader who does not learn that distinction early will paste keys pi
silently ignores — the load-bearing lesson of this chapter.

## The two settings files, and which one wins

pi reads JSON settings from two locations, with the project file overriding the global one:

| Location | Scope |
|----------|-------|
| `~/.pi/agent/settings.json` | Global (all projects) |
| `.pi/settings.json` | Project (current directory) |

You can edit these files directly, or change common options interactively with the `/settings`
command inside a session. There is no third location and no merge mode to configure: this two-file
override is the whole model
(`earendil-works/pi` → `packages/coding-agent/README.md` § Settings;
`packages/coding-agent/docs/settings.md` § Settings).

Project settings override global settings, and **nested objects are merged**, not replaced:
if the global file sets `compaction.enabled` and a project sets `compaction.reserveTokens`, the
result has both (`packages/coding-agent/docs/settings.md` § Project Overrides). For arrays,
upstream documents replacement explicitly where it matters — e.g. a project `defaultTools` array
replaces the global array (§ Tools) — so treat arrays as replace-when-set and read the specific
key's row in the settings doc before relying on either behaviour.

One gate sits in front of the project file, and it is not a settings key: **pi does not load
`.pi/settings.json` at all until the project is trusted** (see [Project trust](#project-trust--what-it-gates-and-what-it-does-not)
below). Before that decision, only context files, user/global extensions, and CLI `-e` extensions
load. This is why a project file can fail to "apply" with no error: the trust decision has not
been made, so the file was never read.

## The authoritative key list, by category

The full key catalog is upstream's to own, not this chapter's. A document that transcribes it
becomes a stale cache the moment upstream adds a key — the exact "rots into wrong instructions"
failure this template exists to avoid. So: the categories below reproduce upstream's own
organization, name the keys that matter to a newcomer, and point at the authoritative source
(`earendil-works/pi` → `packages/coding-agent/docs/settings.md` § All Settings) for everything else.
`/settings` inside a session lists the common options interactively.

**Model & thinking** — `defaultProvider`, `defaultModel`, `defaultThinkingLevel`,
`modelThinkingLevels`, `thinkingBudgets`. These are where pi records the provider, model, and
thinking level you saved as your startup defaults (see [Choosing a model and provider](#choosing-a-model-and-provider--by-lookup-not-by-pinned-name)
below). `enabledModels` controls which models are available to Ctrl+P cycling.

**Project trust** — `defaultProjectTrust`. One key, global-only, covered in its own section
below. Everything trust-related that is *state* rather than *settings* lives in
`~/.pi/agent/trust.json`, not here.

**Compaction** — `compaction.enabled`, `compaction.reserveTokens`, `compaction.keepRecentTokens`,
plus `compaction.modelOverrides` for per-model values. What compaction is and what it loses is
[chapter 6](06-memory-mcp-context.md)'s subject; the keys are pi core.

**Retry** — `retry.enabled`, `retry.maxRetries`, `retry.baseDelayMs`, `retry.provider.timeoutMs`.
Upstream documents a caution worth reading before touching `retry.provider.maxRetries`: setting it
above its default can let SDK-level retries handle an out-of-quota error before pi sees it, which
may block the agent until the provider quota resets. Read the current guidance in the settings doc
before changing it.

**Shell** — `shellPath`, `shellCommandPrefix`, `npmCommand`. `npmCommand` matters if you use a
version manager: it lets you name the argv (for example `["mise", "exec", "node@20", "--", "npm"]`)
that pi should use for package operations instead of a bare `npm`.

**Tools** — `defaultTools`, the built-in tools enabled at startup. The upstream built-in list is
exactly `read`, `bash`, `powershell` (Windows), `edit`, `write`, `grep`, `find`, `ls`; `defaultTools`
selects among those, and extension/SDK custom tools stay enabled regardless. `--tools` is a strict
allowlist across all tool sources; `--no-tools` disables everything.

**Network and telemetry** — `httpProxy`, `enableInstallTelemetry`, `enableAnalytics`. The telemetry
behavior, what it pings, and the opt-outs (`PI_SKIP_VERSION_CHECK`, `--offline`/`PI_OFFLINE`) are
documented in the settings doc's telemetry section.

**Resources** — `packages`, `extensions`, `skills`, `prompts`, `themes`. These arrays say where to
load each resource type from. Paths in the global file resolve relative to `~/.pi/agent`; paths in
the project file resolve relative to `.pi`. Arrays support glob patterns and exclusions. The
`packages` entry is the one [chapter 4](04-packages.md) teaches you to manage through `pi install`
rather than by hand, because the CLI maintains pinning semantics a hand edit can get wrong.

Everything else — UI, terminal, images, markdown, sessions, branch summary, message delivery — is
cosmetic or situational, and the settings doc is the authority. If you need a key this chapter
does not name, look there first; if the key is not there, it is not pi's.

## Core keys versus extension-contributed keys — the method

This is the single most important thing this chapter teaches, and it comes directly from the
reference setup: the settings file this template generalizes from contains a `smartCompact`
block. It works there — and pasting it into a bare pi install does nothing, because
**`smartCompact` is not a pi core key**. It is contributed by the `pi-smart-compact` extension:
upstream's `docs/settings.md` does not mention it, and the extension's own README is the document
that tells you to add it to `settings.json` and what its sub-keys are
(`pi-smart-compact` → `README.md` § Configuration; verified absent from
`earendil-works/pi` → `packages/coding-agent/docs/settings.md`).

Nothing warns you. Whatever the loader's exact policy on an unrecognized key (see the
verification note below — this guide does not claim to know it), a key whose owning extension is
absent has no reader, so the setting arrives nowhere. The failure looks like "the extension is
broken" from the outside when the real state is "the key's owner is not installed".

**Failure prevented:** pasting a settings block whose keys belong to an extension you have not
installed, then debugging the extension when the actual state is that pi silently ignores keys it
does not know.

The method, applied to any settings block you copy from anywhere:

1. **Ask who owns the key.** The owner is the thing that *reads* it. pi core reads the keys in
   its own settings doc. An extension reads the keys its own documentation says it reads. A
   settings file copied from a working setup is a mix of both, and nothing labels which is which.
2. **Check against the core catalog.** The current authority is
   `earendil-works/pi` → `packages/coding-agent/docs/settings.md` § All Settings. A key absent
   from that catalog is not pi's — it belongs to something installed in that setup.
3. **Confirm the owner actually loads.** `pi list` is a **package** inventory
   (`packages/coding-agent/README.md` § Pi Packages: "`pi list # List installed packages`"),
   not a complete extension inventory. Extensions also arrive via CLI `-e` and via paths in
   settings. If the owner is not a package, check those other routes before installing a
   duplicate or deleting a live block. If nothing loads the key, either install the owner
   ([chapter 4](04-packages.md)) or drop the block — a key without its reader is dead weight.
4. **Read the owner's own doc for the sub-keys.** For `smartCompact` that is the extension's
   README, not pi's docs. Sub-keys of an extension block change with the extension, and only its
   own documentation tracks them.

The same test applies in reverse: keys can *move*. An extension key pi later adopts into core
(upstream decides to build a feature in) stops being an extension key, and a key that moves the
other way breaks. This is why the method is "check against the current catalog", not "memorize
the list" — the check is cheap and reflects the live catalog; any transcribed list reflects only
the day it was written.

## Project trust — what it gates, and what it does not

A project folder can carry its own settings, resources, and skills. Before pi loads any of that,
it wants a trust decision: **on interactive startup, pi asks before trusting a project folder that
contains project-local settings, resources, or project `.agents/skills` and has no saved decision
for the folder (or a parent) in `~/.pi/agent/trust.json`.**

Trusting a project allows pi to:

- load `.pi/settings.json` and `.pi` resources,
- install missing project packages, and
- execute project extensions.

(`earendil-works/pi` → `packages/coding-agent/docs/settings.md` § Project Trust.)

### Trust gates loading — it is not a permission system

Read that allow-list carefully, because every verb on it is a **loading** verb. Project trust
answers one question: *may pi read and load the project-local configuration at all?* It does not
restrict what a tool may do once everything is loaded. `defaultProjectTrust: always` therefore
widens what is **loaded** — project settings, resources, packages, extensions — not what is
**permitted**.

This matters because it is easy to mistake trust for containment: "I trust only my own repos, so an
agent in an untrusted repo can't touch anything." That inference is exactly backwards for what it
does not cover. Upstream states the boundary in plain terms: pi does not include a built-in
permission system for restricting filesystem, process, network, or credential access, and by
default runs with the permissions of the user and process that launched it
(`earendil-works/pi` → `README.md` (monorepo root) § Permissions & Containerization). Trusting or
not-trusting a folder changes which *configuration* pi loads there — nothing more. For actual
boundaries, upstream points at containerization patterns (its `docs/containerization.md` lists
three) rather than at any pi setting. This template is not a security guide; the boundary is named
here so you do not mistake a loading gate for a sandbox.

**Failure prevented:** assuming `defaultProjectTrust: always` (or `never`) constrains what an
agent can *do* in a folder, when it only constrains what configuration pi *loads* there.

### `defaultProjectTrust` — the fallback, and the global-only rule

`defaultProjectTrust` is one string in the global settings file, with three values:

| Value | Behaviour |
|---|---|
| `"ask"` | prompt on interactive startup (the default) |
| `"always"` | trust project-local settings, resources, and packages without prompting |
| `"never"` | never load project-local settings, resources, or packages, without prompting |

It is a **global setting only**: it cannot be set per-project — and this follows from the
mechanism itself, since a project file pi has not yet loaded cannot influence the decision about
loading itself. A `defaultProjectTrust` inside `.pi/settings.json` would never be read in time to
govern the trust decision that gates that same file
(`earendil-works/pi` → `packages/coding-agent/docs/settings.md` § All Settings,
`defaultProjectTrust` row). You can set it by editing `~/.pi/agent/settings.json`, or change it
interactively through `/settings`.

### Non-interactive modes never prompt

`-p`/`--print`, `--mode json`, and `--mode rpc` do not show a trust prompt — there is no one to
ask. Without an applicable saved decision they fall back to `defaultProjectTrust`: `ask` and
`never` ignore the project resources; `always` trusts them. For one run you can force either way
with `--approve`/`-a` or `--no-approve`/`-na`. `pi config` and package commands follow the same
flow, with one carve-out: **`pi update` never prompts.**

**Failure prevented:** wiring pi into a script or CI job, having it silently ignore
`.pi/settings.json` (with `ask` as the default in a non-interactive run), and diagnosing the wrong
thing — the fix is `--approve` or `defaultProjectTrust`, not touching the project file.

### `/trust` and the restart requirement

Inside an interactive session, `/trust` saves a trust decision for future sessions — including
trust for the immediate parent folder — by writing `~/.pi/agent/trust.json`. **It does not reload
the current session**: the project-local settings and resources you just trusted are not live in
the session that saved the decision. Restart pi for the change to take effect.

**Failure prevented:** running `/trust`, seeing the prompt stop appearing, and concluding the
project settings are now loaded in the running session — then "fixing" it by hand-editing the
global file, which was never the problem.

The trust decisions themselves live in `~/.pi/agent/trust.json`, keyed by folder. That file is
state, not settings; you generally manage it through pi (`/trust`, `--approve`, `--no-approve`)
rather than by hand.

## Choosing a model and provider — by lookup, not by pinned name

pi talks to many providers. Authentication and the provider list are [chapter 2](02-install.md)'s
territory; what belongs here is how the *choice* is recorded and how to re-make it without
guessing.

The interactive path is `/model` (or Ctrl+L): it lists the models your configured providers make
available, and **Ctrl+S in the picker saves the highlighted model as your startup default** —
written to `defaultProvider`/`defaultModel` in the global settings file. `/thinking` does the same
for the thinking level (`defaultThinkingLevel`). Catalogs refresh automatically; `pi update
--models` forces an immediate refresh. For non-interactive use, the same choice can be made with
`--provider` and `--model` flags per run, or by editing the keys directly
(`earendil-works/pi` → `packages/coding-agent/README.md` § Providers & Models, § CLI Reference).

To see what is available *before* choosing, use the lookup, not a memory:

```bash
pi --list-models            # list available models; optional search argument narrows it
pi --version                # confirm which pi you are actually running
```

(`packages/coding-agent/README.md` § CLI Reference: `--list-models [search]`, `-v`/`--version`.)

This chapter therefore names no model — the anti-pinning rule that requires it is owned by
[README.md](../README.md) ("Lookup over literal"). Model identities churn constantly: a name a
guide recommends today is gone or wrong-priced or wrong-shaped within months, and the guide has
no maintenance promise to fix it. The durable instruction is the lookup command, which asks the
live system rather than trusting a transcription — though the command itself can age, so a failure
from one is news about the command, not only about the value (see
[docs/02-install.md](02-install.md) for that qualification). If you are writing instruction files for
your own setup (see [chapter 7](07-instruction-files.md)) and want to record a default, record it
in pi's own settings keys via `/model` + Ctrl+S — pi resolves the current catalog at startup —
rather than naming a model in prose that a human or agent will later treat as truth.

**Failure prevented:** copying a model name out of a blog, a colleague's config, or an old
snapshot of this document and troubleshooting provider errors that are actually "that model ID no
longer exists" — which the picker never shows you because the picker only lists live models.

For provider credentials, the same principle applies to provider identity: pi supports both
subscription auth (`/login`) and API-key auth, per provider, and the environment-variable name is
per-provider. The authoritative table of provider names, their env vars, and their `auth.json` keys
is upstream's to own (`earendil-works/pi` → `packages/coding-agent/docs/providers.md` § API Keys)
because it grows with every release. Export the right variable, or run `/login` and let pi store
the key in `~/.pi/agent/auth.json` — do not copy a variable name from a document that may not
name your provider or its current variable.

## Verification notes

Every version-sensitive claim above was checked against pristine upstream at the time of writing,
not against the local installation (which is a fork and not proof of what a reader has). Re-run
these yourself; the guide makes no maintenance promise.

**Resolved upstream revisions** (branch `main`):

- `earendil-works/pi` branch HEAD: `71dca871` (2026-09-11)
- `packages/coding-agent/docs/settings.md` last touched: `46bde88a` (2026-09-10)
- `packages/coding-agent/docs/providers.md` last touched: `aa23e784` (2026-09-07)
- `packages/coding-agent/README.md` last touched: `47acd8e6` (2026-09-07)
- `alpertarhan/pi-smart-compact` HEAD: `687f72c` (2026-09-05); npm `pi-smart-compact` latest
  publishes from exactly that git head (registry `gitHead` matches)

| Claim in this chapter | How verified | Source (public) |
|---|---|---|
| Two settings files; project overrides global; nested objects merge; project `defaultTools` array replaces global | fetched and read upstream doc, § Settings, § Tools, § Project Overrides | `github.com/earendil-works/pi` → `packages/coding-agent/docs/settings.md` |
| `smartCompact` absent from pi core settings | grep of upstream `docs/settings.md` at HEAD `71dca871`: zero matches | same |
| `smartCompact` owned by `pi-smart-compact`, added to `settings.json` by its README § Configuration | fetched extension README from registry + GitHub; confirmed `pi` block with `extensions` entry; sub-keys listed in its Configuration section | `registry.npmjs.org/pi-smart-compact`, `github.com/alpertarhan/pi-smart-compact` |
| Trust prompt trigger, what trusting permits (three load-time verbs), `--approve`/`--no-approve`, `/trust` writes trust.json only, restart required | fetched and read upstream `docs/settings.md` § Project Trust; cross-checked README § Settings → Project Trust | `github.com/earendil-works/pi` → `packages/coding-agent/docs/settings.md`, `packages/coding-agent/README.md` |
| `defaultProjectTrust` `ask`/`always`/`never`, default `ask`, global setting only | upstream settings doc, `defaultProjectTrust` row in § All Settings | same settings doc |
| Non-interactive modes never prompt; `pi update` never prompts | same § Project Trust section, verbatim | same |
| pi has no built-in permission system; runs with the launching user's permissions | fetched monorepo root README § Permissions & Containerization, verbatim | `github.com/earendil-works/pi` → `README.md` (monorepo root) |
| `/model` + Ctrl+S saves startup default; `pi --list-models`; `pi --version`; `pi update --models`; `--provider`/`--model` flags | fetched and read upstream README § Providers & Models, § Commands, § CLI Reference | `github.com/earendil-works/pi` → `packages/coding-agent/README.md` |
| `pi list` lists installed packages | upstream README § Pi Packages (`pi list # List installed packages`) | `github.com/earendil-works/pi` → `packages/coding-agent/README.md` |
| Provider env vars are per-provider; table is the authority | fetched and read upstream `docs/providers.md` § API Keys (table present, growing) | `github.com/earendil-works/pi` → `packages/coding-agent/docs/providers.md` |
| Built-in tool list `read`/`bash`/`powershell`/`edit`/`write`/`grep`/`find`/`ls` | upstream `docs/settings.md` § Tools | same settings doc |
| Default `compaction.reserveTokens`/`keepRecentTokens` are pi core keys | upstream settings doc § Compaction (values deliberately not reproduced here; they are in the doc) | same |

Re-verification, for any future reader (all network lookups, nothing local):

```bash
curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/settings.md | grep -n "defaultProjectTrust"
curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/settings.md | grep -cn "smartCompact"   # expect 0
curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/README.md | grep -n "built-in permission system"
curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/README.md | grep -n "list-models"
```

**Not verified by a runtime check in this chapter** (source-verified only — no live pi session was
run to produce it, deliberately, since an isolated install is [chapter 2](02-install.md)'s
verification): the interactive feel of `/settings`, `/model`, and `/trust`, the trust prompt's
exact wording, and pi's behaviour on a settings file containing an unknown key. The first two
are described from upstream documentation text, which is the source pi ships; a discrepancy
between the doc and the binary would be an upstream bug, not a claim this guide invented. Unknown-key behaviour is **not** established here: a loader can ignore an unknown key, warn, or
reject the file. The reference setup appears to ignore unknown keys; that is an observation, not
an isolated upstream runtime probe, and it is not a claim about every loader.

**Deliberately excluded:** this chapter names no model identities, no provider-by-provider
env-var list, and no copied default values for settings keys that upstream documents — every one
of those goes stale, and the lookup that replaces it is given beside the claim. The
`smartCompact` sub-key list is likewise the extension's to own.

**Where this boundary sits.** The rule above is about *this* chapter, which is the one a reader
opens to configure a key: it teaches the lookup instead of the value. A chapter may still show a
default when the default IS the point it is making — `docs/01` and `docs/06` quote the compaction
numbers to explain what compaction does and what it costs — and those places carry the upstream
revision they were read at. The distinction is not "values are forbidden" but "a value is either
the subject of the sentence or it is replaced by the command that fetches it."
