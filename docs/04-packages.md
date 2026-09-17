# Pi packages — extending the minimal core

Pi's core is deliberately small. Upstream states it plainly
(`earendil-works/pi` → `packages/coding-agent/README.md` § Philosophy):

> Pi is aggressively extensible so it doesn't have to dictate your workflow. Features that other
> tools bake in can be built with extensions, skills, or installed from third-party pi packages.
> This keeps the core minimal while letting you shape pi to fit how you work.

The same section names what pi does **not** ship, each with the alternative it points you to: no
MCP, no sub-agents, no permission popups, no plan mode, no built-in to-dos, no background bash.
None of that is a gap to work around — it is the design. Every capability that arrives past the
four built-in tools (`read`, `write`, `edit`, `bash`) reaches you through a **pi package** or a
skill, which is why this chapter is where the stack you see in `docs/05` and `docs/06` actually
comes from.

**Failure prevented:** an engineer arriving from another harness assumes MCP, sub-agents, and
permission prompts are pi defaults, configures as if they were, and the agent silently does less
than they think it does — or blames pi for features it deliberately refuses to ship. Treating
these as packages you chose keeps the boundary visible.

## Where the capability comes from

A pi package is an npm package or a git repository that bundles **extensions** (TypeScript/JS
code pi loads at startup), **skills** (see `docs/05-skills.md`), **prompt templates**, and
**themes**. A package declares its resources under a `pi` key in `package.json`, or ships them in
conventional directories (`extensions/` loads `.ts` and `.js`, `skills/` is scanned recursively
for `SKILL.md`, `prompts/` loads `.md`, `themes/` loads `.json`) that pi auto-discovers when no
manifest exists. The `pi-package` keyword makes a package findable on npm and in the public
gallery at `https://pi.dev/packages`.

Verified against `earendil-works/pi` → `packages/coding-agent/docs/packages.md` (§ Package
Structure, § Creating a Pi Package, § Gallery Metadata).

**Failure prevented:** pasting an extension's `.ts` file somewhere pi never reads, or hand-copying
a `skills/` directory into a package that declares its own `pi.skills` list — pi only loads what a
manifest or the convention directories say, so misplaced resources are silently inert.

## The authority boundary — read this before installing anything

Pi packages are not sandboxed add-ons. Upstream's own security warning
(`packages/coding-agent/docs/packages.md` § Install and Manage) says, in substance:

- **Pi packages run with full system access.** They execute with the authority of the user and
  process that launched pi.
- **Extensions execute arbitrary code**, loaded at startup.
- **Skills can instruct the model to perform any action, including running executables.**
- Upstream's answer is the same every time: **review the source before installing a third-party
  package.**

Monorepo root `README.md` § Permissions & Containerization adds the frame: pi has **no built-in
permission system**; by default it runs with the permissions of the user and process that launched
it, and upstream's containment answer is containerization — it documents three patterns (the
Gondolin extension, plain Docker, OpenShell) in `packages/coding-agent/docs/containerization.md`,
as pointers rather than instructions.

Two mechanisms you meet earlier in this template are **not** containment, and the whole point of
naming them here is to stop them being mistaken for it:

- `--ignore-scripts` (see `docs/02-install.md`) bounds what an *install-time lifecycle script* of
  pi's own dependencies can do during `npm install`. It is not a sandbox and it does not follow the
  code into your sessions.
- Project trust (see `docs/03-configuration.md`) gates **loading** of project-local settings,
  resources and extensions. Trusting a project widens what gets loaded; it does not restrict what
  a loaded tool may then do.

**Failure prevented:** `--ignore-scripts` plus a trusted project reads as "the dangerous stuff is
handled," which is exactly the moment a reader skips reviewing the source of something they are
about to install — the one precaution upstream actually requires. Nothing here *prevents* an
installed package from executing. Source review informs whether to install or load it.
Appropriately configured containerization limits the authority of code that does run; it does
not stop that code from running inside the container.

