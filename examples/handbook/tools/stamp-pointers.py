#!/usr/bin/env python3
"""stamp-pointers.py — inject/refresh a handbook pointer block between sentinels.

CLI:
    python3 stamp-pointers.py --repo <ordinary-root> --handbook <handbook-root>
    python3 stamp-pointers.py --self-test --ordinary-repo <ordinary-root>

The managed block is a PREFIX of the target AGENTS.md: the start sentinel must be
the file's first line and the end sentinel a standalone line after it, and exactly
one of each must occur. Everything after the end sentinel is preserved verbatim.
Anchoring the block at byte zero is what makes the tool's safety property decidable
without parsing Markdown — see docs/08-cross-cutting-docs.md for why the alternative
was abandoned.

Derive the relative link from the two supplied roots. Never scan home, never
discover repos, never write outside the supplied --repo path.

Status: 0 on success (including unchanged); 1 on validation/usage errors;
2 on I/O errors. Status 0 for both first-run `changed` and second-run
`unchanged`.

This is an example utility, not an installer. It never writes the reader's
home configuration.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import sys
import tempfile
import urllib.parse

PROG = "stamp-pointers.py"
START = "<!-- handbook-pointer:start -->"
END = "<!-- handbook-pointer:end -->"
TARGET_REL = "AGENTS.md"
INDEX_REL = os.path.join("docs", "boundaries", "index.md")

# Portable bound independent of host PATH length. Relative links stay short.
MAX_LINK_CHARS = 4096


def _silence(stream_name):
    """Point a stream at /dev/null so CPython's shutdown flush cannot fail.

    Redirecting only stdout is not enough: when stderr is the stream that failed, the
    interpreter's own flush of stderr produces exit 120 — a status this tool never
    documents. Both streams are handled the same way.
    """
    try:
        stream = getattr(sys, stream_name)
        if stream is None:
            return
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stream.fileno())
        os.close(devnull)
    except (OSError, ValueError, AttributeError):
        pass


def fail(message, code=1):
    """Report a problem and exit with the documented status.

    The write is guarded: a diagnostic that cannot be written — a full disk, a closed
    stderr — must not turn the exit status into whatever CPython's shutdown flush
    produces. The status the caller sees is the one chosen here.
    """
    if sys.stderr is None:
        _silence("stderr")
        _silence("stdout")
        sys.exit(2)
    try:
        sys.stderr.write(f"{PROG}: {message}\n")
        sys.stderr.flush()
    except (BrokenPipeError, OSError):
        # Undeliverable diagnostic: the caller received no verdict, so report an I/O
        # error rather than the code that would have described the problem.
        _silence("stderr")
        _silence("stdout")
        sys.exit(2)
    if not _stdout_usable():
        # The diagnostic was written, but stdout is not a destination this run could
        # ever report to (/dev/full, or closed before startup). Nothing reaches the
        # caller, so the status is an I/O error rather than the validation code.
        _silence("stderr")
        _silence("stdout")
        sys.exit(2)
    sys.exit(code)


def require_dir(path, flag):
    if not path:
        fail(f"{flag} is required")
    if not os.path.isdir(path):
        fail(f"{flag} is not a directory: {path}")
    return os.path.realpath(path)


def require_contained(path, root, what):
    """Resolve path and refuse it if it escapes root, following symlinks.

    A symlinked target would otherwise let a stamp read or write a file outside
    the two roots the caller supplied, which is exactly the boundary this tool
    promises to respect.
    """
    real = os.path.realpath(path)
    if real != root and not real.startswith(root + os.sep):
        fail(f"{what} resolves outside the supplied root, refusing: {path}")
    return real


def posix_relpath(from_dir, to_path):
    """Relative path from from_dir to to_path, POSIX separators, no leading ./.

    Each path component is percent-encoded for use inside a Markdown link
