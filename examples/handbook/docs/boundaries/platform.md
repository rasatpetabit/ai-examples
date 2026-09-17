# Platform boundary

**Question this leaf answers:** what are the conventions and repo ownership
for **platform** work — shared services no single product repo owns?

This is a genericized example leaf. There is no real platform service in
this template; the leaf exists so the index has a second domain to name,
and so a reader can see how two leaves sit behind one index without either
leaf duplicating the other.

## What "platform" means here

A platform concern is true of **more than one application repository** and
belongs to none of them: a shared authentication convention, a logging
shape, a "how we name environment variables" rule, a runbook for a service
several products call. If only one repository needs it, it is not
platform — it is that repository's `AGENTS.md`.

Platform work is **not**:

- the behaviour of a single product (that is [application.md](application.md));
- a reader's personal global policy (tier 1);
- a restatement of the split rule (that chapter already exists).

## Ownership

| Concern | Owner | Where it lives |
|---|---|---|
| A shared convention several application repos must follow | this handbook | this leaf (or a future leaf this index names) |
| Implementation of a shared service | a dedicated platform repository, if you have one | that repo, linked from this leaf |
| Pointer from an application repo into this handbook | machine-stamped block | sentinels in that repo's `AGENTS.md` |

**Failure prevented:** a shared convention living in the first application
repo that happened to need it, so the second application repo's agent
never sees it and invents a conflicting one.

## Conventions this example demonstrates

These are invented so the leaf has substance. Replace them with yours.

- **Names are stable once published.** A platform identifier that appears
  in more than one repository is an inbound reference. Renaming it is a
  migration, not a tidy-up.
  **Failure prevented:** a rename that looks local and breaks every
  consumer the author did not have open.
- **Runbooks live here, not in each consumer.** If three application repos
  would otherwise paste the same "how to talk to X" section, that section
  is a platform leaf, and each consumer links to it.
  **Failure prevented:** copy 2 of 3 drifting, and an agent loading the
  stale copy because it was standing in that repo.
- **Absence is explicit.** If this organisation has *no* shared platform
  service yet, say so in this leaf rather than leaving it empty. An empty
  leaf reads as "we forgot", not as "nothing belongs here".
  **Failure prevented:** a future author filling the silence with a
  convention that was never agreed.

This template's ordinary example has no platform dependency — `tally`
talks to no shared service. That is a deliberate gap in the *example
product*, not a claim that platform never exists. When you copy this
tree, this is the leaf you fill first if you actually have shared
services.

## Inbound references

Same load-bearing rule as [application.md](application.md): the index names this
file, and stamped pointers target the index. What a leaf move requires is owned
by [`docs/08-cross-cutting-docs.md`](../../../../docs/08-cross-cutting-docs.md).
**Failure prevented:** a leaf that is current in git history and 404 from
every working tree that still points at the old path.

## What this leaf deliberately does not do

- It does not describe a real internal platform, service, hostname, or
  tool. Those are the private specifics this template is forbidden to
  leak.
- It does not restate instruction-file policy.
  [`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md)
  owns that.
- It is not a security or compliance guide.
