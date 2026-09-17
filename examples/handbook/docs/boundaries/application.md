# Application boundary

**Question this leaf answers:** what are the conventions and repo ownership
for **application** work — product code a user runs?

This is a genericized example leaf, not a real organisation's policy. Copy
the *shape* (one question, one owner, inbound references treated as
load-bearing) and fill in your own conventions.

## What "application" means here

An application repository ships something a person or another service
invokes: a CLI, a library with a documented interface, a small web
handler. In this template the worked example is
[`ordinary-repo`](../../../ordinary-repo/), which ships `tally`.

Application work is **not**:

- a shared platform service that several products consume (that is
  [platform.md](platform.md));
- a cross-cutting handbook (that is this repository);
- a reader's global instruction file (that is tier 1 in
  [`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md)).

## Ownership

| Concern | Owner | Where it lives |
|---|---|---|
| Behaviour of the program | the application repository | that repo's source and `AGENTS.md` |
| Why the repository exists | the application repository | that repo's `INTENT.md` |
| Domain conventions shared by several application repos | this handbook | this leaf |
| Pointer from an application repo into this handbook | machine-stamped block in that repo's `AGENTS.md` | that repo's `AGENTS.md`; the region's ownership rule is owned by [`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md) |

**Failure prevented:** a convention that is true of every application repo
getting copied into each of them, then updated in three and not the
fourth. The fourth copy is the one an agent loads on the day it matters.

## Conventions this example demonstrates

These are *example* conventions so the leaf is not an empty heading. They
are not a recommendation that every application should look like `tally`.

- **The runnable surface is named.** Which command proves an application's
  program works belongs in that repository's own `AGENTS.md`; this leaf's job
  is to point at it, not to restate it.
  **Failure prevented:** a handbook that drifts from the repositories it
  describes — the leaf quietly becomes a second, staler authority.
- **Each repository declares its own wire formats.** Which format a given
  application owns, and the rule for changing it, are in that repository's own
  `AGENTS.md`; this leaf records that the boundary exists, not what the format is.
  **Failure prevented:** a handbook that becomes a second, staler authority on a
  format the owning repository already specifies.
- **Intent is consulted, not amended to fit.** A repository that marks a
  consultation-rule block binds substantive changes to its own `INTENT.md`; the
  rule and its reasoning live in that repository, not here.
  **Failure prevented:** a locally-correct change that violates what the
  repository is for.

Which of the conventions above belong in *this* leaf rather than in a single
repository's own `AGENTS.md` is decided by the tier test owned by
[`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md).

## Inbound references

This leaf's path is load-bearing to **this handbook**, not to the stamped
pointers: those target the index, so a sibling repository never links here
directly. What a leaf move requires — and why it differs from an index move —
is owned by
[`docs/08-cross-cutting-docs.md`](../../../../docs/08-cross-cutting-docs.md).
**Failure prevented:** a "cleanup" rename that leaves the index pointing at a
file that is no longer there — a broken second hop, so a reader following the
pointer arrives at the index and finds the domain gone.

## What this leaf deliberately does not do

- It does not restate the split rule. Link
  [`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md).
- It does not tell the reader how to secure, sandbox, or govern an
  application. That is outside this template's non-goals.
- It does not claim to be installable policy. It is a copyable shape.
