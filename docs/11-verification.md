# 11 — Verification

This chapter is the evidence record for this template: what was mechanically
checked, the exact command that proved each fact, what was **not** verified,
and the suite a reader (or a later agent) re-runs to re-establish the same
bar. It is not a maintenance promise. Commands, package names, and paths in
the other chapters were true when those chapters were written; this chapter
tells you how to look them up again.

**Failure prevented:** a dated guide treated as a live product, or a
completion claim that rests on inspection instead of a command.

The suite below is the executable half. It is invoked, never copied into a
shell by hand as a second source of truth:

```text
bash tools/leak-scan.sh --verify-document docs/11-verification.md
```

That command reads **exactly one** fenced Bash region between the
`verification-suite` sentinels in this file and runs it with
`errexit`/`nounset`/`pipefail` from the project root. It never fetches
executable content and never writes the reader's configuration. Do not
invoke `--verify-document` from inside the block (the suite would recurse).

<!-- verification-suite:start -->
```bash
python3 - <<'PY'
"""Integrated export + evidence suite. Python 3 stdlib only.

No bare assert: python3 -O / PYTHONOPTIMIZE=1 strip assertions, so every
check is an explicit conditional plus sys.exit('FAIL: ...'). Every check
also fails on an empty or absent target.
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import urllib.parse

ROOT = os.getcwd()
MANIFEST_REL = "MANIFEST.txt"
# The negative regressions replay the suite's own block in a child process, and they
# need a path to the chapter because __file__ is the literal '<stdin>' when the program
# arrives on stdin. The launcher does NOT pass this argument — it runs the extracted
# bash block, which invokes Python through a heredoc — so in practice the fallback below
# is what is used, and it is resolved relative to the working directory the suite is run
# from. Running `python3 docs/11-verification.md` directly is not supported: this file is
# Markdown, and the launcher extracts the fenced block and runs that.
CHAPTER_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join("docs", "11-verification.md")
# The export digest is an EVIDENCE record for whoever runs this suite, not part
# of the published tree. It is taken from the environment when set, so this
# shipped chapter never hardcodes an internal workspace path. When unset it
# defaults to the name below IN THE WORKING DIRECTORY — which a delivered, read-only
# copy cannot write, so a certification run against one must set the variable. A write
# failure there is reported with that instruction rather than as a bare traceback.
DIGEST_REL = os.environ.get("EXPORT_DIGEST_PATH", ".export-digest.txt")
DETECTOR = os.path.join("tools", "leak-scan.sh")
STAMPER = os.path.join("examples", "handbook", "tools", "stamp-pointers.py")
INVENTORY = os.path.join("examples", "handbook", "inventory.yaml")
TALLY = os.path.join("examples", "ordinary-repo", "src", "example.py")

PASS = 0
FAIL = 0
NOTES = []


def fail(msg):
    global FAIL
    FAIL += 1
    sys.stderr.write("FAIL: %s\n" % msg)
    sys.exit(1)


def check(cond, msg):
    global FAIL
    if not cond:
        fail(msg)
    note_pass(msg)


def emit_child(text):
    """Echo a child process's stdout INDENTED so it cannot impersonate a parent PASS.

    Several checks run a subprocess (`leak-scan.sh --self-test`, the stamper self-test,
    the rule gate, the tally) and then show its output. Printing that output verbatim at
    column 0 made the child's own `PASS:` lines indistinguishable from this suite's, so
    the run printed 188 PASS lines while reporting PASS_COUNT=187 -- two counts of the
    same run, disagreeing, in a record whose whole purpose is evidence. The child's
    output still appears in full; it is simply no longer mistakable for the parent's.
    """
    for line in text.splitlines():
        print("  | " + line)


def note_pass(msg):
    """Record and print one PASS. The ONLY way a PASS is counted.

    The provers used to hand-roll `print("PASS: ...")` plus `PASS += 1`, which let the
    printed lines and the tally disagree: one run printed 189 PASS lines while
    reporting PASS_COUNT=186, because a prover printed its own success without
    incrementing. An evidence record whose two counts of the same thing differ can be
    cited for neither, and a reader cannot tell which is right. Routing every PASS
    through one function makes that divergence impossible.
    """
    global PASS
    PASS += 1
    print("PASS: %s" % msg)


def note(msg):
    NOTES.append(msg)
    print("NOTE: %s" % msg)


def require_file(path, what):
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        fail("%s missing or empty: %s" % (what, path))
    return path


def run(cmd, cwd=None, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    return proc.returncode, out, err


def load_manifest(path):
    require_file(path, "manifest")
    raw = open(path, "rb").read()
    if not raw:
        fail("manifest is empty: %s" % path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("manifest is not UTF-8: %s" % exc)
    lines = text.splitlines()
    if not lines:
        fail("manifest has no entries")
    seen = []
    dup = []
    for i, raw_line in enumerate(lines, 1):
        p = raw_line.strip()
        if not p:
            fail("blank line at %d in manifest" % i)
        if p.startswith("/") or p.startswith("#") or p.endswith("/"):
            fail("absolute, comment, or directory at %d: %s" % (i, p))
        if any(ch in p for ch in "*?[]"):
            fail("glob metacharacter at %d: %s" % (i, p))
        parts = p.split("/")
        if ".." in parts or any(part.startswith(".") for part in parts):
            fail("traversal or hidden path at %d: %s" % (i, p))
        # A dotted component is already rejected above. The real boundary is the
        # manifest allowlist plus the unlisted-file check, not a named directory.
        if ".git/" in p or p.startswith(".git"):
            fail("git-history path at %d: %s" % (i, p))
        if p in seen:
            dup.append(p)
        seen.append(p)
    if dup:
        fail("duplicate manifest entries: %s" % ", ".join(dup))
    return seen


def decode_utf8_no_nul(path, label):
    require_file(path, label)
    data = open(path, "rb").read()
    if not data:
        fail("%s is empty: %s" % (label, path))
    if b"\x00" in data:
        fail("%s contains a NUL byte: %s" % (label, path))
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("%s is not valid UTF-8: %s (%s)" % (label, path, exc))


def check_no_symlink_ancestor(src_root, rel):
    """Refuse a path any of whose ANCESTORS is a symlink.

    Checking only the final component missed the real case: moving a whole directory
    — templates/, say — outside the tree and replacing it with a directory symlink
    leaves every file a regular file, so the manifest entries resolve through the link
    and the export silently leaves its own tree.
    """
    parts = rel.split("/")
    walked = src_root
    for part in parts[:-1]:
        walked = os.path.join(walked, part)
        if os.path.islink(walked):
            fail(
                "symlinked directory in export path, refusing: %s (ancestor %s)"
                % (rel, os.path.relpath(walked, src_root))
            )


def copy_export(src_root, entries, dest_root):
    copied = []
    for rel in entries:
        src = os.path.join(src_root, rel)
        if os.path.islink(src):
            fail("symlink in export set, refusing: %s" % rel)
        check_no_symlink_ancestor(src_root, rel)
        # Order matters for the DIAGNOSTIC, not just the refusal. `os.path.isfile`
        # returns False for a fifo, device or socket as well as for a missing path, so
        # testing it first reported a fifo as "manifest lists a missing file" and left
        # the S_ISREG branch below unreachable. Existence is asked of the path, and
        # regularity of lstat -- which does not follow the symlink already rejected above.
        if not os.path.exists(src):
            fail("manifest lists a missing file: %s" % rel)
        if not stat.S_ISREG(os.lstat(src).st_mode):
            fail("manifest lists a non-regular file: %s" % rel)
        dst = os.path.join(dest_root, rel)
        parent = os.path.dirname(dst)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy2(src, dst)
        if os.path.islink(dst):
            fail("copy produced a symlink: %s" % rel)
        decode_utf8_no_nul(dst, "exported file")
        copied.append(rel)
    return copied


def classify_citation_url(rel, url, is_https):
    """Classify one citation URL. Returns a list of (rel, url, reason) findings.

    Extracted from main so a prover can exercise it: while it was inline, no negative
    regression could reach it and deleting any single denylist branch below left the
    suite green over a real defect. Returns [] for a public https citation.

    Structural only: this decides whether a host is a plausible public source, NOT
    whether it is the upstream repository rather than a fork, nor whether the citation
    is the semantically right source. Those are the reviewer's job.
    """
    if not is_https:
        return [(rel, url, "not-https")]
    host = host_of(url)
    if not host:
        return [(rel, url, "unparseable")]
    # Reject file-URI and local/private shapes. No exemptions: a
    # placeholder or localhost URL in a citation table is a real
    # defect, because skipping it lets an invalid source ride along
    # beside a valid one.
    # .localhost is reserved for loopback (RFC 6761), so a SUBDOMAIN of it
    # is as local as the bare name. Matching only the exact host let
    # https://foo.localhost/x pass as a public source.
    if host == "localhost" or host.endswith(".localhost"):
        return [(rel, url, "local-or-address")]
    # An IPv4 address in ANY accepted notation, not just dotted-quad:
    # `inet_aton` accepts 127.1, 0x7f.1 and 2130706433, all of which are
    # loopback, and matching only \d+.\d+.\d+.\d+ certified them as public.
    try:
        socket.inet_aton(host)
    except OSError:
        pass
    else:
        return [(rel, url, "local-or-address")]
    # A hostname with an empty label, or a port that is not a number, is
    # not a usable citation destination.
    if ".." in host or host.startswith(".") or host.endswith("."):
        return [(rel, url, "malformed-host")]
    # The port is read from the PARSER, not by splitting the authority by
    # hand: a hand-split swallowed a query or fragment into the port and
    # rejected valid URLs like https://github.com:443?x=y.
    try:
        parsed_port = urllib.parse.urlsplit(url).port
    except ValueError:
        return [(rel, url, "malformed-port")]
    if parsed_port is not None and not (0 < parsed_port <= 65535):
        return [(rel, url, "malformed-port")]
    if host.endswith(".local"):
        return [(rel, url, "local")]
    # All three RFC 2606 placeholder domains, matched as suffixes as well as exactly:
    # matching only `.example.com` let `docs.example.org` classify as a public source and
    # increment the ok-count, which made that count not a count of public citations.
    if host in ("example.com", "example.org", "example.net") or any(
        host.endswith("." + d) for d in ("example.com", "example.org", "example.net")
    ):
        return [(rel, url, "placeholder-host")]
    # RFC 2606/6761 reserved names can never resolve, so a citation using
    # one is not a source. The denylist alone let https://localhost.invalid
    # through as a "public host".
    if (
        host == "invalid"
        or host.endswith(".invalid")
        or host == "test"
        or host.endswith(".test")
        or host.endswith(".localdomain")
    ):
        return [(rel, url, "reserved-tld")]
    # A bare label with no dot (http://intranet) cannot be a public host.
    if "." not in host:
        return [(rel, url, "not-a-public-hostname")]
    # A public https citation. The docstring above states what this does NOT decide
    # (upstream vs fork, semantic rightness), so the reminder is not repeated here where
    # it would sit after the return and be unreachable.
    return []


def export_file_set(dest_root):
    """Every regular file under the export, INCLUDING any .git/node_modules
    subtree. Pruning them here would let an export carrying git history report
    the same file set as a clean one — the inventory must see what is there,
    and the manifest comparison is what rejects it."""
    found = []
    for dirpath, dirnames, filenames in os.walk(dest_root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, dest_root).replace(os.sep, "/")
            found.append(rel)
    return found


def sha256_export(dest_root, entries):
    h = hashlib.sha256()
    for rel in sorted(entries):
        h.update(rel.encode("utf-8") + b"\x00")
        h.update(open(os.path.join(dest_root, rel), "rb").read())
        h.update(b"\x00")
    return "sha256:" + h.hexdigest()


def prove_undecodable_fails_certification():
    """An export seeded with an undecodable regular file must FAIL, not skip.

    This invokes the SAME certifier the real export uses, in a child process, and
    requires a nonzero exit. A fixture that re-implemented the check would keep
    passing after the production check was weakened or removed.
    """
    tmp = tempfile.mkdtemp(prefix="export-bad-utf8-")
    try:
        bad = os.path.join(tmp, "docs")
        os.makedirs(bad)
        open(os.path.join(bad, "ok.md"), "w", encoding="utf-8").write("ok\n")
        bad_path = os.path.join(bad, "bad.md")
        open(bad_path, "wb").write(b"good text\xff\xfe not utf-8\n")
        if not os.path.getsize(bad_path):
            fail("seeded undecodable fixture is empty")
        # Run the real certifier over the seeded tree in a child process and
        # require that IT rejects. `--certify-only` is this suite's own mode.
        #
        # `__file__` is '<stdin>' when the suite is piped into the interpreter, so
        # the child would fail to launch and any nonzero status would look like a
        # successful rejection. The child's own diagnostic must therefore name the
        # UTF-8 failure; a launch error cannot satisfy that.
        # The launcher pipes this program to the interpreter, so __file__ is the
        # literal '<stdin>' and the program text cannot be re-read from disk. The
        # chapter path IS available, though, so the block is extracted from it the same
        # way the launcher extracted it: the fenced region holding the suite. The child
        # then runs the real certifier, and its own UTF-8 diagnostic is required below
        # so a launch failure cannot be mistaken for a rejection.
        chapter_lines = open(CHAPTER_PATH, encoding="utf-8").read().split(chr(10))
        # The suite is the chapter's one fenced `bash` block. Look for the opening
        # fence line that announces it and take everything to the next column-0 fence.
        # Hand-rolling a second delimiter scan here reproduced the very bug this
        # project removed: the first attempt swallowed the terminator into the child
        # program and the child died on an undefined name.
        # The suite is the region between the chapter's verification-suite sentinels,
        # and inside that region the program is a `python3 - <<'PY' ... PY` heredoc.
        # Both delimiters are read from the chapter rather than guessed at: an earlier
        # attempt scanned for the first import line and swallowed the terminator, and
        # the child died on an undefined name.
        src = chr(10).join(chapter_lines)
        # The sentinel names are CONSTRUCTED, not written literally: this program is
        # itself inside the region it is parsing, and a literal copy would make the
        # chapter contain two sentinel pairs, which the launcher refuses.
        open_mark = "<!-- verification-suite:" + "start -->"
        close_mark = "<!-- verification-suite:" + "end -->"
        fm = re.search(
            re.escape(open_mark) + "(.*?)" + re.escape(close_mark),
            src,
            re.S,
        )
        if fm is None:
            fail("cannot find the verification-suite sentinels in %s" % CHAPTER_PATH)
        hm = re.search(r"<<'PY'\n(.*?)\nPY\n", fm.group(1), re.S)
        if hm is None:
            fail("cannot find the python heredoc inside the suite region in %s" % CHAPTER_PATH)
        source = hm.group(1)
        runner = os.path.join(tmp, "certifier.py")
        with open(runner, "w", encoding="utf-8") as handle:
            handle.write(source)
        proc = subprocess.run(
            [sys.executable, runner, "--certify-only", tmp],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        err = proc.stderr.decode("utf-8", "replace")
        if "Traceback" in err:
            fail("the certifier crashed on the undecodable fixture:\n" + err)
        if proc.returncode == 0:
            fail(
                "seeded undecodable file PASSED certification; the production "
                "UTF-8 check does not reject it"
            )
        if "utf-8" not in err.lower() and "utf" not in err.lower():
            fail(
                "the certifier rejected the fixture but not for the UTF-8 reason; "
                "a launch failure would look identical:\n" + err
            )
        note_pass(
            "seeded undecodable regular file fails certification "
            "(child exit %s, not skipped)" % proc.returncode
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BARE_DEST_IMPORT = re.compile(r"^@([^\s]+)", re.M)


def is_url(target):
    return target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:")


def split_link(target):
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if " " in target and not target.startswith("http"):
        target = target.split(" ", 1)[0]
    frag = ""
    if "#" in target:
        path, frag = target.split("#", 1)
    else:
        path = target
    return path, frag


def github_slug(heading):
    """Approximate GitHub heading slugs.

    Punctuation including em/en-dash is dropped (not turned into a hyphen).
    Each remaining space becomes a hyphen, so a dash that sat between spaces
    becomes '--' — which is what the in-chapter links actually use.
    """
    h = heading.strip().lower()
    h = re.sub(r"[^\w\s-]", "", h)
    h = h.replace(" ", "-").strip("-")
    return h


def check_anchor(path, frag):
    if not frag:
        return True
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return False
    slug = frag.strip().lower()
    for line in text.splitlines():
        # Up to three leading spaces is still an ATX heading in CommonMark; requiring
        # column zero rejected a link to an indented heading that the scope claims to
        # support.
        m = re.match(r" {0,3}#{1,6}\s+(.*)$", line)
        if not m:
            continue
        if github_slug(m.group(1)) == slug:
            return True
    if re.search(r'id=["\']' + re.escape(frag) + r'["\']', text):
        return True
    return False


def line_in_fence(lines, lineno):
    """True if 1-based lineno sits inside a fenced code block (column-0 fence).

    Both backtick and tilde fences count. Recognising only backticks meant a link
    quoted inside a ~~~ example was treated as a real reference.
    """
    in_fence = False
    fence = None
    fence_indent = 0
    for i, line in enumerate(lines, 1):
        # Up to three leading spaces is still a fence in CommonMark. The CLOSER must
        # allow at least the opener's own indentation: matching it at column zero only
        # left an indented fence open forever, so a later example looked like real
        # prose and its @-import was reported missing.
        m = re.match(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})", line)
        if m:
            mark = m.group("fence")
            indent = len(m.group("indent"))
            if not in_fence:
                in_fence = True
                fence = mark
                fence_indent = indent
            elif indent <= fence_indent and line.lstrip().startswith(fence):
                in_fence = False
                fence = None
            if i == lineno:
                return True  # the fence line itself is example chrome
            continue
        if i == lineno:
            return in_fence
    return False


def check_links_in_export(dest_root, entries):
    broken = []
    checked = 0
    dest_imports = []
    for rel in entries:
        if not rel.endswith((".md", ".txt")):
            continue
        full = os.path.join(dest_root, rel)
        text = open(full, encoding="utf-8").read()
        here = os.path.dirname(full)
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if line_in_fence(lines, i):
                continue
            # Inline `code` may contain example markdown links that are not
            # navigable references (a table showing the stamped pointer).
            # Backticks pair up only when UNESCAPED. An escaped backtick (\`) is
            # literal text, and pairing it anyway made everything between it and the
            # next backtick look like a code span — so a real link written between two
            # escaped backticks was skipped entirely and a broken one passed.
            ticks = []
            pos = 0
            while pos < len(line):
                idx = line.find("`", pos)
                if idx < 0:
                    break
                backslashes = 0
                j = idx - 1
                while j >= 0 and line[j] == "\\":
                    backslashes += 1
                    j -= 1
                if backslashes % 2 == 0:
                    ticks.append(idx)
                pos = idx + 1
            # A run of N backticks closes only at a run of exactly N, so runs are
            # grouped by length. Pairing individual backticks made `` ... `` swallow a
            # real link between them. The loop variable is `n`, NOT `i`: reusing `i`
            # overwrote the line number and every diagnostic printed file:0.
            runs = []
            pos = 0
            while pos < len(line):
                idx = line.find("`", pos)
                if idx < 0:
                    break
                backslashes = 0
                j = idx - 1
                while j >= 0 and line[j] == "\\":
                    backslashes += 1
                    j -= 1
                run = 0
                if backslashes % 2 == 0:
                    while idx + run < len(line) and line[idx + run] == "`":
                        run += 1
                    runs.append((idx, run))
                pos = idx + (run if run else 1)
            inline_spans = []
            used = set()
            for n, (idx, run) in enumerate(runs):
                if n in used:
                    continue
                for m2 in range(n + 1, len(runs)):
                    if m2 in used:
                        continue
                    if runs[m2][1] == run:
                        inline_spans.append((idx, runs[m2][0] + run))
                        used.add(n)
                        used.add(m2)
                        break
            for m in MD_LINK.finditer(line):
                if any(a <= m.start() and m.end() <= b + 1 for a, b in inline_spans):
                    continue
                raw = m.group(2).strip()
                path, frag = split_link(raw)
                if not path:
                    # fragment-only link in the same file
                    if frag and not check_anchor(full, frag):
                        broken.append("%s:%d dead-anchor #%s" % (rel, i, frag))
                    continue
                if is_url(path):
                    checked += 1
                    continue
                if path.startswith("~/") or path.startswith("$HOME") or path.startswith("~"):
                    dest_imports.append("%s:%d destination-layout %s" % (rel, i, path))
                    checked += 1
                    continue
                target = os.path.normpath(os.path.join(here, path))
                rel_t = os.path.relpath(target, dest_root).replace(os.sep, "/")
                if rel_t.startswith(".."):
                    broken.append("%s:%d escapes export: %s" % (rel, i, path))
                    continue
                if os.path.isdir(target) or os.path.isfile(target):
                    checked += 1
                    if frag and os.path.isfile(target) and not check_anchor(target, frag):
                        broken.append("%s:%d dead-anchor %s#%s" % (rel, i, path, frag))
                    continue
                broken.append("%s:%d missing %s" % (rel, i, path))
            for m in BARE_DEST_IMPORT.finditer(line):
                spec = m.group(1).strip()
                if spec.startswith("~/"):
                    dest_imports.append("%s:%d @-import destination-layout @%s" % (rel, i, spec))
                    checked += 1
                    continue
                if spec.endswith(".md") or spec == "AGENTS.md":
                    sibling = os.path.normpath(os.path.join(here, spec))
                    if os.path.isfile(sibling):
                        checked += 1
                    else:
                        broken.append("%s:%d missing @-import %s" % (rel, i, spec))
    return broken, checked, dest_imports


