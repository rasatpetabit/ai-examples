# 02 — Install pi, authenticate, and run a first verified session

This chapter takes you from a machine with Node.js to a pi session that has provably worked:
install by either official path, authenticate by either official path, and verify each step with a
command whose output you can see. Everything here is a command you run yourself; this guide ships
no installer and never writes to your configuration.

What you finish with: a globally installed `pi` on your `PATH`, working provider credentials, a
first session in a real project directory, and the habit of checking a claim with a command rather
than trusting a document — including this one.

> **How to read the citations in this chapter.** Facts are cited to the pristine upstream
> repository `earendil-works/pi` by file and section at a recorded revision, never by line number.
> Beware one trap: the upstream repo has **two** files called `README.md`. The *monorepo root*
> README covers packaging and permissions; the *package* README
> (`packages/coding-agent/README.md`) is the one that ships with the npm package and holds Quick
> Start, Settings, and Philosophy. Where this chapter says `packages/coding-agent/README.md`, use
> exactly that path — the same section name in the root README may not exist.

## What you are installing

`pi` is the npm package `@earendil-works/pi-coding-agent` from the upstream repository
`github.com/earendil-works/pi`, MIT-licensed (check it yourself: `npm view
@earendil-works/pi-coding-agent version license repository.url --json`).

It is deliberately **not** the kitchen-sink agent you may be expecting. Upstream's design
philosophy (`packages/coding-agent/README.md` § Philosophy) is an aggressively minimal core that
you extend instead of configure: **no MCP** (write CLI tools with READMEs, or add MCP via an
extension), **no sub-agents** (spawn pi instances via tmux, or add them with an extension or
package), **no permission popups** (containerize, or build your own confirmation flow), **no plan
mode** (write plans to files), **no built-in to-dos** (use a TODO file), **no background bash**
(use tmux). Every one of those absences is reachable — through extensions and third-party
packages, covered in [docs/04-packages.md](04-packages.md) and
[docs/06-memory-mcp-context.md](06-memory-mcp-context.md).

**Failure prevented:** an engineer arriving from another harness assumes MCP servers, subagent
fan-outs, and permission prompts are defaults, then wastes an evening looking for settings that
do not exist. The minimal core is the product; capability is added explicitly, which is why later
chapters teach *adding* rather than *toggling*.

**Prerequisite.** Node.js. No version number is stated here, per the anti-pinning rule owned by
[README.md](../README.md) ("Lookup over literal") — the package's own `engines` field is
authoritative and changes:

```bash
npm view @earendil-works/pi-coding-agent engines --json
node --version   # your side of the comparison
```

**Failure prevented:** a version floor copied into a document silently rots into either "too old
to be useful" or "lies about the minimum," and the reader who trusted it gets install-time
surprises instead of a fact.

## Install path A — npm global install

The upstream-documented command (`packages/coding-agent/README.md` § Quick Start):

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

`--ignore-scripts` disables npm *dependency lifecycle scripts* for this install — postinstall
hooks and their kin, which run arbitrary code from every transitive dependency's package. Upstream
states pi does not require install scripts for a normal npm install, so the flag costs nothing and
removes an entire class of supply-chain execution at install time.

