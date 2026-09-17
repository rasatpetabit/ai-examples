# CLAUDE.md (home root — pointer only)

```text
TEMPLATE — home-root pointer file
Copy to:      ~/CLAUDE.md
Adjust:       the two paths below, only if your canonical file or your Claude
              Code overlay live elsewhere. Links are relative to the template
              repository — remove them when you copy. Delete this fenced block
              after copying.
Reasoning:    why this file exists at all — ../../docs/07-instruction-files.md
```

This path is **not** the Claude Code global instructions file. It exists only
because harnesses read instruction files by walking up from the working
directory, which makes a file at your home directory root load for every session
started anywhere beneath it. A pointer here turns that accident into a signpost;
policy here would turn it into a trap.

- **Claude Code global instructions:** `~/.claude/CLAUDE.md` — the real overlay.
  It imports the canonical file with a single line, `@~/AGENTS.md`, and holds
  only Claude-specific mechanics below the import.
- **Canonical global policy:** `~/AGENTS.md` — the vendor-neutral policy file;
  pi loads it directly, and Claude Code reaches it through the `~/.claude/CLAUDE.md`
  import above.
- **Per-repo instructions:** the `AGENTS.md` at each repository root, with a
  one-line `CLAUDE.md` shim beside it that reads `@AGENTS.md` and imports that
  repository's own canonical file from the same directory.

Do not add policy here. Policy added to this file loads only for sessions
started under your home directory — Claude Code concatenates every `CLAUDE.md`
it finds from the working directory upward. How *other* harnesses discover
`AGENTS.md` is documented in the canonical file, not here. A half-loading copy
drifts from the canonical the moment you edit one and not the other, and its
length is a recurring per-turn cost for every session that does load it — see
[01-mental-model.md](../../docs/01-mental-model.md) for why instruction-file
length is a per-turn cost, not a one-time one.

**Failure prevented:** an edit lands here because `~/CLAUDE.md` is the natural
first guess for "the global CLAUDE.md"; it then half-works — loading for some
sessions and not others — instead of failing visibly, which is the hardest kind
of misconfiguration to notice.

Two deliberate absences:

- This file contains no import. The canonical already reaches Claude Code through
  `~/.claude/CLAUDE.md`, and a second import here would expand the same content
  twice for every session started under your home directory — nothing in the
  documented import behaviour deduplicates one target imported from two files.
- Every import form above appears inside code spans, which Claude Code's import
  parser skips. A pointer file must stay inert wherever it is read, including
  inside a repository that ships it as a template.
