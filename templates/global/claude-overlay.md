# CLAUDE.md — Claude Code overlay

```text
TEMPLATE — Claude Code overlay skeleton
Copy to:      ~/.claude/CLAUDE.md
Adjust:       the @-import line only if your canonical file lives elsewhere;
              links are relative to the template repository — remove or repoint
              them when you copy. Delete this fenced block after copying.
Reasoning:    why overlays carry mechanics only — ../../docs/07-instruction-files.md
Convention:   every Claude-specific rule you add carries a "Failure prevented:"
              line naming the failure it exists to prevent.
```

This overlay carries Claude-Code mechanics only. The import below is what
brings in the policy; what may live here rather than there is decided by the
per-line test owned by `docs/07-instruction-files.md`.

@~/AGENTS.md

**Failure prevented:** a rule restated in this overlay and in the canonical file
diverges the moment one is edited and the other is not — and because this file
reloads on every launch, the copy here is the one that is constantly served
stale.

## Where this loads

Claude Code loads this file (and `~/.claude/rules/`) at session start as your
user-scope memory. Repository-level `CLAUDE.md` files load from the working
directory upward and are concatenated after it. The full load order, and the
approval dialog Claude Code shows for external imports, are in the official
memory documentation — see [09-claude-code.md](../../docs/09-claude-code.md)
for the verified summary.

<!-- Placeholder: add your Claude-specific mechanics below, following the
     shipped sections as examples of the convention. Delete any you do not
     need, and keep every rule's Failure prevented line. -->

## Tools that differ

The native tools this harness exposes that pi does not ship, and any behaviour
that differs from what the canonical file describes. Include the decision
mechanism (`AskUserQuestion` and equivalents) if your setup uses one, and any
subagent, task-list, or plan-mode tooling that shapes how the agent works here.
<!-- Placeholder: name your harness tools and their contracts. -->
**Failure prevented:** an agent reasoning from another harness's tool set
executes the wrong action names and reports success while nothing happened.

## Hook wiring

Only if your setup runs Claude Code hooks: list the **Claude events** they bind
(`PreToolUse`, `PostToolUse`, …), the command that lists them, and the tool
names those events carry. Vendor-neutral denial-handling (do not retry a denied
write under a different command form) belongs in canonical `AGENTS.md`, not here.
<!-- Placeholder: your Claude hook events and tool names. -->
**Failure prevented:** an agent that cannot name the events your hooks bind
cannot tell a hook denial from a tool error, so it debugs the wrong thing or
binds its own guard to an event that never fires — and a gate that never fires is
indistinguishable from no gate at all.

## Plugins and skills

Which Claude plugins and skills are enabled here, and any package that ships
them. (Where a must-have behaviour may live, given that skill loading is
probabilistic, is owned by `docs/05-skills.md`.)
<!-- Placeholder: your enabled plugins, skills, and their sources. -->
**Failure prevented:** an agent that does not know which plugins are enabled
reaches for a capability this project never installed — or assumes a plugin's
tool exists and reports success while the call silently went nowhere.

## Subagent constraints

Claude Code's documented subagent model surface is an Anthropic-family enum
(see `docs/09-claude-code.md`). Custom-gateway pass-through is documented and
unverified here for other vendors. Reviewer *diversity policy* (cross-vendor
bar vs same-vendor review still counting as review) belongs in canonical
`AGENTS.md`, not in this overlay.
<!-- Placeholder: your Claude subagent roster. -->
**Failure prevented:** an agent assumes a delegation can be pointed at another
vendor's model on this harness and configures a reviewer that silently resolves
to the author's own family, so the review looks independent and is not.
