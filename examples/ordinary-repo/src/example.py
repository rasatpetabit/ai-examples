#!/usr/bin/env python3
"""tally — summarize a line-oriented records file.

Each record is one input line: <count> TAB <label>. Blank lines are skipped.
Every other line must match that shape exactly: the count is ASCII decimal
digits with no sign and no leading zero (except "0" itself) and at most 256
digits, and the label is any non-empty text. The digit bound is a portable
guard against the interpreter's own integer-string limit, which varies by build;
a longer count is a data error, not a crash. Only the FIRST tab splits a record, so labels may contain
tabs. Duplicate labels are legal and are merged by summation. A summed count is NOT
re-validated against the 256-digit input bound, so an output row whose sum exceeds
it is legal to print but rejected if fed back in; the bound constrains input, and
carrying past it is a property of the data rather than a bug.

The summary prints one row per distinct label, ordered by descending count
and then by ascending label compared by Unicode code point (not locale
collation), and ends with a TOTAL footer line. Output is deterministic: the
same input bytes always produce the same output bytes and the same exit
code, on any machine.

Usage:
    python3 src/example.py            process a built-in demo input
    python3 src/example.py FILE       process FILE
    python3 src/example.py -           process standard input

Exit codes: 0 success; 1 data error (invalid records, or input that is not
valid UTF-8); 2 usage or I/O error.
"""

import os
import sys

PROG = "tally"
USAGE = "usage: python3 src/example.py [FILE | -]   (no arguments: demo input)\n"

# What the no-argument run processes, so the tool runs with zero setup.
DEMO_INPUT = "3\tred\n1\tblue\n2\tgreen\n3\tblue\n"

DIGITS = "0123456789"
# Portable bound independent of sys.int_info.str_digits_limit (often 4300).
MAX_COUNT_DIGITS = 256


def _write_utf8(stream, text):
    """Write text to a stream that may be None.

    When a descriptor is closed before the interpreter starts (the shell's `1>&-`),
    Python sets the corresponding sys attribute to None rather than raising. Writing to
    it produced an AttributeError traceback and status 1 — a data-error status for what
    is an I/O failure.
    """
    if stream is None:
        raise OSError("standard stream is closed")
    data = text.encode("utf-8")
    buf = getattr(stream, "buffer", None)
    if buf is not None:
        buf.write(data)
        buf.flush()
    else:
        stream.write(text)
        stream.flush()


def _silence(stream_name):
    """Point a stream at /dev/null so CPython's shutdown flush cannot fail.

    Redirecting only stdout is not enough: when stderr is the stream that failed, the
    interpreter's own flush of stderr yields exit 120, which this program's usage text
    does not promise.
    """
    try:
        stream = getattr(sys, stream_name)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stream.fileno())
        os.close(devnull)
    except (OSError, ValueError, AttributeError):
        pass


def die(message, code):
    """Report a fatal problem on stderr and exit. Usage errors show USAGE.

    Every write is guarded: a diagnostic that cannot be written must not replace the
    documented status with whatever CPython's shutdown flush produces.
    """
    try:
        _write_utf8(sys.stderr, f"{PROG}: {message}\n")
        if code == 2:
            _write_utf8(sys.stderr, USAGE)
    except (BrokenPipeError, OSError):
        # The diagnostic could not be delivered. Reporting the original code would
        # claim a verdict the caller never received, so this is an I/O error (2).
        _silence("stderr")
        _silence("stdout")
        sys.exit(2)
    if not _stdout_usable():
        # The diagnostic WAS written, but stdout is not a destination this run could
        # ever report to (/dev/full, or closed before startup). Rule 2: nothing can
        # reach the caller, so the status is an I/O error rather than the verdict.
        _silence("stderr")
        _silence("stdout")
        sys.exit(2)
    sys.exit(code)


def parse_record(line):
    """Parse one non-blank line. Return (count, label), or an error message."""
    if "\t" not in line:
        return "record must be <count> TAB <label>"
    count_str, label = line.split("\t", 1)
    if not count_str or any(c not in DIGITS for c in count_str):
        return f"count {count_str!r} is not an ASCII decimal integer"
    if len(count_str) > MAX_COUNT_DIGITS:
        return f"count has more than {MAX_COUNT_DIGITS} digits"
    if len(count_str) > 1 and count_str[0] == "0":
        return f"count {count_str!r} has a leading zero"
    if label == "":
        return "label is empty"
    return (int(count_str), label)


