#!/usr/bin/env bash
# leak-scan.sh — structural leak detector for a tree you are about to publish.
#
# CLI (must match README.md):
#   bash tools/leak-scan.sh <export-root>              # 0 clean, 1 hits, 2 error
#   bash tools/leak-scan.sh --self-test
#   bash tools/leak-scan.sh --verify-document <chapter>
#
# This is a detector, not an installer. It never fetches executable content
# and never writes the reader's configuration. --verify-document executes a
# locally reviewed fenced Bash example from a chapter already on disk.
#
# Failure prevented: a public export that still carries private path forms,
# internal addresses, credential material, or site-specific identifiers —
# or a detector that quietly scans nothing.
#
# ---------------------------------------------------------------------------
# Central category definitions (mandatory keys — keep non-empty).
# Adding a pattern is a one-line edit in the Python CATEGORIES list below.
# Never put a real private identifier (org name, hostname, mailbox, token,
# gateway URL, port, private repo name) in this file or its fixtures.
#
#   private_paths        private path forms
#   host_address         host/address forms
#   credentials          credential material
#   config_identifiers   configurable identifier patterns
#
# Manual-review categories (named here; not regex-scanned — generic patterns
# cannot reliably infer exact company/customer/tool names):
#   company_org_names, customer_names, private_repo_names, internal_tool_names
# ---------------------------------------------------------------------------
set -euo pipefail

PROG="leak-scan.sh"

# Every write below is guarded. An unguarded write that fails — a full disk, a closed
# reader — makes the shell exit with 1 or 141, which this script's own usage line
# documents as "hits" or does not document at all. A diagnostic must never be
# mistakable for a scan result.
silence_streams() {
  exec 1>/dev/null 2>/dev/null || true
}

# A descriptor closed before the script starts (`1>&-`) makes EVERY write fail,
# including the one that would report the failure. Reopening both streams onto
# /dev/null at startup means later diagnostics always have somewhere to go, so the
# script's own exit statuses survive instead of bash reporting a write error.
# Set when a descriptor was closed before this script started. Reopening it onto
# /dev/null keeps bash from spewing "Bad file descriptor" on every later write, but
# that would also HIDE the condition, so it is recorded: a run whose report cannot
# reach the caller has no evidence to give, and says so with status 2.
STDOUT_UNAVAILABLE=0
# Only stdout is tracked. A STDERR_UNAVAILABLE flag was set here but never read
# anywhere, so the surrounding prose promised a handling path that did not exist;
# undeliverable diagnostics are reported through stdout's own status instead.

ensure_streams() {
  # Probe the descriptor itself. Several write-based probes looked correct in
  # isolation but reported "available" here, because a redirect on the probe supplies
  # its own descriptor and the write then succeeds regardless. Asking the kernel
  # whether the descriptor EXISTS has no such failure mode, and a healthy run stays
  # silent because nothing is written.
  #
  # /proc/self/fd is Linux-only. On macOS and *BSD that path never exists, so the test
  # would read "unavailable" for EVERY run and every documented status (0 clean, 1 hits)
  # would be unreachable -- a detector that cannot run at all, on platforms this
  # template's own install chapter covers. /dev/fd is the portable equivalent and is
  # what /proc/self/fd resolves to on Linux, so the first path that exists is used and
  # a host with neither falls back to running without the pre-check rather than dying.
  fdroot=""
  for candidate in /dev/fd /proc/self/fd; do
    # The candidate must EXIST and actually ENUMERATE this process's descriptors.
    # Keying on descriptor 0 alone broke a caller with stdin closed (`0<&-`), which
    # silently disabled both pre-checks on a normal host; keying on the directory alone
    # accepts a static /dev whose /dev/fd exists but lists nothing, which would then
    # report every descriptor closed and make statuses 0 and 1 unreachable. Any one of
    # the three standard descriptors being visible is enough to prove enumeration; if
    # none is, there is no probe available and the run proceeds without the pre-check.
    if [[ -d "$candidate" ]] && { [[ -e "$candidate/0" ]] || [[ -e "$candidate/1" ]] || [[ -e "$candidate/2" ]]; }; then
      fdroot="$candidate"; break
    fi
  done
  if [[ -n "$fdroot" && ! -e "$fdroot/1" ]]; then
    STDOUT_UNAVAILABLE=1
    exec 1>/dev/null
  fi
  if [[ -n "$fdroot" && ! -e "$fdroot/2" ]]; then
    exec 2>/dev/null
  fi

}
ensure_streams

usage() {
  if [[ "${STDOUT_UNAVAILABLE}" -eq 1 ]]; then
    # Recorded at startup: nothing this script prints can reach the caller. Checked
    # explicitly because ensure_streams reopened the descriptor onto /dev/null, so a
    # later write SUCCEEDS and would otherwise look like a delivered message.
    silence_streams
    exit 2
  fi
  if ! cat <<EOF
Usage:
  bash tools/${PROG} <export-root>
  bash tools/${PROG} --self-test
  bash tools/${PROG} --verify-document <chapter>

Exit: 0 clean, 1 hits, 2 operational/configuration error.
EOF
  then
    # The usage text could not be delivered, so the caller asked for text and did not
    # get it: an operational failure (2), never success. The SCAN path is different —
    # there the tool holds a real verdict about the tree, and a closed reader
    # (`| head`) must not change it — and that case is handled inside the scanner.
    silence_streams
    exit 2
  fi
  return 0
}

# SIGPIPE is IGNORED for the whole script. A diagnostic written to a pipe whose
# reader has gone kills the shell with 141 before `exit` runs, so the documented
# status is never reached — guarding printf's RETURN CODE does not help, because the
# shell dies from the signal rather than seeing a failure. With SIGPIPE ignored the
# write returns an error instead, which the guards below handle and which lets the
# intended status survive.
trap '' PIPE

