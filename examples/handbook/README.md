# example-handbook

A copyable, genericized **cross-cutting documentation** repository: one
place that owns navigation, inventory, and domain-boundary leaves so
sibling implementation repos do not each keep a drifting copy.

This tree is an example inside a larger template. Copy it, rename it,
replace the invented repository identifiers, and fill the leaves with
your own conventions. It is not a real organisation's handbook and it
names none.

The pattern this example exists to demonstrate — three instruction-file
tiers, managed sentinel blocks, and why a rule must not live in two
files — is owned by
[`docs/07-instruction-files.md`](../../docs/07-instruction-files.md).
This README does not restate that chapter.

## What you get

```text
examples/handbook/
  AGENTS.md                         ownership boundary and navigation
  README.md                         this file
  inventory.yaml                    sibling membership (JSON-compatible YAML)
  docs/boundaries/index.md          names what each leaf answers
  docs/boundaries/application.md    application-domain leaf
  docs/boundaries/platform.md       platform-domain leaf
  tools/stamp-pointers.py           pointer-block stamper (example utility)
```

The sibling it stamps against is `examples/ordinary-repo/`, whose
`AGENTS.md` already contains exactly one ordered
`<!-- handbook-pointer:start -->` / `<!-- handbook-pointer:end -->`
pair.

## Copy and edit

```text
cp -r examples/handbook /path/to/your-handbook
```

**The copy leaves several links dangling.** The seven files above are
self-contained in *content*, not in *navigation*: every file in this tree points
outside it for the rules it defers to. A standalone copy breaks all of these:

| Points at | Linked from | What to do |
|---|---|---|
| `docs/07-instruction-files.md` | all five prose files | keep the handbook inside a tree carrying that chapter, or retarget the links |
| `docs/08-cross-cutting-docs.md` | all five prose files | same |
| `examples/ordinary-repo/` | `docs/boundaries/application.md` | retarget at your own example, or delete that bullet |

Retargeting is a find-and-replace across the tree, not a two-link edit.
**Failure prevented:** a copied handbook whose authority links 404, so the reader
cannot tell whether a rule was omitted or merely moved.

Then:

1. Replace the invented identifiers in `inventory.yaml` (`ordinary-example`,
   `example-handbook`) with your own repository names. Keep `path` values relative to the
   handbook directory; the inventory's path rule is owned by
   [`docs/08-cross-cutting-docs.md`](../../docs/08-cross-cutting-docs.md).
   **Failure prevented:** a copied handbook that still points at the
   template author's disk layout.
2. Rewrite the two leaves so they answer *your* domain questions. Keep the
   index as the file that *names what each leaf answers*.
3. Point sibling repos at this handbook with the stamper, below.

## Stamping a sibling

The stamper derives the relative link from two roots you pass. It never
scans home, never discovers repositories, and never writes a path it was
not given. It is an example utility, not an installer, and it does not
edit anyone's configuration.

From the template root (the directory that contains both example
trees):

```text
python3 examples/handbook/tools/stamp-pointers.py \
  --repo examples/ordinary-repo \
  --handbook examples/handbook
```

| Run | stdout | exit |
|---|---|---:|
| first, when the block differs from what the two roots imply | `changed` | 0 |
| second, when the block already matches | `unchanged` | 0 |

Only the bytes between the two sentinels in the target `AGENTS.md` are
replaced, and everything outside is preserved. What counts as a valid pair —
where the block must sit, and every way a file can be refused — is owned by
[`docs/08-cross-cutting-docs.md`](../../docs/08-cross-cutting-docs.md); this
README does not restate it.
**Failure prevented:** a stamper that "helpfully" inserts markers in a
file that did not opt in, or that clobbers human-owned prose around the
block.

A leaf move and an index move are different repairs, and conflating them leaves a
404. The rule, both repairs, and every path that must be updated for an index
move are stated once in
[`docs/08-cross-cutting-docs.md`](../../docs/08-cross-cutting-docs.md); this
README points there rather than keeping a second copy that can drift.

**Failure prevented:** a tidy-up that looks local and breaks N repos the author
did not have open — the leaf case repaired by restamping (which fixes nothing),
and the index case repaired by editing the index (which is not the broken end).

### Self-test (does not touch the real example)

```text
python3 examples/handbook/tools/stamp-pointers.py \
  --self-test --ordinary-repo examples/ordinary-repo
```

The suite builds synthetic fixtures in a temporary directory — it copies this
handbook's index and writes its own `AGENTS.md` cases; `--ordinary-repo` is only
checked for the presence of that file, never read as content — stales the pointer
block, invokes the real CLI twice, checks the exact expected block and every outside byte, checks
that the second run's complete file bytes are identical to the first,
and checks that missing / duplicate / reversed sentinels reject without
mutating the fixture. It prints each inner run's status and stdout, then
`PASS` if every assertion held.

Python 3 standard library only. `python3 -O` does not disable the
checks: they use explicit `sys.exit("FAIL: …")`, not `assert`.

## Generated versus hand-written

| Bytes | Owner |
|---|---|
| Between `<!-- handbook-pointer:start -->` and `<!-- handbook-pointer:end -->` in a sibling `AGENTS.md` | the stamper |
| This README, `AGENTS.md`, leaves, index, inventory, the stamper source | you |

A hand edit inside the sentinels survives until the next stamp, then
disappears. That is the point of the markers; the instruction-files
chapter is the authority on why.

## Inventory format

`inventory.yaml` is JSON-compatible YAML: a JSON object that `json.load`
accepts, so no third-party YAML parser is required. It carries a
non-empty `repositories` array. Each row has an `id`, a `kind`, and a
`path` relative to this directory.

This example's stamper is invoked **per repo** (`--repo` / `--handbook`)
rather than iterating the inventory itself. That is the smallest useful
version: the membership list is visible and parseable, and the tool does
one named pair of roots. Iterating the inventory is a later, optional
step you can add without changing the file format.

## Verification notes

Recorded when this tree was written. Commands run from the template root.

| Claim | Command | Result |
|---|---|---|
| inventory parses as JSON-compatible YAML with a non-empty `repositories` array | `python3 -c "import json,sys; d=json.load(open('examples/handbook/inventory.yaml')); r=d.get('repositories'); print('…') if (isinstance(r,list) and len(r)>0) else sys.exit('FAIL: …')"` | success line, exit 0 |
| stamper self-test (changed / unchanged / preserved outside bytes / reject malformed without mutation) | `python3 examples/handbook/tools/stamp-pointers.py --self-test --ordinary-repo examples/ordinary-repo` | inner run statuses printed; a `PASS: all N self-test cases held` line; exit 0 |
| absent inventory fails the inventory check | same `json.load` command against a missing file | `FileNotFoundError` (the check fails closed on an absent target) |

No package version, model identity, or star count is claimed. No private
hostname, org name, or absolute workspace path is present in this tree.

## What this example is not

- Not a maintained upstream project.
- Not prescriptive policy for your organisation — fill the leaves.
- Not an installer and not `setup.sh`.
- Not a reimplementation of anyone's private documentation system.