TEMPLATE_FILES = [
    "templates/global/AGENTS.md",
    "templates/global/CLAUDE.md",
    "templates/global/claude-overlay.md",
    "templates/global/pi-overlay.md",
    "templates/repo/AGENTS.md",
    "templates/repo/CLAUDE.md",
    "templates/repo/INTENT.md",
    "templates/repo/WORKLOG.md",
]


# Each enforcement function is a PURE VERDICT: it fails closed on a defect and records
# nothing on success. The success assertions live at the production call sites instead.
#
# That separation is not cosmetic. When the success `check()` calls lived inside these
# functions, a prover exercising them with synthetic fixtures emitted PASS lines reading
# "found 5 https:// citation URLs" and "explanation matrix (1 rows)" into the real
# transcript -- fixture literals presented as evidence, in a run whose true
# count was 30. An evidence record must not manufacture PASS lines, and the only way
# to guarantee that is to keep recording out of any function a prover can call.
def enforce_link_integrity(broken):
    """Fail on any broken link in the export. Records nothing on success."""
    if broken:
        for b in broken:
            sys.stderr.write("BROKEN: %s\n" % b)
        fail("%d broken local link(s); see BROKEN lines" % len(broken))


def enforce_citation_urls(url_hosts_bad):
    """Fail on any non-public-https citation URL. Records nothing on success."""
    if url_hosts_bad:
        for rel, url, why in url_hosts_bad:
            sys.stderr.write("BAD-URL: %s %s (%s)\n" % (rel, url, why))
        fail("%d citation URL(s) are not public https://" % len(url_hosts_bad))


def enforce_rule_explanations(missing):
    """Fail when a rule-like item has no explanation. Records nothing on success."""
    if missing:
        fail("rule item(s) with neither Failure prevented: nor an explanation link: %s" % ", ".join(missing))


def rule_explanation_matrix(dest_root):
    """Pair rule-like items with Failure prevented: or a docs/ path REFERENCE.

    Regex cannot certify semantic adequacy, and it cannot resolve these references
    either: a bare `docs/...` string satisfies this check whether or not the file
    exists. What IS verified is the weaker, still-useful property that the rule carries
    SOME pointer or explanation rather than standing alone — a matrix line labelled
    "explanation link (section)" means a reference was seen, not that it resolves.
    Resolving them is the reviewer's job, and this limitation is stated so the label is
    not mistaken for a stronger claim.

    A Failure prevented: (or a docs/ reference) that follows a *cluster* of bullets in
    the same section counts for every bullet in that section — that is how these
    templates are written. Placeholder WORKLOG fields (What / Decided / Open) are
    format, not rules. The suite fails closed on an empty template, and on a section
    that has hard-rule bullets and no explanation anywhere in that section.
    """
    rows = []
    missing = []
    for rel in TEMPLATE_FILES:
        path = os.path.join(dest_root, rel)
        require_file(path, "template")
        text = open(path, encoding="utf-8").read()
        lines = text.splitlines()
        # Section starts at headings; index 0 is the lead-in before the first heading.
        sections = []
        cur = {"start": 0, "lines": []}
        for i, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+", line):
                sections.append(cur)
                cur = {"start": i, "lines": []}
            cur["lines"].append((i, line))
        sections.append(cur)
        for sec in sections:
            body = "\n".join(ln for _, ln in sec["lines"])
            has_fp = "Failure prevented:" in body
            has_link = bool(re.search(r"\]\([^)]*docs/[^)]+\)", body)) or "`docs/" in body
            bullets = []
            for i, line in enumerate(sec["lines"]):
                idx, text_ln = line
                stripped = text_ln.strip()
                if not stripped.startswith("- "):
                    continue
                if re.match(r"^- \*\*(What|Decided|Open):\*\*", stripped):
                    continue
                if re.match(r"^- (What|Decided|Open):", stripped):
                    continue
                if stripped.startswith("- [") and "](" in stripped:
                    continue
                bullets.append((idx + 1, stripped))
            if not bullets:
                continue
            explained = has_fp or has_link
            for lineno, stripped in bullets:
                loc = "%s:%d" % (rel, lineno)
                low = stripped.lower()
                looks_hard = (
                    stripped.startswith("- **")
                    # The modal/imperative set. "- Always ..." and a bare "MUST" used to
                    # fall through to "orientation (reviewer-judged; not a hard rule)",
                    # so an unexplained hard rule phrased that way never failed the check
                    # while the prose claimed rule-like items are paired with reasons.
                    or " never " in low
                    or " always " in low
                    or low.startswith("- never ")
                    or low.startswith("- always ")
                    or low.startswith("- must")
                    or low.startswith("- do not")
                    or " must " in low
                    or "must not" in low
                )
                if explained:
                    how = ("Failure prevented: (section)" if has_fp
                           else "docs/ reference seen, not resolved (section)")
                    rows.append((loc, how))
                elif looks_hard:
                    missing.append(loc)
                    rows.append((loc, "MISSING explanation"))
                else:
                    rows.append((loc, "orientation (reviewer-judged; not a hard rule)"))
    return rows, missing