die() {
  if ! printf '%s: %s\n' "${PROG}" "$1" >&2; then
    silence_streams
  fi
  exit "${2:-2}"
}

run_python() {
  # Write the program to a temp file. Avoids python3 -c ARG_MAX and does not
  # consume stdin. The exit contract is 0 clean / 1 hits / 2 operational error:
  # a failure to LAUNCH the interpreter (e.g. 127) or any other unexpected
  # status is an operational error, never a "hit".
  local prog="$1"
  shift
  local tmp rc
  tmp="$(mktemp "${TMPDIR:-/tmp}/leak-scan-XXXXXX.py")" || die "cannot create temporary program file"
  printf '%s\n' "${prog}" >"${tmp}" || die "cannot write temporary program file"
  set +e
  python3 "${tmp}" "$@"
  rc=$?
  set -e
  rm -f "${tmp}" || true
  case "${rc}" in
    0|1|2) exit "${rc}" ;;
    # SIGPIPE (141) is deliberately NOT mapped to 0. The embedded program converts an
    # ordinary closed reader into the correct verdict itself (measured: a hits tree
    # piped to `head -c1` still exits 1), so a 141 means the interpreter died BEFORE a
    # verdict was computed. Reporting that as "clean" would be a false negative on the
    # detector's only signal -- the one outcome worse than an ugly exit code. The
    # verdict is unknown, which is an operational failure, not a clean tree.
    141) die "scanner was killed by SIGPIPE before reporting a verdict (undelivered report)" ;;
    *) die "scanner exited ${rc} (operational failure)" ;;
  esac
}

# ---------------------------------------------------------------------------
# Scanner (Python 3, standard library only).
# ---------------------------------------------------------------------------
read -r -d '' SCANNER_PY <<'PY' || true
import os
import re
import stat
import sys

# Central category definitions. Keys and pattern lists live here and nowhere
# else. Every mandatory key must have at least one pattern.
#
# private_paths: Unix-style private/workspace path forms.
# host_address: RFC1918 / loopback / link-local IPv4, and :port forms.
#   No named hostnames — those are a manual-review category.
# credentials: assignment-style secret material. Synthetic key names only.
# config_identifiers: site-specific identifier forms this public template
#   does not itself teach (so a clean export of the template can exist).
CATEGORIES = {
    "private_paths": [
        r"(?i)(?:^|[^\w.-])/(?:home|Users|opt)/[A-Za-z0-9._-]+",
        r"(?i)(?:^|/)(?:home|Users)/[A-Za-z0-9._-]+(?:/|$)",
        r"(?i)(?:^|[^\w.-])~/\.(?:ssh|gnupg|aws)/",
        r"(?i)/var/lib/[A-Za-z0-9._-]+/private",
    ],
    "host_address": [
        r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b",
        r"\b(?:172\.(?:1[6-9]|2\d|3[0-1])|192\.168)\.(?:\d{1,3}\.)\d{1,3}\b",
        r"\b169\.254\.(?:\d{1,3}\.)\d{1,3}\b",
        r"\b(?:(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}|(?:172\.(?:1[6-9]|2\d|3[0-1])|192\.168)\.(?:\d{1,3}\.)\d{1,3}):\d{2,5}\b",
    ],
    "credentials": [
        r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)\s*[:=]\s*\S+",
        r"(?i)\bauthorization:\s*bearer\s+\S+",
        r"(?i)\bBEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY\b",
    ],
    "config_identifiers": [
        r"(?i)\bx-internal-[A-Za-z0-9_-]{4,}\b",
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        r"(?i)/etc/internal/[A-Za-z0-9._/-]+",
    ],
}

# Named, not regex-scanned. Generic patterns cannot reliably infer these.
MANUAL_REVIEW = (
    "company_org_names",
    "customer_names",
    "private_repo_names",
    "internal_tool_names",
)

SKIP_DIR_NAMES = {".git", "node_modules"}


def fail(msg, code=2):
    # The diagnostic itself can be undeliverable (stderr on /dev/full, or closed). An
    # unguarded write raised there and the interpreter exited 1 -- which this script
    # documents as "hits" -- or 120 at shutdown flush. A message nobody received is an
    # operational error, so it is silenced and reported as 2.
    try:
        sys.stderr.write("leak-scan.sh: %s\n" % msg)
        sys.stderr.flush()
    except (BrokenPipeError, OSError, ValueError, AttributeError):
        _silence(2)
    sys.exit(code)


MANDATORY = ("private_paths", "host_address", "credentials", "config_identifiers")
# The launcher and the embedded scanner share one invariant list, so a category
# dropped in one place cannot pass unnoticed in the other.
MANDATORY_KEYS = MANDATORY


def compile_categories():
    # The mandatory-key invariant is enforced HERE, not only in the self-test:
    # iterating CATEGORIES.items() would validate only whatever remains, so
    # deleting a mandatory key — or emptying the dict — would silently scan for
    # less than the contract promises.
    missing = [k for k in MANDATORY_KEYS if k not in CATEGORIES]
    if missing:
        fail("mandatory category missing from CATEGORIES: %s" % ", ".join(missing))
    extra = [k for k in CATEGORIES if k not in MANDATORY_KEYS]
    if extra:
        fail("unexpected CATEGORIES key(s): %s" % ", ".join(sorted(extra)))
    compiled = {}
    for key in MANDATORY_KEYS:
        pats = CATEGORIES[key]
        if not pats:
            fail("category %s has no patterns" % key)
        compiled[key] = []
        for p in pats:
            try:
                compiled[key].append(re.compile(p))
            except re.error as exc:
                fail("pattern failed to compile in category %s: %s (%s)" % (key, p, exc))
    return compiled


