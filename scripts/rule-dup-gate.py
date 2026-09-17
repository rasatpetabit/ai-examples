#!/usr/bin/env python3
"""Concept-level rule-duplication gate.

A rule is owned by exactly one file. Another file that OPENS a sentence by
prescribing the rule's topic, without citing the owner, is restating it — and a
restated rule is how two copies drift into disagreeing.

This exists because the same class of defect was found nine separate times in
one run by nine separate review rounds. Each round swept for the *wording* it
had seen last time and missed the sites that said the same thing differently.
A deterministic check has to search for the CONCEPT, which is what the registry
encodes: a topic regex per rule, not a phrase.

Sentences that merely APPLY a rule ("every one of those goes stale, and the
lookup that replaces it is given beside the claim") do not OPEN with a
prescription and are correctly ignored.

Usage:
  python3 scripts/rule-dup-gate.py [--manifest MANIFEST.txt] [--registry FILE]
  RULE_REGISTRY=... MANIFEST=... for overrides.

Using this gate on your own repository: copy this script into a SUBDIRECTORY of
your tree -- one level below your manifest, exactly as shipped (`scripts/`) --
with your own `rule-registry.json` beside it. Manifest entries resolve against
the script's PARENT directory (`ROOT = dirname(dirname(__file__))`), so a script
placed at your repository root resolves every path one level above your tree and
exits 2. Registry shape is the shipped three-rule example: a JSON object with a
non-empty `rules` array of `{id, owner, topic}`, where `topic` is a
case-insensitive regex and `owner` is the one file permitted to state the rule.
A topic that no longer matches its own owner file is an operational error,
exit 2 -- it means the topic has been mutated to match nothing.

Exit: 0 clean, 1 restatements found, 2 operational error.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_REGISTRY = os.path.join(HERE, "rule-registry.json")
DEFAULT_MANIFEST = os.path.join(ROOT, "MANIFEST.txt")

# The sentence must OPEN with the prescription, optionally after markdown noise.
OPENER = re.compile(
    r"^\s*(?:[-*+>]\s*)?(?:\*\*)?\s*"
    r"(never|always|do not|don't|must|avoid|no\s+\w+\s+(?:in|of))\b",
    re.I,
)


def emit(text, stream=None):
    """Write one line, or exit 2 when it cannot be delivered.

    A report nobody can read is an operational failure, not a verdict: an unguarded
    print to a closed reader raises BrokenPipeError, and to a full device fails at
    interpreter shutdown with status 120. Both are outside this gate's documented
    0/1/2 contract, so the stream is silenced and the status set explicitly.
    """
    stream = sys.stdout if stream is None else stream
    try:
        stream.write(text + "\n")
        stream.flush()
    except BrokenPipeError:
        # A closed READER withholds the report but not the verdict: the scan already
        # computed it, so the caller returns its own status. Forcing 2 here made this
        # gate disagree with both sibling tools, which preserve the verdict on a
        # closed reader (the scanner returns 1 on hits, example.py returns 0).
        #
        # No return value: an earlier version returned True/False and no caller ever
        # inspected it, so the bool advertised a delivery check nobody performed.
        silence_stream(stream)
    except (OSError, ValueError, AttributeError):
        # Any other write failure means the run cannot report at all: operational.
        silence(2)


def silence_stream(stream):
    """Point one stream's descriptor at /dev/null so shutdown cannot re-raise.

    Writing again is not enough -- CPython flushes buffered streams at shutdown, and
    a stream still holding the closed descriptor raises there, replacing the intended
    status with 120. Replacing the DESCRIPTOR is what makes the later flush harmless.
    """
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(devnull, stream.fileno())
        finally:
            # Closed rather than leaked: the sibling implementations in leak-scan.sh do
            # the same, and an unclosed descriptor here would be a slow leak in a tool
            # whose whole point is running under constrained descriptors.
            os.close(devnull)
    except (OSError, ValueError, AttributeError):
        pass


def silence(status):
    """Point the standard descriptors at /dev/null, then exit with `status`.

    Redirecting BEFORE raising avoids CPython's shutdown flush of an unwritable
    buffer, which would replace the intended status with 120.
    """
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        for fd in (1, 2):
            try:
                os.dup2(devnull, fd)
            except OSError:
                pass
    except OSError:
        pass
    sys.exit(status)


def sentences(line):
    return re.split(r"(?<=[.;:])\s+", re.sub(r"[*`_]", "", line).strip())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", default=os.environ.get("MANIFEST", DEFAULT_MANIFEST))
    ap.add_argument("--registry", default=os.environ.get("RULE_REGISTRY", DEFAULT_REGISTRY))
    args = ap.parse_args(argv)

    try:
        with open(args.registry, encoding="utf-8") as fh:
            registry = json.load(fh)
        with open(args.manifest, encoding="utf-8") as fh:
            files = [
                f
                for f in fh.read().split()
                if f.endswith(".md") and os.path.isfile(os.path.join(ROOT, f))
            ]
    except (OSError, ValueError) as exc:
        emit("operational error: %s" % exc, stream=sys.stderr)
        return 2

    # A registry that matches nothing finds nothing and reports clean. That is the
    # one failure mode this gate cannot detect by scanning alone, so the registry
    # is proved USABLE before it is trusted as a control:
    #   - an empty (or absent) rule list would make every scan vacuously clean;
    #   - a topic regex that does not match its OWNER file has been mutated to
    #     match nothing, so its silence says nothing about the other files.
    # Both are operational errors (2), never a clean verdict (0). Without this,
    # deleting the rules or gutting a topic left the gate -- and the suite that
    # calls it -- green.
    # Shape is validated before it is used: valid JSON is not necessarily the shape
    # this gate reads. `[]` or a bare string is valid JSON, and reaching `.get` on it
    # raised AttributeError -- an uncaught traceback exiting 1, which is this gate's
    # "restatements found" status, for what is an operational failure. The exit code
    # contract is the product here, so every path back to 1 must mean a restatement.
    if not isinstance(registry, dict):
        emit("operational error: registry must be a JSON object, got %s" % type(registry).__name__, stream=sys.stderr)
        return 2
    rules = registry.get("rules")
    if not isinstance(rules, list) or not rules:
        emit("operational error: registry declares no rules; a vacuous control", stream=sys.stderr)
        return 2
    if not files:
        emit("operational error: manifest listed no markdown files to scan", stream=sys.stderr)
        return 2
    for rule in rules:
        if not isinstance(rule, dict):
            emit("operational error: rule entries must be JSON objects, got %s" % type(rule).__name__, stream=sys.stderr)
            return 2
        for field in ("id", "owner", "topic"):
            if not isinstance(rule.get(field), str) or not rule[field].strip():
                emit("operational error: rule %r is missing %s" % (rule.get("id"), field), stream=sys.stderr)
                return 2
        owner_path = os.path.join(ROOT, rule["owner"])
        try:
            with open(owner_path, encoding="utf-8", errors="replace") as fh:
                owner_text = fh.read()
        except OSError as exc:
            emit("operational error: cannot read owner %s: %s" % (rule["owner"], exc), stream=sys.stderr)
            return 2
        try:
            owner_topic = re.compile(rule["topic"], re.I)
        except re.error as exc:
            emit("operational error: rule %s has an invalid topic: %s" % (rule["id"], exc), stream=sys.stderr)
            return 2
        if not owner_topic.search(owner_text):
            emit(
                "operational error: rule %s topic does not match its own owner %s; "
                "the topic has been mutated to match nothing" % (rule["id"], rule["owner"]),
                stream=sys.stderr,
            )
            return 2

    total = 0
    # Every byte this gate writes goes through emit(), and every file it reads is
    # inside this guard, because an I/O failure is operational (2) and must never be
    # reported as a verdict. Unguarded, a read error surfaced as a traceback (exit 1 =
    # "restatements found") and an undeliverable diagnostic surfaced as exit 1 or a
    # shutdown-flush 120 -- none of which is in the documented 0/1/2 contract.
    try:
        for rule in rules:
            owner = rule["owner"]
            topic = re.compile(rule["topic"], re.I)
            for rel in files:
                if rel == owner:
                    continue
                path = os.path.join(ROOT, rel)
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for n, line in enumerate(fh, 1):
                        if not line.strip() or line.lstrip().startswith(("#", ">", "```")):
                            continue
                        for sentence in sentences(line):
                            if OPENER.search(sentence) and topic.search(sentence) and owner not in sentence:
                                total += 1
                                emit(
                                    "restatement: %s:%d  rule=%s owner=%s\n    %s"
                                    % (rel, n, rule["id"], owner, sentence.strip()[:100])
                                )
    except (OSError, re.error) as exc:
        emit("operational error: %s" % exc, stream=sys.stderr)
        return 2

    if total:
        emit("\n%d unflagged restatement(s)" % total)
        return 1
    emit("rule-duplication gate: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
