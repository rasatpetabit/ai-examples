# Third-party notices

This file attributes the **public packages and skills whose install or use this
template teaches**. Referencing a package is not redistribution of it. A name that
appears only to DISAMBIGUATE -- the sibling distributions of a project already
attributed here, or an unrelated package a reader might confuse it with -- is
covered by that project's row rather than getting its own, so the rows below are
installable things, not an index of every string in the chapters. The MIT
license in `LICENSE` covers **this template's own prose, templates, and
examples**. It does not relicense anyone else's work.

**Failure prevented:** a reader treats this tree as a bundled copy of pi,
superpowers, or any other named package, and ships it under MIT as if those
works were ours.

Licenses attach to releases. The labels below are a snapshot of a live lookup
run when this file was written. Before you install anything, re-check:

```bash
npm view <pkg> license repository.url --json
```

For a GitHub repository:

```bash
# SPDX id, when GitHub has one:
# GET https://api.github.com/repos/<owner>/<repo>  →  .license.spdx_id
```

**Failure prevented:** copying a license string out of this file after the
package has changed its terms.

## Referencing is not redistribution

| This template does | This template does not |
|---|---|
| Name a public package, cite its upstream URL, and state the license the registry or GitHub API reported at lookup time | Vendor, vendor-copy, or relicense that package |
| Point you at `pi install` / `pip install` / git clone of the **upstream** | Ship a tarball of someone else's source |
| Warn when a license is Elastic-2.0 or undeclared | Pretend those cases are MIT |

If you **redistribute** a third-party package yourself, you take on that
package's own license — read it. Elastic-2.0 in particular is source-available
with usage restrictions (notably around offering the software as a managed
service). An undeclared license is not a grant, and it is also not proof that none exists: treat the status as unresolved
until the publisher says otherwise.

## How this table was produced

Each npm row is the live output of `npm view <pkg> license repository.url --json`
run when this file was written. Each git row is the GitHub API `license.spdx_id`
for that repository.

An empty license field or `NOASSERTION` is recorded as **unverified /
undeclared**, and that label means exactly one thing: *no license could be
established from the lookup.* It is not evidence of permission — an
absent or unidentified license grants you nothing. It is equally not a finding
that the publisher has refused permission: the grant may exist in a file or a
README the registry never read. It is an unknown, and an unknown is not a yes —
nor a confirmed no.

## Core (the thing this template is about)

| Work | Lookup | License at lookup | Upstream |
|---|---|---|---|
| `@earendil-works/pi-coding-agent` | `npm view` | MIT | https://github.com/earendil-works/pi |
| `obra/superpowers` (skills pack) | GitHub API `license.spdx_id` | MIT | https://github.com/obra/superpowers |

Install lookups (do not copy a version out of this file):

```bash
npm view @earendil-works/pi-coding-agent version license repository.url --json
```

## Public npm packages named in the chapters

| Package | License at lookup | Upstream |
|---|---|---|
| `pi-web-access` | MIT | https://github.com/nicobailon/pi-web-access |
| `pi-simplify` | MIT | https://github.com/MattDevy/pi-extensions |
| `@juicesharp/rpiv-advisor` | MIT | https://github.com/juicesharp/rpiv-mono |
| `@juicesharp/rpiv-todo` | MIT | https://github.com/juicesharp/rpiv-mono |
| `pi-mcp-adapter` | MIT | https://github.com/nicobailon/pi-mcp-adapter |
| `pi-sidequest` | MIT | https://github.com/peterp/pi-sidequest |
| `pi-footer` | MIT | https://github.com/wobondar/pi-footer |
| `pi-context-inspector` | MIT | https://github.com/YuGiMob/pi-context-inspector |
| `@luxusai/pi-hindsight` | MIT | https://github.com/luxus/pi-hindsight |
| `pi-smart-compact` | MIT | https://github.com/alpertarhan/pi-smart-compact |
| `context-mode` | **Elastic-2.0** | https://github.com/mksglu/context-mode |
| `pi-meridian-extension` | **undeclared** (npm `license` field empty; GitHub API `license` is null) | https://github.com/lnilluv/pi-meridian-extension |
| `@vectorize-io/hindsight-client` | MIT | https://github.com/vectorize-io/hindsight |

## Public git packages named in the chapters

| Repository | License at lookup | Upstream |
|---|---|---|
| `jrimmer/pi-deepseek-optimized` | BSD-3-Clause | https://github.com/jrimmer/pi-deepseek-optimized |
| `picassio/pi-cc-patch` | MIT | https://github.com/picassio/pi-cc-patch |

## Memory tooling named in the chapters

| Work | Lookup | License at lookup | Upstream |
|---|---|---|---|
| Hindsight project (server / Python client) | GitHub API | MIT | https://github.com/vectorize-io/hindsight |
| `hindsight-api` (the pip distribution to install) | named by the project's own install docs | same project, MIT | install with `pip install hindsight-api` — **not** `pip install hindsight` |

PyPI also publishes an unrelated distribution literally named `hindsight`.
Installing that is a different project. See [`docs/06-memory-mcp-context.md`](docs/06-memory-mcp-context.md).

## Other public works named in the chapters

