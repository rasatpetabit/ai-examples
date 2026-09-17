# Boundaries index

This index names **what each leaf answers**. It does not restate the
leaf. Follow the link for the conventions and ownership of that domain.

The split between "this repo" and "many repos" — and why a rule must never
live in both an instruction file and a handbook leaf — is owned by the
parent template's instruction-files chapter:
[`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md).
This handbook is the worked example of that chapter's tier-3 pattern.

## What lives here

| Leaf | Question it answers |
|---|---|
| [application.md](application.md) | What are the conventions and repo ownership for **application** work — product code a user runs? |
| [platform.md](platform.md) | What are the conventions and repo ownership for **platform** work — shared services no single product repo owns? |

A leaf that is not in this table is not a boundary this handbook claims. What
adding a domain involves, and what a leaf move or an index move each require, are
owned by
[`docs/08-cross-cutting-docs.md`](../../../../docs/08-cross-cutting-docs.md).
**Failure prevented:** a renamed leaf that still looks current from the
index while its own link 404s.

## Ownership

This handbook repository owns navigation, inventory, and the two domain
leaves. Implementation repositories own their own `AGENTS.md`, source, and
intent. The pointer block in a sibling `AGENTS.md` is a **link**, not a
copy of a leaf. **Failure prevented:** a domain rule drifting into N
hand-maintained copies, one per sibling repo, that then disagree.

A sibling `AGENTS.md` carries a machine-owned region between the two pointer
sentinels. Which bytes belong to the machine and which to humans — and why a
hand edit inside the machine's region is lost on the next stamp — is
[`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md)
§ "Managed blocks and sentinels".

## Inventory

Repository membership — which siblings this handbook knows about, and the
relative path to each — lives in [`inventory.yaml`](../../inventory.yaml).
That file is JSON-compatible YAML so the standard library can parse it.
It is the input a stamper would iterate; this example's stamper is
invoked per-repo instead, which is the honest smallest version.

## Generated versus hand-written

Which files in *this* handbook are machine-touched, and which are not:

| File or region | Machine-touched? |
|---|---|
| Sibling `AGENTS.md` between the pointer sentinels | yes — written by `tools/stamp-pointers.py` |
| This index, the two leaves, `AGENTS.md`, `README.md`, `inventory.yaml`, the stamper | no — edit directly |

The ownership principle behind that split, and why a hand edit inside a
machine-owned region is lost, are owned by
[`docs/07-instruction-files.md`](../../../../docs/07-instruction-files.md).
