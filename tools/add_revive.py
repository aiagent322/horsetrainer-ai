#!/usr/bin/env python3
"""Insert the Revive Adserver header (31833) and footer (31834) zones into every HTML page (idempotent).

Placement: directly after the site header (</header>); pages without a
<header> get it after the first </nav> in <body>, else right after <body>.
Run after any rebuild:  python3 -I tools/add_revive.py
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "<!-- revive-header -->"
ZONE = (
    MARK + "\n"
    '<div class="revive-zone revive-header" style="display:flex;justify-content:center;align-items:center;text-align:center;margin:10px auto;max-width:100%;overflow:hidden">\n'
    "<!-- Revive Adserver Hosted edition Asynchronous JS Tag - Generated with Revive Adserver v6.0.6 -->\n"
    '<ins data-revive-zoneid="31833" data-revive-id="727bec5e09208690b050ccfc6a45d384"></ins>\n'
    '<script async src="//servedby.revive-adserver.net/asyncjs.php"></script>\n'
    "</div>\n"
    "<!-- /revive-header -->"
)

FMARK = "<!-- revive-footer -->"
FZONE = (
    FMARK + "\n"
    '<div class="revive-zone revive-footer" style="display:flex;justify-content:center;align-items:center;text-align:center;margin:10px auto;max-width:100%;overflow:hidden">\n'
    "<!-- Revive Adserver Hosted edition Asynchronous JS Tag - Generated with Revive Adserver v6.0.6 -->\n"
    '<ins data-revive-zoneid="31834" data-revive-id="727bec5e09208690b050ccfc6a45d384"></ins>\n'
    '<script async src="//servedby.revive-adserver.net/asyncjs.php"></script>\n'
    "</div>\n"
    "<!-- /revive-footer -->"
)

def inject_footer(s):
    """Footer zone goes immediately before <footer>, else before </body>."""
    if FMARK in s or "<body" not in s:
        return s, False
    b = s.index("<body")
    k = s.find("<footer", b)
    if k < 0:
        k = s.rfind("</body>")
        if k < 0:
            return s, False
    return s[:k] + FZONE + "\n" + s[k:], True

def inject(s):
    if MARK in s or "<body" not in s:
        return s, False
    b = s.index("<body")
    j = s.find("</header>", b)
    if j >= 0:
        k = j + len("</header>")
    else:
        j = s.find("</nav>", b)
        if j >= 0:
            k = j + len("</nav>")
        else:
            k = s.index(">", b) + 1
    return s[:k] + "\n" + ZONE + s[k:], True

def main():
    n = 0
    for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        if "/.git/" in p:
            continue
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        t, ch = inject(s)
        t, ch2 = inject_footer(t)
        ch = ch or ch2
        if ch:
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(t)
            n += 1
    print(f"revive zone added to {n} pages")

if __name__ == "__main__":
    main()