**Rule: review a package's source before installing it.** **Failure prevented:** installing an
extension is `npm install` with a code-execution side effect at every session start; an unreviewed
one is an unreviewed shell hook.

## The packages CLI

Everything below is the real CLI, verified against upstream
`packages/coding-agent/docs/packages.md` § Install and Manage and § Package Sources. It
**supersedes hand-editing `settings.json`**: install/remove update `~/.pi/agent/settings.json`'s
`packages` array (or `.pi/settings.json` with `-l` for project scope) for you, and the CLI's
pinning semantics are things hand-editing routinely gets wrong.

**Failure prevented:** hand-editing `settings.json` means writing a package reference the CLI
would never produce — a wrong `git:` form, an unpinned npm spec, or a local path the settings file
no longer resolves — and pi fails at startup or silently ignores it. The CLI encodes the valid
forms; use it.

### Installing

```bash
pi install npm:@scope/pkg          # from npm, latest
pi install npm:@scope/pkg@1.2.3    # from npm, pinned to an exact version
pi install git:github.com/user/repo            # from a git host, default branch
pi install git:github.com/user/repo@v1.0.0     # from git, pinned to a tag or commit
pi install https://github.com/user/repo        # raw protocol URLs also work
```

- npm installs land under `~/.pi/agent/npm/`; git clones under `~/.pi/agent/git/<host>/<path>`.
- `-l` writes the reference to project settings (`.pi/settings.json`, installed under `.pi/npm/`
  or `.pi/git/`) so a team shares one package list; pi installs missing project packages after
  the project is trusted.
- The `git:` prefix is what enables shorthand (`github.com/user/repo`,
  `git@github.com:user/repo`); **without** it only protocol URLs (`https://`, `http://`,
  `ssh://`, `git://`) are accepted.
- Local paths (`/absolute/...`, `./relative/...`) point at on-disk packages without copying —
  this is how a private team installs its own extensions, and it is the entry form a reader will
  not use unless they develop packages themselves.

### Removing, listing, configuring

```bash
pi remove npm:@foo/bar     # pi uninstall is an alias
pi list                    # show the packages installed from settings
pi config                  # interactive enable/disable of a package's extensions, skills,
                           # prompts, and themes; Tab switches global/project scope
```

### Updating

```bash
pi update --extensions      # update packages and reconcile pinned git refs only
pi update --all             # update pi itself, packages, and reconcile pinned git refs
pi update npm:@foo/bar      # update one package
pi update --self            # update the pi CLI itself
```

`pi update` with no flag updates pi itself; `--models` refreshes model catalogs only.

### Ephemeral use

```bash
pi -e npm:@foo/bar                    # try a package for the current session only
pi -e git:github.com/user/repo
```

`-e`/`--extension` installs to a temporary directory for this run and writes nothing to settings.
Use it to evaluate a package before committing to it — which pairs naturally with reviewing its
source.

## Pinning semantics — what "update" does and does not move

This is the part that makes the CLI safe to recommend in a published document. Verified against
`packages/coding-agent/docs/packages.md` § Package Sources (npm, git):

1. **A versioned npm spec is pinned and skipped.** `npm:@scope/pkg@1.2.3` never moves; `pi update
   --extensions` and `pi update --all` pass it by. An *unpinned* `npm:pkg` is the one that moves.
2. **A git `@ref` is a pinned tag or commit.** `pi update --extensions`/`--all` reconcile an
   existing clone **to the configured ref** (resetting and cleaning the clone, then running
   `npm install` if `package.json` exists) — but they do **not** move the pin forward to a newer
   ref.
3. **To move a pin, re-install at the new ref**: `pi install git:host/user/repo@new-ref` updates
   settings and moves the existing package.
4. **Git packages install runtime dependencies under `dependencies`** — pi runs
   `npm install --omit=dev` on them, so anything the extension imports at runtime must live there,
   not in `devDependencies`.