**Be precise about what `--ignore-scripts` does not do.** It bounds one thing: scripts that would
run *during this npm install*. It is not a sandbox, not a permission system, and not a statement
about what the installed binary does afterwards — see
[The authority boundary](#the-authority-boundary-read-this-before-your-first-session) below.

**Failure prevented:** a reader who sees a security-motivated flag in an install command concludes
the resulting installation is contained. It is not; conflating the two is how people end up
running an agent with full user authority while believing they have sandboxed it.

## Install path B — the pi.dev installer

Upstream also ships a convenience installer (`packages/coding-agent/README.md` § Quick Start,
"Installer alternative"):

```bash
curl -fsSL https://pi.dev/install.sh | sh
```

This is a shell script that, at the time of verification, performs the *same* npm global install
with `--ignore-scripts` under the hood, can bootstrap Node.js/npm first if they are missing, and
can be redirected to a user-writable prefix via its `PI_NPM_INSTALL_PREFIX` environment variable.
Both install paths converge on the same package; choose the curl form if you want Node bootstrapped
for you, and the npm form if your Node setup is already exactly how you want it.

The rule that matters with any `curl | sh` pipe — upstream's or anyone else's — is to read the
script before executing it:

```bash
install_dir=$(mktemp -d)
curl -fsSL https://pi.dev/install.sh -o "$install_dir/install.sh" || { rm -rf "$install_dir"; exit 1; }
less "$install_dir/install.sh"          # what does it write, and where?
sh "$install_dir/install.sh"
rm -rf "$install_dir"
```

**Failure prevented:** piping a URL straight into `sh` executes whatever bytes are served at that
URL *today* with your authority. Reading first costs a minute and converts an act of trust into an
act of verification — the same discipline this chapter applies to every other claim.

Removal is symmetric with however you installed (the curl installer is an npm global install, so
`npm uninstall -g @earendil-works/pi-coding-agent` covers both paths). Upstream notes that
uninstalling leaves settings, credentials, sessions, and installed packages in `~/.pi/agent/` —
delete that directory explicitly if you want a truly clean slate.

## The authority boundary (read this before your first session)

This is the single most important paragraph in the chapter. Upstream says it plainly
(`earendil-works/pi` root `README.md` § Permissions & Containerization): **pi has no built-in
permission system** for restricting filesystem, process, network, or credential access. **It runs
with the full permissions of the user and process that launched it.** The model can read what you
can read, write what you can write, and run what you can run — through its `bash` tool that means
any command, with no confirmation prompt in the core product.

Consequences, stated so they cannot be misread:

- `--ignore-scripts` bounds only package-install lifecycle scripts. It is not a sandbox.
- There are no permission popups in core pi. A write happens because the model decided to write.
- The only real boundary is the one *you* put around the process: run pi inside a container, or
  route its tools into one. Upstream documents three patterns in
  `packages/coding-agent/docs/containerization.md` — the **Gondolin extension** (pi and provider
  auth stay on the host, built-in tools and `!` commands run in a local Linux micro-VM), **plain
  Docker** (the whole pi process in a local container), and **OpenShell** (the whole process in a
  policy-controlled sandbox). Those are pointers, not instructions — this guide is not a security
  guide. Read upstream's own containerization document if you need one.

**Failure prevented:** every "the agent deleted something / ran something / read something"
disaster begins with the operator believing a boundary existed that did not. The two flags this
chapter has already shown you (`--ignore-scripts`, and project trust, covered in
[docs/03-configuration.md](03-configuration.md)) gate *what gets installed and loaded* — never
what an already-running agent may do. Package-supplied code adds further attack surface with the
same authority; [docs/04-packages.md](04-packages.md) covers what to check before installing any
third-party package.

Two habits that **do not replace** the missing permission system, but help you recover covered
project files: start pi in a directory whose contents are disposable or version-controlled, and
rely on your own checkpointing for rollback of those files — upstream's quickstart says this
("Pi runs in your current working directory and can modify files there. Use git or another
checkpointing workflow if you want easy rollback"). A working directory does not confine the
process to that directory. Checkpoints cannot undo credential disclosure, network actions, or
writes outside their coverage. Containment is still the three patterns named above.

## Authentication path A — your existing subscription (no API key needed)

If you already pay for a coding subscription, you need **no API key at all**. Start `pi` in a
project directory and run:

```text
/login
```

then pick your provider from the interactive picker. Upstream's built-in subscription logins
include Anthropic Claude Pro/Max, OpenAI ChatGPT Plus/Pro (Codex), and GitHub Copilot
(`packages/coding-agent/README.md` § Providers & Models); the `/login` picker and
`packages/coding-agent/docs/providers.md` § Subscriptions are the live, authoritative list —
subscription providers have been added over time and more may exist by the time you read this.
The login stores OAuth tokens in `~/.pi/agent/auth.json` and refreshes them automatically;
`/logout` clears them.

**Failure prevented:** a reader concludes they must create an API key, add billing, or manage key
rotation before pi is usable at all. With a subscription, authentication is one command — and if
that is not obvious, a reader pays for a capability they already have.

**Failure prevented:** the same reader assumes the subscription's plan limits cover third-party
harness usage. Upstream's providers document states Anthropic subscription auth bills third-party
usage per token against "extra usage," not against the plan's limits — read your provider's terms
before pointing pi at paid work.

## Authentication path B — an API key

The other official path (`packages/coding-agent/docs/quickstart.md` § Authenticate, "Option 2"):
set a provider-specific environment variable before launching, or store the key in pi's auth
file:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pi
```

— or start `pi` and use `/login`, selecting an API-key provider instead of a subscription; that
stores the key in `~/.pi/agent/auth.json`.

Two facts worth knowing:

- Each provider has its own environment variable name and matching `auth.json` key — Anthropic's
  is `ANTHROPIC_API_KEY`/`anthropic`, but do not guess the rest. The authoritative table is
  `packages/coding-agent/docs/providers.md` § API Keys → "Environment Variables or Auth File",
  which lists every supported provider with both names.
- The auth file is created with `0600` permissions (user read/write only), and credentials in the
  auth file take **priority over** environment variables.

**Failure prevented:** an engineer puts a key in the wrong provider's variable (or invents a
plausible name for a provider whose real variable differs), gets a credentials error, and
concludes pi is broken. The table is the answer; guessing is the failure.

**Failure prevented:** the same engineer exports the key in a shell startup file that lands in a
repo, a screenshot, or a bug report. Prefer the auth file for anything durable, and treat any
credential pasted anywhere as needing cleanup — pi reads keys from one env var or one file, which
makes the audit surface small by design.

## Verifying the install and authentication

Do not trust that an install or a login worked because no error appeared — verify, the same way
you would verify any other system's provisioning. All of the following are checkable
non-interactively, which is what makes them evidence rather than impressions:

```bash
pi --version        # the binary is on PATH and reports a build
pi --help           # full CLI surface: install/remove/update/list/config/auth
pi --list-models    # models visible under your current credentials
pi auth check --provider anthropic --json   # per-provider readiness probe
```

What you should observe:

- `pi --version` prints a version and exits 0. If your shell cannot find `pi`, the install
  directory is not on your `PATH` — that is the one common npm-global failure mode, and it is
  about your shell, not about pi.
- `pi --list-models` prints the model list your credentials unlock. With **no credentials
  configured** it prints a "no models available, use /login" message instead — which is itself a
  useful signal: it proves the binary runs and tells you the exact next step.
- `pi auth check --provider anthropic --json` reports machine-readable status. Before
  authentication it reports a `not_ready` status with a `credentials_not_configured` reason;
  after a working `/login` or key setup for that provider, the same probe reports ready. Swap in
  whichever provider you authenticated with.

The "before" half of those expectations was verified against a pristine upstream install in an
isolated test home during the writing of this chapter (see
[Compact verification notes](#compact-verification-notes) below) — including the "no models
available" message and the `not_ready` JSON. The "after a successful login" half is upstream's
documented behaviour and was **not** exercised here, because verifying it requires real
credentials; run the probe yourself after `/login` and observe the transition.

**Failure prevented:** a claimed-finished install that never worked — a binary shadowed by
another `pi` on the `PATH`, a credentials file with the wrong provider name, a login that
succeeded against a provider you never selected. A one-line probe converts each of these from
"discovered mid-session, in the middle of real work" to "discovered now, in three seconds."

## First session

Start pi in the directory you want it to work on (`packages/coding-agent/docs/quickstart.md` §
First session):

```bash
cd /path/to/project
pi
```

By default the model gets exactly four tools (`packages/coding-agent/README.md` § Quick Start,
§ CLI Reference → Tool Options):

- `read` — read files
- `write` — create or overwrite files
- `edit` — apply targeted patches to files
- `bash` — run shell commands

Three additional built-in *read-only* tools (`grep`, `find`, `ls`) exist but are not enabled by
default; they are available through tool options (`--tools`, `--exclude-tools`) rather than being
something you need before your first session. Give the model a real task and watch it work:

```text
Summarize this repository and tell me how to run its checks.
```

**Observable success** — what a working session looks like on screen, so you can tell "running"
from "hung" without guessing:

- The startup header lists the context files (e.g. `AGENTS.md`) pi loaded, plus any prompt
  templates, skills, and extensions — this is where you confirm pi is actually *in* the project
  you intended, with the context you intended.
- The footer shows working directory, session name, token/cache usage, cost, context usage, and
  current model (`packages/coding-agent/README.md` § Interactive Mode).
- The model's reply arrives as tool calls and results streaming into the message area, and the
  footer's token counters move.

When it has finished, ask for something checkable instead of trusting the prose: e.g. have it
create a file, then `ls` it yourself. An agent claiming completion without evidence is a failure
mode you will meet again — [docs/01-mental-model.md](01-mental-model.md) names it, and the
mitigation is always the same: demand an observable artifact.

Useful first-session facts:

- Sessions are saved automatically under `~/.pi/agent/sessions/`, organized by working directory;
  `pi -c` continues the most recent, `pi -r` browses previous ones.
- One-shot, non-interactive use exists: `pi -p "Summarize this codebase"` prints and exits
  (`-p`/`--print`, or `--mode json` / `--mode rpc` for process integration).
- In interactive mode, `!command` runs a shell command and sends its output to the model;
  `!!command` runs it without adding output to the model's context.
- pi loads instruction files (`AGENTS.md` or `CLAUDE.md`) from your global directory, parent
  directories, and the current directory at startup — the whole instruction-file mechanism, and
  how to structure it, is [docs/07-instruction-files.md](07-instruction-files.md)'s subject; the
  short version is that this is the highest-leverage control you own, and you can put a first
  `AGENTS.md` in this project today.

**Failure prevented:** an "installed, authenticated, and done" claim that has never survived
contact with a real task. The first session is the smoke test; the observables above are its
pass criteria.

## Keeping this chapter true: lookups, not pinned facts

Nothing version-shaped in this chapter is a fact; it is a snapshot. The durable form of every
version-sensitive claim is the command that reports the current value:

```bash
npm view @earendil-works/pi-coding-agent version license repository.url --json
pi --version
pi --help
pi --list-models
pi auth check --provider <your-provider> --json
```

**Failure prevented:** a version number, model list, or provider list copied into a document
becomes false the day upstream changes, and — worse — *stays confidently false*, because the
document looks authoritative. A command ages far more slowly than its output — a flag or an
endpoint can still be renamed upstream — so this chapter teaches you to read the live output and
to treat a failure from one of these commands as news about the command, not just the value. For what was mechanically
verified here and when, see the notes below and
[docs/11-verification.md](11-verification.md).

## Compact verification notes

Evidence obligations for this chapter: every install command,
package, path, flag, and auth fact above was checked against pristine upstream sources at a
recorded revision, or executed as a labeled runtime check in an isolated environment. "Observed"
below is a receipt of what the command printed at verification time — the command, not the
recorded output, is the durable fact. Re-run any of them yourself.

**Upstream revision resolved for all citations below:** `earendil-works/pi` commit
`71dca871bc80b6bc97be37f0ca3189399d651fff` (branch `main`, 2026-09-11). Per-file last-touch
revisions, from the GitHub commits API: `packages/coding-agent/README.md` @ `47acd8e6cfa7`
(2026-09-07), `packages/coding-agent/docs/quickstart.md` @ `42f7f29ad1cf` (2026-08-26),
`packages/coding-agent/docs/providers.md` @ `aa23e784c647` (2026-09-07), root `README.md` @
`caf6dfe7310c` (2026-09-05), `packages/coding-agent/docs/containerization.md` @ `47236c844506`
(2026-09-04).

**Claim-to-source table.** URL column gives the canonical public source; "where" is the location
in this chapter.

| Claim in this chapter | Where | Upstream source (section) | Verifying command | Observed at verification |
|---|---|---|---|---|
| npm package name, MIT license, repository | What you are installing | `npmjs.com/package/@earendil-works/pi-coding-agent`; registry metadata | `npm view @earendil-works/pi-coding-agent version license repository.url --json` | version `0.85.1`, license `MIT`, repository `git+https://github.com/earendil-works/pi.git` |
| npm install command and `--ignore-scripts` rationale | Install path A | `github.com/earendil-works/pi` → `packages/coding-agent/README.md` § Quick Start; `packages/coding-agent/docs/quickstart.md` § Install | `curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/README.md` → § Quick Start | exact command and the rationale sentence present, verbatim |
| `--ignore-scripts` "disables dependency lifecycle scripts during install. Pi does not require install scripts for normal npm installs." | Install path A | same § Quick Start | same | present, verbatim |
| curl installer URL | Install path B | same § Quick Start, "Installer alternative" | `curl -fsSL https://pi.dev/install.sh` (fetch, not execute) | 1728-line POSIX shell script served from that URL |
| curl installer performs the same npm global install with `--ignore-scripts`, can bootstrap Node, honors `PI_NPM_INSTALL_PREFIX` | Install path B | `https://pi.dev/install.sh` itself (functions `install_pi_package`/`run_npm_install_pi`) | fetched script inspected: `npm install -g --ignore-scripts ... "$PI_PACKAGE"` with optional `--prefix "$PI_NPM_INSTALL_PREFIX"`; Node bootstrap paths present | confirmed in the served script |
| no built-in permission system; runs with the launcher's permissions | The authority boundary | `github.com/earendil-works/pi` → root `README.md` § Permissions & Containerization | `curl -fsSL https://raw.githubusercontent.com/earendil-works/pi/main/README.md` | verbatim: "Pi does not include a built-in permission system for restricting filesystem, process, network, or credential access. By default, it runs with the permissions of the user and process that launched it." |
| three containment patterns (Gondolin, plain Docker, OpenShell) | The authority boundary | root `README.md` § Permissions & Containerization; details in `packages/coding-agent/docs/containerization.md` | same fetches | all three named with one-line descriptions, as pointers |
| minimal core: no MCP / sub-agents / permission popups / plan mode / to-dos / background bash, each with alternative | What you are installing | `packages/coding-agent/README.md` § Philosophy | raw fetch of that README | all six absences present with their named alternatives |
| four default tools; `grep`/`find`/`ls` built-in but not default | First session | `packages/coding-agent/README.md` § Quick Start and § CLI Reference → Tool Options; `docs/quickstart.md` § First session | raw fetches | "By default, pi gives the model four tools: read, write, edit, and bash"; Tool Options lists all built-ins |
| `/login` + subscription; no key needed; built-in subscription logins include Claude Pro/Max, ChatGPT Plus/Pro (Codex), GitHub Copilot | Authentication path A | `packages/coding-agent/docs/quickstart.md` § Authenticate → "Option 1: subscription login"; `packages/coding-agent/README.md` § Providers & Models; `docs/providers.md` § Subscriptions | raw fetches | flow and the three named logins present; providers.md adds xAI, OpenRouter, Radius |
| tokens stored in `auth.json`, auto-refresh; `/logout` clears | Authentication path A | `docs/providers.md` § Subscriptions | raw fetch | "Tokens are stored in `~/.pi/agent/auth.json` and auto-refresh when expired" |
| Anthropic subscription usage billed per token against extra usage, not plan limits | Authentication path A | `docs/providers.md` § Subscriptions → Claude Pro/Max | raw fetch | present as described |
| API-key env var path; `/login` → API-key provider stores key in `~/.pi/agent/auth.json` | Authentication path B | `docs/quickstart.md` § Authenticate → "Option 2: API key" | raw fetch | both flows present as described |
| per-provider env-var/`auth.json` key table; auth file 0600; auth file takes priority over env vars | Authentication path B | `docs/providers.md` § API Keys → "Environment Variables or Auth File" + § Auth File | raw fetch | full table present; "created with `0600` permissions"; "Auth file credentials take priority over environment variables" |
| `pi --version`, `pi --help`, `pi --list-models` documented upstream; `pi auth check` found in the upstream binary's own `--help` (the `auth` subcommand group is not in the README's CLI Reference at the recorded revision) | Verifying the install | `packages/coding-agent/README.md` § CLI Reference (Model Options, Other Options); the upstream binary's `pi --help` | executed (see runtime smoke below) | all four ran and reported as described |
| "no models available" message when no credentials are configured | Verifying the install | observed runtime behaviour of the pristine upstream binary (not a README claim) | isolated `pi --list-models` run | message printed, exit 0 |
| unauthenticated `-p` exits non-zero with a credentials message | Verifying the install | observed runtime behaviour of the pristine upstream binary (not a README claim) | isolated `pi -p "test" --no-tools` | exit 1, `No API key found for the selected model.` |
| `pi auth check` reports JSON readiness status per provider | Verifying the install | the upstream binary's `pi auth --help`; observed runtime behaviour | isolated `pi auth check --provider anthropic --json` | `{"status":"not_ready",..."reason":"credentials_not_configured"}` |
| sessions auto-saved; `-c`/`-r`; `pi -p`; `!command`/`!!command`; `@` file references | First session | `docs/quickstart.md` § First session / § Continue later / § Non-interactive mode; README § Interactive Mode | raw fetches | present as described |
| AGENTS.md/CLAUDE.md loaded from global, parents, cwd | First session | `docs/quickstart.md` § "Give pi project instructions" | raw fetch | present; full treatment deferred to docs/07 |
| uninstall leaves `~/.pi/agent/` behind | Install path B | `docs/quickstart.md` § Uninstall | raw fetch | "Uninstalling pi leaves settings, credentials, sessions, and installed pi packages in `~/.pi/agent/`." |
| Node.js prerequisite checkable via `engines` | What you are installing | npm registry metadata for the package | `npm view @earendil-works/pi-coding-agent engines --json` | returns a `node` floor (value intentionally not pinned here — run the command) |

**Executed runtime check (labeled).** Performed during chapter verification, deliberately
isolated: the pristine upstream package installed with `npm install --prefix <tmpdir>
--ignore-scripts @earendil-works/pi-coding-agent` into a temporary directory, and every command
run with `HOME` pointed at that same temporary directory — nothing installed globally, nothing
written to the author's real home. Results, quoted from the actual runs:

- `pi --version` → printed a version and exited 0. ✔ the binary runs from a clean install.
- `pi --help` → full usage listing (exit 0), including the `pi auth` subcommand group. ✔ CLI
  surface matches the README's CLI Reference.
- `pi --list-models` → `No models available. Use /login to log into a provider via OAuth or API
  key. ...` (exit 0). ✔ the no-credentials behaviour described in
  [Verifying the install](#verifying-the-install-and-authentication) is real, not predicted.
- `pi -p "test" --no-tools` → `No API key found for the selected model.` (exit 1). ✔ unauthenticated
  non-interactive mode fails closed with a message, exit code 1 — a non-zero exit on missing
  credentials, worth knowing before scripting.
- `pi auth check --provider anthropic --json` → `{"status":"not_ready","provider":"anthropic","reason":"credentials_not_configured"}`
  (exit 1). ✔ the readiness probe described above exists and reports as claimed.
- `~/.pi/agent/auth.json` and `~/.pi/agent/models-store.json` were created under the temporary
  `HOME` with `0600` permissions, and `sessions/` appeared. ✔ the documented per-user state
  directory layout is real.

**Not verified here (stated, not hidden).**

- Interactive `/login` against a real provider was **not** exercised — it requires live
  credentials and OAuth, and fabricating a successful login would violate this project's honesty
  bar. The `/login` flow, subscription list, token storage, and refresh are cited to upstream
  documents; the post-login `pi auth check` transition is left for the reader's own probe.
- No model call was made; "first session" observables are cited to
  `packages/coding-agent/README.md` § Interactive Mode rather than to a transcript.
- The version and license fields observed above are receipts of one run, not pinned facts; the
  commands are the durable evidence.

## Where to go next

- [docs/03-configuration.md](03-configuration.md) — settings files, project trust, and choosing
  models by lookup rather than by name.
- [docs/04-packages.md](04-packages.md) — installing extensions and skills, with the
  review-before-installing rule that the authority boundary makes mandatory.
- [docs/01-mental-model.md](01-mental-model.md) — what the token counters in pi's footer are
  telling you, and the four ways agents fail expensively.
- [docs/11-verification.md](11-verification.md) — every claim in this guide, with the command
  that proves it and how to re-run it.