target. A raw '#', '?' or '%' in a directory name would otherwise be read as a
fragment, query or escape by the renderer, so a link that looks correct would
not resolve. Encoded components are still valid relative filesystem paths for
every consumer that resolves the link.
    """
    rel = os.path.relpath(to_path, start=from_dir)
    rel = rel.replace(os.sep, "/")
    if rel.startswith("/"):
        fail(f"derived link is absolute, refusing: {rel}")
    rel = "/".join(
        urllib.parse.quote(part, safe="") if part not in (".", "..") else part
        for part in rel.split("/")
    )
    if len(rel) > MAX_LINK_CHARS:
        fail(f"derived link exceeds {MAX_LINK_CHARS} characters")
    return rel


def _terminator_after(text, pos):
    """Return (terminator, next_pos) for the line ending at pos, or (None, pos).

    A lone CR at EOF is NOT a terminator here; it is content, and the splice must
    preserve it verbatim rather than silently dropping it.
    """
    if text.startswith("\r\n", pos):
        return "\r\n", pos + 2
    if text.startswith("\n", pos):
        return "\n", pos + 1
    if pos == len(text):
        return "", pos
    return None, pos


def parse_block(text):
    """Return (value_start, terminator, end_offset) or an error string.

    The block is a PREFIX: START is the first line and END is a standalone line
    after it, exactly once each. That is the whole contract, and it is decidable by
    inspection — nothing precedes the block, so the START marker cannot be inside a
    fence, a span, or an element.

    This is a LEXICAL ownership contract, not a renderer-aware one. Once START is the
    first line, everything up to END belongs to the tool whatever it contains; an END
    that a renderer would place inside a fence still ends the block. What prefix
    placement buys is that the tool never has to decide whether a candidate marker is
    code — the question that could not be answered safely without a full parser.

    Offsets are returned rather than line indices so the caller can preserve the exact
    bytes after END, including a lone CR and the absence of a trailing newline.
    """
    searchable = text.replace("\r\n", "\n")
    if START not in searchable and END not in searchable:
        return "missing sentinels (need exactly one ordered start/end pair)"
    total_start = searchable.count(START)
    total_end = searchable.count(END)
    if total_start != 1 or total_end != 1:
        return (
            f"the file mentions a marker {total_start} time(s) as start and "
            f"{total_end} time(s) as end; the block is delimited by exactly one of "
            "each — refusing to stamp"
        )
    if not text.startswith(START):
        first = text.split("\n", 1)[0][:60]
        return (
            f"the start marker is not the first line of the file (line 1 is "
            f"{first!r}); a managed block is a prefix, and this tool will not infer "
            "which marker in a document is the real one — refusing to stamp"
        )
    terminator, value_start = _terminator_after(text, len(START))
    if terminator is None:
        return (
            "the start marker is not alone on its first line (trailing content "
            "follows it); refusing to stamp"
        )
    m = re.search(r"(?m)^" + re.escape(END) + r"\r?$", text[value_start:])
    if m is None:
        return "the end marker is not a standalone line after the start marker; refusing to stamp"
    return (value_start, terminator, value_start + m.start())


def build_body(link):
    """The generated content only — markers are composed by the caller."""
    return f"- [Boundaries index]({link})"


def build_block(link, terminator="\n"):
    """Bytes from START through END. The block's own newline sits INSIDE the pair,
    so no byte outside the sentinels is ever added or removed."""
    return f"{START}{terminator}{build_body(link).replace(chr(10), terminator)}{terminator}{END}"


def stamp(repo_root, handbook_root, *, dry_run=False):
    repo_root = require_dir(repo_root, "--repo")
    handbook_root = require_dir(handbook_root, "--handbook")
    target = os.path.join(repo_root, TARGET_REL)
    index = os.path.join(handbook_root, INDEX_REL)
    if not os.path.isfile(target):
        fail(f"target does not exist: {target}")
    if not os.path.isfile(index):
        fail(f"handbook index does not exist: {index}")
    require_contained(target, repo_root, "target file")
    require_contained(index, handbook_root, "handbook index")
    try:
        with open(target, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        fail(str(exc), 2)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{target} is not valid UTF-8: {exc}")
    span = parse_block(text)
    if isinstance(span, str):
        fail(span)
    value_start, terminator, end_offset = span
    link = posix_relpath(os.path.dirname(target), index)
    body = build_body(link).replace("\n", terminator) if terminator else build_body(link)
    # Splice by LINE, keeping the original line terminator of the END line. An
    # earlier byte-offset version had to reason about whether a trailing newline
    # was inside or outside the span, and got it wrong at EOF, appending a byte.
    # Here the bytes after the marker on its own line are carried over verbatim:
    # a mid-file END keeps its "\n", an END that is the last line keeps nothing.
    # Everything after the END marker is carried over EXACTLY, with no
    # reinterpretation of its line ending: rebuilding the tail by re-joining lines
    # discarded a lone CR at EOF, a byte outside the sentinel pair, by the one
    # operation whose contract is to preserve it.
    tail = text[end_offset + len(END):]
    new_text = START + terminator + body + terminator + END + tail
    if new_text == text:
        return emit("unchanged\n")
    if dry_run:
        return emit("changed\n")
    # Safe replacement: write a sibling tempfile, then os.replace. The target's
    # mode is captured BEFORE the swap and re-applied after it: mkstemp creates
    # 0600, so a naive replace would silently strip group/other read from a file
    # that had it, and git does not track that change.
    directory = os.path.dirname(target)
    try:
        prior_mode = stat.S_IMODE(os.stat(target).st_mode)
    except OSError as exc:
        fail(str(exc), 2)
    # mkstemp is INSIDE the try: creating the tempfile is an I/O operation like any
    # other, and leaving it outside meant a permission or space failure escaped as a
    # traceback instead of the documented status 2.
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix=".stamp-", suffix=".tmp", dir=directory)
        with os.fdopen(fd, "wb") as handle:
            handle.write(new_text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, prior_mode)
        os.replace(tmp_path, target)
        tmp_path = None  # consumed by the replace; nothing to clean up
    except OSError as exc:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        fail(str(exc), 2)
    return emit("changed\n")


def emit(line):
    """Write a status line to stdout, honouring the documented status contract.

    Every stdout write goes through here. Writing directly left the tool exiting 120 —
    an undocumented status produced by CPython flushing stdout again at interpreter
    shutdown — and worse, on the changed path the file had already been replaced, so
    the caller saw a failure status for work that had succeeded.

    Returns 0 on success and on a broken pipe (the reader went away, which is how a
    pager behaves), and 2 on any other write failure — the documented I/O status. It
    deliberately does NOT exit: the self-test prints progress before each assertion, so
    exiting here on a closed reader would skip the checks that follow and certify a
    defective tool. Callers map the result to their own exit status. The descriptor is
    redirected to /dev/null on failure so the shutdown flush cannot overwrite it.
    """
    if sys.stdout is None:
        # A descriptor closed before startup (`1>&-`) leaves sys.stdout as None, not
        # as a stream that raises. Writing to it produced an AttributeError traceback
        # and status 1 — validation-failure status for an I/O failure.
        _silence("stderr")
        _WRITE_FAILED[0] = 2
        return 2
    try:
        sys.stdout.write(line)
        sys.stdout.flush()
        return 0
    except BrokenPipeError:
        _redirect_stdout_to_devnull()
        return 0
    except OSError:
        _redirect_stdout_to_devnull()
        _WRITE_FAILED[0] = 2
        return 2


def _stdout_usable():
    """True when stdout can actually receive bytes.

    Deliberately SILENT: the self-test asserts that a refusal prints nothing on stdout,
    so this cannot write a probe byte. It forces a real syscall on the descriptor
    instead -- an explicit flush after an empty write, plus a zero-length os.write --
    which fails on a closed descriptor and (measured on Linux, ENOSPC) on a full one. A
    kernel that treats a zero-length write as a pure no-op would make this optimistic;
    that is a known limit of a silent probe, stated rather than assumed away.
    """
    if sys.stdout is None:
        return False
    try:
        sys.stdout.write("")
        sys.stdout.flush()
        os.write(1, b"")
    except (BrokenPipeError, OSError, ValueError, AttributeError):
        return False
    return True


def _redirect_stdout_to_devnull():
    _silence("stdout")


# Set to 2 when any report line could not be written. The self-test's intermediate
# progress lines return their own status to nobody, so the failure is remembered here
# and folded into the final exit status.
_WRITE_FAILED = [0]


def _report(message):
    """Write a diagnostic to stderr without letting a write failure change the status.

    Used by the self-test's own reporting. A full disk or a closed stderr must not turn
    a deliberate failure into whatever CPython's shutdown flush produces.
    """
    try:
        sys.stderr.write(f"{PROG}: {message}\n")
        sys.stderr.flush()
    except (BrokenPipeError, OSError):
        _silence("stderr")
        _silence("stdout")


def _check(cond, message):
    if not cond:
        _report(f"FAIL: {message}")
        sys.exit(1)


def _run_cli(repo, handbook):
    """Invoke this file as a subprocess so the self-test exercises the real CLI."""
    import subprocess

    cmd = [
        sys.executable,
        os.path.abspath(__file__),
        "--repo",
        repo,
        "--handbook",
        handbook,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True)
    except OSError as exc:
        # Launching the child is an I/O operation: exhausting the descriptor table or
        # the process table is an operational error, not a validation failure. An
        # unguarded call surfaced it as a traceback and exit 120.
        fail(f"cannot run the tool under test: {exc}", 2)
    out = result.stdout.decode("utf-8")
    err = result.stderr.decode("utf-8")
    return result.returncode, out, err


def self_test(ordinary_repo):
    """Run the explicit case table. Any deviation is a failure.

    Every case states its fixture bytes, the exact expected exit status, a substring
    the diagnostic must contain (or None), and whether bytes may change. Assertions
    compare whole files and reject tracebacks: an earlier version accepted any
    nonzero exit as a successful refusal, so a crashing tool looked like a careful
    one.
    """
    ordinary_repo = require_dir(ordinary_repo, "--ordinary-repo")
    source_agents = os.path.join(ordinary_repo, TARGET_REL)
    if not os.path.isfile(source_agents):
        fail(f"--ordinary-repo has no {TARGET_REL}: {source_agents}")
    handbook_src = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))
    index_src = os.path.join(handbook_src, INDEX_REL)
    if not os.path.isfile(index_src):
        fail(f"handbook index missing at {index_src} — cannot self-test an empty tree")

    # Building the fixtures is I/O, and it runs before any case does. Leaving it
    # unguarded meant descriptor exhaustion surfaced as a traceback and exit 120 —
    # an I/O failure misreported as a validation failure, which is exactly the
    # distinction the documented statuses exist to make.
    try:
        tmp = tempfile.mkdtemp(prefix="stamp-self-test-")
        copy_repo = os.path.join(tmp, "ordinary-repo")
        copy_handbook = os.path.join(tmp, "handbook")
        os.makedirs(copy_repo)
        os.makedirs(os.path.join(copy_handbook, "docs", "boundaries"))
        shutil.copy2(index_src, os.path.join(copy_handbook, INDEX_REL))
    except OSError as exc:
        fail(f"cannot build the self-test fixtures: {exc}", 2)
    executed = 0
    try:
        target = os.path.join(copy_repo, TARGET_REL)
        # The expected block is written out INDEPENDENTLY of build_body/build_block.
        # Deriving the expectation from the same helper the tool uses made the oracle
        # circular: a mutation that emitted a broken link still passed every case.
        expected_link = "../handbook/docs/boundaries/index.md"
        link = posix_relpath(os.path.dirname(target), os.path.join(copy_handbook, INDEX_REL))
        _check(link == expected_link,
               f"relative link is {link!r}, expected {expected_link!r}")
        # ...and the link must actually resolve to the index the tool was handed.
        resolved = os.path.normpath(os.path.join(os.path.dirname(target), link))
        _check(os.path.isfile(resolved),
               f"generated link does not resolve to a real index: {resolved}")
        block = f"{START}\n- [Boundaries index]({expected_link})\n{END}"

        # --- prefix contract: init, refresh, idempotence, preservation -------------
        NO_CHANGE = "\x00no-change\x00"  # expected final bytes: same as fixture, status 0
        body = "\n# Repository instructions\n\nHuman prose that must survive.\n"
        initialized = block + body
        cases = [
            # (name, fixture bytes, expected status, diagnostic substring or None,
            #  expected final bytes or None to require "unchanged")
            ("init", START + "\n" + END + body, 0, None, initialized),
            ("refresh", START + "\nSTALE\n" + END + body, 0, None, initialized),
            ("idempotent", initialized, 0, None, NO_CHANGE),
            ("eof-end-marker", START + "\n" + END, 0, None, block),
            ("utf8-prose", START + "\n" + END + "\n# Caf\u00e9 \u2014 \u00fcber\n",
             0, None, block + "\n# Caf\u00e9 \u2014 \u00fcber\n"),
            ("crlf-prose", START + "\r\n" + END + "\r\n# after\r\n", 0, None,
             block.replace("\n", "\r\n") + "\r\n# after\r\n"),
            ("crlf-no-trailing-newline", START + "\r\n" + END, 0, None,
             block.replace("\n", "\r\n")),
            # A lone CR at EOF is CONTENT, not a terminator. Rebuilding the tail by
            # re-joining lines silently deleted it — a byte outside the sentinel pair,
            # lost by the one operation whose contract is to preserve such bytes.
            ("lone-cr-at-eof", START + "\n" + END + "\r", 0, None, block + "\r"),
            ("empty-tail-with-newline", START + "\n" + END + "\n", 0, None, block + "\n"),
            # --- refusals: no marker, wrong position, ambiguity, malformed ---------
            ("empty-file", "", 1, "missing sentinels", None),
            ("no-markers", "# Just prose.\n", 1, "missing sentinels", None),
            ("start-not-first", "# Heading first\n" + START + "\n" + END + "\n", 1,
             "not the first line", None),
            ("indented-start", " " + START + "\n" + END + "\n", 1, "not the first line", None),
            ("fenced-only", "```\n" + START + "\n" + END + "\n```\n", 1, "not the first line", None),
            ("inline-only", "Example: `" + START + " " + END + "`\n", 1, "not the first line", None),
            ("duplicate-start", START + "\n" + START + "\n" + END + "\n", 1,
             "mentions a marker", None),
            ("duplicate-end", START + "\n" + END + "\n" + END + "\n", 1,
             "mentions a marker", None),
            ("quoted-example-plus-live", START + "\n" + END + "\nSyntax: `" + START + "`\n",
             1, "mentions a marker", None),
            ("end-before-start", END + "\n" + START + "\n", 1, "not the first line", None),
            ("missing-end", START + "\nbody\n", 1, "mentions a marker", None),
            ("end-not-standalone", START + "\n" + END + " trailing\n", 1,
             "not a standalone line", None),
            ("start-not-alone", START + " trailing\n" + END + "\n", 1,
             "not alone on its first line", None),
        ]
        for name, fixture, want_status, want_msg, want_bytes in cases:
            with open(target, "wb") as handle:
                handle.write(fixture.encode("utf-8"))
            with open(target, "rb") as handle:
                before = handle.read()
            rc, out, err = _run_cli(copy_repo, copy_handbook)
            executed += 1
            emit(
                f"self-test {name}: status={rc} stdout={out!r} stderr={err!r}\n"
            )
            _check("Traceback" not in err, f"{name}: the tool crashed: {err!r}")
            _check(rc == want_status, f"{name}: exited {rc}, expected {want_status}")
            if want_msg is not None:
                _check(want_msg in err, f"{name}: stderr missing {want_msg!r}: {err!r}")
            with open(target, "rb") as handle:
                after = handle.read()
            if want_bytes is None:
                # A refusal: bytes identical, and stdout says nothing was written.
                _check(after == before, f"{name}: bytes changed but should not have")
                _check(out == "", f"{name}: a refusal printed {out!r} on stdout")
            elif want_bytes is NO_CHANGE:
                _check(after == before, f"{name}: bytes changed but should not have")
                _check(out == "unchanged\n", f"{name}: stdout {out!r}, expected unchanged")
            else:
                _check(after == want_bytes.encode("utf-8"),
                       f"{name}: final bytes wrong.\n  got      {after!r}\n  expected {want_bytes.encode('utf-8')!r}")
                expected_out = "unchanged\n" if after == before else "changed\n"
                _check(out == expected_out,
                       f"{name}: stdout {out!r}, expected {expected_out!r}")

        # Idempotence is a property of a SETTLED file, so this runs on the stamped
        # fixture rather than on whichever case happened to run last (the final case
        # is deliberately malformed, and re-running it would only re-test refusal).
        # A real first-output-to-second-input sequence: run once from a stale
        # fixture, capture the bytes the tool produced, then run again over exactly
        # those bytes and require the file, mode, status and diagnostics to be
        # unchanged. Asserting only on stdout would pass over a tool that rewrote
        # its own correct output.
        with open(target, "wb") as handle:
            handle.write((START + "\nSTALE\n" + END + body).encode("utf-8"))
        rc_a, out_a, err_a = _run_cli(copy_repo, copy_handbook)
        with open(target, "rb") as handle:
            after_first = handle.read()
        mode_first = stat.S_IMODE(os.stat(target).st_mode)
        rc, out, err = _run_cli(copy_repo, copy_handbook)
        executed += 1
        emit(f"self-test second-run: status={rc} stdout={out!r} stderr={err!r}\n")
        with open(target, "rb") as handle:
            after_second = handle.read()
        _check("Traceback" not in err_a + err, "repeat-after-refresh crashed")
        _check(rc_a == 0 and out_a == "changed\n", f"first run: {rc_a} {out_a!r} {err_a!r}")
        _check(rc == 0, f"second run exited {rc}, expected 0")
        _check(out == "unchanged\n", f"second run printed {out!r}, expected unchanged")
        _check(after_second == after_first,
               "second run changed complete file bytes")
        _check(stat.S_IMODE(os.stat(target).st_mode) == mode_first,
               "second run changed the file mode")
        _check(err == "", f"second run wrote to stderr: {err!r}")

        # --- containment and mode -------------------------------------------------
        escape_dir = os.path.join(tmp, "escape")
        os.makedirs(escape_dir)
        outside = os.path.join(tmp, "outside-agents.md")
        with open(outside, "wb") as handle:
            handle.write((START + "\n" + END + "\n").encode("utf-8"))
        os.symlink(outside, os.path.join(escape_dir, TARGET_REL))
        rc, out, err = _run_cli(escape_dir, copy_handbook)
        executed += 1
        emit(f"self-test symlink-escape: status={rc} stderr={err!r}\n")
        _check("Traceback" not in err, f"symlink-escape crashed: {err!r}")
        _check(rc == 1, f"symlink-escape exited {rc}, expected 1")
        _check("resolves outside the supplied root" in err,
               f"symlink-escape did not report containment: {err!r}")
        _check(out == "", f"symlink-escape printed {out!r} on stdout")
        with open(outside, "rb") as handle:
            _check(handle.read() == (START + "\n" + END + "\n").encode("utf-8"),
                   "symlink-escape target was modified")

        mode_target = os.path.join(copy_repo, TARGET_REL)
        mode_fixture = START + "\n" + END + "\n"
        with open(mode_target, "wb") as handle:
            handle.write(mode_fixture.encode("utf-8"))
        os.chmod(mode_target, 0o644)
        rc, out, err = _run_cli(copy_repo, copy_handbook)
        executed += 1
        emit(f"self-test mode-preserved: status={rc} stdout={out!r} stderr={err!r}\n")
        _check("Traceback" not in err, f"mode case crashed: {err!r}")
        _check(rc == 0, f"mode case exited {rc}, expected 0")
        # A no-op would leave the pre-existing 0644 in place and look like success, so
        # assert the replacement actually happened before trusting the mode.
        _check(out == "changed\n", f"mode case printed {out!r}, expected changed")
        with open(mode_target, "rb") as handle:
            _check(handle.read() == (block + "\n").encode("utf-8"),
                   "mode case did not write the expected block")
        _check(stat.S_IMODE(os.stat(mode_target).st_mode) == 0o644,
               "replacement did not preserve the target's mode")

        # Mode preservation is only proven by a mode the tool could get wrong on its
        # own: mkstemp creates 0600, so a source of 0600 would hide a failure to
        # re-apply. 0640 is neither the source default nor the tempfile default.
        private_target = os.path.join(copy_repo, TARGET_REL)
        with open(private_target, "wb") as handle:
            handle.write((START + "\n" + END + "\n").encode("utf-8"))
        os.chmod(private_target, 0o640)
        rc, out, err = _run_cli(copy_repo, copy_handbook)
        executed += 1
        emit(f"self-test mode-0640: status={rc} stdout={out!r} stderr={err!r}\n")
        _check("Traceback" not in err, f"mode-0640 crashed: {err!r}")
        _check(out == "changed\n", f"mode-0640 printed {out!r}, expected changed")
        _check(stat.S_IMODE(os.stat(private_target).st_mode) == 0o640,
               "a 0640 target did not keep 0640 after replacement")

        # The handbook root is contained exactly like the target: a symlinked index
        # escaping --handbook must be refused. Only the target was checked before.
        escaping_handbook = os.path.join(tmp, "escaping-handbook")
        os.makedirs(os.path.join(escaping_handbook, "docs", "boundaries"))
        real_index = os.path.join(tmp, "real-index.md")
        with open(real_index, "wb") as handle:
            handle.write(b"# index\n")
        os.symlink(real_index, os.path.join(escaping_handbook, INDEX_REL))
        contained_repo = os.path.join(tmp, "contained-repo")
        os.makedirs(contained_repo)
        with open(os.path.join(contained_repo, TARGET_REL), "wb") as handle:
            handle.write((START + "\n" + END + "\n").encode("utf-8"))
        rc, out, err = _run_cli(contained_repo, escaping_handbook)
        executed += 1
        emit(f"self-test handbook-escape: status={rc} stdout={out!r} stderr={err!r}\n")
        _check("Traceback" not in err, f"handbook-escape crashed: {err!r}")
        _check(rc == 1, f"handbook-escape exited {rc}, expected 1")
        _check("resolves outside the supplied root" in err,
               f"handbook-escape did not report containment: {err!r}")

        # A '#' in a root name must be percent-encoded, or the link silently breaks.
        odd_root = os.path.join(tmp, "hand#book")
        os.makedirs(os.path.join(odd_root, "docs", "boundaries"))
        shutil.copy2(index_src, os.path.join(odd_root, INDEX_REL))
        odd_repo = os.path.join(tmp, "odd-repo")
        os.makedirs(odd_repo)
        with open(os.path.join(odd_repo, TARGET_REL), "wb") as handle:
            handle.write((START + "\n" + END + "\n").encode("utf-8"))
        rc, out, err = _run_cli(odd_repo, odd_root)
        executed += 1
        with open(os.path.join(odd_repo, TARGET_REL), "rb") as handle:
            odd_bytes = handle.read().decode("utf-8")
        emit(f"self-test percent-encoded-link: status={rc}\n")
        _check(rc == 0, f"percent-encoded-link exited {rc}: {err!r}")
        _check("%23book" in odd_bytes,
               f"a '#' in a root name was not percent-encoded: {odd_bytes!r}")
        _check(os.path.isfile(os.path.join(odd_repo, "..", "hand#book", "docs", "boundaries", "index.md")),
               "the encoded link does not resolve to the real index")

        _check(executed > 0, "no self-test cases ran")

        cleanup_ok = True
        try:
            shutil.rmtree(tmp)
        except OSError as exc:
            cleanup_ok = False
            # Routed through the guarded reporter: writing stderr directly here could
            # itself fail, and an unguarded failure at this point yields exit 120.
            _report(f"self-test: could not remove temporary tree {tmp}: {exc}")
        _check(cleanup_ok, "temporary tree removal failed")
        # The PASS line's write result IS the self-test's exit status: if the report
        # cannot be delivered, the run did not succeed from the caller's point of view.
        # A failure recorded on an earlier progress line counts too, so a broken stdout
        # cannot be reported as a passing run just because the last line happened to
        # land somewhere else.
        status = emit(f"PASS: all {executed} self-test cases held\n")
        return status if status != 0 else _WRITE_FAILED[0]
    finally:
        if os.path.isdir(tmp):
            shutil.rmtree(tmp, ignore_errors=True)


class _UsageParser(argparse.ArgumentParser):
    """argparse exits 2 on a usage error; this tool documents 1 for usage errors and
    reserves 2 for I/O failures, so a typo and a full disk are distinguishable."""

    def error(self, message):
        # argparse writes usage and help directly; both are guarded here and in
        # print_help below, because an unguarded write can exit 120.
        if sys.stderr is None:
            _silence("stdout")
            sys.exit(2)
        try:
            self.print_usage(sys.stderr)
            sys.stderr.write(f"{PROG}: {message}\n")
            sys.stderr.flush()
        except (BrokenPipeError, OSError):
            _silence("stderr")
            _silence("stdout")
            sys.exit(2)
        if not _stdout_usable():
            # Usage errors are reported on stderr, but stdout is still the stream a
            # caller would read a report from. If it can never be written, nothing
            # reaches the caller: an I/O error rather than the usage code.
            _silence("stderr")
            _silence("stdout")
            sys.exit(2)
        sys.exit(1)

    def print_help(self, file=None):
        """--help must honour the exit contract too: argparse's default writer is
        unguarded, so a full disk or a closed reader produced exit 120."""
        text = self.format_help()
        stream = file if file is not None else sys.stdout
        if stream is None:
            _silence("stderr")
            sys.exit(2)
        try:
            stream.write(text)
            stream.flush()
        except BrokenPipeError:
            # Help is REQUESTED TEXT, not a verdict: a caller that asked for it and
            # received nothing has hit an I/O error. A closed reader on a status line
            # is different (see emit) — there the tool already did its work.
            _silence("stdout")
            sys.exit(2)
        except OSError as exc:
            _silence("stdout")
            fail(f"cannot write help: {exc}", 2)


def parse_args(argv):
    parser = _UsageParser(
        prog=PROG,
        description="Stamp the prefix pointer block in a repo AGENTS.md (start sentinel on line 1).",
    )
    parser.add_argument("--repo", help="ordinary-repo root (contains AGENTS.md)")
    parser.add_argument("--handbook", help="handbook root (contains docs/boundaries/index.md)")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the temporary-copy safety/idempotence suite",
    )
    parser.add_argument(
        "--ordinary-repo",
        help="source ordinary-repo used as the self-test fixture (copied, never mutated)",
    )
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    if args.self_test:
        if not args.ordinary_repo:
            fail("--self-test requires --ordinary-repo")
        if args.repo or args.handbook:
            fail("--self-test does not take --repo/--handbook (it copies --ordinary-repo)")
        return self_test(args.ordinary_repo)
    if not args.repo or not args.handbook:
        fail("provide --repo and --handbook, or --self-test --ordinary-repo")
    if args.ordinary_repo:
        fail("--ordinary-repo is a --self-test fixture; it is ignored in stamping mode")
    return stamp(args.repo, args.handbook)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