def is_binary_bytes(data):
    if b"\x00" in data:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def scan_text(compiled, text, rel, line_label_override=None):
    hits = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        for cat, regs in compiled.items():
            for rgx in regs:
                if rgx.search(line):
                    label = line_label_override if line_label_override is not None else str(i)
                    hits.append((cat, rel, label))
                    break
    return hits


def walk_tree(root):
    """Yield (relpath, fullpath) for every regular file under root.

    Symlinks whose resolved target is outside root fail closed. Directories
    named .git or node_modules are not descended into. Stat errors fail closed.
    """
    root_real = os.path.realpath(root)
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            names = os.listdir(current)
        except OSError as exc:
            fail("cannot list %s: %s" % (current, exc))
        for name in names:
            full = os.path.join(current, name)
            rel = os.path.relpath(full, root)
            try:
                st = os.lstat(full)
            except OSError as exc:
                fail("cannot stat %s: %s" % (rel, exc))
            if stat.S_ISLNK(st.st_mode):
                try:
                    target = os.path.realpath(full)
                except OSError as exc:
                    fail("cannot resolve symlink %s: %s" % (rel, exc))
                if target != root_real and not (target.startswith(root_real + os.sep)):
                    fail("symlink escape refused: %s -> %s" % (rel, target))
                try:
                    st = os.stat(full)
                except OSError as exc:
                    fail("cannot follow symlink %s: %s" % (rel, exc))
            if stat.S_ISDIR(st.st_mode):
                if name in SKIP_DIR_NAMES:
                    continue
                stack.append(full)
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            # The relative name is matched byte-for-byte: rewriting bytes would
            # make a filename pattern match a path that does not exist and miss
            # the one that does. Backslash is a legal filename byte on POSIX.
            yield rel, full


def scan_root(root):
    if not os.path.isdir(root):
        fail("export-root is not a directory: %s" % root)
    compiled = compile_categories()
    hits = []
    skipped = []
    for rel, full in walk_tree(root):
        hits.extend(scan_text(compiled, rel, rel, line_label_override="filename"))
        try:
            with open(full, "rb") as handle:
                data = handle.read()
        except OSError as exc:
            fail("cannot read %s: %s" % (rel, exc))
        if is_binary_bytes(data):
            skipped.append(rel)
            continue
        text = data.decode("utf-8")
        hits.extend(scan_text(compiled, text, rel))
    return hits, skipped, list(CATEGORIES.keys())


def emit(text):
    """Write a report line, honouring the documented exit contract.

    A broken pipe is not a failure: the reader went away, which is what a pager or
    `| head` does, so the verdict the scan already computed is what exits — 1 on a hits
    tree, 0 on a clean one. Any other write failure is an operational error and exits
    2: never 1, which this script documents as "hits". Reporting a full disk as a hit
    would be a false positive on the one signal the detector exists to produce.
    """
    if sys.stdout is None:
        # A descriptor closed before startup (`1>&-`) leaves sys.stdout as None, not
        # as a stream that raises. Writing to it produced an AttributeError traceback
        # and exit 1 — the detector's "hits" status for what is an I/O failure.
        _silence()
        _WRITE_FAILED[0] = 2
        return
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except BrokenPipeError:
        # The reader went away (a pager, `| head`). Stop writing, but do not decide
        # the exit status here: the scan already produced a verdict, and that verdict
        # is what the caller asked for. Exiting 0 would report a tree with hits as
        # clean merely because the report was truncated.
        _silence()
    except OSError as exc:
        _silence()
        _WRITE_FAILED[0] = 2
        if sys.stderr is not None:
            try:
                sys.stderr.write("leak-scan.sh: cannot write report: %s\n" % exc)
            except OSError:
                pass
        sys.exit(2)


# Set to 2 when a report line could not be written. Progress lines return their
# status to nobody, so the failure is remembered and folded into the final exit.
_WRITE_FAILED = [0]


def _silence(status=None):
    """Point both descriptors at /dev/null, and exit with `status` when given.

    CPython flushes stdout and stderr again at interpreter shutdown; that second
    failure is what turns a deliberate exit status into 120, so the DESCRIPTORS are
    replaced. `status` is optional because this is called both as plain cleanup and as
    the last act of a diagnostic that could not be delivered -- and it exits HERE,
    because a caller that returned and then raised would flush the still-broken stream
    at shutdown and lose the status anyway.
    """
    for name in ("stdout", "stderr"):
        try:
            stream = getattr(sys, name)
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, stream.fileno())
            os.close(devnull)
        except (OSError, ValueError, AttributeError):
            pass
    if status is not None:
        sys.exit(status)


def print_report(hits, skipped, category_keys):
    counts = {k: 0 for k in category_keys}
    for cat, rel, label in hits:
        counts[cat] = counts.get(cat, 0) + 1
        emit("%s:%s:%s\n" % (rel, label, cat))
    for rel in skipped:
        emit("skipped-binary:%s\n" % rel)
    emit("---\n")
    for k in category_keys:
        emit("count:%s:%d\n" % (k, counts[k]))
    for name in MANUAL_REVIEW:
        emit("manual-review:%s\n" % name)
    emit("skipped-binary-count:%d\n" % len(skipped))
    emit("hit-total:%d\n" % len(hits))


