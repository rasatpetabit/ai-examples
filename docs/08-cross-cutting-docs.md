# 8 — Cross-cutting documentation

A handbook is the third instruction-file tier: one repository that owns what is true of
*many* implementation repos and belongs to none of them. The split rule that decides
whether a line lives here, in a per-repo `AGENTS.md`, or in the global file is
[`07-instruction-files.md`](07-instruction-files.md). This chapter does not restate it.
It is the prose guide to the **shipped example** of that tier:
[`examples/handbook/`](../examples/handbook/) stamping a pointer into
[`examples/ordinary-repo/AGENTS.md`](../examples/ordinary-repo/AGENTS.md).

Every command, flag, path, and output word below is taken from those files and was
re-run from this repository's root while writing. Invented snippets would be the cargo-cult
this template exists to stop: a reader copies a flag the tool does not have, and the
example "works" only in the paragraph.

## Why a third tier exists

Per-repo instruction files stay short by saying what is true of *this* product. Global
files stay short by saying what is true *everywhere the reader works*. What remains is
true of several products at once: domain conventions, shared-service ownership, the
question "where does X live?". Paste that into every sibling `AGENTS.md` and the copies
drift. Put it in the global file and every session pays for it, including sessions that
never touch that domain.

The handbook is the remaining place. It does **not** load automatically. A session
started in `ordinary-repo` sees a pointer block in that repo's `AGENTS.md` and follows
it. Treating the handbook as tier-1 global policy is the wrong tier — that sentence is
the first thing [`examples/handbook/AGENTS.md`](../examples/handbook/AGENTS.md) tells
an agent, because it is the mistake a fluent newcomer makes.

**Failure prevented:** N hand-maintained copies of one domain rule, of which copy 3 of 5
disagrees with copy 5 of 5, and neither a human nor an agent can tell which is stale.

## What the shipped handbook is

Seven files, no more:

```text
examples/handbook/
  AGENTS.md                         ownership boundary and navigation
  README.md                         how to copy, stamp, and restamp
  inventory.yaml                    sibling membership
  docs/boundaries/index.md          names what each leaf answers
  docs/boundaries/application.md    application-domain leaf
  docs/boundaries/platform.md       platform-domain leaf
  tools/stamp-pointers.py           pointer-block stamper
```

It is a genericized shape you `cp -r`, not a real organisation's handbook. Repository
identifiers in `inventory.yaml` (`ordinary-example`, `example-handbook`) are invented.
Paths are relative to the handbook directory. The seven files are self-contained in
*content*, not in *navigation*: every prose file points outside the tree for the rules
it defers to, so a standalone copy breaks those references. The exact list — which file
points at what, and what to do about each — is owned by
[`examples/handbook/README.md`](../examples/handbook/README.md), which is the file a
reader copies and therefore the right place for the migration steps.
**Failure prevented:** a copied handbook whose authority link 404s, so the reader cannot
tell whether the rule was omitted or moved.

The sibling it stamps against is `examples/ordinary-repo/`. That file already contains
exactly one ordered sentinel pair. The stamper replaces only the bytes between them.

## Boundaries: index and leaves

[`docs/boundaries/index.md`](../examples/handbook/docs/boundaries/index.md) names **what
each leaf answers**. It does not contain the leaf.

| Leaf | Question it answers |
|---|---|
| [`application.md`](../examples/handbook/docs/boundaries/application.md) | What are the conventions and repo ownership for **application** work — product code a user runs? |
| [`platform.md`](../examples/handbook/docs/boundaries/platform.md) | What are the conventions and repo ownership for **platform** work — shared services no single product repo owns? |

A leaf that is not in that table is not a boundary this handbook claims. Adding a domain
means adding a row **and** a leaf file.

The two leaves are deliberately different questions, not the same conventions under two
headings. `application.md` owns product-repo conventions (the worked example is
`ordinary-repo` shipping `tally`). `platform.md` owns what is true of more than one
application repo and belongs to none of them; this template has no real platform
service, and the leaf says so rather than going silent. An empty platform leaf reads as
"we forgot", not as "nothing belongs here".
**Failure prevented:** a future author filling the silence with a convention that was
never agreed.

