@AGENTS.md

<!--
Copy to: your repository root, as `CLAUDE.md`.
Template skeleton — templates/repo/CLAUDE.md. Claude Code does not read AGENTS.md
natively; it reads CLAUDE.md, and the @AGENTS.md import line above is the documented
bridge that brings the canonical file's content in. This file is deliberately a thin shim:
the import, and nothing else, so that policy exists in exactly one copy.

Add Claude-Code-specific mechanics for this repository below the import if — and only if —
you have some: the names of Claude tools, hooks, or slash commands whose meaning is specific
to this repo. Which line belongs in which file is not decided here; the test that decides,
and why a rule must never live in two files at once, is owned by this guide's
instruction-files chapter: ../../docs/07-instruction-files.md. Links resolve inside this
repository; after copying into your repository they will not — repoint or delete them.

Keep the @AGENTS.md import on the first line: it is the mechanism, and what may sit
beside it is owned by ../../docs/07-instruction-files.md § Pointer mechanisms.
-->

## Claude Code mechanics — <project-name>

TODO: delete this section if this repository has no Claude-Code-only mechanics. If it does,
put them here — a repo-local hook and its trigger point, or a slash command mapping specific to
this project. What belongs here rather than in `AGENTS.md` above is decided by one test, owned by
../../docs/07-instruction-files.md; it is not restated in this file.