def parse_count_block(text):
    counts = {}
    for line in text.splitlines():
        if line.startswith("count:"):
            parts = line.split(":", 2)
            if len(parts) == 3:
                counts[parts[1]] = int(parts[2])
    return counts


# Header names that mark a table's SOURCE column. The column is identified by its header
# rather than by position, so a table whose source column comes first is read correctly
# and an unrelated URL in a Result column is not mistaken for a citation.
ANY_URL_IN_TABLE = re.compile("(?i)\\b(?:[a-z][a-z0-9+.\\-]*://[^\\s)>\"|'`]*|mailto:[^\\s)>\"|'`]*)")


# A table header names a SOURCE column when any of its words is a source word. Matched
# as a TOKEN SET rather than by exact equality: the chapters write "Public source",
# "Upstream source (section)", "Source", "URL". The exact-match list this replaced read
# NONE of the chapter tables -- all 30 classified URLs came from NOTICES.md -- so a bare
# http:// planted in a chapter's Public source cell passed certification. That was
# measured, not theorised, and it is a hole per table rather than a global one, which the
# caller's "at least one sourced table" guard cannot see.
SOURCE_COLUMN_WORDS = ("source", "sources", "upstream", "url")


def is_source_header(name):
    """True when a table header cell names the SOURCE column."""
    words = re.split(r"[^a-z]+", name.strip().strip("*").lower())
    return any(w in SOURCE_COLUMN_WORDS for w in words if w)


