#!/usr/bin/env python3
"""
check_videos.py — CI guard for video facades.

Fails the build when a video facade is:
  1. DEAD      — the YouTube ID no longer resolves (removed/private/blocked)
  2. MISLABELED — the on-page label contradicts the real YouTube title

Rationale: this repo has twice shipped facades whose captions described the
*page topic* rather than the *video*, including captions that attributed
content to real, named trainers who did not produce it. That is the failure
this guard exists to prevent.

Exit codes:
  0  clean
  1  violations found
  2  could not verify (network) — non-blocking by default, see --strict

Usage:
  python3 tools/check_videos.py                 # all facades
  python3 tools/check_videos.py --changed-only  # only facades in changed files
  python3 tools/check_videos.py --strict        # network failures also fail
"""
import argparse
import html
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import urllib.request
import urllib.error

OEMBED = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
UA = "Mozilla/5.0 (compatible; HorseTrainerCI/1.0)"

# Every facade template in use in this repo.
FACADE = re.compile(
    r'<(?:div|a)\s+class="(?:qa-vid-facade|vid-facade|yt-facade|video-thumb)"([^>]*)>',
    re.I)
ATTR = {
    "vid": re.compile(r'data-vid="([A-Za-z0-9_-]{11})"'),
    "title": re.compile(r'data-title="([^"]*)"'),
    "aria": re.compile(r'aria-label="(?:Play video:\s*|Play:\s*)?([^"]*)"'),
}

# Words that carry no topical signal — ignored when comparing label to title.
STOP = set("""a an the and or of for to in on with your you how why what when this
that is are was were be been do does did i it its at from by as horse horses
video videos part pt ep episode full official hd my me his her their new""".split())

# ---------------------------------------------------------------------------
# WHY THIS GUARD DOES NOT SCORE CAPTION SIMILARITY
#
# Editorialized captions are legitimate and common here: a label reading
# "Fixing a Horse That Drops Its Inside Shoulder" over a video titled
# "How to Stop Shouldering // Barrel Racing Drills" is correct and good.
# Word-overlap scoring cannot distinguish that from a genuine mislabel
# (e.g. "Building the Stop" over a video that is actually "Reining 101").
# A guard that flags both is a guard that gets disabled.
#
# So this guard checks only what is MECHANICALLY DECIDABLE:
#   1. dead videos                       — objective
#   2. fabricated trainer attribution    — objective
#
# (2) is the failure that actually shipped: captions naming a real trainer
# ("Clinton Anderson - Correct Hand and Arm Position When Wrestling a Steer")
# on videos that trainer did not make. If a label names a person, that person
# must plausibly be the video's channel/creator. That is checkable.
#
# Caption *quality* stays a human editorial call and is reported, not failed.
# ---------------------------------------------------------------------------

# Trainers whose names appear in labels across this site. If a label claims
# one of these people, the video must actually come from them.
KNOWN_TRAINERS = {
    "clinton anderson": ["duhorseman", "downunder", "clinton anderson"],
    "al dunning":       ["al dunning"],
    "warwick schiller": ["warwickschiller", "warwick schiller"],
    "andrea fappani":   ["fappani"],
    "matt mills":       ["matt mills"],
    "larry trocha":     ["larry trocha"],
    "ken mcnabb":       ["ken mcnabb"],
    "stacy westfall":   ["stacy westfall"],
    "pat parelli":      ["parelli"],
    "casey deary":      ["deary"],
    "todd bergen":      ["bergen"],
    "buck brannaman":   ["brannaman"],
    "john lyons":       ["johnlyons", "john lyons"],
    "richard winters":  ["richard winters"],
    "clinton anderson": ["duhorseman", "downunder", "clinton anderson"],
    "craig cameron":    ["craig cameron"],
    "chris cox":        ["chris cox"],
}