def load_text(source):
    """Read the whole input as strict UTF-8. Splitting is on LF only, so a
    CR character is ordinary label content, never a line separator."""
    # stdin closed before startup (`cmd <&-`) leaves CPython with sys.stdin = None,
    # so `sys.stdin.buffer` raises AttributeError -- not an OSError, so it escaped
    # this handler as a traceback and exited 1 (the documented DATA-error status)
    # for an I/O failure the usage text documents as status 2.
    if source == "-" and sys.stdin is None:
        die("standard input is closed", 2)
    try:
        if source == "-":
            data = sys.stdin.buffer.read()
        else:
            with open(source, "rb") as handle:
                data = handle.read()
    except OSError as exc:
        die(str(exc), 2)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        die(f"{source} is not valid UTF-8: {exc}", 1)


def tally(text):
    """Return (counts-by-label, list of (line-number, error-message))."""
    counts = {}
    errors = []
    # A trailing newline yields one final empty element: blank, so skipped.
    for number, line in enumerate(text.split("\n"), start=1):
        if line == "":
            continue
        parsed = parse_record(line)
        if isinstance(parsed, tuple):
            counts[parsed[1]] = counts.get(parsed[1], 0) + parsed[0]
        else:
            errors.append((number, parsed))
    return counts, errors


def render(counts):
    """Render the summary: rows by descending count, then ascending label
    by Unicode code point; a TOTAL footer line last."""
    rows = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    out = [f"{count}\t{label}" for label, count in rows]
    out.append(f"TOTAL\t{sum(counts.values())}")
    return "\n".join(out) + "\n"


def _write_output(payload, requested=False):
    """Write bytes to stdout, honouring the documented status contract.

    Every path that produces stdout goes through here. Handling only the main summary
    left --help and a broken pipe able to exit 120 — an undocumented status produced by
    CPython's shutdown flush, not by this program.

    A broken pipe means the reader went away, which is normal for a pager or `| head`.
    Whether that is a failure depends on WHAT was being written:

      * a summary is a VERDICT, and the verdict still stands — the caller ran the
        program to learn something, and it learned it before the pipe closed (0);
      * usage or help is REQUESTED TEXT with no verdict behind it, so a caller that
        asked for it and received nothing has hit an I/O error (2).

    Any other write failure is an I/O error in both cases. The descriptor is redirected
    to /dev/null first, because CPython flushes stdout again during interpreter shutdown
    and that second failure would overwrite the status chosen here.
    """
    if sys.stdout is None:
        _silence("stderr")
        return 2
    try:
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()
        return 0
    except BrokenPipeError:
        _redirect_stdout_to_devnull()
        return 2 if requested else 0
    except OSError as exc:
        _redirect_stdout_to_devnull()
        die(f"cannot write output: {exc}", 2)


def _stdout_usable():
    """True when stdout can actually receive bytes.

    Deliberately SILENT: a refusal must print nothing on stdout, so this cannot write
    a probe byte. What it does instead is force a real syscall on the descriptor -- an
    explicit flush after an empty write, plus a zero-length os.write -- which fails on
    a closed descriptor and (measured on Linux, ENOSPC) on a full one. A platform whose
    kernel treats a zero-length write as a pure no-op would make this probe optimistic;
    that is a known limit of a silent probe, not a claim this covers every destination.
    """
    if sys.stdout is None:
        return False
    try:
        sys.stdout.buffer.write(b"")
        sys.stdout.buffer.flush()
        os.write(1, b"")
    except (BrokenPipeError, OSError, ValueError, AttributeError):
        return False
    return True


def _redirect_stdout_to_devnull():
    _silence("stdout")


def main(argv):
    if len(argv) > 2:
        die("too many arguments", 2)
    if len(argv) == 1:
        source, text = "demo", DEMO_INPUT
    else:
        source = argv[1]
        if source in ("-h", "--help"):
            return _write_output(USAGE.encode("utf-8"), requested=True)
        text = load_text(source)
    counts, errors = tally(text)
    if errors:
        # Guarded like every other write: an unguarded diagnostic with a failing
        # stderr exited 120 instead of the documented data-error status 1.
        try:
            for number, message in errors:
                _write_utf8(sys.stderr, f"{PROG}: {source}:{number}: {message}\n")
        except (BrokenPipeError, OSError):
            # Undeliverable: the caller learns nothing about the data, so this is an
            # I/O error rather than the data-error verdict it would otherwise be.
            _silence("stderr")
            _silence("stdout")
            sys.exit(2)
        die(f"{len(errors)} invalid record(s)", 1)
    out = render(counts).encode("utf-8")
    return _write_output(out)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
