# Starting with AI coding agents

A starting-point template for engineers who already know systems work and are
new to AI coding agents — a guide first: eleven chapters, copy-out templates,
and two worked examples. It is **pi-first**, with a Claude Code companion
track. The public, package-installable stack is taught as working instructions;
the private layer is named as patterns with a smallest-useful build recipe for
each, and none of those patterns is installable from here.

**Cloned this to use it?** Start at [`ADOPTING.md`](ADOPTING.md). It sequences
the work — which template goes where, in what order, and how to prove the
harness actually loaded it — and it ends with a self-contained brief you can
hand to an AI agent to do the whole setup for you. You do not need to read the
chapters first: they explain *why* the templates have the shape they do, and
you can read one when a decision actually bites.

Nobody is updating this as pi, npm, or Claude Code change, and that is
deliberate — it is built to be forked, not followed. Commands, package names,
and paths in the chapters were true when those chapters were written, so look
them up again before you trust them; every chapter that needs a current value
gives the command that produces it. A factual error or a broken link is still
worth an issue — see [Maintenance posture](#maintenance-posture).

**Failure prevented:** treating a dated guide as a live product, then following
a command that no longer matches upstream — and, at the other extreme, a
repository that says "here is an example" and leaves you to invent the adoption
path yourself.

## Route

| What you want | Where it lives |
|---|---|
| **Adopt it** — what to copy where, in what order, and the AI-agent brief | [`ADOPTING.md`](ADOPTING.md) |
| Mental model (tokens, compaction, failure modes) | [`docs/01-mental-model.md`](docs/01-mental-model.md) |
| Install and authenticate | [`docs/02-install.md`](docs/02-install.md) |
| Configuration, trust, model lookup | [`docs/03-configuration.md`](docs/03-configuration.md) |
| Public packages | [`docs/04-packages.md`](docs/04-packages.md) |
| Skills | [`docs/05-skills.md`](docs/05-skills.md) |
| Memory, MCP, context | [`docs/06-memory-mcp-context.md`](docs/06-memory-mcp-context.md) |
| Instruction-file hierarchy | [`docs/07-instruction-files.md`](docs/07-instruction-files.md) |
| Cross-cutting handbook pattern | [`docs/08-cross-cutting-docs.md`](docs/08-cross-cutting-docs.md) |
| Claude Code companion | [`docs/09-claude-code.md`](docs/09-claude-code.md) |
| Private patterns (not installable) | [`docs/10-private-patterns.md`](docs/10-private-patterns.md) |
| Verification | [`docs/11-verification.md`](docs/11-verification.md) |
| Global templates | [`templates/global/`](templates/global/) |
| Per-repo templates | [`templates/repo/`](templates/repo/) |
| Ordinary runnable example | [`examples/ordinary-repo/`](examples/ordinary-repo/) |
| Handbook example | [`examples/handbook/`](examples/handbook/) |
| Leak detector | [`tools/leak-scan.sh`](tools/leak-scan.sh) |
| Rule-duplication gate (one rule, one owner) | [`scripts/rule-dup-gate.py`](scripts/rule-dup-gate.py) |

One adoption guide, eleven chapters, two template directories, two examples, one
detector, and the rule-duplication gate — every one of them present here. The
verification chapter is the one that re-checks the rest: run its suite before
you trust any claim in this file, including the ones about the suite.

## Happy path

Four steps. The chapters own the full rationale, the authority boundary, and
the lookup commands; this list is only the order.

Running only Claude Code? Your install, authentication, and instruction-file
track is [`docs/09-claude-code.md`](docs/09-claude-code.md); the list below is
the pi track.

1. **Install.** Either official path from [`docs/02-install.md`](docs/02-install.md):

   ```bash
   npm install -g --ignore-scripts @earendil-works/pi-coding-agent
   ```

   or the convenience installer at `https://pi.dev/install.sh` (read the script
   into a temp file before you run it — the chapter shows the fail-closed
   form). Then confirm the binary:

   ```bash
   pi --version
   npm view @earendil-works/pi-coding-agent version license repository.url --json
   ```

   `--ignore-scripts` bounds **install-time lifecycle scripts only**. It is not
   a sandbox. Pi has **no built-in permission system** and runs with the full
   authority of the user and process that launched it.

2. **Authenticate.** In a project directory, start `pi` and run `/login`, or
   set a provider API-key environment variable / write `~/.pi/agent/auth.json`
   as documented in the same chapter. A subscription login needs **no API key**.
   Look up the current provider list with `/login` and the upstream repo's
   `packages/coding-agent/docs/providers.md` (`github.com/earendil-works/pi`)
   — do not copy a provider name out of this README.

3. **First session.** Start `pi` in a directory you can afford to modify (git
   or equivalent checkpointing helps you roll back *project files*; it does
   not confine the process). Use the four built-in tools — `read`, `write`,
   `edit`, `bash` — on something small and check that the change actually
   landed. Observable success is the evidence; a session that printed no error
   is not.

4. **Starter packages.** Only after a session has worked. Install by pain, not
   by copying a list, using the real CLI from [`docs/04-packages.md`](docs/04-packages.md):

   ```bash
   pi install npm:pi-web-access
   pi install npm:pi-mcp-adapter
   pi install git:github.com/obra/superpowers
   pi install npm:context-mode          # Elastic-2.0 — read NOTICES.md first
   pi install npm:pi-smart-compact
   ```

   Packages run with full system access, which is why
   [docs/04-packages.md](docs/04-packages.md) owns the rule about reading what you
   install. One concrete case from that chapter: `context-mode` is **Elastic-2.0**,
   not MIT.

   There is no safe preview step. `pi -e <spec>` is an *ephemeral run*, not an
   inspection — loading a package executes its code, so `-e` is how you use a
   package once, not how you look at it first. What to do instead is
   [docs/04-packages.md](docs/04-packages.md)'s rule, and it is the step this
   list is tempting you to skip.

**Failure prevented:** a numbered list that skips the authority boundary, so a
reader finishes step 1 believing they sandboxed the agent.

## Maintenance posture

Nobody is updating this as pi, npm, or Claude Code change. That is a design
decision, not neglect: it is built to be cloned and modified, and the
discipline below is what makes a fork survivable.

- **Lookup over literal.** Version numbers, model names, and star counts do
  not belong in reader-facing prose. Each chapter that needs a current value
  gives the command that produces it, so a fork does not inherit a stale
  number.
- **Re-verify before you trust.** [`docs/11-verification.md`](docs/11-verification.md)
  is the replay surface: it carries the executable suite and the per-chapter
  verification notes. [`NOTICES.md`](NOTICES.md) is the license lookup.
- **No installer.** There is no `setup.sh`. You run the commands, or you hand
  [`ADOPTING.md`](ADOPTING.md)'s brief to an agent that runs them. An installer
  would be a second, rotting copy of the same instructions.
- **Corrections welcome.** A factual error, a broken link, or a claim that no
  longer matches upstream is worth an issue, even though nothing here is
  tracked against releases. The promise is narrow and it is real: corrections
  get applied. No response time, no feature work, and no support.

**Failure prevented:** a "current recommended version" copied out of a README
becoming a lie the day upstream ships — and an Issues tab that silently implies
a support commitment nobody intends to keep.

## License and notices

- [`LICENSE`](LICENSE) — MIT, covering **this template's own** prose, templates,
  and examples. Copyright is generic ("the authors of this template"); no
  person or organisation is named as owner.
- [`NOTICES.md`](NOTICES.md) — third-party attribution for every public
  package and skill this template *names*. Referencing is not redistribution.
  Elastic-2.0 and the undeclared-license case are called out there, not
  papered over.

## Export — only if you fork this

This section is for [`ADOPTING.md`](ADOPTING.md)'s mode 2: making your own
version of the guide. If you only want the templates for your own repositories,
skip it — nothing you copy depends on any of it.

Publication is an **export** bounded by [`MANIFEST.txt`](MANIFEST.txt), not a
git archive and not "whatever is in this checkout." The workspace this
repository was built in also held run evidence — planning state, receipts,
review transcripts — deliberately not part of the published tree. The manifest
is what draws that line, and an export copies nothing it does not list.

`MANIFEST.txt` is one exact regular-file path per line: no comments, no globs,
no directories. It lists itself, and every path in it exists in this tree. An
export that copies a path the manifest does not list, or that skips a path the
manifest does list, is a defect. That second direction matters as much as the
first: an unlisted file in the export is exactly how private material rides
alongside a clean manifest.

### What an exporter must reject

The integrated suite that implements this contract is
[`docs/11-verification.md`](docs/11-verification.md), and you can run it
yourself. Running it proves the tree, but it does not leave you an export: the
suite builds its copy in a temporary directory and discards it. To produce an
export, copy the files `MANIFEST.txt` lists — the sketch below is the whole
shape. The contract the suite enforces:

- Reject absolute paths, `..` traversal, duplicates, hidden paths, symlinks and
  missing files. Any path not named in the manifest is rejected, which is the
  general form of "no internal working files".
- Reject unlisted product files so an omission cannot evade the leak scan.
- Copy only listed files into a **new temporary tree** (Python standard
  library: `tempfile.mkdtemp`, `os.path`, `shutil.copy2`). Do not publish the
  git repository, do not delete private history, do not run an installer.
- After copy, assert that **every regular file in the export decodes as valid
  UTF-8 with no NUL**. This is a text-only deliverable. The leak detector
  skips binary contents; an undecodable file copied into the export would be
  the one place a leak could ship uninspected. Fail closed on that file —
  never skip it.

A sketch of the validation/copy shape, which the real suite implements:

```python
# Python 3 standard library only. Fail closed; no bare assert
# (python3 -O / PYTHONOPTIMIZE=1 strip assertions).
import os, sys, tempfile, shutil, pathlib

def fail(msg):
    sys.stderr.write("FAIL: " + msg + "\n")
    sys.exit(1)

def load_manifest(path):
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        fail("manifest missing or empty: " + path)
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    if not lines:
        fail("manifest has no entries")
    seen = set()
    for i, raw in enumerate(lines, 1):
        p = raw.strip()
        if not p:
            fail("blank line at %d" % i)
        if p.startswith("/") or p.startswith("#") or p.endswith("/"):
            fail("absolute, comment, or directory at %d: %s" % (i, p))
        # Any glob metacharacter, not just '*': '?' and '[' are glob syntax too,
        # and a manifest that advertises "no globs" must reject all of them.
        if any(ch in p for ch in "*?[]"):
            fail("glob metacharacter at %d: %s" % (i, p))
        parts = p.split("/")
        if ".." in parts or any(part.startswith(".") for part in parts):
            fail("traversal or hidden path at %d: %s" % (i, p))
        # A dotted component is already rejected above, so the only internal
        # paths that could appear here are ones a maintainer added by mistake;
        # the manifest's own allowlist is the real boundary (see the suite).
        if p in seen:
            fail("duplicate at %d: %s" % (i, p))
        seen.add(p)
    return list(seen)

# Copy each listed relative file from src_root to a fresh dest_root with
# shutil.copy2, creating parent directories. Refuse if the source is a
# symlink, is missing, or is not a regular file. After copy, read each
# exported file as UTF-8 (errors='strict') and reject any NUL byte.
```

**Failure prevented:** `git archive` or a recursive copy of `docs/` shipping
the private bundle; or an undecodable file riding into the export while the
detector skipped its bytes.

The detector is:

```bash
bash tools/leak-scan.sh <export-root>     # 0 clean, 1 hits, 2 operational error
bash tools/leak-scan.sh --self-test
bash tools/leak-scan.sh --verify-document docs/11-verification.md
```

## Verification notes

| Claim | Command | Result (when this was written) | Chapter |
|---|---|---|---|
| Routing table names all 11 chapter files | visual: rows `docs/01` … `docs/11` in the table above | 11 rows present; all 11 exist on disk | this file |
| LICENSE is MIT | `grep -nF 'MIT License' LICENSE` | match | this file |
| Elastic-2.0 caution exists | `grep -nF 'Elastic-2.0' NOTICES.md` | match | NOTICES.md |
| Manifest is non-empty | `test -s MANIFEST.txt` | exit 0 | MANIFEST.txt |
| Manifest vs tree | see `docs/11-verification.md` | every listed file exists; no unlisted files in the publication area | MANIFEST.txt |
| pi package license | `npm view @earendil-works/pi-coding-agent license repository.url --json` | MIT, `earendil-works/pi` | NOTICES.md |
| context-mode license | `npm view context-mode license repository.url --json` | Elastic-2.0 | NOTICES.md |

Re-run the lookups. Do not copy a version number out of any chapter.

## What this is not

- Not a maintained upstream project — a starting point you fork.
- Not prescriptive policy for your organisation.
- Not a security or compliance guide.
- Not a reimplementation of anyone's private infrastructure.
- Not harness-agnostic: pi is the recommendation; Claude Code is covered
  because the reference setup — the working dual-harness setup this template
  generalizes from — runs both.
- Not an installer and not `setup.sh`.