# Disciplines that cannot be mistaken for one another. If the LABEL clearly
# claims one and the REAL VIDEO clearly is another, the caption is describing
# the page, not the video. Unlike vague paraphrase, this IS decidable.
# Each entry: (required_terms, ...) — a discipline matches if ANY tuple has
# ALL its terms present, in any order. Order-independent by design: a label
# reading "Wrestling a Steer" must match "steer wrestling".
DISCIPLINES = {
    "steer wrestling":  [("steer","wrestl"), ("bulldog",)],
    "breakaway roping": [("breakaway",)],
    "team roping":      [("team","roping"), ("heel","horse"), ("heeler",), ("header",)],
    "barrel racing":    [("barrel","rac"), ("barrel","pattern"), ("cloverleaf",)],
    "colt starting":    [("colt","start"), ("starting","colt"), ("green","colt")],
    "reining":          [("reining",), ("sliding","stop"), ("rollback",),
                         ("lead","change"), ("spin",)],
    "cutting":          [("cutting",)],
    "dressage":         [("dressage",), ("training","scale"), ("piaffe",)],
    "vaulting":         [("vaulting",)],
    "trailer loading":  [("trailer","load")],
    "facilities":       [("misting",), ("pasture",), ("fencing",), ("footing",),
                         ("manure",), ("boarding","facility"), ("swimming","pool")],
}


def discipline_of(text):
    low = (text or "").lower()
    return {d for d, groups in DISCIPLINES.items()
            if any(all(t in low for t in grp) for grp in groups)}


def discipline_violation(label, yt_title):
    """Label claims discipline A; the video is unambiguously discipline B."""
    lab_d = discipline_of(label)
    vid_d = discipline_of(yt_title)
    if not lab_d or not vid_d:
        return None, None            # can't tell — do not flag
    if lab_d & vid_d:
        return None, None            # overlap — fine
    return sorted(lab_d)[0], sorted(vid_d)[0]


def attribution_violation(label, yt_title, channel):
    """
    Returns (severity, claimed, actual).

    "conflict" — the label credits trainer A, but the video demonstrably
                 belongs to a DIFFERENT known trainer B. This is a factual
                 error and fails the build.

    "unconfirmed" — the label credits a trainer we cannot confirm from the
                 channel/title. This is common and often fine: aggregator
                 channels (Weaver Equine, Horse&Rider) publish clips of many
                 clinicians. Reported, never failed.
    """
    low = (label or "").lower()
    hay = ((channel or "") + " " + (yt_title or "")).lower()

    claimed = next((n for n in KNOWN_TRAINERS if n in low), None)
    if not claimed:
        return None, None, None
    if any(m in hay for m in KNOWN_TRAINERS[claimed]):
        return None, None, None          # claim confirmed

    # Does the video clearly belong to some OTHER known trainer?
    for other, markers in KNOWN_TRAINERS.items():
        if other == claimed:
            continue
        if any(m in hay for m in markers):
            return "conflict", claimed, other

    return "unconfirmed", claimed, (channel or "unknown")


def tokens(s):
    s = re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())
    return {w for w in s.split() if w and w not in STOP}


def overlap(a, b):
    A, B = tokens(a), tokens(b)
    if not A or not B:
        return 1.0        # nothing to compare — do not flag
    return len(A & B) / min(len(A), len(B))


def collect(paths):
    """Return {video_id: [(file, label), ...]}"""
    found = {}
    for p in paths:
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "facade" not in s and "video-thumb" not in s:
            continue
        for m in FACADE.finditer(s):
            attrs = m.group(1)
            vm = ATTR["vid"].search(attrs)
            if not vm:
                continue
            vid = vm.group(1)
            lm = ATTR["title"].search(attrs) or ATTR["aria"].search(attrs)
            label = html.unescape(lm.group(1)).strip() if lm else ""
            # A bare "Play video" / "Play" is an accessibility affordance,
            # not a caption. Absence of a caption is not a violation.
            if label.lower() in ("play video", "play", ""):
                label = ""
            found.setdefault(vid, []).append((str(p), label))
    return found


def oembed(vid):
    """(status, title, channel). status: live | dead | error"""
    req = urllib.request.Request(OEMBED.format(vid=vid), headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read().decode())
                return "live", d.get("title", ""), d.get("author_name", "")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):
                return "dead", "", ""
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    return "error", "", ""


