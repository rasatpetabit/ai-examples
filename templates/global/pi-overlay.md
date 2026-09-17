# Global pi instructions (overlay)

```text
TEMPLATE — pi overlay skeleton
Copy to:      ~/.pi/agent/AGENTS.md
Adjust:       if your canonical policy lives at `~/AGENTS.md`, the first line
              after this header must be a one-line prose pointer telling the
              model to treat `~/AGENTS.md` as policy, with the mechanics below
              it — see the copy-destinations table in
              ../../docs/07-instruction-files.md. If this very path IS your
              canonical file, keep the mechanics and skip the pointer. Links
              are relative to the template repository — remove or repoint them
              when you copy. Delete this fenced block after copying.
Reasoning:    why overlays carry mechanics only — ../../docs/07-instruction-files.md
Convention:   every pi-specific rule you add carries a "Failure prevented:" line
              naming the failure it exists to prevent.
```

Pi-specific mechanics only. The canonical file is the single source of policy.
pi loads the global file first, then every parent directory walking up from the
working directory (the order, and the per-directory filename precedence, are
stated once in `docs/07-instruction-files.md`). `~/AGENTS.md` is therefore in
context **only when some ancestor of the working directory is your home
directory**. A session working in a checkout outside your home tree does **not**
see it via that walk. Do not assume the canonical is already loaded there; see
`docs/07-instruction-files.md` for how to compose this overlay with the
canonical without overwriting it.

**Failure prevented:** a rule restated here and in the canonical file
diverges the moment one is edited and the other is not — and pi loads both on
the same session, so the stale copy is not skipped, it is served.

## How the canonical reaches pi

Orientation only; the loading mechanisms live in
[07-instruction-files.md](../../docs/07-instruction-files.md) and in the
canonical's own "How this file reaches each harness" section — nothing here
restates them.

If cwd is not under your home directory, the ancestor walk cannot reach
`~/AGENTS.md`. Options that do not depend on cwd: (1) put a prose pointer at
`~/.pi/agent/AGENTS.md` (never a hand-maintained second copy of the canonical —
see `docs/07-instruction-files.md`); (2) symlink
`~/.pi/agent/APPEND_SYSTEM.md` at the canonical — a **trusted** project's own
`.pi/APPEND_SYSTEM.md` replaces the global append rather than adding to it, so a
project file can silently drop the append you configured. (Upstream names
`.pi/APPEND_SYSTEM.md` and `~/.pi/agent/APPEND_SYSTEM.md` as the two locations for
one append setting, and lists the project one as a trust-gated resource; that the
project file wins over the global is the observed behaviour of that arrangement.)

**Failure prevented:** the global append silently stops applying. A trusted
project that ships its own `.pi/APPEND_SYSTEM.md` replaces the global one rather
than adding to it, so the canonical policy you symlinked in is simply absent —
and nothing in the session reports that the file you configured was not read.

<!-- Placeholder: add your pi-specific mechanics below, following the shipped
     sections as examples. Delete any you do not need, keep every rule's
     Failure prevented line. -->

## Package-provided tools

Only if your install adds tools beyond pi's built-ins (`read`, `write`, `edit`,
`bash`, plus the other built-ins listed in pi's own README — the current list is
always what pi's documentation reports): which packages add which tools, and
where their behaviour differs from the built-ins. When a package entry in
settings uses the object form, an empty list (`"extensions": []`) loads *none*
of that type from the package — record where you have filtered a package
deliberately, or the next session will wonder why a named tool never works.
<!-- Placeholder: your installed packages and their tools. -->
**Failure prevented:** an agent calls a tool that came from a package you have
not installed on another machine, or that your own filter disabled, and reports
success while nothing happened.

## Skills here

Which skills are installed for pi, where they load from, and any invocation
convention your team uses. (Where a must-have behaviour may live, given that
skill loading is probabilistic, is owned by `docs/05-skills.md`.)
<!-- Placeholder: your skill locations and conventions. -->
**Failure prevented:** an agent that does not know where this install's skills
live invents an invocation the loader does not recognise, so a skill the team
relies on is never reached and nothing reports that it was skipped.

## Extension and tool quirks

Any nonstandard build or patched behaviour your pi has that a fresh upstream
install would not: say so here, because an agent reading generic pi
documentation will otherwise reason from defaults your install does not have.
<!-- Placeholder: your quirks, or delete this section. -->
**Failure prevented:** an agent applies generic pi defaults to your nonstandard
build and "fixes" configuration that was deliberately different.