def main(argv):
    if len(argv) != 2:
        fail("usage: leak-scan.sh <export-root>")
    root = argv[1]
    hits, skipped, keys = scan_root(root)
    print_report(hits, skipped, keys)
    if _WRITE_FAILED[0] != 0:
        # The report could not be delivered, so the caller has no evidence either way.
        # Reporting "hits" (1) would be a false positive on the detector's only signal;
        # reporting clean (0) would be worse. An undelivered report is an operational
        # error (2), which is what the usage line documents for it.
        sys.exit(2)
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main(sys.argv)
PY

# ---------------------------------------------------------------------------
# Self-test harness. Explicit sys.exit("FAIL: ..."); never bare assert.
# ---------------------------------------------------------------------------
read -r -d '' SELFTEST_PY <<'PY' || true
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Set to 2 when a report line could not be written. Progress lines return their status
# to nobody, so the failure is remembered and folded into the final exit.
_WRITE_FAILED = [0]


def _silence():
    """Point both streams at /dev/null before exiting.

    CPython flushes stdout and stderr again at interpreter shutdown; a failing second
    flush replaces the chosen exit status with 120.
    """
    for name in ("stdout", "stderr"):
        try:
            stream = getattr(sys, name)
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, stream.fileno())
            os.close(devnull)
        except (OSError, ValueError, AttributeError):
            pass


def emit(text):
    """Write a self-test report line without letting a write failure change the status.

    A closed reader is normal (a pager, `| head`) and exits 0; any other failure is an
    operational error and exits 2. Writing stdout directly made --self-test exit 2 with
    a BrokenPipeError traceback whenever its reader had gone.
    """
    if sys.stdout is None:
        _silence()
        _WRITE_FAILED[0] = 2
        return
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except BrokenPipeError:
        # A closed READER is normal; silence and carry on. This program's exit status
        # is its verdict, so exiting here would skip the assertions and report success
        # for a defective scanner.
        _silence()
    except OSError:
        # Any other write failure (a full disk) is an operational error, and it must
        # survive to the exit status rather than being swallowed as a mere broken pipe.
        _silence()
        _WRITE_FAILED[0] = 2


def fail(msg):
    if sys.stderr is not None:
        try:
            sys.stderr.write("FAIL: %s\n" % msg)
            sys.stderr.flush()
        except (BrokenPipeError, OSError):
            _silence()
    sys.exit(1)


# The invariant list is a literal here, deliberately NOT read from the scanner:
# a self-test that learned the expected categories from the tree it is
# testing could not detect a category that was dropped from that tree.
MANDATORY = ("private_paths", "host_address", "credentials", "config_identifiers")


def check(cond, msg):
    if not cond:
        fail(msg)