| Work | Lookup | License at lookup | Upstream |
|---|---|---|---|
| `pi-continuous-learning` | npm | MIT | https://github.com/MattDevy/pi-extensions |
| `pi-rewind` | npm | MIT | https://github.com/arpagon/pi-rewind |
| `pi-usage-widget` | npm | MIT | https://github.com/cullendotdev/pi-usage-widget |
| `pi-headroom` | npm + package tarball | **unresolved at package level** — the npm `license` field is empty; the packaged README declares MIT, so the likely answer is MIT but the registry does not confirm it. Read the README yourself | https://www.npmjs.com/package/pi-headroom |
| `@vectorize-io/hindsight-control-plane` | npm | ISC | https://github.com/vectorize-io/hindsight |
| `@vectorize-io/hindsight-coding-agents` | npm | **unresolved at package level** — no `license` field on npm; the upstream project is MIT, which is suggestive but not a package-level grant | https://github.com/vectorize-io/hindsight |
| `@modelcontextprotocol/server-everything` | npm + packaged README + upstream `LICENSE` | **unresolved at package level** — the registry field is a pointer (`SEE LICENSE IN LICENSE`), the tarball ships no such file, its packaged README says MIT, and the upstream repository is mid-transition MIT → Apache-2.0 (docs CC-BY-4.0). Three sources, no single answer: read them before relying on it | https://github.com/modelcontextprotocol/servers |
| `pi-subagents` | npm | MIT | https://github.com/nicobailon/pi-subagents |
| `mattpocock/skills` | GitHub API | MIT | https://github.com/mattpocock/skills |
| `vercel-labs/skills` | GitHub API | MIT | https://github.com/vercel-labs/skills |
| `langfuse/skills` | GitHub API | MIT | https://github.com/langfuse/skills |
| `@anthropic-ai/claude-code` | npm | **unresolved from the registry** — the field reads `SEE LICENSE IN README.md`, and that README points at the vendor's Commercial Terms of Service rather than naming a licence. Read those terms; do not infer a permission from this row | https://github.com/anthropics/claude-code |

## Cautions that are load-bearing

**Elastic-2.0 (`context-mode`).** Source-available, not OSI open source. Referencing
it here is not redistribution. If you install it, you take on Elastic-2.0, including
restrictions around offering the software as a managed service. Read
https://www.elastic.co/licensing/elastic-license before you adopt it.

**Unresolved license (`pi-meridian-extension`).** Its npm `license` field is
empty and GitHub reports no license classification. That is an absence of
*metadata*, not proof that no grant exists — the authoritative text, if any, is
upstream and has not been inspected here. Treat the status as unverified rather
than as a confirmed all-rights-reserved default, and check the repository before
you depend on it.
The package's purpose (routing a Claude Max subscription through a local proxy)
is also provider-terms-adjacent — that is your call as the account holder, not
a recommendation of this template.

**An empty or indirect `license` field is a metadata gap, not a licence
conclusion.** Two packages here show why the field alone cannot be trusted in
either direction. `pi-headroom` publishes an empty `license` field while its
packaged README declares MIT. `@modelcontextprotocol/server-everything` points
at a file its tarball does not contain, and the upstream repository is mid
transition from MIT to Apache-2.0. In both cases the authoritative text is the
upstream licence file, not the registry field — so read it before you rely on
either package, and do not read an empty field as *either* a grant or a refusal.

**`@anthropic-ai/claude-code` does not state a licence in its registry
field.** That field reads `SEE LICENSE IN README.md`, and the README points at
the vendor's commercial terms instead of naming one. Treat it as unresolved
rather than as either a grant or a refusal: this template names the tool because
it describes the harness, it does not redistribute it, and you should read those
terms before building on it.

**Failure prevented:** a published recommendation that omits the packages
whose terms are not "just MIT", so a reader installs them under a false
assumption of OSI-open terms.

## What this file deliberately does not list

Private or unpublished packages, local forks, and host-only skills. Those are
not installable from this template; [`docs/10-private-patterns.md`](docs/10-private-patterns.md)
describes the *patterns*, not the code. Listing them here would either leak
internal names or imply they ship with this tree.

## Verification notes

| Claim | Command | Result (when this was written) | Where used |
|---|---|---|---|
| pi-coding-agent MIT | `npm view @earendil-works/pi-coding-agent license repository.url --json` | `"license": "MIT"`, repo `earendil-works/pi` | Core table |
| context-mode Elastic-2.0 | `npm view context-mode license repository.url --json` | `"license": "Elastic-2.0"` | Cautions; README smoke grep |
| pi-meridian-extension undeclared | `npm view pi-meridian-extension license repository.url --json` | license field absent; only `repository.url` returned | Cautions |
| superpowers MIT | GitHub API `obra/superpowers` `.license.spdx_id` | `MIT` | Core table |
| hindsight project MIT | GitHub API `vectorize-io/hindsight` `.license.spdx_id` | `MIT` | Memory tooling table |
| jrimmer BSD-3-Clause | GitHub API `jrimmer/pi-deepseek-optimized` `.license.spdx_id` | `BSD-3-Clause` | Git table |
| picassio MIT | GitHub API `picassio/pi-cc-patch` `.license.spdx_id` | `MIT` | Git table |

The tables above state no package version number as current. Re-run the
lookup; do not copy a number out of a chapter.