def claim_table_bare_http(path):
    """Yield bare http:// URLs found in ANY cell of a claim-to-source table.

    Separate from claim_table_source_urls because it must look at EVERY cell, not only
    the source column: a downgraded citation sitting in a cell the header match does not
    name is still a downgraded citation. Reading only markdown link targets missed this
    entirely -- measured: a bare http:// planted in a Public source cell passed
    certification with no BAD-URL line.
    """
    header = None
    for line in open(path, encoding="utf-8"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        for cell in cells:
            for m in ANY_URL_IN_TABLE.finditer(cell):
                url = m.group(0).rstrip(".,;")
                if url.lower().startswith("http://") and not url.lower().startswith("http://localhost"):
                    yield url


def claim_table_source_urls(path):
    """Yield (url, is_https) for URLs in the SOURCE column of a claim-to-source table.

    The column is identified by its HEADER, not by position. Scanning cells[2:] assumed
    a fixed layout, which both missed a table whose Source column came first and
    rejected an unrelated http:// value sitting in a Result column — the rule is about
    sources, so the header is what decides. A table with no recognisable source column
    yields nothing, and the caller's separate requirement that at least one sourced
    table exists keeps that from becoming a silent hole.
    """
    header = None
    for line in open(path, encoding="utf-8"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue  # the alignment row
        for idx, name in enumerate(header):
            if not is_source_header(name):
                continue
            if idx >= len(cells):
                continue
            for m in ANY_URL_IN_TABLE.finditer(cells[idx]):
                url = m.group(0).rstrip(".,;")
                yield url, url.lower().startswith("https://")


def host_of(url):
    """Return just the hostname: no scheme, no userinfo, no port, no trailing dot.

    This is deliberately delegated to the standard library rather than hand-parsed.
    Successive hand-written trims each missed a case the previous one did not —
    a port, a trailing DNS dot, then a query string — because "the authority ends at
    the first slash" is not what a URL's grammar says. urlsplit implements the
    grammar, so the failure mode disappears instead of being patched again.
    """
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return ""
    host = (parts.hostname or "").lower()
    # A repeated dot is malformed and must be seen BEFORE normalising: stripping first
    # turned "github.com.." into the valid name "github.com", so a malformed host
    # certified as public.
    if ".." in host:
        return host
    # A single terminal dot is the absolute form of the same name; urlsplit keeps it.
    return host.rstrip(".")


def _replay_certifier(tmp, label, expect_message):
    """Run the real certifier over `tmp` in a child process and require rejection.

    The child is fed this program's own text, extracted from the chapter the same way
    the launcher extracts it. Requiring the child's own diagnostic keeps a launch
    failure from being mistaken for a rejection.
    """
    chapter_lines = open(CHAPTER_PATH, encoding="utf-8").read().split(chr(10))
    src = chr(10).join(chapter_lines)
    open_mark = "<!-- verification-suite:" + "start -->"
    close_mark = "<!-- verification-suite:" + "end -->"
    fm = re.search(re.escape(open_mark) + "(.*?)" + re.escape(close_mark), src, re.S)
    if fm is None:
        fail("cannot find the verification-suite sentinels in %s" % CHAPTER_PATH)
    hm = re.search(r"<<\'PY\'\n(.*?)\nPY\n", fm.group(1), re.S)
    if hm is None:
        fail("cannot find the python heredoc inside the suite region")
    runner = os.path.join(tmp, "certifier.py")
    with open(runner, "w", encoding="utf-8") as handle:
        handle.write(hm.group(1))
    proc = subprocess.run(
        [sys.executable, runner, "--certify-only", tmp],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    err = proc.stderr.decode("utf-8", "replace")
    if "Traceback" in err:
        fail("%s: the certifier crashed:\n%s" % (label, err))
    if proc.returncode == 0:
        fail("%s: the certifier PASSED a tree it must reject" % label)
    if expect_message not in err:
        fail(
            "%s: rejected for the wrong reason (expected %r):\n%s"
            % (label, expect_message, err)
        )


def prove_nul_file_fails_certification():
    """A NUL byte in an exported file must be rejected by the real certifier."""
    tmp = tempfile.mkdtemp(prefix="export-nul-")
    try:
        os.makedirs(os.path.join(tmp, "docs"))
        with open(os.path.join(tmp, "docs", "ok.md"), "w", encoding="utf-8") as handle:
            handle.write("ok\n")
        with open(os.path.join(tmp, "docs", "nul.md"), "wb") as handle:
            handle.write(b"text with a \x00 NUL byte\n")
        _replay_certifier(tmp, "seeded NUL file", "NUL")
        note_pass("seeded NUL-byte file fails certification (real certifier, real reason)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def prove_symlink_ancestor_fails_certification():
    """A manifest path whose ANCESTOR is a symlink must be refused by copy_export.

    The end-to-end case: move a whole manifest-covered directory outside the tree and
    replace it with a directory symlink, so every listed file is still a regular file
    and only the ancestor gives it away.
    """
    tmp = tempfile.mkdtemp(prefix="export-ancestor-")
    try:
        tree = os.path.join(tmp, "tree")
        os.makedirs(os.path.join(tree, "docs"))
        outside = os.path.join(tmp, "outside-docs")
        os.makedirs(outside)
        with open(os.path.join(outside, "page.md"), "w", encoding="utf-8") as handle:
            handle.write("content\n")
        shutil.rmtree(os.path.join(tree, "docs"))
        os.symlink(outside, os.path.join(tree, "docs"))
        dest = os.path.join(tmp, "dest")
        os.makedirs(dest)
        # copy_export calls fail(), which raises SystemExit after printing its
        # diagnostic. Catching it is what lets this prover report its own PASS line
        # instead of the whole suite aborting on the refusal it was testing for.
        # copy_export calls fail(), which increments the FAIL counter before exiting.
        # That increment is correct when the suite aborts, but here the refusal IS the
        # expected behaviour, so the counter is decremented and a PASS recorded —
        # otherwise the prover reports its own success and a failure in the same run.
        global FAIL
        # The expected refusal is written to stderr by fail() before it raises. That
        # message is indistinguishable in a log from a real failure, so stderr is
        # REDIRECTED into a buffer for the duration. It is buffered rather than thrown
        # away because the message is the evidence: any fail() inside copy_export exits
        # 1, so asserting only the status cannot tell this refusal from a different one
        # the fixture happened to trip.
        buffer = io.StringIO()
        saved_stderr = sys.stderr
        try:
            sys.stderr = buffer
            try:
                copy_export(tree, ["docs/page.md"], dest)
            except SystemExit as exc:
                if exc.code != 1:
                    sys.stderr = saved_stderr
                    fail("symlink-ancestor refusal exited %s, expected 1" % exc.code)
                FAIL -= 1
                captured = buffer.getvalue()
                sys.stderr = saved_stderr
                # The diagnostic is asserted, not merely the exit status: any fail()
                # inside copy_export returns 1, so a fixture that started tripping a
                # different refusal would otherwise still record a PASS here.
                if "symlinked directory" not in captured:
                    fail(
                        "symlink-ancestor refusal gave the wrong reason (expected "
                        "'symlinked directory', got %r)" % captured.strip()[:120]
                    )
                    return
                note_pass("a symlinked ancestor is refused by copy_export")
                return
            sys.stderr = saved_stderr
        finally:
            sys.stderr = saved_stderr
        fail("copy_export accepted a manifest path with a symlinked ancestor")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)



def prove_broken_inline_link_is_caught():
    """The link checker must REPORT a broken inline link, not merely run.

    The chapter guarantees that "a deliberately broken inline link added to one of
    them is caught". That guarantee had no executed check behind it: the checker ran
    once on the unmodified export and only `checked > 0` guarded the call, so a
    checker that counted targets and never appended to `broken` left the suite
    fully green. A count of things examined is not evidence that anything was ever
    rejected, so this seeds a real defect into a real destination tree and requires
    the checker to name it -- including the positive control that the SAME tree with
    the link repaired reports nothing, which is what stops a checker that flags
    everything from passing this prover.
    """
    tmp = tempfile.mkdtemp(prefix="export-linkprover-")
    try:
        dest = os.path.join(tmp, "dest")
        os.makedirs(os.path.join(dest, "docs"))
        with open(os.path.join(dest, "docs", "ok.md"), "w", encoding="utf-8") as handle:
            handle.write("# Title\n\nSee [the other page](other.md).\n")
        with open(os.path.join(dest, "docs", "other.md"), "w", encoding="utf-8") as handle:
            handle.write("# Other\n\nBack to [title](ok.md).\n")
        entries = ["docs/ok.md", "docs/other.md"]
        clean_broken, clean_checked, _ = check_links_in_export(dest, entries)
        if clean_checked == 0:
            fail("link prover examined no links; the checker is not looking at the fixture")
            return
        if clean_broken:
            fail("link prover's CLEAN tree was reported broken: %r" % (clean_broken,))
            return
        # Seed the defect: one link whose target does not exist.
        with open(os.path.join(dest, "docs", "ok.md"), "a", encoding="utf-8") as handle:
            handle.write("\nDangling [gone](missing-page.md).\n")
        broken, _, _ = check_links_in_export(dest, entries)
        if not any("missing-page.md" in b for b in broken):
            fail("a deliberately broken inline link was NOT caught: %r" % (broken,))
            return
        note_pass("a deliberately broken inline link is caught by the link checker")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def prove_refusal_reasons_are_distinguished():
    """copy_export must refuse a symlinked ENTRY and a non-regular file, and say why.

    Two refusals had no negative regression at all: deleting either left the suite
    green while the property they guard ("Symlinks are refused") is what stops the
    export from following a manifest entry out of its own tree. The direct-symlink
    check is also the ONLY guard for an entry that is itself a link, because
    check_no_symlink_ancestor deliberately walks ancestors only.

    Each case asserts the DIAGNOSTIC, not merely a non-zero exit: an ancestor
    refusal and a fifo refusal are different defects, and a prover that accepts any
    SystemExit cannot tell them apart or notice a fixture that started failing for
    an unrelated reason.
    """
    # FAIL is decremented when the refusal under test is the expected outcome; without
    # this declaration that assignment raises, and the consumer proves it: the suite
    # crashed with "cannot access local variable 'FAIL'" before this line existed.
    global FAIL
    tmp = tempfile.mkdtemp(prefix="export-refusal-")
    try:
        tree = os.path.join(tmp, "tree")
        dest = os.path.join(tmp, "dest")
        os.makedirs(tree)
        os.makedirs(dest)
        outside = os.path.join(tmp, "outside.md")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write("content that must not be exported\n")
        os.symlink(outside, os.path.join(tree, "linked.md"))
        fifo = os.path.join(tree, "pipe.md")
        if hasattr(os, "mkfifo"):
            os.mkfifo(fifo)
        for rel, expect, label in (
            ("linked.md", "symlink in export set", "a symlinked manifest entry"),
            ("pipe.md", "non-regular file", "a non-regular (fifo) manifest entry"),
        ):
            if not os.path.exists(os.path.join(tree, rel)):
                fail("refusal prover could not build the %s fixture" % label)
                return
            # stderr is CAPTURED, not discarded: the diagnostic is the evidence that
            # the refusal came from the check under test and not from some other
            # fail() inside copy_export that the fixture happened to trip.
            captured = io.StringIO()
            saved = sys.stderr
            try:
                sys.stderr = captured
                try:
                    copy_export(tree, [rel], dest)
                except SystemExit as exc:
                    if exc.code != 1:
                        sys.stderr = saved
                        fail("%s refusal exited %s, expected 1" % (label, exc.code))
                        return
                    FAIL -= 1
                else:
                    sys.stderr = saved
                    fail("copy_export ACCEPTED %s" % label)
                    return
            finally:
                sys.stderr = saved
            if expect not in captured.getvalue():
                fail(
                    "%s was refused for the wrong reason (expected %r, got %r)"
                    % (label, expect, captured.getvalue().strip()[:120])
                )
                return
            note_pass("%s is refused by copy_export, with the right reason" % label)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def prove_unexplained_hard_rule_is_detected():
    """A hard-rule bullet with no explanation must be REPORTED by the matrix.

    The matrix is the suite's enforcement of "every rule-like item is paired with a
    reason", and it was the last production check with no negative regression: deleting
    the `if missing: fail(...)` call left the suite green while the prose kept claiming
    the pairing. A check whose failure path is never exercised is indistinguishable
    from one that cannot fail, so this plants an unexplained hard rule in a copy of a
    template and requires the matrix to name it -- with the clean copy as the control,
    proving the detector is not simply flagging everything.
    """
    global FAIL
    tmp = tempfile.mkdtemp(prefix="rule-matrix-")
    try:
        dest = os.path.join(tmp, "dest")
        # Every file in TEMPLATE_FILES is required by rule_explanation_matrix, so the
        # fixture is built FROM that list rather than from a hardcoded pair: adding a
        # template moves the fixture with it instead of breaking this prover.
        for rel in TEMPLATE_FILES:
            path = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("# %s\n" % os.path.basename(rel))
        victim = os.path.join(dest, "templates", "repo", "AGENTS.md")
        # The control is a bullet with NO hard-rule marker, which the matrix is
        # documented to file as orientation rather than to flag. (A `- **Never** ...`
        # line here would be correctly flagged, so it cannot serve as the clean case.)
        with open(victim, "w", encoding="utf-8") as handle:
            handle.write("# AGENTS\n\n## Hard rules\n\n- Prefer small commits.\n")
        rows, missing = rule_explanation_matrix(dest)
        if missing:
            fail("rule matrix flagged a bullet that carries no hard-rule marker: %r" % (missing,))
            return
        if not rows:
            fail("rule matrix produced no rows for the fixture at all")
            return
        with open(victim, "a", encoding="utf-8") as handle:
            handle.write("- **Always** rewrite history before pushing.\n")
        rows2, missing2 = rule_explanation_matrix(dest)
        if not missing2:
            fail("an unexplained hard-rule bullet was NOT reported (rows=%r)" % (rows2,))
            return
        # The REAL enforcement path is invoked, in a child process, and must exit 1.
        # Calling the matrix alone would pass even with the production `fail()` deleted,
        # which is exactly how this check previously had no negative coverage.
        saved_stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
            try:
                enforce_rule_explanations(missing2)
            except SystemExit as exc:
                sys.stderr = saved_stderr
                FAIL_LOCAL = exc.code
            else:
                sys.stderr = saved_stderr
                fail("the rule-explanation enforcement accepted an unexplained hard rule")
                return
        finally:
            sys.stderr = saved_stderr
        if FAIL_LOCAL != 1:
            fail("rule-explanation enforcement exited %s, expected 1" % FAIL_LOCAL)
            return
        FAIL -= 1  # the refusal under test IS the expected outcome
        note_pass("an unexplained hard-rule bullet is reported by the rule matrix")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def prove_enforcement_paths_bite():
    """Each enforcement function must FAIL on a real defect and pass on a clean input.

    The three enforcement sites (links, citation URLs, rule explanations) previously
    had provers only for their DETECTORS, so deleting the enforcement left the suite
    green over the real defect -- a check one level up from the one being proved. Each
    is exercised here through the same function production calls, with a clean control
    so a function that fails unconditionally cannot pass.
    """
    global FAIL
    cases = (
        ("link integrity", enforce_link_integrity,
         lambda: ([], ), lambda: (["docs/x.md:1 missing y.md"],)),
        ("rule explanations", enforce_rule_explanations,
         lambda: ([], ), lambda: (["a:1"],)),
    )
    for label, fn, clean_args, dirty_args in cases:
        saved = sys.stderr
        try:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
            # Clean control: must NOT exit.
            try:
                fn(*clean_args())
            except SystemExit:
                sys.stderr = saved
                fail("%s enforcement rejected a CLEAN input" % label)
                return
            # Dirty: must exit 1.
            try:
                fn(*dirty_args())
            except SystemExit as exc:
                FAIL -= 1
                if exc.code != 1:
                    sys.stderr = saved
                    fail("%s enforcement exited %s, expected 1" % (label, exc.code))
                    return
            else:
                sys.stderr = saved
                fail("%s enforcement ACCEPTED a defective input" % label)
                return
        finally:
            sys.stderr = saved
        note_pass("%s enforcement fails closed on a defect and passes clean" % label)

    # Citation URLs take an extra count argument, so they are exercised separately.
    saved = sys.stderr
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
        try:
            enforce_citation_urls([])
        except SystemExit:
            sys.stderr = saved
            fail("citation-URL enforcement rejected a clean input")
            return
        try:
            enforce_citation_urls([("docs/x.md", "http://h/p", "not-https")])
        except SystemExit as exc:
            FAIL -= 1
            if exc.code != 1:
                sys.stderr = saved
                fail("citation-URL enforcement exited %s, expected 1" % exc.code)
                return
        else:
            sys.stderr = saved
            fail("citation-URL enforcement ACCEPTED a non-https citation")
            return
    finally:
        sys.stderr = saved
    note_pass("citation-URL enforcement fails closed on a defect and passes clean")


def prove_citation_classifier_bites():
    """Every rejection branch of the citation classifier must fire on its own shape.

    The classifier was inline in main, so no prover could reach it: deleting any single
    denylist branch left the suite green over a real defect. Each shape below is a URL
    that MUST be rejected, paired with a clean control proving the classifier is not
    simply rejecting everything.
    """
    must_reject = (
        ("http://github.com/x", False, "not-https"),
        ("https://localhost/x", True, "local-or-address"),
        ("https://foo.localhost/x", True, "local-or-address"),
        ("https://127.1/x", True, "local-or-address"),
        ("https://0x7f.1/x", True, "local-or-address"),
        ("https://2130706433/x", True, "local-or-address"),
        ("https://a..b/x", True, "malformed-host"),
        # :99999 raises in urlsplit().port and is caught by the ValueError arm; :0 does
        # NOT raise, so it is the case that actually exercises the range test.
        ("https://github.com:99999/x", True, "malformed-port"),
        ("https://github.com:0/x", True, "malformed-port"),
        ("https://intranet/x", True, "not-a-public-hostname"),
        ("https://example.com/x", True, "placeholder-host"),
        ("https://x.test/y", True, "reserved-tld"),
        ("https://x.invalid/y", True, "reserved-tld"),
        ("https://x.local/y", True, "local"),
        # The remaining branches. `unparseable` had NO shape, so deleting it left the
        # suite green (an empty host fell through to a different reason no test pinned).
        # The example.org/.net subdomains exposed an asymmetry: only .example.com was
        # matched as a suffix, so subdomains of the other two RFC 2606 placeholder
        # domains classified as public and inflated the ok-count.
        ("https://[::1/x", True, "unparseable"),
        ("https://docs.example.org/x", True, "placeholder-host"),
        ("https://a.example.net/y", True, "placeholder-host"),
    )
    for url, is_https, want in must_reject:
        got = classify_citation_url("docs/x.md", url, is_https)
        if not got:
            fail("citation classifier ACCEPTED %r (expected reason %r)" % (url, want))
            return
        if got[0][2] != want:
            fail("citation classifier gave %r for %r, expected %r" % (got[0][2], url, want))
            return
    # Clean control: a real public https citation must produce no findings.
    for url in ("https://github.com/earendil-works/pi", "https://registry.npmjs.org/x"):
        got = classify_citation_url("docs/x.md", url, True)
        if got:
            fail("citation classifier REJECTED a valid citation %r: %r" % (url, got))
            return
    note_pass(
        "citation classifier rejects all %d local/placeholder/reserved shapes and accepts public https"
        % len(must_reject)
    )


def certify_only(dest_root):
    """Certify an already-exported tree: every regular file must decode as
    valid UTF-8 with no NUL byte. Exits nonzero on the first violation.

    Used by the undecodable-file fixture so that proof runs the SAME code path
    the real export uses. A fixture that re-implemented the check would keep
    passing after this one was weakened or removed.
    """
    if not os.path.isdir(dest_root):
        fail("certify-only: not a directory: %s" % dest_root)
    seen = 0
    for dirpath, dirnames, filenames in os.walk(dest_root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, dest_root).replace(os.sep, "/")
            decode_utf8_no_nul(full, "exported file %s" % rel)
            seen += 1
    if seen == 0:
        fail("certify-only: no files found under %s" % dest_root)
    print("certify-only: %d file(s) certified" % seen)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--certify-only":
        if len(sys.argv) != 3:
            fail("usage: --certify-only <export-root>")
        certify_only(sys.argv[2])
        return
    print("suite: integrated export + evidence")
    print("cwd: %s" % ROOT)
    print("python: %s" % sys.version.split()[0])
    print("PYTHONOPTIMIZE=%s" % os.environ.get("PYTHONOPTIMIZE", ""))

    # --- manifest ---
    man_path = os.path.join(ROOT, MANIFEST_REL)
    entries = load_manifest(man_path)
    # note_pass, not check(): load_manifest already fail()s on a missing, empty or
    # blank-line manifest and appends every accepted line, so a returned list is
    # non-empty by construction. The COUNT is the earned fact; the comparison cannot fail.
    note_pass("manifest has %d entries" % len(entries))
    check("MANIFEST.txt" in entries, "manifest lists itself")
    check("docs/11-verification.md" in entries, "manifest lists this chapter")
    # The prose says the manifest lists LICENSE, NOTICES and README; that was asserted
    # for none of them, so removing LICENSE from both the tree and the manifest left
    # the suite green.
    for required in ("LICENSE", "NOTICES.md", "README.md", "MANIFEST.txt"):
        check(required in entries, "manifest lists %s" % required)
    # Every text file ends with exactly one newline. Twenty-one did not when this check
    # was added - a publishing defect no assertion covered, so a reader opening a
    # chapter saw a file whose last line ran into the end.
    for rel in entries:
        # EVERY manifest file is checked, not a list of extensions: LICENSE has no
        # extension, and an extension filter silently exempted it - so removing its
        # final newline left the suite green.
        raw = open(os.path.join(ROOT, rel), "rb").read()
        if b"\x00" in raw:
            continue  # binary content: a trailing-newline rule does not apply
        check(raw.endswith(b"\n"), "%s ends with a newline" % rel)
        check(not raw.endswith(b"\n\n"), "%s ends with exactly one newline" % rel)
    check("tools/leak-scan.sh" in entries, "manifest lists the detector")
    expected_prefixes = (
        "docs/",
        "templates/",
        "examples/",
        "tools/",
        "scripts/",
        "ADOPTING.md",
        "README.md",
        "LICENSE",
        "NOTICES.md",
        "MANIFEST.txt",
    )
    # The loop fails closed on an unexpected path; the PASS line records HOW MANY
    # entries were checked, so it states a fact instead of restating that no failure
    # occurred. A bare `check(True, ...)` is an always-true PASS line.
    checked_paths = 0
    for rel in entries:
        if not any(rel == p or rel.startswith(p) for p in expected_prefixes if p.endswith("/") or rel == p):
            if rel not in ("README.md", "LICENSE", "NOTICES.md", "MANIFEST.txt"):
                fail("unexpected manifest path: %s" % rel)
        checked_paths += 1
    # note_pass, not check(): the loop's fail() already exits on any deviation, so a
    # `checked_paths == len(entries)` condition would be true by construction -- the same
    # shape as the `copied == entries` line removed earlier. The COUNT is the earned fact
    # and is worth recording; the comparison is not a check and must not be dressed as one.
    note_pass("all %d manifest paths are in the approved publication set" % checked_paths)

    chapters = [e for e in entries if e.startswith("docs/") and e.endswith(".md") and "/boundaries/" not in e]
    check(len(chapters) == 11, "eleven chapter files in manifest (got %d)" % len(chapters))
    for n in range(1, 12):
        needle = "docs/%02d-" % n
        check(any(e.startswith(needle) for e in chapters), "chapter %02d listed" % n)

    # --- copy only listed files; never recurse docs ---
    dest = tempfile.mkdtemp(prefix="export-suite-")
    print("export_root=%s" % dest)
    try:
        copied = copy_export(ROOT, entries, dest)
        # `copied == entries` was checked here and could never fail: copy_export appends
        # each input element in order and exits via fail() on any deviation, so the PASS
        # was true by construction. The independent observation is the walk of the
        # destination below, which reads what actually landed on disk.
        del copied
        found = export_file_set(dest)
        check(sorted(found) == sorted(entries), "export regular-file set equals manifest")
        # bytes identity, counted so the PASS line states a fact
        identical = 0
        for rel in entries:
            src_b = open(os.path.join(ROOT, rel), "rb").read()
            dst_b = open(os.path.join(dest, rel), "rb").read()
            if src_b != dst_b:
                fail("exported bytes differ from source: %s" % rel)
            identical += 1
        # note_pass for the same reason: the in-loop fail() already exits on a mismatch,
        # so comparing the counter to len(entries) cannot fail. The count is the fact.
        note_pass("exported bytes match source for all %d listed files" % identical)
        # The "export does not contain a git directory" check that stood here could
        # never fail: `dest` is a fresh mkdtemp written only by copy_export, and the
        # manifest already rejects any path with a hidden component. It was asserting a
        # property of mkdtemp, not of the template. The real guarantee is the set
        # equality above (nothing beyond the manifest landed) plus the source-tree
        # exclusions, so it is removed rather than kept as a ceremonial PASS.

        # An `extra == 0` check sat here and could never fail once the set equality
        # above had passed -- the same duplicate-PASS shape removed elsewhere.

        # ...and, separately, that the SUBMITTED TREE contains nothing the manifest
        # omits. The check above only inspects the copy, which was built by walking the
        # manifest — so by construction it can never see a source file that was left
        # out. A file added under the repository root would pass it silently.
        # Only the PUBLICATION area is checked for completeness. The planning bundle
        # under docs/masterplan/ is explicitly outside the export (it holds the
        # process record and is not part of the published tree), so it is scanned as a
        # subtree exclusion rather than as an allowlist of individual names.
        # Exclusions are DECLARED, matched against whole relative paths, and their
        # contents are counted and reported. Pruning directory names inside the walk
        # instead made them invisible: a file dropped into .git/, node_modules/,
        # __pycache__/ or docs/masterplan/ passed certification silently, because
        # nothing ever looked. A declared exclusion that reports how many files it
        # covered cannot hide a file without saying so.
        EXCLUDED_TREES = (
            # These two name the layout of a working copy that still holds the private
            # planning bundle and the review evidence owned by whoever ran the review;
            # both live outside the export by design.
            # They are ordinary directory names, not private identifiers, and they are
            # INERT in a published copy -- _excluded matches paths, and a tree without
            # those directories never produces the keys. A reader's copy therefore needs
            # nothing added; the check below accounts for the difference instead of
            # demanding these trees exist.
            # The match below is root-relative, so a builder's own ROOT-level
            # directory named `review` inherits this exclusion silently and its
            # files go un-inspected: rename yours, or edit this list in your copy.
            "docs/masterplan",   # planning bundle (working copy that still holds it)
            "review",            # review evidence (same; not in a published copy)
            ".git",              # version control, not publication content
            "node_modules",      # vendored dependencies, if any are ever added
            "__pycache__",       # interpreter bytecode caches
            ".pi",               # the harness's own runtime state (memory, queues)
        )
        EXCLUDED_FILES = (".export-digest.txt",)  # evidence, deliberately outside

        def _excluded(rel):
            for tree in EXCLUDED_TREES:
                if rel == tree or rel.startswith(tree + "/"):
                    return tree
            for name in EXCLUDED_FILES:
                # Root-relative only. Matching on basename also excluded a nested file
                # that merely shared the name, hiding it from the completeness walk
                # while the declaration names one root-level evidence file.
                if rel == name:
                    return name
            return None

        source_files = set()
        skipped = {}
        # onerror is set because the default silently swallows PermissionError: files
        # beneath an unreadable directory would never enter source_files, and
        # "no unlisted files in the publication area" would pass over a tree region
        # that was never looked at -- a completeness claim failing open.
        for dirpath, dirnames, filenames in os.walk(ROOT, onerror=lambda e: fail("cannot list the tree: %s" % e)):
            for name in filenames:
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
                which = _excluded(rel)
                if which is not None:
                    skipped[which] = skipped.get(which, 0) + 1
                    continue
                source_files.add(rel)
        unlisted_source = sorted(source_files - set(entries))
        # The claim is scoped to the PUBLICATION AREA, which is what this check can
        # actually see. A declared exclusion (.git, the planning bundle, a vendored
        # tree, a bytecode cache) may contain anything: those are not publication
        # content, and .git in particular must exist. Saying "no unlisted files in the
        # submitted tree" would overstate that, because the excluded subtrees are by
        # definition not inspected.
        check(
            len(unlisted_source) == 0,
            "no unlisted files in the publication area (found %s)" % unlisted_source[:10],
        )
        # Two checks used to sit here that could NEVER fail, and both are gone:
        #   * a per-exclusion `count > 0`, whose dict keys only ever arrived by
        #     incrementing from 1;
        #   * `k not in declared` over keys produced solely by the function that returns
        #     members of `declared` -- a tautology.
        # Each contributed an always-true PASS line, and idle PASS lines are the one
        # thing an evidence record must not manufacture.
        #
        # What IS assertable is that a working copy's own exclusions are still
        # matched, because a tree that silently stops being excluded stops being
        # inspected. The two layouts differ, so the check is scoped:
        #   * a working copy that still holds the planning bundle has .git AND it;
        #   * a CLEAN export -- built from MANIFEST.txt alone, and where this
        #     chapter's own instructions tell the reader to run it -- has neither.
        # Scoping is by the planning bundle's presence, not .git's: a reader who puts
        # an export under version control gains a .git, which would otherwise be read
        # as "still holds the bundle" and fail certification on the tree it certifies.
        # The asymmetric case is a FAILURE, not a note: a tree carrying the private
        # planning bundle but no version control is a layout this suite does not know,
        # and guessing which one it is is how a completeness claim fails open.
        has_planning = os.path.isdir(os.path.join(ROOT, "docs/masterplan"))
        has_git = os.path.isdir(os.path.join(ROOT, ".git"))
        if has_planning:
            if has_git:
                check(
                    "docs/masterplan" in skipped,
                    "working copy holding the planning bundle: a declared, counted exclusion"
                )
            else:
                fail(
                    "this tree holds docs/masterplan but no .git: it is neither a working "
                    "copy holding the bundle nor a clean export, so the exclusion layout is unknown"
                )
        else:
            note("published copy (no planning bundle): source-checkout exclusions do not apply")


        print(
            "source-tree exclusions (NOT inspected, NOT part of the export): %s"
            % ", ".join("%s=%d file(s)" % (k, v) for k, v in sorted(skipped.items()))
        )

        # One negative regression per production check in the certifier, each proving
        # that a REAL defect makes the real certifier fail. A single fixture covering
        # UTF-8 left the NUL check and the symlink-ancestor check with no negative
        # coverage at all: disabling either left the suite green.
        prove_undecodable_fails_certification()
        prove_nul_file_fails_certification()
        prove_symlink_ancestor_fails_certification()
        prove_broken_inline_link_is_caught()
        prove_refusal_reasons_are_distinguished()
        prove_unexplained_hard_rule_is_detected()
        prove_enforcement_paths_bite()
        prove_citation_classifier_bites()

        digest = sha256_export(dest, entries)
        if not digest.startswith("sha256:") or len(digest) != len("sha256:") + 64:
            fail("digest is malformed: %s" % digest)
        digest_path = os.path.join(ROOT, DIGEST_REL)
        digest_dir = os.path.dirname(digest_path)
        # Creating the directory is part of writing the digest, so it belongs inside the
        # same handler: a read-only parent failed here with a bare traceback while the
        # write itself already had an actionable message.
        try:
            if not os.path.isdir(digest_dir):
                os.makedirs(digest_dir, exist_ok=True)
        except OSError as exc:
            fail(
                "cannot create the digest directory %s: %s\n"
                "       Set EXPORT_DIGEST_PATH to a writable location, e.g.\n"
                "         EXPORT_DIGEST_PATH=/tmp/export-digest.txt bash %s --verify-document %s"
                % (digest_dir, exc, DETECTOR, CHAPTER_PATH)
            )
        # Refuse to write an empty digest; fail closed if the parent dir vanished.
        if not os.path.isdir(digest_dir):
            fail("digest directory missing: %s" % digest_dir)
        payload = digest + "\n"
        if payload.strip() == "":
            fail("refusing to write an empty digest")
        try:
            with open(digest_path, "w", encoding="utf-8") as handle:
                handle.write(payload)
        except OSError as exc:
            # A read-only copy of this template is the common case here, and the default
            # location is inside it. Say what to do rather than crashing with a
            # traceback that reads like a failed assertion.
            fail(
                "cannot write the digest to %s: %s\n"
                "       Set EXPORT_DIGEST_PATH to a writable location, e.g.\n"
                "         EXPORT_DIGEST_PATH=/tmp/export-digest.txt bash %s --verify-document %s"
                % (digest_path, exc, DETECTOR, CHAPTER_PATH)
            )
        check(
            os.path.isfile(digest_path) and open(digest_path, encoding="utf-8").read().strip() == digest,
            "wrote export digest %s" % digest,
        )
        print("digest_path=%s" % digest_path)

        # --- README routes + local markdown links ---
        readme = os.path.join(dest, "README.md")
        require_file(readme, "exported README")
        readme_text = open(readme, encoding="utf-8").read()
        for n in range(1, 12):
            needle = "docs/%02d-" % n
            check(needle in readme_text, "README routes to chapter %02d" % n)
        for needle in (
            "templates/global/",
            "templates/repo/",
            "examples/ordinary-repo/",
            "examples/handbook/",
            "tools/leak-scan.sh",
            "MANIFEST.txt",
        ):
            check(needle in readme_text, "README routes to %s" % needle)

        broken, n_checked, dest_imports = check_links_in_export(dest, entries)
        print("link_targets_checked=%d" % n_checked)
        for row in dest_imports:
            print("destination-layout: %s" % row)
        enforce_link_integrity(broken)
        check(n_checked > 0, "checked %d local/remote link targets" % n_checked)

        # handbook pointer in the ordinary example
        agents = os.path.join(dest, "examples/ordinary-repo/AGENTS.md")
        require_file(agents, "ordinary AGENTS.md")
        agents_text = open(agents, encoding="utf-8").read()
        n_start = agents_text.count("<!-- handbook-pointer:start -->")
        n_end = agents_text.count("<!-- handbook-pointer:end -->")
        check(n_start == 1 and n_end == 1, "exactly one handbook-pointer sentinel pair")
        start = agents_text.find("<!-- handbook-pointer:start -->")
        end = agents_text.find("<!-- handbook-pointer:end -->")
        block = agents_text[start:end]
        check(
            "handbook/docs/boundaries/index.md" in block,
            "pointer block names the handbook boundaries index",
        )
        check(
            "<!-- intent:consultation-rule v1 -->" in agents_text
            and "<!-- /intent:consultation-rule -->" in agents_text,
            "ordinary AGENTS.md carries the intent consultation-rule sentinel (canonical dialect)",
        )
        shim = os.path.join(dest, "examples/ordinary-repo/CLAUDE.md")
        require_file(shim, "ordinary CLAUDE.md shim")
        shim_text = open(shim, encoding="utf-8").read()
        check(shim_text.lstrip().startswith("@AGENTS.md"), "ordinary CLAUDE.md starts with @AGENTS.md")
        require_file(os.path.join(dest, "examples/ordinary-repo/INTENT.md"), "ordinary INTENT.md")
        require_file(os.path.join(dest, "examples/ordinary-repo/WORKLOG.md"), "ordinary WORKLOG.md")

        repo_shim = os.path.join(dest, "templates/repo/CLAUDE.md")
        require_file(repo_shim, "repo CLAUDE.md shim")
        check(
            open(repo_shim, encoding="utf-8").read().lstrip().startswith("@AGENTS.md"),
            "templates/repo/CLAUDE.md starts with @AGENTS.md (repo-relative import)",
        )
        glob_overlay = os.path.join(dest, "templates/global/claude-overlay.md")
        require_file(glob_overlay, "claude overlay")
        glob_text = open(glob_overlay, encoding="utf-8").read()
        check(
            "@~/AGENTS.md" in glob_text,
            "claude overlay documents destination-layout @~/AGENTS.md (not a repo path)",
        )

        # --- no installer ---
        installer_hits = []
        for rel in entries:
            base = os.path.basename(rel).lower()
            if base in ("setup.sh", "install.sh") or base.endswith("-install.sh"):
                installer_hits.append(rel)
        check(len(installer_hits) == 0, "no installer/setup.sh in the export")

        rows, missing = rule_explanation_matrix(dest)
        print("rule_explanation_matrix:")
        for loc, expl in rows:
            print("  %s -> %s" % (loc, expl))
        enforce_rule_explanations(missing)
        check(len(rows) > 0, "printed rule location -> explanation matrix (%d rows)" % len(rows))

        # --- detector self-test, then scan the export ---
        det = os.path.join(ROOT, DETECTOR)
        require_file(det, "detector")
        rc, out, err = run(["bash", det, "--self-test"])
        print("detector_self_test: status=%s" % rc)
        emit_child(out)
        if err:
            print(err, file=sys.stderr)
        check(rc == 0, "detector --self-test exits 0")
        check("PASS: all self-test assertions held" in out, "detector self-test printed PASS")
        # The claim is that the self-test prints counts INCLUDING ZEROS -- the zeros
        # are the load-bearing half, because they are what shows the clean tree was
        # actually scanned rather than skipped. Asserting only `len(...) > 0` was
        # satisfied by the known-bad block's positive counts alone, so the zeros the
        # prose names were never verified.
        # Parsed rather than merely counted: the export scan below derives its expected
        # category set from this, so the two sides cannot drift apart. (It was computed
        # and unused in an earlier round; it now has a consumer.)
        self_counts = parse_count_block(out)
        all_count_lines = [ln for ln in out.splitlines() if ln.startswith("count:")]
        print("detector_self_test_count_lines=%d" % len(all_count_lines))
        for ln in all_count_lines:
            print("  %s" % ln)
        check(len(all_count_lines) > 0, "self-test reported per-category counts")
        zero_counts = [ln for ln in all_count_lines if ln.rstrip().endswith(":0")]
        check(
            len(zero_counts) > 0,
            "self-test reported ZERO counts for a clean tree (the claim names them; "
            "positive counts alone do not show the clean tree was scanned)",
        )
        for line in out.splitlines():
            if line.startswith("manual-review:"):
                print("manual_review_category: %s" % line.split(":", 1)[1])
        check("manual-review:company_org_names" in out, "manual-review categories named")

        rc, out, err = run(["bash", det, dest])
        print("detector_export_scan: status=%s" % rc)
        emit_child(out)
        if err:
            print(err, file=sys.stderr)
        if rc == 2:
            fail("detector export scan is an operational error (exit 2); fail closed")
        check(rc == 0, "detector on export exits 0 (clean)")
        exp_counts = parse_count_block(out)
        # The loop below is vacuous on an empty dict: a detector that stopped printing
        # `count:` lines entirely would satisfy "every category is 0" by having none to
        # check, and this side had no non-empty guard while the self-test side did.
        # The expected category set is DERIVED from the detector's own self-test output
        # (which asserts its mandatory list against its configuration) rather than
        # duplicated here as a second hand-maintained list that could drift.
        check(
            set(self_counts).issubset(exp_counts),
            "export scan reported a count for every category the detector's own "
            "self-test declared (got %s, want at least %s)" % (sorted(exp_counts), sorted(self_counts)),
        )
        for k, v in exp_counts.items():
            check(v == 0, "export scan category %s count is 0 (got %s)" % (k, v))
        check("hit-total:0" in out.splitlines(), "export scan hit-total is 0")

        # filename sensitivity: a binary whose NAME carries a private-looking host
        sens = tempfile.mkdtemp(prefix="export-filename-sens-")
        try:
            blob = os.path.join(sens, "%d.%d.%d.%d-dump.bin" % (192, 168, 7, 7))
            open(blob, "wb").write(b"\x00\x01binary")
            rc, out, err = run(["bash", det, sens])
            print("filename_sensitivity: status=%s" % rc)
            emit_child(out)
            check(rc == 1, "filename-sensitivity fixture returns 1 (a hit)")
            check("filename" in out, "filename-sensitivity labelled as filename")
            check("skipped-binary" in out, "binary contents reported skipped-binary")
        finally:
            shutil.rmtree(sens, ignore_errors=True)

        # --- stamper self-test on temp copies of the *exported* examples ---
        stamper_src = os.path.join(dest, STAMPER)
        require_file(stamper_src, "exported stamper")
        ordinary_src = os.path.join(dest, "examples/ordinary-repo")
        check(os.path.isdir(ordinary_src), "exported ordinary-repo exists")
        stamp_tmp = tempfile.mkdtemp(prefix="stamper-suite-")
        try:
            copy_ord = os.path.join(stamp_tmp, "ordinary-repo")
            copy_hb = os.path.join(stamp_tmp, "handbook")
            shutil.copytree(ordinary_src, copy_ord)
            shutil.copytree(os.path.join(dest, "examples/handbook"), copy_hb)
            for base in (copy_ord, copy_hb):
                for dirpath, dirnames, filenames in os.walk(base):
                    os.chmod(dirpath, 0o755)
                    for name in filenames:
                        try:
                            os.chmod(os.path.join(dirpath, name), 0o644)
                        except OSError:
                            pass
            # Place the stamper next to the copied handbook so --self-test can
            # find its own handbook (it derives the handbook from __file__).
            rc, out, err = run(
                ["python3", os.path.join(copy_hb, "tools", "stamp-pointers.py"),
                 "--self-test", "--ordinary-repo", copy_ord],
                cwd=stamp_tmp,
            )
            print("stamper_self_test: status=%s" % rc)
            # The child's stdout goes through emit_child: see its docstring for why the
            # verbatim reprint made the printed PASS lines outnumber the real tally.
            emit_child(out)
            if err:
                print(err, file=sys.stderr)
            check(rc == 0, "stamper --self-test exits 0")
            # The self-test runs an explicit case table and reports how many cases
            # held. Anchoring on the count keeps this check honest: a table that
            # silently ran zero cases cannot print a passing line.
            m = re.search(r"PASS: all (\d+) self-test cases held", out)
            check(m is not None, "stamper self-test printed the PASS line with a case count")
            if m:
                check(int(m.group(1)) >= 15,
                      "stamper self-test ran a plausible number of cases (ran %s)" % m.group(1))
            check("self-test init: status=0" in out, "stamper init case recorded")
            check("self-test idempotent: status=0 stdout='unchanged\\n'" in out,
                  "stamper idempotent case recorded unchanged")
            check("self-test start-not-first: status=1" in out,
                  "stamper records a refusal for a misplaced block")
            check("self-test symlink-escape: status=1" in out,
                  "stamper records a refusal for a symlink escaping --repo")
        finally:
            shutil.rmtree(stamp_tmp, ignore_errors=True)

        # --- concept-level rule duplication ---
        # Nine separate review rounds each found one more file that restated a rule
        # another file owns, because each sweep matched the WORDING it saw last time
        # rather than the concept. scripts/rule-dup-gate.py searches for the concept
        # via scripts/rule-registry.json, so this class cannot recur silently.
        #
        # A clean exit alone proves only that nothing matched -- which is also what a
        # DELETED detection path reports. The gate's registry preconditions (non-empty
        # rules, every topic matching its own owner) rule out the vacuous-registry case,
        # but not the case where the scan loop itself is gone. So the gate is exercised
        # in BOTH directions here: clean on the real tree, and non-zero on a copy with
        # one restatement planted. Without the second half, removing the detection code
        # left the suite green.
        gate = os.path.join(dest, "scripts", "rule-dup-gate.py")
        require_file(gate, "rule-duplication gate")
        rc, out, err = run(["python3", gate], cwd=dest)
        print("rule_dup_gate: status=%s" % rc)
        emit_child(out)
        if err:
            print(err, file=sys.stderr)
        check(rc == 0, "rule-duplication gate exits 0 on the tree under test")
        check("clean" in out, "rule-duplication gate reports a clean result")

        # The planted-restatement half. A sentence that opens by prescribing a topic
        # another file owns, without citing that owner, is the exact defect class.
        plant_dir = tempfile.mkdtemp(prefix="rule-dup-planted-")
        try:
            planted = os.path.join(plant_dir, "tree")
            shutil.copytree(dest, planted)
            victim = os.path.join(planted, "docs", "03-configuration.md")
            require_file(victim, "planted-restatement target")
            with open(victim, "a", encoding="utf-8") as handle:
                handle.write("\nNever pin a model name in a config file.\n")
            rc2, out2, err2 = run(["python3", os.path.join(planted, "scripts", "rule-dup-gate.py")], cwd=planted)
            print("rule_dup_gate_planted: status=%s" % rc2)
            emit_child(out2)
            check(rc2 == 1, "gate reports a planted restatement as a finding (exit 1), got %s" % rc2)
            check("restatement" in out2, "planted restatement was named in the gate's output")

            # Third direction: a gutted registry must be an OPERATIONAL error (2), never a
            # clean verdict. Without this the gate's "clean" could come from a control
            # that matches nothing, and claim 11's exit-2 promise would be prose only.
            gutted_registry = os.path.join(planted, "scripts", "rule-registry.json")
            with open(gutted_registry, "w", encoding="utf-8") as handle:
                handle.write('{"rules": []}\n')
            rc3, out3, err3 = run(["python3", os.path.join(planted, "scripts", "rule-dup-gate.py")], cwd=planted)
            print("rule_dup_gate_gutted_registry: status=%s" % rc3)
            check(rc3 == 2, "gate exits 2 on an emptied registry (a vacuous control), got %s" % rc3)
            # Assert the REASON, as the planted-restatement case does: any exit 2 is
            # otherwise indistinguishable from the gate failing for an unrelated reason.
            check("no rules" in err3 or "vacuous" in err3, "emptied registry reported as a vacuous control")

            # Fourth direction: a topic pattern mutated so it no longer matches its own
            # owner file. That precondition was documented but never exercised, so its
            # deletion would have left the suite green while the prose claimed it held.
            import json as _json
            reg_path = os.path.join(planted, "scripts", "rule-registry.json")
            # Read from the EXPORT's copy, not the emptied fixture above: that fixture
            # replaced this file with {"rules": []}, so indexing it here would crash.
            with open(os.path.join(dest, "scripts", "rule-registry.json"), encoding="utf-8") as handle:
                registry = _json.load(handle)
            if not registry.get("rules"):
                fail("the shipped registry declares no rules; the topic fixture cannot run")
                return
            registry["rules"][0]["topic"] = "ZZZ_NEVER_MATCHES_ANYTHING_ZZZ"
            with open(reg_path, "w", encoding="utf-8") as handle:
                _json.dump(registry, handle)
            rc4, out4, err4 = run(["python3", os.path.join(planted, "scripts", "rule-dup-gate.py")], cwd=planted)
            print("rule_dup_gate_gutted_topic: status=%s" % rc4)
            check(rc4 == 2, "gate exits 2 when a topic no longer matches its own owner, got %s" % rc4)
            check("does not match its own owner" in err4, "gate named the mutated topic as the cause")
        finally:
            shutil.rmtree(plant_dir, ignore_errors=True)

        # Fifth direction: a CLOSED READER must preserve the gate's verdict rather than
        # forcing 2. This was the one sentence of claim 11 with no executed check -- every
        # other gate invocation here runs with stdout=PIPE held open, so deleting the
        # BrokenPipeError branch left the suite green while the prose claimed it held.
        #
        # The dead reader is created DETERMINISTICALLY: the pipe is made up front, its read
        # end closed before the gate starts, and the write end handed to it. (Closing the
        # parent's read end after Popen also produces EPIPE -- the failure depends on the
        # absence of a read end, not on free buffer space -- but that relies on the parent
        # closing before the child's first write, which is a timing argument.) Both verdicts
        # are exercised, because claim 11 says the reader preserves "(0 or 1)".
        # The verdict-1 case needs its own tree: plant_dir is torn down by its own finally
        # above, so a fresh copy is made here with one restatement appended.
        cr_tree = tempfile.mkdtemp(prefix="rule-dup-closed-reader-")
        try:
            shutil.copytree(dest, cr_tree, dirs_exist_ok=True)
            cr_victim = os.path.join(cr_tree, "docs", "03-configuration.md")
            with open(cr_victim, "a", encoding="utf-8") as handle:
                handle.write("\nNever pin a model name in a config file.\n")
            # Control: with an OPEN reader the same tree must report 1, so a fixture that
            # silently failed to plant would be visible rather than passing as a verdict.
            cr_rc, cr_out, _ = run(["python3", os.path.join(cr_tree, "scripts", "rule-dup-gate.py")], cwd=cr_tree)
            check(cr_rc == 1, "the closed-reader fixture's planted tree reports 1 with an open reader (got %s)" % cr_rc)
        except OSError as exc:
            fail("cannot build the closed-reader fixture tree: %s" % exc)

        for expect_rc, label, tree in (
            (0, "clean tree", dest),
            (1, "planted restatement", cr_tree),
        ):
            r_fd, w_fd = os.pipe()
            os.close(r_fd)  # no reader exists before the gate even starts
            try:
                closed = subprocess.Popen(
                    ["python3", os.path.join(tree, "scripts", "rule-dup-gate.py")],
                    cwd=tree,
                    stdout=w_fd,
                    stderr=subprocess.DEVNULL,
                )
            finally:
                os.close(w_fd)
            rc5 = closed.wait()
            print("rule_dup_gate_closed_reader_%s: status=%s" % (label.replace(" ", "_"), rc5))
            check(
                rc5 == expect_rc,
                "gate preserves its %d verdict on a closed reader (%s; got %s); the scan "
                "already computed an answer, so withholding the report is not an "
                "operational failure" % (expect_rc, label, rc5),
            )
        shutil.rmtree(cr_tree, ignore_errors=True)

        # independent two-run on temp copies (not only the self-test's word)
        two = tempfile.mkdtemp(prefix="stamper-tworun-")
        try:
            o2 = os.path.join(two, "ordinary-repo")
            h2 = os.path.join(two, "handbook")
            shutil.copytree(ordinary_src, o2)
            shutil.copytree(os.path.join(dest, "examples/handbook"), h2)
            agents = os.path.join(o2, "AGENTS.md")
            # A caller may hand this suite a read-only export — the review workflow
            # does exactly that, so a reviewer cannot alter what they are reviewing.
            # copytree preserves modes, so the fixture would inherit read-only and the
            # suite would crash trying to stale it. The fixture is disposable, so its
            # permissions are normalised rather than assumed.
            for base in (o2, h2):
                for dirpath, dirnames, filenames in os.walk(base):
                    os.chmod(dirpath, 0o755)
                    for name in filenames:
                        try:
                            os.chmod(os.path.join(dirpath, name), 0o644)
                        except OSError:
                            pass
            before = open(agents, "rb").read()
            if not before:
                fail("copied AGENTS.md is empty")
            # stale the block
            text = before.decode("utf-8")
            text2 = re.sub(
                r"(<!-- handbook-pointer:start -->).*?(<!-- handbook-pointer:end -->)",
                r"\1\n- STALE\n\2",
                text,
                count=1,
                flags=re.S,
            )
            open(agents, "w", encoding="utf-8").write(text2)
            rc1, out1, err1 = run(
                ["python3", os.path.join(h2, "tools", "stamp-pointers.py"),
                 "--repo", o2, "--handbook", h2],
            )
            print("stamper_cli_run1: status=%s stdout=%r stderr=%r" % (rc1, out1, err1))
            check(rc1 == 0, "stamper CLI first run exits 0")
            check(out1 == "changed\n", "stamper CLI first run prints changed")
            mid = open(agents, "rb").read()
            check(b"STALE" not in mid, "stale marker was replaced")
            check(b"handbook/docs/boundaries/index.md" in mid, "pointer names the boundaries index")
            # outside bytes: strip the block and compare
            def strip_block(b):
                t = b.decode("utf-8")
                return re.sub(
                    r"<!-- handbook-pointer:start -->.*?<!-- handbook-pointer:end -->",
                    "BLOCK",
                    t,
                    flags=re.S,
                )
            check(strip_block(before) == strip_block(mid), "outside-block bytes preserved")
            rc2, out2, err2 = run(
                ["python3", os.path.join(h2, "tools", "stamp-pointers.py"),
                 "--repo", o2, "--handbook", h2],
            )
            print("stamper_cli_run2: status=%s stdout=%r stderr=%r" % (rc2, out2, err2))
            check(rc2 == 0, "stamper CLI second run exits 0")
            check(out2 == "unchanged\n", "stamper CLI second run prints unchanged")
            after = open(agents, "rb").read()
            check(after == mid, "second run left complete file bytes identical")
        finally:
            shutil.rmtree(two, ignore_errors=True)

        # --- inventory ---
        inv_path = os.path.join(dest, INVENTORY)
        require_file(inv_path, "inventory")
        inv_raw = open(inv_path, "rb").read()
        if not inv_raw:
            fail("inventory is empty")
        try:
            inv = json.loads(inv_raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            fail("inventory is not JSON-compatible YAML: %s" % exc)
        repos = inv.get("repositories")
        if not isinstance(repos, list) or len(repos) == 0:
            fail("inventory.repositories must be a non-empty list")
        check(len(repos) >= 2, "inventory lists %d repositories" % len(repos))
        names = [r.get("name") for r in repos if isinstance(r, dict)]
        check("ordinary-repo" in names, "inventory names ordinary-repo")
        check("handbook" in names, "inventory names handbook")
        for rel in (
            "examples/handbook/docs/boundaries/index.md",
            "examples/handbook/docs/boundaries/application.md",
            "examples/handbook/docs/boundaries/platform.md",
            "examples/handbook/AGENTS.md",
            "examples/handbook/README.md",
            "examples/handbook/tools/stamp-pointers.py",
        ):
            check(rel in entries, "inventory-related file listed: %s" % rel)

        # --- exported ordinary source ---
        tally = os.path.join(dest, TALLY)
        require_file(tally, "exported tally")
        rc, out, err = run([sys.executable, tally], cwd=os.path.dirname(os.path.dirname(tally)))
        print("ordinary_source: status=%s" % rc)
        emit_child(out)
        if err:
            print(err, file=sys.stderr)
        check(rc == 0, "exported ordinary source exits 0")
        check("TOTAL" in out and "\t" in out, "exported tally printed the documented summary shape")
        # The shape check above cannot tell a correct total from a wrong one: mutating
        # the footer to sum(counts.values()) + 1 still prints rows and "TOTAL". The
        # ARITHMETIC is what the example exists to demonstrate, so it is checked here
        # by recomputing the footer from the rows.
        rows = [ln for ln in out.splitlines() if ln and not ln.startswith("TOTAL")]
        footer = [ln for ln in out.splitlines() if ln.startswith("TOTAL")]
        check(len(footer) == 1, "exported tally printed exactly one TOTAL footer")
        try:
            row_total = sum(int(ln.split("\t", 1)[0]) for ln in rows)
            stated = int(footer[0].split("\t", 1)[1])
        except (IndexError, ValueError) as exc:
            fail("exported tally output is not parseable as <count>TAB<label>: %s" % exc)
        check(
            row_total == stated,
            "exported tally TOTAL equals the sum of its rows (%d vs %d)" % (row_total, stated),
        )

        # --- claim-to-source matrix: structural https:// check ---
        # Look in the exported chapters + NOTICES + README. Do not regex-judge
        # reader prose for pinned literals (false-positives on floors).
        url_hosts_ok = 0
        url_hosts_bad = []
        for rel in entries:
            if not rel.endswith(".md"):
                continue
            path = os.path.join(dest, rel)
            text = open(path, encoding="utf-8").read()
            # A bare-`http://` CITATION is a downgrade from the https the template
            # documents. Two scans are needed, because a citation can appear either way:
            #   * markdown link TARGETS, not a substring search -- the scheme is also
            #     NAMED in prose and in this suite's own source, and a substring test
            #     flagged those as citations (while the clause that guarded against it,
            #     `and "https://" not in ...`, disabled the check in every file carrying
            #     a citation at all, which is every file it exists to police);
            #   * table CELLS, which are not link targets and were invisible to the scan
            #     above -- measured: a planted bare http:// in a Public source cell
            #     passed certification with no BAD-URL line.
            # `http://localhost` is the documented local default, not a citation.
            for link_match in MD_LINK.finditer(text):
                target = link_match.group(2).strip()
                if target.startswith("http://localhost"):
                    continue
                if target.startswith("http://"):
                    url_hosts_bad.append((rel, target, "not-https"))
            for bare in claim_table_bare_http(path):
                url_hosts_bad.append((rel, bare, "not-https"))
            for url, is_https in claim_table_source_urls(path):
                findings = classify_citation_url(rel, url, is_https)
                if findings:
                    url_hosts_bad.extend(findings)
                else:
                    # The classifier returns [] only for a public https citation, so the
                    # count is incremented here rather than inside it: the function is a
                    # pure verdict and records nothing.
                    url_hosts_ok += 1
        # `matrix_files > 0` enforced only that ONE file qualified, so eight of nine
        # chapters could lose their tables with the suite green. The stronger, true
        # property is per-chapter: every chapter that carries a verification section
        # carries a claim-to-source TABLE in it. The table is what is asserted, NOT an
        # https row -- several chapters cite a repository, a package-relative path or a
        # reproducible command rather than a URL, and requiring a URL would have been a
        # different (false) claim about their sources. The expected set is derived from
        # the chapters the suite already walks, so it moves with the manifest.
        # Each chapter is classified ONCE. Two evasion holes had to be closed after the
        # first version: the section slice ran to END OF FILE, so a table under any later
        # heading satisfied "a table in that section"; and the row test was fence-blind,
        # so a pipe diagram in a code block counted as a table. The slice is now bounded
        # at the next heading and fenced lines are skipped. The non-empty guard matters
        # too: without it, deleting every verification heading in the tree left the check
        # vacuously green, which would make it a check that cannot fail.
        table_missing = []
        chapters_with_verification = []
        for c in chapters:
            full_c = os.path.join(dest, c)
            if not os.path.isfile(full_c):
                continue
            text_c = open(full_c, encoding="utf-8").read()
            # The verification SECTION is the top-level heading that names it, matched at
            # `##` only. Two mistakes were made getting here: matching any heading level
            # picked up a `###` whose prose merely mentioned verification (docs/04), and
            # bounding at the next heading of ANY level cut the section off before its own
            # `### Claim-to-source table` subsection (docs/06). The section therefore runs
            # from the `##` verification heading to the next `##` heading, so its own
            # subsections stay inside it.
            m = re.search(r"(?im)^##\s+[^\n]*[Vv]erification[^\n]*$", text_c)
            if not m:
                continue
            chapters_with_verification.append(c)
            rest = text_c[m.end():]
            nxt = re.search(r"(?m)^##\s+\S", rest)
            section = rest[:nxt.start()] if nxt else rest
            section_lines = section.splitlines()
            # A table needs a header row AND a separator row. Testing for "any line with a
            # pipe" accepted a single stray `||`, which is not a table and carries no
            # sources -- the fourth version of this check to be too permissive.
            rows = [ln for i, ln in enumerate(section_lines, 1)
                    if not line_in_fence(section_lines, i)
                    and re.match(r"^\|[^\n]*\|\s*$", ln)]
            has_table = len(rows) >= 2 and any(
                re.match(r"^\|[\s:|-]+\|\s*$", ln) and "-" in ln for ln in rows
            )
            if not has_table:
                table_missing.append(c)
        check(
            len(chapters_with_verification) > 0,
            "at least one chapter carries a verification section (the per-chapter table "
            "check below cannot be satisfied by having none)",
        )
        check(
            not table_missing,
            "every chapter with a verification section carries a claim-to-source table "
            "(%d chapters checked; missing in %s)" % (len(chapters_with_verification), table_missing),
        )
        enforce_citation_urls(url_hosts_bad)
        check(url_hosts_ok > 0, "found %d https:// citation URLs" % url_hosts_ok)
        # Stated as what was checked: a denylist of local, placeholder and reserved
        # shapes, not proof that a host is publicly reachable or is the right source.
        # Reachability, fork-vs-upstream, and semantic correctness are the reviewer's
        # job; claiming them here would be a stronger statement than this code makes.
        # The always-true `check(True, "citation URLs are https:// ...")` that stood here
        # is gone: enforce_citation_urls above already fails on any non-public-https URL,
        # and url_hosts_ok > 0 proves the check had something to look at. A PASS line that
        # cannot fail is the one thing an evidence record must not manufacture.


        print("export_identity=%s files=%d digest=%s" % (os.path.basename(dest), len(entries), digest))
    finally:
        shutil.rmtree(dest, ignore_errors=True)

    print("----")
    print("PASS_COUNT=%d FAIL_COUNT=%d" % (PASS, FAIL))
    print("target=%s" % ROOT)
    if FAIL:
        fail("suite finished with %d FAIL" % FAIL)
    print("SUITE_RESULT=PASS")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        sys.stderr.write("FAIL: suite crashed: %s\n" % exc)
        sys.exit(1)
PY
```
<!-- verification-suite:end -->

## How to run the suite

From the repository root (the directory that contains `MANIFEST.txt`):

```text
bash tools/leak-scan.sh --verify-document docs/11-verification.md
```

Exit 0 means every assertion above held. Exit 1 means the run did not pass —
either a failed assertion or an unhandled error, both of which print `FAIL:` on
stderr. Exit 2 is an operational error detected by the *launcher* (a missing or
unreadable chapter, malformed fences, or a verification block that exited with a
status outside the contract). Re-run after you change a listed file: the
export is rebuilt from `MANIFEST.txt` each time, so a stale digest cannot
silently certify a different tree.

**Failure prevented:** a reader (or an agent) claiming the template is
verified because a previous run was green, after the bytes have changed.

The suite **writes** the export digest to `$EXPORT_DIGEST_PATH`, defaulting to
`.export-digest.txt` in the working directory the suite runs from. That name is
not in `MANIFEST.txt`, so the digest cannot hash itself, and it is **not** a path
in this chapter — the published text must not name an internal workspace
location. Set the variable when the tree is read-only (a published copy usually
is): the default needs a writable directory, and a permission failure there is
reported as the operational error it is rather than being mistaken for a failed
assertion. Whoever runs the certification points the variable at their
own evidence store and binds the review receipt to the value in that file. Do
not paste a hash into this chapter as if it were the live digest — it would be
stale the moment the chapter is edited.

## What the suite asserts

Each item is implemented as a command in the block above, not as prose:

1. `MANIFEST.txt` is non-empty, UTF-8, one relative regular-file path per
   line, no comments/globs/directories/duplicates/traversal/hidden/absolute
   paths, no git directory, and nothing that is not in the manifest. It lists itself, all eleven
   chapters, both template trees, both examples, the detector, LICENSE,
   NOTICES, and README.
2. Only those paths are copied, with `shutil.copy2`, into a fresh temporary
   tree. The copy is never a recursive `docs/` walk. Symlinks are refused.
   Source and destination bytes match. The export's regular-file set equals
   the manifest.
3. Every exported regular file decodes as UTF-8 with no NUL. A **fixture**
   export that contains an undecodable regular file is run through the same
   check and **must fail** — the detector's binary skip is not a certification
   skip. This suite owns that check.
4. The export digest (`sha256:` + 64 hex) is written to the operator-owned
   path named above.
5. README routes to all eleven chapters, both template directories, both
   examples, the detector, and the manifest. Links in the export are scanned by a
   line-oriented heuristic that reports destinations it cannot resolve, at
   `file:line`; absolute URLs (`http://`, `https://`, `mailto:`) are treated as
   external and not resolved, and destination-layout `@~/…` imports are recognised
   as such rather than mistaken for repo files. **The heuristic's accuracy is not
   claimed here** — see the note below for what is and is not guaranteed. The
   ordinary example's pointer block, intent sentinel, and `@AGENTS.md` shim are
   present.

   **This link check is a heuristic, and this paragraph is its whole claim.** It scans
   Markdown line by line and reports destinations that do not resolve. It is not a
   conformant parser, and no wording here promises which cases it handles correctly:
   every boundary statement written so far — as a list of exceptions, and then as a
   positive description of what is "checked" — has been falsified by the next probe,
   because a line-oriented scan cannot be described by a boundary at all. Percent-encoded
   paths, duplicate-heading suffixes, Setext headings, directory fragments, indented
   code, multiline code spans and reference-style definitions are all handled
   approximately, in both directions: a link that works can be reported broken, and a
   broken link can pass. Both were reproduced during review.

   What the suite does guarantee is narrower and is asserted above: the export's own
   links — every file in `MANIFEST.txt` — resolve, and a deliberately
   broken inline link added to a destination tree is caught. That is evidence about this
   repository, not a general claim about Markdown. Judging the rest is the reviewer's job,
   and the reason the claim is written this way is that the pointer stamper in
   `docs/08-cross-cutting-docs.md` reached the same conclusion: a heuristic that cannot
   state its boundary should not pretend to have one.

6. No `setup.sh` / `install.sh` in the export. Every template is non-empty.
   Rule-like list items are paired with a nearby `Failure prevented:` or an
   explanation link; the matrix is printed. Semantic adequacy of those
   explanations is a reviewer's job, not this regex.
7. `bash tools/leak-scan.sh --self-test` exits 0 and prints per-category
   counts (including zeros) plus named manual-review categories. The same
   detector run against the export exits 0 with `hit-total:0`. A
   filename-sensitivity fixture (binary file whose *name* looks like a
   private address) returns 1 and reports `skipped-binary`.
8. The handbook stamper `--self-test` is run against **synthetic fixtures** it
   builds itself (`--ordinary-repo` is only checked for the presence of an
   `AGENTS.md`; its contents are not read), and separately an independent two-run
   of the real CLI **against copies of the exported examples** records
   `changed` then `unchanged`, preserved outside bytes, and identical file
   bytes after the second run.
9. `inventory.yaml` parses as JSON-compatible YAML with a non-empty
   `repositories` array naming the two examples. The exported ordinary
   source (`src/example.py`) runs and prints the documented summary shape.
10. Every chapter that carries a verification-notes heading carries a
    claim-to-source table in that section (not merely that one such file
    exists). Recorded `https://` citation URLs are on public hosts rather than
    local paths; this is structural only — the check cannot tell an upstream repository
    from a fork of it, nor whether a cited URL is the semantically right source,
    and it does not try.

11. `scripts/rule-dup-gate.py` exits 0 (clean) on the export, and exits 1 naming the
    restatement when one is planted in a copy of the tree. Its registry is proved
    usable first: an empty rule list, or a topic pattern that no longer matches its own
    owner file, is an operational error (exit 2) rather than a silent pass. Both
    preconditions are exercised: a copy whose rule list is emptied
    must exit 2, and so must a copy whose topic pattern no longer matches its own owner
    file -- so the gate cannot report "clean" from a control that matches nothing. A closed READER deliberately preserves the gate's verdict (0 or 1) rather
    than forcing 2 — the scan already computed an answer, so withholding its report is
    not an operational failure.

## Public verification notes

Re-run at writing of this chapter. These are **receipts of one run**, not
pinned facts. The command is the durable evidence; the number is a snapshot.

| Claim | Command | Result (when this was written) | Limitation |
|---|---|---|---|
| npm package `@earendil-works/pi-coding-agent` is MIT, repository `earendil-works/pi` | `npm view @earendil-works/pi-coding-agent version license repository.url --json` | license `MIT`; repository `git+https://github.com/earendil-works/pi.git`; a version string was returned | version is a snapshot; re-run, do not copy the number into other chapters |
| `context-mode` is Elastic-2.0 | `npm view context-mode license repository.url --json` | `"license": "Elastic-2.0"`; repository `git+https://github.com/mksglu/context-mode.git` | Elastic-2.0 is source-available, not OSI; see `NOTICES.md` |
| `pi-meridian-extension` license field empty | `npm view pi-meridian-extension license repository.url --json` | license key absent; `repository.url` present | license key absent; status unresolved, not a confirmed refusal |
| Hindsight **server** install is `pip install hindsight-api` | `curl -s https://pypi.org/pypi/hindsight-api/json` (parsed for `info.name` / `info.summary`) | name `hindsight-api`; summary names the agent-memory project | PyPI `hindsight` is a **different** project — do not `pip install hindsight` |
| Superpowers ships a public skill directory listing | `curl --fail --silent --show-error https://api.github.com/repos/obra/superpowers/contents/skills` | HTTP 200; 14 directories | unauthenticated GitHub API may 403; count is a snapshot |
| Detector self-test | `bash tools/leak-scan.sh --self-test` | exit 0; `PASS: all self-test assertions held` | exercises synthetic fixtures, not the export |
| Detector on this chapter's export | run by the suite above | must be exit 0 / `hit-total:0` | fails closed on scan error (exit 2) |
| Stamper self-test | `python3 examples/handbook/tools/stamp-pointers.py --self-test --ordinary-repo examples/ordinary-repo` | exit 0; first run `changed`, second `unchanged`; malformed markers reject without mutation | self-test copies; does not mutate the real example |
| Ordinary example | `python3 examples/ordinary-repo/src/example.py` | exit 0; prints a `TOTAL` footer | demo input only |
| Manifest non-empty | `test -s MANIFEST.txt` | exit 0 | existence, not completeness — completeness is the suite |

### Chapter verification commands (replay)

Each chapter already carries its own compact verification-notes table. This
index does not duplicate those tables. Replay is: open the chapter, run the
command in the table, compare. A keyword grep that the file exists is not
replay.

| Chapter | Replay from |
|---|---|
| `docs/01-mental-model.md` | its Verification notes |
| `docs/02-install.md` | Compact verification notes (claim-to-source table + isolated runtime smoke, labeled) |
| `docs/03-configuration.md` | Verification notes |
| `docs/04-packages.md` | Verification notes |
| `docs/05-skills.md` | Verification notes (claim-to-source) |
| `docs/06-memory-mcp-context.md` | Verification notes (includes the executed MCP example) |
| `docs/07-instruction-files.md` | Verification notes |
| `docs/08-cross-cutting-docs.md` | Verification notes |
| `docs/09-claude-code.md` | Verification notes |
| `docs/10-private-patterns.md` | Verification notes |

**Executed during this chapter (labeled).** Isolated registry/API lookups
only; no home-config writes, no global installs, no interactive `/login`:

- `npm view @earendil-works/pi-coding-agent version license repository.url --json` → MIT, `earendil-works/pi`.
- `npm view context-mode license repository.url --json` → Elastic-2.0.
- `npm view pi-meridian-extension license repository.url --json` → license field absent.
- `curl -s https://pypi.org/pypi/hindsight-api/json` → project name and summary match the memory-server install path in `docs/06`.
- GitHub contents API for `obra/superpowers` `/skills` → HTTP 200, 14 directories.
- `bash tools/leak-scan.sh --self-test` → PASS.
- `python3 examples/handbook/tools/stamp-pointers.py --self-test --ordinary-repo examples/ordinary-repo` → PASS.
- `python3 examples/ordinary-repo/src/example.py` → exit 0, `TOTAL` footer.

**Not verified here (stated, not hidden).**

- Interactive `/login` against a live provider. It needs credentials and
  OAuth; fabricating a successful login would violate the honesty bar.
  Cited to upstream documents in `docs/02-install.md`.
- A model completion (a "first session" that actually calls a model). Cited
  to upstream interactive-mode docs, not to a transcript.
- Semantic adequacy of every `Failure prevented:` line. Regex can check that a
  reason is PRESENT (claim 6) but not that it is a good one; that is what the
  independent review is for.
- **Rule duplication is checked mechanically, within limits.** `scripts/rule-dup-gate.py`
  is run against the export (claim 11) and must be clean; a restatement is planted in a
  copy and the gate must report it. What that cannot decide is whether two files *ought*
  to be merged or whether a rule is stated in a way the registry's topic patterns do not
  recognise — the registry is a curated list of concept patterns, not a general theory of
  duplication, so a rule it does not know about is outside its reach.
- Exact-name leak categories that generic patterns cannot infer (company,
  customer, private repo, internal tool names). The detector names them as
  **manual-review**. A private exact-name grep is run by the parent on the
  export using terms that must **not** appear in this chapter (they would
  self-match). Public record: the parent greps the export for a private
  term list and requires grep status 1 (zero matches); status 2 is an
  error. The terms themselves live only in the private receipt.
- That every citation is *semantically* the right section of the right
  document. The suite checks URL shape (`https://` on a public host), not
  meaning.

## Claim-to-source matrix

The per-chapter tables are the matrix. This chapter's structural check
(suite item 10) asserts they exist and that recorded `https://` URLs are
public. It does not re-copy the tables — a second copy would drift.

Authoritative public hosts observed in this tree include GitHub, the npm
registry, PyPI, `pi.dev`, and the Elastic license page. Re-run the lookup
in the chapter that made the claim.

## MCP interaction

Executed in `docs/06-memory-mcp-context.md`, labeled as a runtime check
(not source-only): JSON-RPC over stdio to a public account-free reference
server (`@modelcontextprotocol/server-everything` via `npx -y`), isolated
temp cwd, no home-config writes.

- `initialize` → server identity and capabilities.
- `tools/list` → 13 tools.
- one harmless `echo` call → `isError: false`.

That server's own README states it is a reference/test server, not a
useful production server. The point of the example is the **shape**
(initialize, list, one call) against something that requires no account.

Hindsight install path, re-checked above: `pip install hindsight-api` is
the real server distribution. PyPI project `hindsight` is unrelated.

## Package and license attribution

`NOTICES.md` is the attribution file. Referencing is not redistribution.
Live re-lookup when this was written:

- `@earendil-works/pi-coding-agent` — MIT.
- `context-mode` — Elastic-2.0 (source-available; managed-service
  restriction — read the license before you adopt it).
- `pi-meridian-extension` — undeclared (empty npm `license` field). An
  unknown is not a yes.

Re-check before you install:

```text
npm view <pkg> license repository.url --json
```

## Six-lane recon failure (honest)

An early attempt to gather evidence for this template dispatched six
parallel recon lanes. It returned **zero durable output**.

Cause, as later reconstructed: the briefs were over-scoped (each child was
asked for a report that would not fit its context), the execution context
was too small for the brief, concurrency was high enough that every lane
competed, and there was **no write-early contract** — children researched
until their context was gone and never wrote a file. A stalled child then
had nothing on disk to resume from.

The lesson is in `docs/01-mental-model.md` (hallucinated completion,
context rot) and `docs/10-private-patterns.md` (write-early, disjoint
scopes, per-task verify). This chapter exists in part because that failure
was real and common. No model identity, private run path, or
infrastructure label is published about it; the failure is about the
*shape* of the fan-out, which is what a reader can actually use.

## Independent review

The authentic verdict of a fresh-context reviewer from a **different model
family** than the author, against the exported bytes (not the authoring
workspace that produced them), is recorded as a receipt held by whoever runs
the certification — alongside the
export digest, **outside** the export and outside this chapter's scope. The
receipt is not part of the published tree, so this chapter does not name its
location. This heading exists so the verdict can be cited; it cannot manufacture
one. A missing receipt, a blocking verdict, a reviewer family that matches
the author's, a malformed digest, or a digest that does not match the value the
suite wrote to `$EXPORT_DIGEST_PATH` fails the delivery bar. The receipt is
bound to that file, not to a fixed path: whoever certifies chooses the evidence
store, and the check compares against whatever that run recorded.

The verdict has since been recorded. What follows is **reported by that receipt
and not verifiable from this tree** — the receipt is held outside the export by
design, so no command in this chapter can read it. Treat these as claims to check
against the receipt itself, in the same spirit as the "Not verified here" list:

- **The verdict is approving.** It was reached against the assembled export, not
  against the working tree this template was built in, so it is evidence about the
  delivered bytes.
- **The reviewer's model family differs from the author's.** That separation is
  the reason the review is evidence at all; a same-family review would be a second
  reading of the same blind spots, and the receipt records the two families so the
  separation is checkable rather than asserted.
- **`blocking_findings` is empty.** Nothing was left open against the export at the
  time the verdict was recorded.
- **The receipt binds to the export digest** computed over `MANIFEST.txt` — every
  listed path, in sorted order, with the file bytes — so a review of a different
  export cannot be reused to certify this one. Note the consequence for this very
  chapter: `docs/11-verification.md` is itself a listed file, so recording the
  verdict here moves that digest. The binding therefore names the bytes that were
  reviewed, and any later edit to a listed file requires the re-run described under
  "How to run the suite" — a mismatch is the expected signal that the tree
  changed, not a defect in the receipt.

What is deliberately *not* here: the receipt's location (for the reason given
above) and the digest value itself (for the reason given under "How to run the
suite"). Neither is repeated in this section — the two rules already have one home
in this chapter each.

## Residual risks

- Generic leak patterns cannot identify every private proper noun. Manual
  review of the named categories (company/org, customer, private repo,
  internal tool) remains mandatory; the parent's private exact-name grep
  supplements it. This chapter does not contain those terms.
- Semantic duplication of rules across instruction files, and the quality
  of each `Failure prevented:` line, are judged by the independent
  reviewer, not by this suite.
- The export digest is rewritten on every successful suite run. Treat the
  file on disk as current; do not copy the hash into prose.
- Unauthenticated GitHub API calls may 403. A 403 is not a census of zero
  skills; it is an unavailable measurement.
- Interactive authentication and live model calls were not exercised, as
  stated above.