**Failure prevented:** treating `pi update --extensions` as "pull the latest of everything." It
is not, and a reader who thinks it is will either get surprises they did not ask for (unpinned npm
specs do move) or believe a pinned package is stale when it is exactly as pinned as they left it.
Pin what you care about; know that the pin, not the command, decides movement.

**Rule: pin anything you rely on.** **Failure prevented:** an unpinned spec moves under you; a
pinned one reconciles. The pins of the reference setup — the working setup this template
generalizes from — are why its behavior is reproducible, and why a dead pin needs an explicit
act to move (see the dead-fork trap below).

## Installed versus enabled

The reference configuration this template generalizes from has a distinction you will reproduce
yourself:

- **Enabled** = listed in the `packages` array of `settings.json` (or `.pi/settings.json`) — this
  is what pi loads at startup. `pi list` shows it.
- **Installed** = present in the on-disk npm tree (`~/.pi/agent/npm/`, whose `package.json`
  `dependencies` list survives even when the entry is removed from `packages`).

A package can be installed but not enabled — present in the npm tree, absent from the `packages`
array. The reference setup had exactly this case: `pi-smart-compact` was installed as an npm
package under the tree while the *enabled* entry was a git fork pin of it (see the dead-fork trap
below — a reader should enable the npm upstream instead).

How to inspect your own state:

```bash
pi list                                        # what is enabled
cat ~/.pi/agent/npm/package.json               # what is installed on disk (npm scope)
ls ~/.pi/agent/git/                            # what is installed on disk (git scope)
```

**Failure prevented:** debugging a feature that "should be there" when its package is on disk but
not in the `packages` array — or believing you removed something when only the enabled entry
went. `pi list` and the npm tree are two different questions; ask both.

## The dead-fork trap

The reference setup pinned git forks whose repositories are now **gone** — they return
HTTP 404 for any outsider:

| The reference setup pinned | What an outsider gets | The public npm upstream |
|---|---|---|
| a private fork of `pi-smart-compact` | HTTP 404 — repo private or deleted | `npm:pi-smart-compact` (MIT, `github.com/alpertarhan/pi-smart-compact`) |
| a private fork of the rpiv monorepo | HTTP 404 — repo private or deleted | `npm:@juicesharp/rpiv-advisor` and `npm:@juicesharp/rpiv-todo` (MIT, `github.com/juicesharp/rpiv-mono`) |

Publishing those pins would be the exact "rot into wrong instructions" failure — a reader
following them gets a 404 and concludes the guide is wrong. The pins are also instructive as a
**class**: a git pin points at a host/path that can go private or away, while an npm name points
at a registry entry that can be yanked. Published tarballs are usually still fetchable after a
yank; npm can also unpublish under defined conditions, so a version pin is not a durability
guarantee. Both rot; they rot differently.

