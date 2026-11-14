"""Mid-page Revive zone (31835) placement helper used by add_revive.py.

Q&A answer pages: directly after </article> (between the answer and the CTA/video/related blocks).
Every other page: after the top-level content block where cumulative visible text first reaches 50%
(descending into a wrapper that holds >70% of the text). Never inside header/footer/nav/script.
"""
import re
from html.parser import HTMLParser

VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
SKIP = {"header","footer","nav","script","style","noscript","form","button","svg","iframe"}
CAND = {"section","div","article","aside","ul","ol","table","p","h2","h3","blockquote","details","figure","main"}

class Node:
    __slots__ = ("tag","cls","start","end","kids","text","parent")
    def __init__(s, tag, cls, start, parent):
        s.tag, s.cls, s.start, s.end, s.kids, s.text, s.parent = tag, cls, start, None, [], 0, parent

class P(HTMLParser):
    def __init__(s, src):
        super().__init__(convert_charrefs=True)
        s.src = src
        s.lines = [0]
        for m in re.finditer("\n", src):
            s.lines.append(m.end())
        s.root = Node("#root", "", 0, None)
        s.root.end = len(src)
        s.stack = [s.root]
    def off(s):
        l, c = s.getpos()
        return s.lines[l - 1] + c
    def handle_starttag(s, tag, attrs):
        n = Node(tag, dict(attrs).get("class") or "", s.off(), s.stack[-1])
        s.stack[-1].kids.append(n)
        if tag in VOID:
            n.end = n.start + len(s.get_starttag_text())
        else:
            s.stack.append(n)
    def handle_startendtag(s, tag, attrs):
        n = Node(tag, dict(attrs).get("class") or "", s.off(), s.stack[-1])
        n.end = n.start + len(s.get_starttag_text())
        s.stack[-1].kids.append(n)
    def handle_endtag(s, tag):
        if tag in VOID:
            return
        for i in range(len(s.stack) - 1, 0, -1):
            if s.stack[i].tag == tag:
                gt = s.src.find(">", s.off())
                end = gt + 1
                for n in s.stack[i:]:
                    n.end = end
                del s.stack[i:]
                return
    def handle_data(s, d):
        t = len(d.strip())
        if t:
            for n in s.stack:
                n.text += t

def _find(n, pred):
    for k in n.kids:
        if pred(k):
            return k
        r = _find(k, pred)
        if r:
            return r

def mid_offset(src):
    """Return the character offset at which to insert the mid zone, or None."""
    p = P(src)
    try:
        p.feed(src); p.close()
    except Exception:
        return None
    body = _find(p.root, lambda n: n.tag == "body")
    if not body or body.end is None:
        return None
    art = _find(body, lambda n: n.tag == "article" and "answer-wrap" in n.cls)
    if art is not None and art.end:
        return art.end
    cont = _find(body, lambda n: n.tag == "main") or body
    GRIDLIKE = re.compile(r"layout|grid|flex|row|col|split|two|sidebar", re.I)
    for _ in range(10):
        kids = [k for k in cont.kids if k.tag in CAND and k.end is not None
                and not re.search(r"revive-zone|breadcrumb|modal|drawer|overlay|cookie|toast", k.cls) and k.text > 0]
        total = sum(k.text for k in kids)
        if not kids or total < 150:
            return None
        big = max(kids, key=lambda k: k.text)
        # never split a grid/flex container: descend into its main column instead
        if GRIDLIKE.search(cont.cls) or (big.text > 0.6 * total and any(c.tag in CAND for c in big.kids)):
            if any(c.tag in CAND for c in big.kids):
                cont = big
                continue
            return None
        if len(kids) < 2:
            return None
        cum, best, bd = 0, None, None
        for i, k in enumerate(kids[:-1]):
            cum += k.text
            d = abs(cum - total / 2)
            if bd is None or d < bd:
                best, bd = i, d
        return kids[best].end
    return None