def run_scan(script, root):
    proc = subprocess.run(
        ["bash", script, root],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def parse_counts(stdout):
    counts = {}
    skipped = []
    hit_total = None
    manuals = []
    for line in stdout.splitlines():
        if line.startswith("count:"):
            parts = line.split(":")
            check(len(parts) == 3, "malformed count line: %r" % line)
            counts[parts[1]] = int(parts[2])
        elif line.startswith("skipped-binary:") and not line.startswith("skipped-binary-count:"):
            skipped.append(line.split(":", 1)[1])
        elif line.startswith("hit-total:"):
            hit_total = int(line.split(":", 1)[1])
        elif line.startswith("manual-review:"):
            manuals.append(line.split(":", 1)[1])
    return counts, skipped, hit_total, manuals


def _skip_string_literal(text, i):
    """Return the index just past a Python string literal starting at i.

    Delimiter counting that ignores string contents is wrong: a regex such as
    r"foo\\]" contains a ']' that would otherwise close the enclosing list early,
    truncating the category and making a healthy scanner look degraded.
    """
    quote = text[i]
    triple = text[i : i + 3] in ('"""', "'''")
    if triple:
        end = text.find(text[i : i + 3], i + 3)
        return len(text) if end < 0 else end + 3
    j = i + 1
    while j < len(text):
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == quote:
            return j + 1
        j += 1
    return len(text)


def _balanced_slice(text, open_at, open_ch, close_ch):
    """Index just past the delimiter matching the one at open_at, string-aware."""
    depth = 0
    j = open_at
    while j < len(text):
        ch = text[j]
        if ch in ('"', "'"):
            j = _skip_string_literal(text, j)
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return None


def extract_categories(script_text):
    start = script_text.find("CATEGORIES = {")
    check(start >= 0, "could not find CATEGORIES in scanner")
    i = script_text.find("{", start)
    end_after = _balanced_slice(script_text, i, "{", "}")
    check(end_after is not None, "CATEGORIES dict is unterminated")
    body = script_text[i + 1 : end_after - 1]
    keys = re.findall(r'"([a-z_]+)"\s*:', body)
    lists = {}
    for k in keys:
        key_at = body.find('"%s"' % k)
        check(key_at >= 0, "category %s missing" % k)
        lb = body.find("[", key_at)
        check(lb >= 0, "category %s has no list" % k)
        rb_after = _balanced_slice(body, lb, "[", "]")
        check(rb_after is not None, "category %s list unterminated" % k)
        chunk = body[lb + 1 : rb_after - 1]
        pats = re.findall(r'r"((?:\\.|[^"\\])*)"', chunk)
        lists[k] = pats
    return keys, lists


def write(path, data, mode="w"):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if mode == "wb":
        with open(path, "wb") as handle:
            handle.write(data)
    else:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(data)


def main(argv):
    if len(argv) != 2:
        fail("self-test usage: leak-scan.sh --self-test")
    script = argv[1]
    check(os.path.isfile(script) and os.path.getsize(script) > 0, "scanner script missing or empty: %s" % script)

    text = open(script, encoding="utf-8").read()
    keys, lists = extract_categories(text)

    for k in MANDATORY:
        check(k in keys, "mandatory category key missing from CATEGORIES: %s" % k)
        check(len(lists.get(k) or []) > 0, "mandatory category %s is empty" % k)
    extra = [k for k in keys if k not in MANDATORY]
    check(len(extra) == 0, "unexpected CATEGORIES keys: %s" % extra)

    tmp = tempfile.mkdtemp(prefix="leak-scan-self-test-")
    script_abs = os.path.abspath(script)
    unread_victim = None
    locked_dir = None
    try:
        # --- known-bad: one independently asserted content hit per category ---
        # Payloads are assembled at runtime so this script's own bytes are not a
        # hit when the export is scanned.
        home_seg = "ho" + "me"
        user_seg = "example" + "-user"
        octet = "10" + ".0.0." + "1"
        key_name = "api" + "_key"
        hdr = "x-" + "internal-fixture-id"
        bad = os.path.join(tmp, "bad")
        os.makedirs(bad)
        write(os.path.join(bad, "paths.txt"), "workspace lives at /%s/%s/project\n" % (home_seg, user_seg))
        write(os.path.join(bad, "net.txt"), "bind %s for the fixture listener\n" % octet)
        write(os.path.join(bad, "secrets.txt"), "%s: SYNTHETICFIXTURETOKENVALUE\n" % key_name)
        write(os.path.join(bad, "ids.txt"), "header %s on the synthetic request\n" % hdr)

        # filename-only hits (clean bodies)
        write(os.path.join(bad, home_seg, user_seg, "notes.txt"), "no leak in this body\n")
        write(os.path.join(bad, octet + "-listener.txt"), "no leak in this body\n")

        rc, out, err = run_scan(script_abs, bad)
        emit("self-test known-bad: status=%s\n" % rc)
        emit(out)
        if err:
            emit(err)
        check(rc == 1, "known-bad scan must return exactly 1, got %s (2 is not success)" % rc)
        counts, skipped, hit_total, manuals = parse_counts(out)
        for k in MANDATORY:
            check(k in counts, "known-bad report missing count for %s" % k)
            check(counts[k] > 0, "known-bad scan produced no hit in category %s (counts=%s)" % (k, counts))
        check(hit_total is not None and hit_total > 0, "known-bad scan hit-total missing or zero")
        filename_hits = [ln for ln in out.splitlines() if ":filename:" in ln]
        check(len(filename_hits) > 0, "filename-only hits missing (no :filename: lines)")
        for name in (
            "company_org_names",
            "customer_names",
            "private_repo_names",
            "internal_tool_names",
        ):
            check(name in manuals, "manual-review category %s not listed" % name)

        # --- clean control ---
        clean = os.path.join(tmp, "clean")
        os.makedirs(clean)
        write(os.path.join(clean, "README.md"), "# example\nThis tree has no private path, address, secret, or identifier forms.\n")
        write(os.path.join(clean, "notes.txt"), "ordinary prose about a public package.\n")
        rc, out, err = run_scan(script_abs, clean)
        emit("self-test clean: status=%s\n" % rc)
        emit(out)
        check(rc == 0, "clean control must return 0, got %s stderr=%r" % (rc, err))
        counts, skipped, hit_total, manuals = parse_counts(out)
        for k in MANDATORY:
            check(counts.get(k, -1) == 0, "clean control hit in %s: %s" % (k, counts.get(k)))
        check(hit_total == 0, "clean control hit-total %s" % hit_total)

        # --- skip .git / node_modules ---
        skip_root = os.path.join(tmp, "skip")
        os.makedirs(os.path.join(skip_root, ".git"))
        os.makedirs(os.path.join(skip_root, "node_modules", "pkg"))
        skip_secret = ("api" + "_key") + ": SHOULDNOTFIRE\n"
        write(os.path.join(skip_root, ".git", "secret.txt"), skip_secret)
        write(os.path.join(skip_root, "node_modules", "pkg", "x.txt"), skip_secret)
        write(os.path.join(skip_root, "ok.txt"), "public text\n")
        rc, out, err = run_scan(script_abs, skip_root)
        emit("self-test skip-dirs: status=%s\n" % rc)
        emit(out)
        check(rc == 0, "skip-dir tree must be clean, got %s stderr=%r" % (rc, err))
        check("SHOULDNOTFIRE" not in out, "skipped subtree contents leaked into the report")

        # --- skipped-binary ---
        bin_root = os.path.join(tmp, "bin")
        os.makedirs(bin_root)
        write(os.path.join(bin_root, "ok.txt"), "public text\n")
        write(os.path.join(bin_root, "blob.bin"), b"\xff\xfe\x00\x01not-utf8", mode="wb")
        rc, out, err = run_scan(script_abs, bin_root)
        emit("self-test skipped-binary: status=%s\n" % rc)
        emit(out)
        check(rc == 0, "undecodable extra file must not count as a leak hit, got %s stderr=%r" % (rc, err))
        check("skipped-binary:blob.bin" in out.splitlines(), "undecodable file was not reported as skipped-binary")
        check("skipped-binary-count:1" in out.splitlines(), "skipped-binary-count missing or wrong")

        # --- nonexistent root -> 2 ---
        rc, out, err = run_scan(script_abs, os.path.join(tmp, "no-such-export-root"))
        emit("self-test nonexistent-root: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "nonexistent root must return 2, got %s" % rc)
        check(
            "not a directory" in err,
            "nonexistent root must be diagnosed as not-a-directory, got stderr %r" % err,
        )

        # --- unreadable file -> 2. Confirm the open/list actually failed;
        # never claim chmod alone proves unreadability. ---
        # --- unreadable file -> 2. Confirm the read actually failed; never claim
        # chmod alone proves unreadability. The directory fallback exists only for
        # privileged runs, and it asserts the DIRECTORY diagnostic explicitly: a
        # directory-list failure must not be accepted as proof that an unreadable
        # REGULAR FILE is handled, which is the behaviour under test. ---
        unread = os.path.join(tmp, "unread")
        os.makedirs(unread)
        unread_victim = os.path.join(unread, "locked.txt")
        write(unread_victim, "public text\n")
        injected = False
        unread_rc = None
        try:
            os.chmod(unread_victim, 0)
            unread_rc, out, err = run_scan(script_abs, unread)
            if unread_rc == 2 and "cannot read" in err:
                injected = True
                emit("self-test unreadable-file: status=%s stderr=%r (read failed after chmod 0)\n" % (unread_rc, err))
        finally:
            if unread_victim and os.path.exists(unread_victim):
                try:
                    os.chmod(unread_victim, 0o644)
                except OSError:
                    pass
        # The assertion must not contradict the tolerance above it. When chmod 0 did
        # not block the read (a privileged run), the scan legitimately returns its
        # normal verdict -- 0 or 1 -- and demanding 2 there FAILED the self-test in the
        # exact case the NOT-EXERCISED branch was added to tolerate. The 2 is required
        # only when the unreadable state was actually produced.
        if injected:
            check(unread_rc == 2, "unreadable target must return 2, got %s" % unread_rc)
        else:
            # The fixture holds only clean public text, so a correct scanner MUST
            # return 0 here. Accepting 1 as well would let a regression that reports an
            # unreadable file as "hits" pass this self-test green -- the exact status
            # confusion this case exists to pin.
            check(
                unread_rc == 0,
                "unreadable case not exercised: a clean fixture must still scan clean, got %s" % unread_rc,
            )

        # --- unreadable DIRECTORY -> 2 (its own case, with its own diagnostic) ---
        locked_dir = os.path.join(tmp, "locked-dir")
        os.makedirs(locked_dir)
        write(os.path.join(locked_dir, "x.txt"), "public\n")
        dir_rc = None
        try:
            os.chmod(locked_dir, 0)
            dir_rc, out, err = run_scan(script_abs, locked_dir)
            if dir_rc == 2:
                emit("self-test unreadable-dir: status=%s stderr=%r\n" % (dir_rc, err))
        finally:
            if locked_dir and os.path.isdir(locked_dir):
                try:
                    os.chmod(locked_dir, 0o755)
                except OSError:
                    pass
        # Same privileged-run tolerance as the unreadable FILE case above: the 2 is
        # required only when the directory actually became unreadable.
        if dir_rc == 2:
            # Assert the DIAGNOSTIC, as the unreadable-FILE case does: any exit 2 is
            # indistinguishable from a scanner failing for an unrelated reason.
            check("cannot list" in err, "unreadable directory reported the list failure, got %r" % err[:120])
        else:
            # Same reasoning as the unreadable FILE case: a clean fixture scanned by a
            # correct scanner returns 0, and nothing else.
            check(
                dir_rc == 0,
                "unreadable-dir case not exercised: a clean fixture must still scan clean, got %s" % dir_rc,
            )

        # --- malformed pattern compilation -> 2 ---
        needle = r"(?i)(?:^|[^\w.-])/(?:home|Users|opt)/[A-Za-z0-9._-]+"
        mutated = text.replace(needle, r"(?P<unterminated", 1)
        check(mutated != text, "could not inject a malformed pattern into a scanner copy")
        bad_script = os.path.join(tmp, "broken-scan.sh")
        with open(bad_script, "w", encoding="utf-8") as handle:
            handle.write(mutated)
        os.chmod(bad_script, 0o755)
        rc, out, err = run_scan(bad_script, clean)
        emit("self-test malformed-pattern: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "malformed pattern must return 2, got %s" % rc)
        check("failed to compile" in err, "malformed pattern did not report compile failure")

        # --- symlink escape -> 2 ---
        esc = os.path.join(tmp, "escape")
        os.makedirs(esc)
        outside = os.path.join(tmp, "outside.txt")
        write(outside, ("api" + "_key") + ": SYNTHETIC\n")
        os.symlink(outside, os.path.join(esc, "link.txt"))
        rc, out, err = run_scan(script_abs, esc)
        emit("self-test symlink-escape: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "symlink escape must return 2, got %s" % rc)
        check("symlink escape" in err, "symlink escape diagnostic missing")

        # --- --verify-document parser failures ---
        def run_verify(chapter):
            proc = subprocess.run(
                ["bash", script_abs, "--verify-document", chapter],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")

        missing = os.path.join(tmp, "no-fences.md")
        write(missing, "# no suite here\n")
        rc, out, err = run_verify(missing)
        emit("self-test verify-missing: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "missing fences must return 2, got %s" % rc)
        check("missing verification-suite fences" in err, "missing-fence case must report the fence diagnostic, got %r" % err)

        dup = os.path.join(tmp, "dup-fences.md")
        write(
            dup,
            "<!-- verification-suite:start -->\n```bash\necho a\n```\n<!-- verification-suite:end -->\n"
            "<!-- verification-suite:start -->\n```bash\necho b\n```\n<!-- verification-suite:end -->\n",
        )
        rc, out, err = run_verify(dup)
        emit("self-test verify-duplicate: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "duplicate fences must return 2, got %s" % rc)
        check("fence count" in err, "duplicate-fence case must report the count diagnostic, got %r" % err)

        empty = os.path.join(tmp, "empty-fences.md")
        write(empty, "<!-- verification-suite:start -->\n<!-- verification-suite:end -->\n")
        rc, out, err = run_verify(empty)
        emit("self-test verify-empty: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "empty fenced block must return 2, got %s" % rc)

        wrong = os.path.join(tmp, "wrong-fences.md")
        write(wrong, "<!-- verification-suite:end -->\n```bash\necho x\n```\n<!-- verification-suite:start -->\n")
        rc, out, err = run_verify(wrong)
        emit("self-test verify-reversed: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "reversed fences must return 2, got %s" % rc)

        nofile = os.path.join(tmp, "does-not-exist.md")
        rc, out, err = run_verify(nofile)
        emit("self-test verify-absent: status=%s stderr=%r\n" % (rc, err))
        check(rc == 2, "absent chapter must return 2, got %s" % rc)

        ok_chapter = os.path.join(tmp, "ok-suite.md")
        write(
            ok_chapter,
            "# example\n"
            "<!-- verification-suite:start -->\n"
            "```bash\n"
            "echo verify-document-ok\n"
            "```\n"
            "<!-- verification-suite:end -->\n",
        )
        rc, out, err = run_verify(ok_chapter)
        emit("self-test verify-ok: status=%s stdout=%r stderr=%r\n" % (rc, out, err))
        check(rc == 0, "well-formed suite must return 0, got %s" % rc)
        check("verify-document-ok" in out, "suite stdout missing")

        emit("PASS: all self-test assertions held\n")
        # A write failure on any report line — not just this one — means the run could
        # not deliver its evidence, so it is not a success even though every assertion
        # held.
        return _WRITE_FAILED[0]
    finally:
        if unread_victim and os.path.exists(unread_victim):
            try:
                os.chmod(unread_victim, 0o644)
            except OSError:
                pass
        if locked_dir and os.path.isdir(locked_dir):
            try:
                os.chmod(locked_dir, 0o755)
            except OSError:
                pass
        shutil.rmtree(tmp, ignore_errors=False)


if __name__ == "__main__":
    sys.exit(main(sys.argv) or 0)
PY

# ---------------------------------------------------------------------------
# --verify-document parser + runner.
# ---------------------------------------------------------------------------
read -r -d '' VERIFY_PY <<'PY' || true
import os
import re
import subprocess
import sys
import tempfile

# Set to 2 when this program's own output could not be written. Declared here because
# each embedded program is separate: the scanner's helpers are not in scope.
_WRITE_FAILED = [0]


def _silence(status=None):
    """Redirect both descriptors to /dev/null, and exit with `status` when given.

    CPython flushes stdout and stderr again at interpreter shutdown; that second
    failure is what turns a deliberate exit status into 120, so the DESCRIPTORS are
    replaced. Exiting HERE (rather than returning) keeps that flush from undoing the
    status the caller asked for.
    """
    for name in ("stdout", "stderr"):
        try:
            stream = getattr(sys, name)
            if stream is None:
                continue
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, stream.fileno())
            os.close(devnull)
        except (OSError, ValueError, AttributeError):
            pass
    if status is not None:
        sys.exit(status)


def fail(msg, code=2):
    # The diagnostic itself can be undeliverable (stderr on /dev/full, or closed). An
    # unguarded write raised there and the interpreter exited 1 -- which this script
    # documents as "hits" -- or 120 at shutdown flush. A message nobody received is an
    # operational error, so it is silenced and reported as 2.
    try:
        sys.stderr.write("leak-scan.sh: %s\n" % msg)
        sys.stderr.flush()
    except (BrokenPipeError, OSError, ValueError, AttributeError):
        _silence(2)
    sys.exit(code)


def main(argv):
    if len(argv) != 2:
        fail("usage: leak-scan.sh --verify-document <chapter>")
    chapter = argv[1]
    if not os.path.isfile(chapter):
        fail("chapter is missing or not a file: %s" % chapter)
    if os.path.getsize(chapter) == 0:
        fail("chapter is empty: %s" % chapter)
    try:
        text = open(chapter, encoding="utf-8").read()
    except OSError as exc:
        fail("cannot read chapter %s: %s" % (chapter, exc))
    except UnicodeDecodeError as exc:
        fail("chapter is not valid UTF-8: %s" % exc)

    starts = [m.start() for m in re.finditer(r"<!-- verification-suite:start -->", text)]
    ends = [m.start() for m in re.finditer(r"<!-- verification-suite:end -->", text)]
    if not starts and not ends:
        fail("missing verification-suite fences (need exactly one ordered start/end pair)")
    if len(starts) != 1 or len(ends) != 1:
        fail(
            "verification-suite fence count is start=%d end=%d; need exactly one of each"
            % (len(starts), len(ends))
        )
    start_i = starts[0]
    end_i = ends[0]
    marker_s = "<!-- verification-suite:start -->"
    if end_i < start_i + len(marker_s):
        fail("verification-suite fences are reversed or overlapping")
    inner = text[start_i + len(marker_s) : end_i]
    if inner.strip() == "":
        fail("verification-suite block is empty")

    # Exactly one fenced Bash region, and it must be a real top-level fence:
    # re.search would take the FIRST of several blocks, and an unanchored
    # triple-backtick match can select a literal example nested inside a
    # longer fence. Count fences at column 0 first, then take the single block.
    fence_re = re.compile(r"^(?P<fence>`{3,})(?P<lang>[A-Za-z]*)[ \t]*\n(?P<body>.*?)^(?P=fence)[ \t]*$", re.S | re.M)
    blocks = [m for m in fence_re.finditer(inner)]
    if len(blocks) == 0:
        fail("verification-suite block has no fenced Bash region")
    if len(blocks) > 1:
        fail("verification-suite block has %d fenced regions; need exactly one" % len(blocks))
    block = blocks[0]
    lang = block.group("lang").lower()
    if lang not in ("bash", "sh", ""):
        fail("verification-suite fenced region is %r, not a Bash block" % lang)
    body = block.group("body")
    if body.strip() == "":
        fail("verification-suite fenced Bash region is empty")

    chapter_abs = os.path.abspath(chapter)
    chapter_dir = os.path.dirname(chapter_abs)
    if os.path.basename(chapter_dir) == "docs":
        project_root = os.path.dirname(chapter_dir)
    else:
        project_root = chapter_dir

    fd, tmp_path = tempfile.mkstemp(prefix="leak-scan-verify-", suffix=".sh")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("set -euo pipefail\n")
            handle.write(body)
            if not body.endswith("\n"):
                handle.write("\n")
        # The child inherits this process's stdout. When the reader has gone, its
        # own prints raise BrokenPipeError and CPython's shutdown flush turns the
        # result into 120 — an operational failure for a run whose checks all passed.
        # Pointing the child at /dev/null lets it finish and report its real status;
        # the verdict is what the caller asked for, and a truncated report is not a
        # failed verification.
        # The child's output is CAPTURED and relayed through emit() rather than
        # inherited. Inheriting meant the child wrote straight into a pipe whose reader
        # had gone; its own prints then failed and CPython's shutdown flush turned a
        # successful verification into exit 120 — an operational failure reported for a
        # run whose every check passed. Capturing keeps the child's verdict intact and
        # lets this program decide how to deliver the report.
        proc = subprocess.run(
            ["bash", tmp_path],
            cwd=project_root,
            stdout=subprocess.PIPE,
        )
        # The relay is attempted whenever the child ran, not only when it produced
        # output: a silent verification block still needs its destination checked, and
        # gating on proc.stdout let a /dev/full run return 0 because nothing was
        # written and nothing failed.
        try:
            if proc.stdout:
                sys.stdout.write(proc.stdout.decode("utf-8", "replace"))
            # Flushing an EMPTY buffer performs no syscall, so it succeeds even on
            # /dev/full or a closed descriptor, and `os.write` of a zero-length buffer
            # is likewise a no-op -- which is why the probe below writes ONE byte. The
            # code used to perform the zero-length writes this comment warns about,
            # leaving the silent-block case (no captured output) with no destination
            # probe at all: a dead stdout could then exit 0. The newline is what a text
            # report would end with anyway, and it is written only after the block's own
            # output, so it cannot disturb an exact-output comparison.
            sys.stdout.write("\n")
            sys.stdout.flush()
        except BrokenPipeError:
            _silence()
        except OSError:
            _silence()
            _WRITE_FAILED[0] = 2

        # The documented contract is 0 clean / 1 hits / 2 operational error. A
        # block exiting 3, or failing with command-not-found 127, must surface as
        # an operational error (2), never as a status outside the contract.
        rc = proc.returncode
        if _WRITE_FAILED[0] != 0:
            # The verification ran, but its report never reached the caller: nothing
            # was delivered to read, so success would be a claim this run cannot
            # support. Reported as the operational error it is.
            if sys.stderr is not None:
                try:
                    sys.stderr.write(
                        "leak-scan.sh: verification report could not be delivered\n"
                    )
                except OSError:
                    pass
            sys.exit(2)
        if rc in (0, 1, 2):
            sys.exit(rc)
        # Routed through fail() rather than written directly: this was the last unguarded
        # stream write in the file, so with stderr undeliverable it raised OSError and the
        # interpreter exited 1 or 120 -- outside the documented 0/1/2 contract, on the one
        # path (a block exiting outside 0/1/2) that is already an operational failure.
        fail("verification block exited %s (operational failure)" % rc, 2)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    main(sys.argv)
PY

mode=""
export_root=""
chapter=""

if [[ $# -eq 0 ]]; then
  usage >&2
  die "missing argument" 2
fi

case "$1" in
  -h|--help)
    # usage() exits 2 when the text could not be delivered; reaching the next line
    # means it was written, so the status here is the documented success.
    usage
    exit 0
    ;;
  --self-test)
    if [[ $# -ne 1 ]]; then
      die "--self-test takes no extra arguments"
    fi
    mode="self-test"
    ;;
  --verify-document)
    if [[ $# -ne 2 ]]; then
      die "--verify-document requires exactly one <chapter> path"
    fi
    mode="verify"
    chapter="$2"
    ;;
  --*)
    die "unknown option: $1"
    ;;
  *)
    if [[ $# -ne 1 ]]; then
      die "scan mode takes exactly one <export-root>"
    fi
    mode="scan"
    export_root="$1"
    ;;
esac

SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"

# A stdout closed from startup means nothing this script prints can reach the caller.
# The embedded programs handle a stream that becomes unusable mid-run; this covers the
# case where it never existed, which they cannot see because it was reopened above.
if [[ "${STDOUT_UNAVAILABLE}" -eq 1 ]]; then
  # Every mode either prints a report (scan, self-test) or relays one (verify), so a
  # closed stdout means the caller receives no evidence whatever the mode. `die` is
  # used rather than a bare exit so the reason is recorded on stderr when that is
  # still available.
  die "stdout is closed; no report can be delivered" 2
fi

case "${mode}" in
  scan)
    run_python "${SCANNER_PY}" "${export_root}"
    ;;
  self-test)
    run_python "${SELFTEST_PY}" "${SCRIPT_PATH}"
    ;;
  verify)
    run_python "${VERIFY_PY}" "${chapter}"
    ;;
  *)
    die "internal: unknown mode ${mode}"
    ;;
esac