**How to detect the class yourself, for any pin you copy from anyone's setup:**

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://github.com/<owner>/<repo>   # 404 = not publicly accessible (private, deleted, or wrong path)
npm view <pkg> license repository.url --json                                # live npm state
npm view <pkg> version                                                      # current version
```

**Failure prevented:** copying a config that works for its author because their fork exists,
without checking that the pin still resolves publicly. The check is one command per entry.

## The inventory, accounted for

The rule this chapter follows: **every entry is accounted for** — public ones by name
and purpose, private ones by a neutral description, none dropped. That is what makes
reading someone's `settings.json` transferable rather than a copy of one team's working
set. The reference setup's own counts are deliberately not published: they measure one
private machine and would rot. The procedure transfers instead — run `pi list`, put
every entry of your own into a class (public npm, public git, local path, dead pin), and
give each one a name-and-purpose or a neutral description before you copy anything.

### Public npm

Every one of these is installable by a reader today. The starter/advanced split into
"what you actually install on day one" comes after, justified by pain.

| Package | What it provides | License |
|---|---|---|
| `pi-web-access` | Web search, URL fetching, GitHub repo cloning, PDF extraction | MIT |
| `pi-simplify` | Reviews recently changed code for clarity | MIT |
| `@juicesharp/rpiv-advisor` | A second opinion the model can request from an advisor agent | MIT |
| `@juicesharp/rpiv-todo` | A todo list for the model, rendered live | MIT |
| `pi-mcp-adapter` | MCP (Model Context Protocol) support for pi | MIT |
| `pi-sidequest` | A side channel for context-aware questions | MIT |
| `pi-footer` | Multi-line footer/statusline; supports the object form with per-resource filters (upstream § Package Filtering) | MIT |
| `pi-context-inspector` | Inspect the system prompt, active tools, messages | MIT |
| `@luxusai/pi-hindsight` | Durable Hindsight-backed long-term memory | MIT |
| `context-mode` | Context-window saving (see `docs/06`) | **Elastic-2.0** |
| `pi-meridian-extension` | Routes a Claude Max subscription through a local proxy | **unresolved** — npm `license` field absent |

`pi-footer` is the one entry here that may appear as an object rather than a bare
string — `{ "source": ..., "extensions": ... }` — which is the supported mechanism for
filtering what a package loads (verified in upstream
`packages/coding-agent/docs/packages.md` § Package Filtering). A reader copying this
inventory decides their own filters, not anyone else's.

### Public git

| Repository | What it provides | License |
|---|---|---|
| `github.com/jrimmer/pi-deepseek-optimized` | Harness techniques the project says close a reasoning-quality gap for a specific model family, implemented for pi — the upstream project's stated aim, not a measurement reproduced here | BSD-3-Clause |
| `github.com/picassio/pi-cc-patch` | Use your Pro/Max subscription billing with pi instead of hitting third-party-app billing detection; patches the request payload to bypass the classifier | MIT |

### Private — not installable; described as patterns only

Some entries in the reference setup's `packages` array resolve to local paths on private infrastructure.
They are named only by the capability they provide — which is all a reader can take
from them: governed subagent dispatch, deterministic multi-agent workflow orchestration,
unified hook enforcement, compiled footer extensions, compiled workflow extensions, and
a private snapshot of the public superpowers pack. **A reader cannot install any of
these**; see `docs/10-private-patterns.md` for what each class is for and the smallest
useful public version of each.

**Failure prevented:** treating a package list as a one-shot copy-paste. It is an
accounting exercise — half the value of reading someone's `settings.json` is seeing
which entries are public, which are private, and which are dead. Account for every entry
of your own with `pi list` before adopting any of them.

## The starter set — by pain

The split below is justified by pain, not by taste. The test for the starter set: **its absence
hurts within your first working session, without further infrastructure.** An entry that needs a
server, a second tool, or a pain you have not felt yet is advanced, whatever its quality. Install
the starter entries in this order. Read the source first — fetching it is inspection. `pi -e` is
an *execution* trial: it runs the package for one session, which means its code runs, so it is
something to do after you have looked, not instead of looking.

1. **`pi-web-access`** (`pi install npm:pi-web-access`) — **pain: your agent has no dedicated
   web tooling.** The default agent ships no *search* or *fetch* tool. It is not incapable of
   reaching the network — its `bash` tool can run `curl` or `git clone` with your authority, which
   is precisely why `docs/02-install.md` is emphatic about that surface. What this package adds is
   a purpose-built, reviewable path for the task, and every downstream chapter assumes it.
2. **`pi-mcp-adapter`** (`pi install npm:pi-mcp-adapter`) — **pain: pi deliberately ships no MCP.**
   Upstream's philosophy section says so and points to exactly this: an extension that adds MCP
   support. Most tooling ecosystems speak MCP now; this adapter is the bridge. See `docs/06`.
3. **`superpowers`** (`pi install git:github.com/obra/superpowers`) — **pain: the model does not
   follow a good process on its own.** The public skills pack (`docs/05`) — brainstorming,
   systematic-debugging, test-driven development, writing-plans, verification-before-completion —
   is process discipline in skill form. MIT.
4. **`context-mode`** (`pi install npm:context-mode`) — **pain: large command output destroys
   your session.** The context-window saving described in `docs/06`; it runs as a **local MCP
   process**, so there is no hosted service to sign up for and no account — but it is not
   zero-setup: `docs/06` gives the global npm install plus the `mcpServers` entry. **Elastic-2.0 —
   read the license caution below before adopting.**
5. **`pi-smart-compact`** (`pi install npm:pi-smart-compact`) — **pain: default compaction loses
   what you needed.** Verification-oriented smart compaction, likewise self-contained. Use the
   npm upstream, not any fork pin you may find in someone's config (dead-fork trap above).

**Failure prevented:** installing the whole reference list because it is there. Each entry above
earns its place by a specific pain — if you have not felt the pain, do not install the entry,
because a capability you have never needed is another thing to review, pin, and update.

## The advanced set — by pain

Everything else in the public inventory, each of which only matters once a specific pain is felt:

| Package | Install when you feel this pain | License |
|---|---|---|
| `@luxusai/pi-hindsight` | Every session starts amnesiac — but the remedy needs the Hindsight server (`docs/06`), so it is a project, not a one-liner | MIT |
| `pi-simplify` | A review pass of recently changed code for clarity, on demand | MIT |
| `@juicesharp/rpiv-advisor` | You want an advisor the *model* can consult mid-session | MIT |
| `@juicesharp/rpiv-todo` | The model needs a live todo list rendered in the UI | MIT |
| `pi-sidequest` | A side channel for context-aware questions without polluting the main thread | MIT |
| `pi-footer` | A multi-line footer/statusline in the UI | MIT |
| `pi-context-inspector` | You need to see the actual system prompt, active tools, and messages | MIT |
| `github.com/jrimmer/pi-deepseek-optimized` | You run that model family and want to try the harness techniques its project claims narrow the gap | BSD-3-Clause |
| `github.com/picassio/pi-cc-patch` | Your provider blocks subscription billing for third-party apps | MIT |
| `pi-meridian-extension` | You want to route a Claude Max subscription through a local proxy | **unresolved** — npm `license` field absent |

The ToS-adjacent pair (`pi-cc-patch`, `pi-meridian-extension`) exists to make subscription
billing work with pi where a provider's classifier blocks third-party apps. One is MIT; the other's registry metadata
states no license at all (see the cautions above). Both do exactly what their READMEs say; both are also, in
substance, workaround tools for provider terms — adopting one is your call as the account
holder, not this guide's recommendation.

**Failure prevented:** adopting advanced entries preemptively. Each row names the pain; no pain,
no entry — for the same reason as the starter list.

## Licenses

Every package in this chapter's tables was checked against the public npm registry and the
GitHub API during verification (see the verification notes at the end). Licenses can change
when a release changes, so the table is a snapshot, not a guarantee: the lookup that produced it
is the durable part.

**How to check any package's license yourself, before or after adopting it:**

```bash
npm view <pkg> license repository.url --json
```

**Failure prevented:** copying a license label out of a document. Licenses attach to releases;
the registry is the authority at the moment you care.

### The two honest cautions (and a third, found during verification)

**`context-mode` is Elastic-2.0, not open source.** The npm `license` field and the upstream
LICENSE file both say **Elastic License 2.0**. That is **source-available with usage
restrictions** — notably you may not provide the software to others as a hosted or managed
service that offers a substantial set of its features or functionality — not an OSI-approved
license, and it must never be presented as "MIT-like" or open source. Referencing a package in
a document is not redistribution. Read the LICENSE text for the actual restriction before you
depend on it.

**`pi-meridian-extension` has no license field on npm.** The latest published version's
`package.json` has no `license` field, and the GitHub repository reports none either. An empty
registry field is **not** proof that no grant exists — a LICENSE file in the tarball, or an
upstream license, can still apply. Until those are inspected, treat the licensing status as
**unverified**, not as a confirmed all-rights-reserved default. Its stated purpose — routing a
Claude Max subscription through a local proxy — is also provider-ToS-adjacent.

**`pi-headroom` has an empty npm `license` field but declares MIT in its packaged README.**
Found while checking every installed reference package, not in the original recon. It is the
cleanest example of why the field alone cannot be trusted in *either* direction: the metadata is
absent while the packaged README declares MIT. That makes MIT the likely answer, not a confirmed
package-level grant — check the README and any upstream `LICENSE` yourself before deciding.
It is not part of the reference enabled set, but a reader following the package trail would meet it.

**Failure prevented:** a "just MIT, ship it" read of the inventory. One package is source
available under usage restrictions, one declares a licence only in its packaged README rather
than its registry field, and one leaves the status unresolved — and a template that omits
those facts would send a reader into a dependency they would not have chosen knowingly.

## What this chapter deliberately does not do

- **No installer.** Every command here is one you run yourself; this template ships nothing that
  writes to your configuration.
- **No pinned versions in prose**, per the anti-pinning rule owned by
  [README.md](../README.md) ("Lookup over literal"). The lookup commands above are the durable
  form. This whole template is a snapshot with no maintenance promise — see
  `docs/11-verification.md` for how to re-check anything.
- **No private identities.** The fork URLs in the reference setup are dead links for an outsider
  and are named only as a class (dead-fork trap), never as install targets.

## Related chapters

- `docs/02-install.md` — installing pi itself and its execution-authority boundary.
- `docs/03-configuration.md` — the settings files this CLI edits on your behalf, and project trust.
- `docs/05-skills.md` — what packages can ship besides extensions, and how skills are discovered.
- `docs/06-memory-mcp-context.md` — Hindsight and MCP, both of which arrive as packages.
- `docs/10-private-patterns.md` — what the private classes in the inventory map to.
- `docs/11-verification.md` — the full claim-to-source matrix, consolidated.

## Verification notes

Claims in this chapter were verified live when this chapter was written (not from the private planning
snapshot alone — source and registry commands were re-run to prove each published
claim). Upstream citations name the repo, package-relative path, and section — never
fork-relative line numbers. Registry facts (license, repository URL, what a package ships) are
point-in-time: re-run the commands in this table to confirm they still hold.

| Claim in this chapter | Where | Verified by (command) | Result at verification | Public source |
|---|---|---|---|---|
| pi packages bundle extensions/skills/prompts/themes; `pi` manifest key; conventional dirs | § Where the capability comes from | fetched `packages/coding-agent/docs/packages.md` § Package Structure | auto-discovery dirs: `extensions/` `.ts`/`.js`, `skills/` recursive `SKILL.md`, `prompts/` `.md`, `themes/` `.json` | `earendil-works/pi` |
| Security warning (full system access; extensions run arbitrary code; skills instruct any action incl. executables; review source) | § The authority boundary | same doc § Install and Manage | warning present, quoted in substance | `earendil-works/pi` |
| No built-in permission system; runs with user/process authority; containment = containerize; three patterns in containerization.md | § The authority boundary | `README.md` § Permissions & Containerization (monorepo root) | present as cited | `earendil-works/pi` |
| `pi install` / `remove` / `list` / `update --extensions` / `--all` / `<pkg>` / `--self` / `-e` CLI surface | § The packages CLI | fetched `packages/coding-agent/docs/packages.md` § Install and Manage | all commands present as documented | `earendil-works/pi` |
| Versioned npm spec pinned, skipped by `--extensions`/`--all`; git refs reconciled to configured ref, never moved forward; move a pin via `pi install git:...@new-ref`; git deps use `dependencies` (`npm install --omit=dev`) | § Pinning semantics | same doc § Package Sources | semantics present as cited | `earendil-works/pi` |
| `git:` prefix enables shorthand; without it only protocol URLs | § Installing | same doc § Package Sources | present as cited | `earendil-works/pi` |
| Install destinations `~/.pi/agent/npm/`, `~/.pi/agent/git/<host>/<path>`, `-l` project scope | § Installing | same doc § Install and Manage, § Package Sources | present as cited | `earendil-works/pi` |
| `pi-smart-compact` npm upstream is public, MIT | dead-fork trap table | `npm view pi-smart-compact license repository.url --json` | `"license": "MIT"`, `github.com/alpertarhan/pi-smart-compact` | registry.npmjs.org |
| rpiv npm upstreams public, MIT | dead-fork trap table | `npm view @juicesharp/rpiv-advisor license repository.url --json`; same for `rpiv-todo` | `"license": "MIT"`, `github.com/juicesharp/rpiv-mono`, both | registry.npmjs.org |
| 11 public npm entries + replacements, licenses, purposes | inventory tables | `npm view <pkg> license repository.url --json` per entry; `npm view <pkg> description pi --json` per entry | MIT ×9 (web-access, simplify, rpiv-advisor, rpiv-todo, mcp-adapter, sidequest, footer, context-inspector, pi-hindsight); Elastic-2.0 (context-mode); license field absent, status unresolved (meridian) | registry.npmjs.org |
| 2 public git entries, licenses | inventory tables | GitHub API `GET /repos/<owner>/<repo>` | `jrimmer/pi-deepseek-optimized` BSD-3-Clause; `picassio/pi-cc-patch` MIT | api.github.com |
| DeepSeek-optimized purpose (harness techniques aimed at one model family) | inventory table | fetched repo README | present as described; the chapter deliberately states no count of techniques | `github.com/jrimmer/pi-deepseek-optimized` |
| cc-patch purpose (subscription billing bypass; payload patching) | inventory table | fetched repo README | present as described | `github.com/picassio/pi-cc-patch` |
| `pi-meridian-extension` license field absent, status unresolved; purpose = Claude Max via local proxy | Licenses; inventory | `npm view pi-meridian-extension license repository.url --json` (license field absent); registry manifest fetch; GitHub API | license field absent from latest version; `license: None` on GitHub | registry.npmjs.org, api.github.com |
| `context-mode` is Elastic-2.0 (npm field + LICENSE file) | Licenses | `npm view context-mode license repository.url --json`; fetched upstream `LICENSE` | `"license": "Elastic-2.0"`; LICENSE text titled "Elastic License 2.0 (ELv2)" | registry.npmjs.org, `github.com/mksglu/context-mode` |
| `pi-headroom` has no license field on npm (its README declares MIT) | Licenses | `npm view pi-headroom license --json` | **empty result** — no license field | registry.npmjs.org |
| Installed-but-not-enabled is a real state, and how to inspect it (`pi list` vs `~/.pi/agent/npm/package.json`) | § Installed versus enabled | fetched `packages/coding-agent/docs/packages.md` § Install and Manage, § Package Sources | npm installs land under `~/.pi/agent/npm/`; settings `packages` array is what loads | `earendil-works/pi` |
| `superpowers` public, MIT, installable via git | starter set | GitHub API + `pi` block in upstream `package.json` | MIT; `pi.extensions`/`pi.skills` declared | `github.com/obra/superpowers` |
| Upstream doc revision for all `earendil-works/pi` citations | verification notes | `GET /repos/earendil-works/pi/commits/main` | `main` at `71dca871bc80b6bc97be37f0ca3189399d651fff` (2026-09-11) | api.github.com |

**Not verified (explicit gaps):**

- No runtime check was performed that `pi install <pkg>` succeeds for any of these packages —
  the verification is source-level (registry + upstream docs), per the distinction
  [`11-verification.md`](11-verification.md) records between source verification and executed
  runtime checks. Installing them is the
  reader's step.
- The exact per-package configuration surface (settings keys each package contributes) was not
  exhaustively inventoried for the public set — only `context-mode`, `@luxusai/pi-hindsight`,
  and `pi-mcp-adapter` were examined in depth, and their config shapes live in `docs/06`.
