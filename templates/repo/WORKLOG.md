# WORKLOG.md — <project-name>

<!--
Copy to: your repository root, as `WORKLOG.md`.
Template skeleton — templates/repo/WORKLOG.md: the repository's session handover file.
The convention is the four rules in "The convention" below. Keep them; fill "Entries" with
your first entry; delete the guidance when the entries are real.

Why this file exists: every session here starts with whatever the previous session left
behind. Without it, session N re-learns what session N−1 already learned. The log is the
cheapest possible handover — no prose a human would polish, just what a future session
needs: what changed, what was decided, what is open.

AGENTS.md points here; its pointer names only the two actions that make it actionable. The
convention — the four rules below — is stated once, here.
-->

## The convention

1. **Read at session start.** The newest entry is where the previous session ended: what it
   did, what it decided, what it left open.
   **Failure prevented:** a session that starts without it re-derives, from the source tree,
   what the previous session could have stated in one line — every session pays again for
   knowledge that already exists.
2. **Append at session end.** A session that ends without an entry hands nothing to the next
   one; the work is done again or the decision is made again.
   **Failure prevented:** the next session re-learns, by investigation, something this file
   could have named in one line.
3. **Newest entry on top.** The newest entry must be the cheapest to reach, because the
   newest is the one the next session actually needs; a log ordered oldest-first buries the
   useful entry at the bottom of a growing file.
   **Failure prevented:** the most current state being the hardest to find, so sessions skip
   the read that would have saved them.
4. **Never rewrite history.** An old entry is a record of what was believed and decided *at
   the time* — when the decision changes, the change is a new entry, not an edit of the old
   one.
   **Failure prevented:** a log that "always said" whatever is currently true is a log whose
   history cannot be trusted to explain why anything is the way it is; the reasoning behind
   past decisions is lost exactly when a later session needs it to know what not to redo.

<!-- Entry format — newest first; each entry is a dated heading with three lines:
## YYYY-MM-DD — <scope>
- What: <one line, the substance — the diff records detail>
- Decided: <any decision and why — one line>
- Open: <what the next session should pick up, or "none">
-->

## Entries

## <YYYY-MM-DD> — <scope>
- What: <what this session changed, in one line>
- Decided: <decision and the reason, in one line — decisions are why the log exists>
- Open: <what is unfinished, what the next session should pick up first>