Each leaf's path is load-bearing. Sibling repositories reach the handbook through the
stamped pointer, which currently targets the **index**, not a leaf. That distinction
decides the repair when something moves — see [Moving a leaf is not the same as moving
the index](#moving-a-leaf-is-not-the-same-as-moving-the-index).

Do not add product behaviour to a handbook leaf. Do not copy a leaf into a sibling
`AGENTS.md`. The pointer is a **link**, not a copy.
**Failure prevented:** the drift the pattern exists to stop — N copies of one domain
rule, disagreeing.

## Inventory

[`inventory.yaml`](../examples/handbook/inventory.yaml) is JSON-compatible YAML: a JSON
object that the Python 3 standard library `json.load`s, so no third-party YAML parser is
required. It carries a non-empty `repositories` array. Each row in this example has
`id`, `name`, `kind`, `path` (relative to the handbook directory), `pointer_file`, and
`notes`. The handbook row's `pointer_file` is JSON `null` — the handbook is not a
pointer target of itself.

This example's stamper is invoked **per repo** (`--repo` / `--handbook`) rather than
iterating the inventory. That is the smallest useful version: the membership list is
visible and parseable, and the tool does one named pair of roots. Iterating the
inventory is a later, optional step you can add without changing the file format.

Add a sibling by adding a row, not by inventing a second inventory format. Never put an
absolute workspace path in this file.
**Failure prevented:** a membership list that only one tool can read, so the next author
rebuilds it by grepping paths; or a copied handbook that still points at the template
author's disk layout.

The check that proves the file is what it claims:

```text
python3 -c "import json,sys; d=json.load(open('examples/handbook/inventory.yaml')); r=d.get('repositories'); print('inventory.yaml parses as JSON-compatible YAML with a repositories array') if (isinstance(r,list) and len(r)>0) else sys.exit('FAIL: repositories must be a non-empty list')"
```

Run from the repository root. An **absent** file raises `FileNotFoundError` — the
check fails closed. An **empty** file (`{}` or `[]`) is a different failure (`repositories`
missing or not a non-empty list) and is not claimed by that command; do not collapse the
two.

## Pointer stamping

[`tools/stamp-pointers.py`](../examples/handbook/tools/stamp-pointers.py) is an example
utility, not an installer. It never writes the reader's home configuration. It never
scans `$HOME`, never discovers git remotes, and never writes a path it was not given.

CLI, from the repository root (the directory that contains both example trees):

```text
python3 examples/handbook/tools/stamp-pointers.py \
  --repo examples/ordinary-repo \
  --handbook examples/handbook
```

The block is a **prefix**, and that is the whole contract:

1. `<!-- handbook-pointer:start -->` is the **first line of the file**.
2. `<!-- handbook-pointer:end -->` is a **standalone line** somewhere after it.
3. Exactly **one** occurrence of each marker exists in the file.
4. Every byte after the `END` line is preserved verbatim — including the absence
   of a trailing newline at EOF, and including any Markdown at all.

The tool derives the relative link from the two roots (`os.path.relpath` of the
index from the target file's directory, POSIX separators, path components
percent-encoded), writes via a sibling tempfile, and only then `os.replace`s it over
the target. The target's original file mode is copied onto the tempfile *before* the
swap, because `mkstemp` creates the file 0600 and swapping would otherwise strip
group and other read from a file that had it. It writes only after validation
succeeds.

**Why a prefix rather than "find the block anywhere in the document".** A block that
may sit anywhere has to be told apart from an *example* of the block — and deciding
whether a given marker is inside a fenced block, an inline code span, an indented
block, or an HTML element is a Markdown parsing problem. Approximating that parser
was tried and abandoned: each approximation was wrong in a new way, and every wrong
guess silently rewrote a reader's documentation. Anchoring the block at byte zero
removes the question instead of answering it better — there is nothing before it, so
no construct can contain it. The cost is that a managed block cannot sit beside a
heading; the benefit is that the safety property is decidable by inspection.

It refuses, prints a diagnostic on stderr, exits nonzero, and mutates nothing, when:

| Condition | Exit | Diagnostic contains |
|---|---|---|
| the file contains no marker at all | 1 | `missing sentinels (need exactly one ordered start/end pair)` |
| a marker does not occur exactly once — a second copy, an example of the syntax quoted in the document, or a missing counterpart | 1 | `the file mentions a marker 1 time(s) as start and 0 time(s) as end; the block is delimited by exactly one of each — refusing to stamp` (the counts vary with what is present) |
| the start marker is not the first line — a heading above it, leading whitespace, or markers inside a fence or an inline span | 1 | `the start marker is not the first line of the file (line 1 is '# h'); a managed block is a prefix, and this tool will not infer which marker in a document is the real one — refusing to stamp` |
| the end marker is not alone on its line, or never appears as a line | 1 | `the end marker is not a standalone line after the start marker; refusing to stamp` |
| the target resolves outside `--repo` through a symlink | 1 | `target file resolves outside the supplied root, refusing:` |

Every row leaves the file byte-identical. Nothing in this table requires knowing what
a Markdown renderer would do — that is the point of the prefix.

A CRLF file is supported: the trailing `\r` is read as part of the line terminator,
and the generated block adopts the file's own terminator rather than flipping a
Windows checkout to LF.

`--ordinary-repo` is a `--self-test` fixture. Passing it in stamping mode is rejected
(`--ordinary-repo is a --self-test fixture; it is ignored in stamping mode`) rather than
silently ignored.

### What the prefix contract costs you

The costs, stated plainly, because a trade-off you have to discover yourself is worse:

- **The block must be the first thing in the file.** A repository wanting a title or a
  one-line summary above it cannot have one — move that prose below the `END` line.
- **YAML front matter is incompatible.** Front matter must begin at byte zero, which is
  where the start sentinel must begin, and moving front matter below `END` is not the
  same document: nothing that reads front matter at the top of the file will find it.
  A file that needs front matter should carry its pointer by hand.
- **A leading byte-order mark breaks it.** A BOM before the start sentinel means the
  marker is not the first line, and the file is refused.
- **Only one generator may own the prefix.** Two tools cannot both claim byte zero.
- **Mentioning a marker anywhere else disables stamping**, even in the human-owned prose
  below `END`, because occurrence counts cover the whole file. Writing *about* this
  convention in the file that uses it makes that file unstampable.

The alternative was a heuristic that decided, per marker, whether it sat inside code —
and it could not be made safe without a full Markdown parser, which is too much
dependency for a pointer stamper. Prefix placement is the chosen trade, not the only
possible one; a maintained parser with source maps is a real alternative if a caller
genuinely needs arbitrary placement.

**Failure prevented:** a stamper that "helpfully" inserts markers in a file that did not
opt in; that clobbers human-owned prose around the block; that treats a quoted example
of the sentinels as the operational pair; or that follows a symlink out of the roots
the caller named.

## Exit statuses when output cannot be written

Both shipped tools document their statuses (the stamper in its module docstring, the
detector in its usage text). One case is worth stating because it is easy to get
wrong in a way that looks like a result:

- **A tool that produced a verdict keeps it when the reader goes away.** A pager or
  `| head` closing the pipe is how normal output ends, so a scan whose report is
  truncated still exits with the verdict it reached — `0` clean, `1` hits. It never
  reports "clean" merely because the report was cut short.
- **Text that could not be delivered is an I/O error (status 2).** If the caller asked
  for output — usage text, a help screen, a report — and no byte could be written, then
  the caller received nothing to act on, and the tool says so rather than exiting
  successfully. This covers a full disk, an unwritable stream, and a descriptor that was
  closed before the process started.
- **An error path keeps its own status where it can.** Missing input, a usage mistake,
  or an invalid record still exits with its documented status — *unless the diagnostic
  itself could not be delivered*, in which case the status is `2`, because the caller
  never learned what the problem was.
- **Status `1` is never produced by a write failure.** `1` is the detector's "hits"
  result: a claim about the work under review. A tool that could not write its report has made
  no such claim, and reporting one would be a false positive on the only signal the
  detector exists to produce.

Two implementation notes, because both cost real time to discover: a descriptor closed
before the process starts (`1>&-`) leaves Python's `sys.stdout` as `None` rather than a
stream that raises, so it must be tested for explicitly; and CPython flushes both
standard streams again at interpreter shutdown, so a failing second flush replaces a
deliberate status with `120` unless the descriptor is redirected to `/dev/null` first.

**Failure prevented:** a detector that reports "no leaks found" when it could not write
its report, or a tool that exits `1` — a *result* status — because its own diagnostic
could not be delivered.

## Generated versus handwritten regions

| Bytes | Owner |
|---|---|
| Between `<!-- handbook-pointer:start -->` and `<!-- handbook-pointer:end -->` in a sibling `AGENTS.md` | the stamper |
| The handbook's own `README.md`, `AGENTS.md`, leaves, index, inventory, and the stamper source | you (hand-written; no sentinels) |
| The sibling `AGENTS.md` *outside* its pointer sentinels | that repo's humans |

The handbook repository itself is hand-written. The only generated region it *produces*
is the pointer block inside a sibling. Sentinel semantics — why a hand edit inside the
markers is silently gone on the next stamp, and why the fix belongs in the source the
script stamps from — are
[`07-instruction-files.md`](07-instruction-files.md) § "Managed blocks and sentinels".
This chapter does not copy that section.

`examples/ordinary-repo/AGENTS.md` currently holds this generated block (the link is
derived, not hardcoded):

```markdown
<!-- handbook-pointer:start -->
- [Boundaries index](../handbook/docs/boundaries/index.md)
<!-- handbook-pointer:end -->
```

Everything above and below those two lines in that file is human-owned, including the
`intent:consultation-rule` block that follows. A stamp must leave those bytes identical.

**Failure prevented:** two sources of truth for the same pointer, one of which the next
refresh discards without a diff the author was looking at.

## Two runs of the stamper

The live pair `--repo examples/ordinary-repo --handbook examples/handbook` is already
current in this tree. Both runs print `unchanged` and exit 0 — that is the honest
result, not a demonstration of a stale-to-fresh transition. The **stale-then-current**
sequence is what `--self-test` exists to show: it builds synthetic fixtures under a
temporary directory and invokes the **real CLI** on them. (It does not read the tree
you pass to `--ordinary-repo` — it only requires that an `AGENTS.md` is there. The
*integrated* suite in `docs/11-verification.md` is what performs a genuine
copied-example two-run test; the standalone self-test is the fast check.)

```text
python3 examples/handbook/tools/stamp-pointers.py \
  --self-test --ordinary-repo examples/ordinary-repo
```

Recorded by running the shipped tool, from the repository root:

```text
self-test init: status=0 stdout='changed\n' stderr=''
self-test refresh: status=0 stdout='changed\n' stderr=''
self-test idempotent: status=0 stdout='unchanged\n' stderr=''
self-test eof-end-marker: status=0 stdout='changed\n' stderr=''
self-test utf8-prose: status=0 stdout='changed\n' stderr=''
self-test crlf-prose: status=0 stdout='changed\n' stderr=''
self-test crlf-no-trailing-newline: status=0 stdout='changed\n' stderr=''
self-test lone-cr-at-eof: status=0 stdout='changed\n' stderr=''
self-test empty-tail-with-newline: status=0 stdout='changed\n' stderr=''
self-test empty-file: status=1 stdout='' stderr='stamp-pointers.py: missing sentinels (need exactly one ordered start/end pair)\n'
self-test no-markers: status=1 stdout='' stderr='stamp-pointers.py: missing sentinels (need exactly one ordered start/end pair)\n'
self-test start-not-first: status=1 stdout='' stderr="stamp-pointers.py: the start marker is not the first line of the file (line 1 is '# Heading first'); a managed block is a prefix, and this tool will not infer which marker in a document is the real one — refusing to stamp\n"
self-test indented-start: status=1 stdout='' stderr="stamp-pointers.py: the start marker is not the first line of the file (line 1 is ' <!-- handbook-pointer:start -->'); a managed block is a prefix, and this tool will not infer which marker in a document is the real one — refusing to stamp\n"
self-test fenced-only: status=1 stdout='' stderr="stamp-pointers.py: the start marker is not the first line of the file (line 1 is '```'); a managed block is a prefix, and this tool will not infer which marker in a document is the real one — refusing to stamp\n"
self-test inline-only: status=1 stdout='' stderr="stamp-pointers.py: the start marker is not the first line of the file (line 1 is 'Example: `<!-- handbook-pointer:start --> <!-- handbook-poin'); a managed block is a prefix, and this tool will not infer which marker in a document is the real one — refusing to stamp\n"
self-test duplicate-start: status=1 stdout='' stderr='stamp-pointers.py: the file mentions a marker 2 time(s) as start and 1 time(s) as end; the block is delimited by exactly one of each — refusing to stamp\n'
self-test duplicate-end: status=1 stdout='' stderr='stamp-pointers.py: the file mentions a marker 1 time(s) as start and 2 time(s) as end; the block is delimited by exactly one of each — refusing to stamp\n'
self-test quoted-example-plus-live: status=1 stdout='' stderr='stamp-pointers.py: the file mentions a marker 2 time(s) as start and 1 time(s) as end; the block is delimited by exactly one of each — refusing to stamp\n'
self-test end-before-start: status=1 stdout='' stderr="stamp-pointers.py: the start marker is not the first line of the file (line 1 is '<!-- handbook-pointer:end -->'); a managed block is a prefix, and this tool will not infer which marker in a document is the real one — refusing to stamp\n"
self-test missing-end: status=1 stdout='' stderr='stamp-pointers.py: the file mentions a marker 1 time(s) as start and 0 time(s) as end; the block is delimited by exactly one of each — refusing to stamp\n'
self-test end-not-standalone: status=1 stdout='' stderr='stamp-pointers.py: the end marker is not a standalone line after the start marker; refusing to stamp\n'
self-test start-not-alone: status=1 stdout='' stderr='stamp-pointers.py: the start marker is not alone on its first line (trailing content follows it); refusing to stamp\n'
self-test second-run: status=0 stdout='unchanged\n' stderr=''
self-test symlink-escape: status=1 stderr='stamp-pointers.py: target file resolves outside the supplied root, refusing: /tmp/stamp-self-test-9nl3mkj_/escape/AGENTS.md\n'
self-test mode-preserved: status=0 stdout='changed\n' stderr=''
self-test mode-0640: status=0 stdout='changed\n' stderr=''
self-test handbook-escape: status=1 stdout='' stderr='stamp-pointers.py: handbook index resolves outside the supplied root, refusing: /tmp/stamp-self-test-9nl3mkj_/escaping-handbook/docs/boundaries/index.md\n'
self-test percent-encoded-link: status=0
PASS: all 28 self-test cases held
```

Exit 0. Each row of the case table states its fixture bytes, the exact exit status, a
substring the diagnostic must contain, and the exact final bytes — so a refusal is
proven by identical bytes, and a success by the whole file rather than by the word
`unchanged`. The table also rejects a traceback, which matters because "exited
nonzero" is not the same claim as "refused carefully".

The two auxiliary checks make the same demand of themselves. The repeat run performs
a real first-output-to-second-input sequence and compares the second run's complete
bytes and file mode against the first run's, not just its stdout. The mode check
asserts the replacement actually happened before checking that the mode survived it —
otherwise a tool that did nothing would pass by leaving the old mode in place.

The suite is mutation-tested rather than merely executed: replacing the generated link
with a nonexistent path, deleting the containment refusal, making the splice a no-op,
and dropping a trailing byte at EOF each make it fail. A suite that passes a knowingly
broken tool is not evidence, and the case count on its own is bookkeeping.

`--self-test` writes only under `tempfile.mkdtemp` and never mutates
`examples/ordinary-repo/`. Checks use explicit failures, not `assert`, so
`python3 -O` does not disable them.

On the real sibling, the same CLI after the self-test still reports `unchanged` —
confirmation that the suite did not write back.

**Failure prevented:** a verification command that mutates the thing it was meant only
to check; or a self-test that treats the output word `unchanged` as proof of
idempotence when the file bytes moved.

## Moving a leaf is not the same as moving the index

Stamped pointers currently target `docs/boundaries/index.md`. Conflating a leaf move
with an index move leaves a 404 at the end that was not broken.

- **Moving a boundary leaf** (`application.md` or `platform.md`): every stamped pointer
  still resolves, because it points at the index. What breaks is the **index's own
  links** to that leaf. Repair: edit the index. Restamping siblings does nothing useful
  here.
- **Moving or renaming the index itself**: every stamped pointer now points at a path
  that no longer exists. Repair: update the stamper's index target (`INDEX_REL` in
  `stamp-pointers.py`, and the `pointer.leaf` field in `inventory.yaml`) and restamp
  every sibling.

**Failure prevented:** a tidy-up that looks local and breaks N repos the author did not
have open — the leaf case "fixed" by restamping (which fixes nothing), and the index
case "fixed" by editing the index (which is not the broken end).

The same load-bearing rule applies to any hand-written link into a leaf. An inbound
reference is a contract. Renaming without updating every referrer leaves a
valid-looking git history and a dead path from every working tree that still points at
the old name.

## What this chapter does not own

- The split rule, the per-line test, harness loading, and sentinel *policy* —
  [`07-instruction-files.md`](07-instruction-files.md).
- Global and per-repo skeletons — `templates/`.
- The ordinary example's program, intent block, and human-owned `AGENTS.md` —
  `examples/ordinary-repo/`.
- Publication routing, license, notices, and the export manifest — later chapters.
- Security, sandboxing, or compliance. Named as a non-goal of this template, not taught
  here.

## Verification notes

Commands run from the repository root (the directory that contains both
`examples/handbook/` and `examples/ordinary-repo/`). `docs/11-verification.md` consolidates the matrix.
No package version, model identity, or star count is claimed. No private hostname,
org name, or absolute workspace path appears in the handbook tree this chapter
describes.

| Claim | Command | Result | Where claimed |
|---|---|---|---|
| `inventory.yaml` is JSON-compatible YAML with a non-empty `repositories` array | `python3 -c "import json,sys; d=json.load(open('examples/handbook/inventory.yaml')); r=d.get('repositories'); print('inventory.yaml parses as JSON-compatible YAML with a repositories array') if (isinstance(r,list) and len(r)>0) else sys.exit('FAIL: repositories must be a non-empty list')"` | printed that success line; exit 0 | Inventory |
| absent inventory fails closed | same `json.load` against `examples/handbook/no-such-inventory.yaml` | `FileNotFoundError: [Errno 2] No such file or directory: 'examples/handbook/no-such-inventory.yaml'`; exit 1 | Inventory |
| live stamp of the already-current sibling is a no-op | `python3 examples/handbook/tools/stamp-pointers.py --repo examples/ordinary-repo --handbook examples/handbook` twice | `unchanged` then `unchanged`; both exit 0 | Two runs of the stamper |
| self-test: first CLI `changed`, second `unchanged`, refusals without mutation, complete-byte idempotence | `python3 examples/handbook/tools/stamp-pointers.py --self-test --ordinary-repo examples/ordinary-repo` | inner statuses as quoted above; a `PASS: all N self-test cases held` line reporting the number of cases that ran; exit 0 | Two runs of the stamper |
| derived pointer is a relative link to the index, not a hardcoded string | inspect `examples/ordinary-repo/AGENTS.md` sentinels; stamper `build_block` + `posix_relpath` | `- [Boundaries index](../handbook/docs/boundaries/index.md)` | Pointer stamping; Generated versus handwritten |
| chapter names the stamper and the inventory file | `grep -nF 'stamp-pointers.py' docs/08-cross-cutting-docs.md && grep -nF 'inventory.yaml' docs/08-cross-cutting-docs.md` | both match (smoke only) | this file exists |

### Intentionally not claimed

- That the live `--repo` / `--handbook` pair on this tree prints `changed` on a first
  run. It does not; the sibling is already stamped. The `changed`/`unchanged` pair is
  the self-test's, which stales a copy.
- That an empty (present-but-`{}`) inventory fails the same way as an absent file. Only
  absence was exercised as `FileNotFoundError`.
- Any pi or Claude Code loading behaviour of the handbook itself. The handbook is linked
  into, not loaded as, a sibling session. Loading rules live in
  [`07-instruction-files.md`](07-instruction-files.md).