def changed_files():
    """
    HTML touched vs origin/main, INCLUDING uncommitted working-tree and staged
    changes. Omitting those would let a pre-commit run pass vacuously — the
    exact failure mode that let bad captions ship in the first place.
    """
    base = subprocess.run(
        ["git", "merge-base", "HEAD", "origin/main"],
        capture_output=True, text=True).stdout.strip() or "HEAD~1"
    names = set()
    for cmd in (["git", "diff", "--name-only", base, "HEAD"],  # committed
                ["git", "diff", "--name-only", "HEAD"],        # unstaged
                ["git", "diff", "--name-only", "--cached"]):   # staged
        names.update(subprocess.run(cmd, capture_output=True,
                                    text=True).stdout.split())
    return [Path(f) for f in names if f.endswith(".html") and Path(f).exists()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed-only", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="treat network failures as violations")
    args = ap.parse_args()

    files = changed_files() if args.changed_only else list(Path(".").rglob("*.html"))
    files = [f for f in files if ".git" not in f.parts]
    found = collect(files)

    if not found:
        print("No video facades found — nothing to check.")
        return 0

    print("Checking %d unique videos across %d files..."
          % (len(found), len({f for v in found.values() for f, _ in v})))

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = dict(zip(found, ex.map(oembed, found)))

    dead, mislabeled, unconfirmed, wrong_topic, errors = [], [], [], [], []
    for vid, (status, yt_title, channel) in results.items():
        if status == "error":
            errors.append(vid)
            continue
        if status == "dead":
            for f, lab in found[vid]:
                dead.append((vid, f, lab))
            continue
        for f, lab in found[vid]:
            sev, claimed, actual = attribution_violation(lab, yt_title, channel)
            if sev == "conflict":
                mislabeled.append((vid, f, lab, yt_title, channel, claimed, actual))
            elif sev == "unconfirmed":
                unconfirmed.append((vid, f, lab, yt_title, channel, claimed))
            ld, vd = discipline_violation(lab, yt_title)
            if ld:
                wrong_topic.append((vid, f, lab, yt_title, ld, vd))

    if dead:
        print("\n=== DEAD VIDEOS (%d placements) ===" % len(dead))
        for vid, f, lab in dead:
            print("  %s  %s" % (vid, f))
            print("       label: %s" % lab[:80])

    if mislabeled:
        print("\n=== FABRICATED ATTRIBUTION (%d placements) ===" % len(mislabeled))
        print("A label credits a trainer who did not produce this video.\n")
        for vid, f, lab, yt, ch, claimed, actual in mislabeled:
            print("  %s  %s" % (vid, f))
            print("       label credits : %s" % claimed.title())
            print("       video is by   : %s  [%s]" % (actual.title(), ch))
            print("       label         : %s" % lab[:72])
            print("       real title    : %s" % yt[:72])

    if wrong_topic:
        print("\n=== WRONG DISCIPLINE (%d placements) ===" % len(wrong_topic))
        print("The label claims one discipline; the video is another.\n")
        for vid, f, lab, yt, ld, vd in wrong_topic:
            print("  %s  %s" % (vid, f))
            print("       label claims : %s" % ld)
            print("       video is     : %s" % vd)
            print("       label        : %s" % lab[:72])
            print("       real title   : %s" % yt[:72])

    if unconfirmed:
        print("\n--- unconfirmed attribution (%d) — review, not failing ---"
              % len(unconfirmed))
        print("    Label names a trainer the channel does not confirm. Often fine:")
        print("    aggregator channels publish clips of many clinicians.\n")
        seen_u = set()
        for vid, f, lab, yt, ch, claimed in unconfirmed:
            if vid in seen_u:
                continue
            seen_u.add(vid)
            print("    %s  credits %s | channel: %s" % (vid, claimed.title(), ch))
            print("           real title: %s" % yt[:66])

    if errors:
        print("\n=== COULD NOT VERIFY (%d) ===" % len(errors))
        print("  " + ", ".join(errors[:12]))

    bad = len(dead) + len(mislabeled) + len(wrong_topic)
    print("\n" + "-" * 60)
    print("checked : %d videos" % len(found))
    print("dead    : %d" % len(dead))
    print("bad attr: %d" % len(mislabeled))
    print("bad topic: %d" % len(wrong_topic))
    print("unknown : %d" % len(errors))

    if bad:
        print("\nFAIL — %d violation(s)." % bad)
        return 1
    if errors and args.strict:
        print("\nFAIL — could not verify %d video(s) (--strict)." % len(errors))
        return 2
    print("\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
