# AGENTS.md — example-handbook

Canonical instruction file for this handbook repository. An agent that reads
instruction files natively picks this up as the repository's own file, and
anything true and useful regardless of which agent is reading belongs here.
The split rule — which file a line belongs in, and why a rule must never live
in two files — is
[`docs/07-instruction-files.md`](../../docs/07-instruction-files.md) in
the template root. This file does not restate it.

## Project context

This repository is a **genericized cross-cutting handbook**: navigation,
inventory, and domain-boundary leaves that belong to no single
implementation repo. It exists so a reader can `cp -r` a working shape
rather than invent one from a paragraph of prose.

It is deliberately not an organisation's real handbook. Repository names
in `inventory.yaml` are invented example identifiers. Paths are relative
to this tree. **Failure prevented:** a copied example that still names
someone else's private layout, which is how a template leaks.

The one thing a fluent newcomer most often gets wrong: the handbook is
**linked into** sibling repos, not loaded as their instruction file. A
session started in `ordinary-repo` does not automatically see these
leaves; it sees a pointer block, and follows it. Treating this repo as
tier-1 global policy is the wrong tier.

## Ownership boundary

| This repository owns | Sibling implementation repos own |
|---|---|
| `docs/boundaries/` index and leaves | their own source, `INTENT.md`, and human-owned `AGENTS.md` |
| `inventory.yaml` | nothing in this tree |
| `tools/stamp-pointers.py` | the *target* `AGENTS.md` the stamper writes into, except the machine-owned block |
| navigation and the generated-vs-hand-written convention | quirks, domain conventions, and first-day commands of that product |

The rule that a handbook leaf carries no product behaviour, and is never copied
into a sibling `AGENTS.md`, is owned by
[`docs/08-cross-cutting-docs.md`](../../docs/08-cross-cutting-docs.md) — stated
there once, with its failure mode. This line is the pointer.

## Navigation

| Path | What it is for |
|---|---|
| [README.md](README.md) | How to copy, stamp, and restamp. Start here as a human. |
| [docs/boundaries/index.md](docs/boundaries/index.md) | Names what each leaf answers. Start here as an agent following a pointer. |
| [docs/boundaries/application.md](docs/boundaries/application.md) | Application-domain conventions and ownership. |
| [docs/boundaries/platform.md](docs/boundaries/platform.md) | Platform-domain conventions and ownership. |
| [inventory.yaml](inventory.yaml) | Membership: which sibling repos this handbook knows, as relative paths. |
| [tools/stamp-pointers.py](tools/stamp-pointers.py) | The stamper. Example utility, not an installer. |

## Hard rules

- Edit leaves and the index by hand. Sibling pointer blocks are machine-owned:
  the ownership rule and why a hand edit there is lost are owned by
  [`docs/07-instruction-files.md`](../../docs/07-instruction-files.md); the command
  that refreshes them is in
  [`docs/08-cross-cutting-docs.md`](../../docs/08-cross-cutting-docs.md) and in this
  repository's own first-day commands below.
- `inventory.yaml` stays JSON-compatible YAML (an object the Python standard
  library can `json.load`). How to add a sibling, and why a second inventory
  format is the failure, are owned by
  [`docs/08-cross-cutting-docs.md`](../../docs/08-cross-cutting-docs.md).
- The stamper takes explicit `--repo` and `--handbook` roots. It does not
  scan `$HOME`, discover git remotes, or write a path it was not given.
  **Failure prevented:** an example utility that behaves like an
  installer and touches a machine the reader did not name.
- Do not put private hostnames, org names, or absolute workspace paths in
  this tree. Relative example locations only.
  **Failure prevented:** a publishable template that is not publishable.

## Generated versus hand-written

The only generated region this handbook *produces* is the pointer block
inside a sibling `AGENTS.md`. This repository itself is hand-written.
Sentinel semantics are
[`docs/07-instruction-files.md`](../../docs/07-instruction-files.md)
§ "Managed blocks and sentinels" — link, do not copy.

## First-day commands

From the **template root** (the directory that contains both
`examples/handbook/` and `examples/ordinary-repo/`):

```text
python3 examples/handbook/tools/stamp-pointers.py \
  --repo examples/ordinary-repo \
  --handbook examples/handbook
```

First successful stamp on a stale block prints `changed` and exits 0;
the next prints `unchanged` and exits 0. To confirm the suite without
touching the real example:

```text
python3 examples/handbook/tools/stamp-pointers.py \
  --self-test --ordinary-repo examples/ordinary-repo
```

`--self-test` builds synthetic fixtures in a temporary directory and never
writes back. It only checks that `--ordinary-repo` contains an `AGENTS.md`; it
does not read that repo's contents as a fixture. **Failure prevented:** a verification command that
mutates the thing it was meant only to check.

## Verification notes

Recorded when this tree was written. `docs/11-verification.md` consolidates the matrix.

| Claim | Command | Result | Where claimed |
|---|---|---|---|
| `inventory.yaml` is JSON-compatible and has a non-empty `repositories` array | `python3 -c "import json,sys; d=json.load(open('examples/handbook/inventory.yaml')); …"` from the template root | prints the success line; exit 0 | this file; README.md |
| Stamper self-test: first run `changed`, second `unchanged`, outside bytes preserved, malformed/duplicate/reversed sentinels reject without mutation | `python3 examples/handbook/tools/stamp-pointers.py --self-test --ordinary-repo examples/ordinary-repo` | a `PASS: all N self-test cases held` line; exit 0 | README.md; this file |
| Derived pointer is a relative link computed from the two roots, not a hardcoded string | self-test checks the expected link equals `os.path.relpath` of the temp copies | asserted inside `--self-test` | `tools/stamp-pointers.py` |
| Stamper does not mutate `examples/ordinary-repo/` during `--self-test` | self-test writes only under `tempfile.mkdtemp` | no write to the source tree; confirmed by the suite using copies | `README.md` § What this example is; `docs/11-verification.md` claim 8 |

No upstream pi or Claude Code capability is claimed in this tree. No
package version, model name, or star count appears here.
