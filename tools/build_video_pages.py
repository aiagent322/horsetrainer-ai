#!/usr/bin/env python3
"""Build the video library: one page per video, a library index and category pages.

Sources (nothing is invented):
  videos.json            - YouTube oEmbed title + channel for the older videos (verified values)
  data/qa_videos.json    - every Q&A answer page that carries a video block (id, title, page)
  the pages themselves   - h1 and meta description of each page that uses a video

Output:
  videos/watch/<slug>/index.html      one page per video
  videos/library/index.html           all topics with counts
  videos/library/<category>/index.html  every video in one topic
  data/video_slugs.json               id -> slug, so URLs stay stable between runs

Channel is shown only when videos.json (oEmbed) has it. Titles come from oEmbed when present,
otherwise from the facade title already on the site. Run from the repo root:
  python3 tools/build_video_pages.py
Then run tools/build_sitemaps.py.
"""
import os, re, json, html, collections, shutil

HOST = 'https://horsetrainer.ai'
E = html.escape
SKIP_CATS = {'famous-trainers', 'find-a-trainer', 'trainers', 'about', 'list-your-training', 'videos', 'tv',
             'training', 'css', 'js', 'images', 'functions', 'workers', 'data', 'tools'}
LISTING = re.compile(r'^(videos/|qa/[^/]+/index\.html$|qa/index\.html$|index\.html$)')

def slugify(t):
    t = html.unescape(t).lower().replace('&', ' and ')
    t = re.sub(r"[’']", '', t)
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    if len(t) > 60:
        t = t[:60]
        t = t[:t.rfind('-')] if '-' in t else t
    return t or 'video'

def cat_name(slug):
    fix = {'qa': 'Q&A'}
    if slug == 'trainer-profiles': return 'Trainer Profile'
    return ' '.join(fix.get(w, w.capitalize()) for w in slug.split('-'))

def page_info(path, cache={}):
    if path in cache: return cache[path]
    info = None
    if os.path.exists(path):
        t = open(path, encoding='utf-8', errors='ignore').read()
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
        ds = re.search(r'<meta name="description" content="([^"]*)"', t)
        can = re.search(r'<link rel="canonical" href="([^"]+)"', t)
        if h1:
            title = re.sub(r'<[^>]+>', '', h1.group(1))
            title = re.sub(r'\s+', ' ', html.unescape(title)).strip()
            url = can.group(1) if can else HOST + '/' + (path[:-10] if path.endswith('index.html') else path[:-5])
            url = url.replace(HOST, '')
            info = {'path': path, 'title': title, 'desc': html.unescape(ds.group(1)).strip() if ds else '', 'url': url}
    cache[path] = info
    return info

def load():
    vj = {v['id']: v for v in json.load(open('videos.json'))['videos']}
    qa = json.load(open('data/qa_videos.json'))
    vids = {}
    for key, blk in qa['blocks'].items():
        m = re.search(r'data-vid="?([\w-]+)"?\s+data-title="([^"]*)"', blk)
        if not m: continue
        vid, ttl = m.group(1), html.unescape(m.group(2))
        v = vids.setdefault(vid, {'id': vid, 'site_title': ttl, 'pages': []})
        v['pages'].append('qa/' + key + '/index.html')
    for vid, j in vj.items():
        v = vids.setdefault(vid, {'id': vid, 'site_title': (j['site_titles'] or [j['youtube_title']])[0], 'pages': []})
        v['pages'] += [p for p in j['pages']]
    out = []
    for vid, v in vids.items():
        j = vj.get(vid)
        v['title'] = (j['youtube_title'] if j else v['site_title']).strip()
        v['channel'] = (j['channel'].strip() if j and j.get('channel') else None)
        # pages: dedupe, keep real files that have an h1
        seen, pages = set(), []
        for p in v['pages']:
            if p in seen: continue
            seen.add(p)
            pi = page_info(p)
            if pi: pages.append(pi)
        v['pages_info'] = pages
        cats = collections.Counter()
        for p in pages:
            parts = p['path'].split('/')
            if parts[0] == 'qa' and len(parts) > 2: cats[parts[1]] += 1
            elif parts[0] == 'videos' and len(parts) > 2: cats[parts[1]] += 1
            elif len(parts) > 1 and parts[0] not in SKIP_CATS: cats[parts[0]] += 1
        v['cats'] = cats
        if not cats and any(p['path'].startswith('famous-trainers/') for p in pages): cats['trainer-profiles'] += 1
        v['cat'] = sorted(cats.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if cats else 'general'
        out.append(v)
    return sorted(out, key=lambda v: v['id'])

def assign_slugs(vids):
    sp = 'data/video_slugs.json'
    slugs = json.load(open(sp)) if os.path.exists(sp) else {}
    used = set(slugs.values())
    for v in vids:
        if v['id'] in slugs: continue
        s = slugify(v['title']); base = s; n = 2
        while s in used:
            s = f'{base}-{n}'; n += 1
        slugs[v['id']] = s; used.add(s)
    json.dump(slugs, open(sp, 'w'), indent=0, sort_keys=True)
    for v in vids: v['slug'] = slugs[v['id']]

def shell():
    s = open('videos/index.html', encoding='utf-8').read()
    nav = s[s.find('<nav class="nav">'):s.find('<section class="page-header">')]
    foot = ('<footer class="footer"><div class="container"><div class="footer-bottom"><div class="footer-copy">'
            '© 2026 HorseTrainer.ai — A Bridle &amp; Bit Magazine property.</div>'
            '<a href="/videos/library/" style="font-size:.875rem;color:var(--muted);">← Back to the Video Library</a></div></div></footer>\n'
            '<script src="/js/app.js"></script>\n')
    return nav, foot

CSS = json.load(open('data/qa_videos.json'))['meta']['css'] if os.path.exists('data/qa_videos.json') else ''
SCRIPT = json.load(open('data/qa_videos.json'))['meta']['script']
EXTRA = """
.vp-wrap{max-width:760px}
.vp-wrap .qa-vid-card{max-width:100%;border-radius:8px}
.vp-meta{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 1rem;font-size:.875rem;color:var(--muted)}
.vp-chip{display:inline-block;padding:.3rem .75rem;border:1px solid rgba(255,255,255,.55);border-radius:99px;color:#fff;text-decoration:none;font-size:.8rem}
.page-header .vp-meta{color:rgba(255,255,255,.85)}
.vp-yt{display:inline-block;margin:.85rem 0 0;font-size:.875rem}
.vp-list{list-style:none;padding:0;margin:0}
.vp-list li{padding:.8rem 0;border-top:1px solid var(--border)}
.vp-list li:first-child{border-top:0}
.vp-list a{font-weight:600;color:var(--primary);text-decoration:none}
.vp-list p{margin:.25rem 0 0;font-size:.875rem;color:var(--muted);line-height:1.5}
.vp-h2{font-size:1.15rem;margin:2rem 0 .75rem}
.vp-grid{display:grid;gap:1rem;grid-template-columns:1fr}
@media(min-width:640px){.vp-grid{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1024px){.vp-grid.wide{grid-template-columns:repeat(3,1fr)}}
.vp-card{display:block;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;overflow:hidden;text-decoration:none;color:inherit}
.vp-card img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;background:#0a0a0a}
.vp-card span{display:block;padding:.7rem .85rem;font-size:.875rem;font-weight:600;color:var(--primary);line-height:1.4}
.vp-card small{display:block;padding:0 .85rem .7rem;font-size:.75rem;color:var(--muted)}
.vp-cats{display:grid;gap:.75rem;grid-template-columns:1fr}
@media(min-width:560px){.vp-cats{grid-template-columns:repeat(2,1fr)}}
@media(min-width:900px){.vp-cats{grid-template-columns:repeat(3,1fr)}}
.vp-cat{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.1rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);text-decoration:none;color:var(--primary);font-weight:600;min-height:56px}
.vp-cat b{color:var(--muted);font-weight:500;font-size:.85rem}
"""

def head(title, desc, canon, extra_ld, extra_css=''):
    t = E(title, quote=True); d = E(desc, quote=True)
    og = HOST + '/images/og/og-videos.jpg?v=1'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <link rel="canonical" href="{canon}">
  <script type="application/ld+json">{json.dumps(extra_ld, ensure_ascii=False)}</script>
  <link rel="stylesheet" href="/css/style.css?v=2">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐎</text></svg>">
<meta property="og:type" content="website">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{t}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{og}">
  <style>{CSS}{EXTRA}{extra_css}</style>
</head>
<body>
'''

def crumbs(items):
    parts = []
    for i, (name, url) in enumerate(items):
        parts.append(f'<a href="{url}">{E(name)}</a>' if url else f'<span>{E(name)}</span>')
    return '<div class="breadcrumb">' + '<span class="breadcrumb-sep">›</span>'.join(parts) + '</div>'

def bc_ld(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': HOST + (u or '')} for i, (n, u) in enumerate(items) if u]}

def trim(s, n):
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) <= n: return s
    s = s[:n - 1]
    return s[:s.rfind(' ')].rstrip(',;:-– ') + '…'

def video_page(v, nav, foot, by_cat, vmap):
    cat, cname = v['cat'], cat_name(v['cat'])
    title = v['title']
    qa_pages = [p for p in v['pages_info'] if p['path'].startswith('qa/')]
    other = [p for p in v['pages_info'] if not p['path'].startswith('qa/') and not LISTING.match(p['path'])]
    n = len(qa_pages)
    ttag = title + ' | HorseTrainer.ai' if len(title) + 18 <= 60 else trim(title, 60)
    if n:
        desc = trim(f'Watch “{title}” and see the {n} horse training question{"s" if n != 1 else ""} it helps answer on HorseTrainer.ai.', 160)
    else:
        desc = trim(f'Watch “{title}” — a horse training video in the {cname} section of HorseTrainer.ai.', 160)
    canon = f'{HOST}/videos/watch/{v["slug"]}/'
    bc = [('Home', '/'), ('Videos', '/videos/'), ('Video Library', '/videos/library/'), (cname, f'/videos/library/{cat}/'), (trim(title, 48), None)]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'description': desc, 'url': canon,
         'isPartOf': {'@type': 'WebSite', 'name': 'HorseTrainer.ai', 'url': HOST + '/'}}, bc_ld(bc)]}
    h = head(ttag, desc, canon, ld) + nav
    h += f'\n<section class="page-header"><div class="container vp-wrap">{crumbs(bc)}\n<h1>{E(title)}</h1>\n'
    meta = [f'<a class="vp-chip" href="/videos/library/{cat}/">{E(cname)}</a>']
    for c, _ in sorted(v['cats'].items(), key=lambda kv: (-kv[1], kv[0])):
        if c != cat and c in by_cat: meta.append(f'<a class="vp-chip" href="/videos/library/{c}/">{E(cat_name(c))}</a>')
    if v['channel']: meta.append(f'<span>Channel: {E(v["channel"])}</span>')
    h += '<div class="vp-meta">' + ''.join(meta[:5]) + '</div></div></section>\n'
    h += '<section class="section-sm" style="padding-top:0;"><div class="container vp-wrap">\n'
    t = E(title, quote=True)
    h += (f'<div class="qa-vid-card"><div class="qa-vid-facade" data-vid="{v["id"]}" data-title="{t}">'
          f'<img src="https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg" alt="{t}" width="480" height="270">'
          f'<div class="qa-vid-play">&#9654;</div></div></div>\n'
          f'<a class="vp-yt" href="https://www.youtube.com/watch?v={v["id"]}" rel="noopener" target="_blank">Watch on YouTube ↗</a>\n')
    if qa_pages:
        h += f'<h2 class="vp-h2">Questions this video helps answer</h2>\n<ul class="vp-list">\n'
        for i, p in enumerate(sorted(qa_pages, key=lambda p: p['title'])):
            snip = f'<p>{E(trim(p["desc"], 200))}</p>' if p['desc'] and i < 6 else ''
            h += f'<li><a href="{p["url"]}">{E(p["title"])}</a>{snip}</li>\n'
        h += '</ul>\n'
    if other:
        h += '<h2 class="vp-h2">Also featured on</h2>\n<ul class="vp-list">\n'
        for p in sorted(other, key=lambda p: p['title']):
            h += f'<li><a href="{p["url"]}">{E(p["title"])}</a></li>\n'
        h += '</ul>\n'
    # related: same primary category, most shared pages first, then stable order
    mine = {p['path'] for p in v['pages_info']}
    rel = [o for o in by_cat.get(cat, []) if o['id'] != v['id']]
    rel.sort(key=lambda o: (-len(mine & {p['path'] for p in o['pages_info']}), o['id']))
    if rel:
        h += f'<h2 class="vp-h2">More {E(cname)} videos</h2>\n<div class="vp-grid">\n'
        for o in rel[:6]:
            h += card(o)
        h += '</div>\n'
        h += f'<p style="margin-top:1rem;"><a href="/videos/library/{cat}/">All {len(by_cat[cat])} {E(cname)} videos →</a></p>\n'
    h += '</div></section>\n' + foot + '<script>' + SCRIPT.replace('<script>', '').replace('</script>', '') + '</script>\n</body></html>\n'
    return h

def card(o):
    ch = f'<small>{E(o["channel"])}</small>' if o['channel'] else ''
    return (f'<a class="vp-card" href="/videos/watch/{o["slug"]}/"><img src="https://i.ytimg.com/vi/{o["id"]}/hqdefault.jpg" '
            f'alt="" loading="lazy" width="480" height="270"><span>{E(o["title"])}</span>{ch}</a>\n')

def library_index(by_cat, total, nav, foot):
    cats = sorted(by_cat.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    canon = HOST + '/videos/library/'
    desc = f'Browse {total} horse training videos by topic. Every video has its own page with the questions it helps answer.'
    bc = [('Home', '/'), ('Videos', '/videos/'), ('Video Library', None)]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': 'Horse Training Video Library', 'description': desc, 'url': canon}, bc_ld(bc)]}
    h = head('Horse Training Video Library — All Videos by Topic', desc, canon, ld) + nav
    h += f'\n<section class="page-header"><div class="container">{crumbs(bc)}\n<h1>Horse Training Video Library</h1>\n'
    h += f'<p class="lead">{total} videos across {len(cats)} topics. Each video has its own page with the questions it helps answer.</p></div></section>\n'
    h += ('<section class="section-sm" style="padding-top:0;"><div class="container">'
          '<p style="margin:0 0 1.25rem;"><a class="btn btn-primary" href="/videos/inventory/">Search every video &amp; browse by group →</a></p>'
          '<div class="vp-cats">\n')
    for c, vs in cats:
        h += f'<a class="vp-cat" href="/videos/library/{c}/"><span>{E(cat_name(c))}</span><b>{len(vs)}</b></a>\n'
    h += '</div></div></section>\n' + foot + '</body></html>\n'
    return h

def category_page(c, vs, nav, foot):
    cname = cat_name(c)
    canon = f'{HOST}/videos/library/{c}/'
    desc = trim(f'{len(vs)} {cname} videos from the HorseTrainer.ai library. Each links to the questions it helps answer.', 160)
    bc = [('Home', '/'), ('Videos', '/videos/'), ('Video Library', '/videos/library/'), (cname, None)]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': f'{cname} Videos', 'description': desc, 'url': canon}, bc_ld(bc)]}
    h = head(f'{cname} Videos | HorseTrainer.ai', desc, canon, ld) + nav
    h += f'\n<section class="page-header"><div class="container">{crumbs(bc)}\n<h1>{E(cname)} Videos</h1>\n<p class="lead">{len(vs)} video{"s" if len(vs) != 1 else ""}.</p></div></section>\n'
    h += '<section class="section-sm" style="padding-top:0;"><div class="container"><div class="vp-grid wide">\n'
    for o in sorted(vs, key=lambda o: o['title'].lower()):
        h += card(o)
    h += '</div></div></section>\n' + foot + '</body></html>\n'
    return h


GROUPS = [
    ('Ground Work & Handling', 'Manners, pressure and release, longeing, liberty and voice cues.',
     ['ground-manners-handling', 'groundwork', 'groundwork-longing', 'backing-on-the-ground', 'desensitization-sacking-out',
      'yielding-to-pressure', 'leadership-bonding', 'liberty', 'voice-cues', 'trailer-loading']),
    ('Young Horses & Colt Starting', 'Foals, yearlings, first rides and wild or mustang starts.',
     ['colt-starting', 'starting-young-horses', 'imprinting', 'weanling-handling', 'yearling-groundwork',
      'wild-horse-training', 'mustang']),
    ('Training Philosophy & Problem Solving', 'Methods, principles, problem behavior and choosing a trainer.',
     ['natural-horsemanship', 'training-principles', 'horsemanship', 'western-horsemanship', 'problem-horse',
      'problem-solving-under-saddle', 'choosing-a-trainer', 'trainer-profiles']),
    ('Rider Skills & Aids', 'Seat, reins, bits, lateral work, collection, gaits and leads.',
     ['position-seat', 'body-position-communication', 'rein-aids', 'neck-reining', 'bit-progression', 'mounting-dismounting',
      'lateral-work-suppling', 'collection', 'gaits', 'counter-canter', 'lead-changes']),
    ('Dressage, English & Jumping', 'Dressage, hunters and jumpers, English classes and working equitation.',
     ['dressage', 'dressage-lessons', 'english-competition', 'english-pleasure', 'hunter-jumper', 'working-equitation']),
    ('Western Performance', 'Reining, cutting, cow horse, western pleasure and ranch classes.',
     ['reining', 'cutting', 'working-cow-horse', 'reined-cow-horse', 'western-pleasure', 'ranch-riding',
      'versatility-ranch-horse', 'working-western-rail']),
    ('Rodeo, Roping & Speed', 'Team roping, breakaway, steer wrestling, barrels and mounted shooting.',
     ['team-roping', 'breakaway-roping', 'steer-wrestling', 'timed-events', 'barrel-racing', 'speed', 'mounted-shooting']),
    ('Trail, Driving & Specialty', 'Trail, obstacles, driving, packing, vaulting and therapeutic riding.',
     ['trail', 'obstacle-training', 'driving', 'packing', 'vaulting', 'therapeutic-riding']),
    ('Care, Safety & Equipment', 'Horse care, safety, facilities, tack and equipment.',
     ['horse-care', 'safety', 'facilities', 'equipment', 'tack']),
    ('Competition & General', 'Showing and competing, plus videos that cover several topics.',
     ['competition', 'general']),
]

INV_CSS = """
.inv-search{display:flex;flex-wrap:wrap;gap:.6rem;margin:0 0 .5rem}
.inv-search input[type=search]{flex:1 1 280px;min-width:0;padding:.8rem 1rem;font-size:1rem;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--cream)}
.inv-search select{flex:0 1 260px;padding:.8rem .9rem;font-size:1rem;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--cream)}
.inv-search input:focus,.inv-search select:focus{outline:2px solid var(--accent);outline-offset:1px}
.inv-status{font-size:.9rem;color:var(--muted);margin:.4rem 0 1rem;min-height:1.3em}
.inv-results{display:none}
.inv-results.on{display:block}
.inv-more{display:block;margin:1.25rem auto 0;padding:.75rem 1.6rem;font-size:1rem;font-weight:600;color:var(--primary);background:#fff;border:1px solid var(--primary);border-radius:8px;cursor:pointer}
.inv-more:hover{background:var(--bg-raised)}
.inv-tag{display:inline-block;margin:0 .85rem .75rem;padding:.15rem .55rem;font-size:.7rem;font-weight:600;color:var(--secondary);background:var(--bg-raised);border-radius:99px}
.inv-groups{display:grid;gap:1rem;grid-template-columns:1fr}
@media(min-width:700px){.inv-groups{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1050px){.inv-groups{grid-template-columns:repeat(3,1fr)}}
.inv-group{display:flex;flex-direction:column;border:1px solid var(--border);border-radius:10px;background:var(--bg-card);padding:1.15rem 1.2rem}
.inv-group h3{margin:0;font-size:1.1rem;color:var(--primary);line-height:1.3}
.inv-group .n{margin:.2rem 0 .5rem;font-size:.85rem;font-weight:600;color:var(--gold-dim)}
.inv-group p{margin:0 0 .8rem;font-size:.9rem;line-height:1.5;color:var(--cream-dim)}
.inv-topics{display:flex;flex-wrap:wrap;gap:.35rem;margin:0 0 1rem;padding:0;list-style:none}
.inv-topics a{display:inline-block;padding:.28rem .65rem;font-size:.78rem;color:var(--primary);background:var(--bg-raised);border:1px solid var(--border);border-radius:99px;text-decoration:none}
.inv-topics a:hover{border-color:var(--secondary)}
.inv-topics b{font-weight:500;color:var(--muted)}
.inv-group button{margin-top:auto;align-self:flex-start;padding:.55rem 1.1rem;font-size:.9rem;font-weight:600;color:#fff;background:var(--primary);border:0;border-radius:6px;cursor:pointer}
.inv-group button:hover{background:var(--primary-light)}
"""

INV_JS = r"""
(function(){
var q=document.getElementById('inv-q'),g=document.getElementById('inv-g'),st=document.getElementById('inv-status'),
    res=document.getElementById('inv-results'),grid=document.getElementById('inv-grid'),more=document.getElementById('inv-more'),
    browse=document.getElementById('inv-browse');
var DATA=null,loading=false,list=[],shown=0,PAGE=48;
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function load(cb){
  if(DATA){cb();return}
  if(loading)return;loading=true;st.textContent='Loading the video list…';
  fetch('/videos/inventory/data.json').then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){
    DATA=d;loading=false;cb();
  }).catch(function(){loading=false;st.innerHTML='The video list could not be loaded. <a href="/videos/library/">Browse the library by topic</a> instead.'});
}
function card(v){
  var t=esc(v[1]),ch=v[2]?'<small>'+esc(v[2])+'</small>':'';
  return '<a class="vp-card" href="/videos/watch/'+v[0]+'/"><img src="https://i.ytimg.com/vi/'+v[4]+'/hqdefault.jpg" alt="" loading="lazy" width="480" height="270"><span>'+t+'</span>'+ch+
         '<em class="inv-tag" style="font-style:normal">'+esc(DATA.cats[v[3]]||v[3])+'</em></a>';
}
function render(){
  var terms=q.value.toLowerCase().split(/\s+/).filter(Boolean),gi=g.value;
  var allowed=null;
  if(gi!==''){allowed={};DATA.groups[+gi].cats.forEach(function(c){allowed[c]=1})}
  list=DATA.videos.filter(function(v){
    if(allowed&&!allowed[v[3]])return false;
    if(!terms.length)return true;
    var hay=(v[1]+' '+(v[2]||'')+' '+(DATA.cats[v[3]]||'')).toLowerCase();
    for(var i=0;i<terms.length;i++){if(hay.indexOf(terms[i])<0)return false}
    return true;
  });
  var active=terms.length||gi!=='';
  res.className='inv-results'+(active?' on':'');
  browse.style.display=active?'none':'';
  grid.innerHTML='';shown=0;
  if(!active){st.textContent=DATA.videos.length+' videos. Type to search, or pick a group.';more.style.display='none';return}
  list.sort(function(a,b){return a[1].toLowerCase()<b[1].toLowerCase()?-1:1});
  st.textContent=list.length?list.length+(list.length===1?' video found':' videos found'):'No videos match. Try fewer or different words.';
  next();
  var u=new URLSearchParams();if(q.value.trim())u.set('q',q.value.trim());if(gi!=='')u.set('group',gi);
  history.replaceState(null,'',location.pathname+(u.toString()?'?'+u.toString():''));
}
function next(){
  var end=Math.min(shown+PAGE,list.length),h='';
  for(var i=shown;i<end;i++)h+=card(list[i]);
  grid.insertAdjacentHTML('beforeend',h);shown=end;
  more.style.display=shown<list.length?'':'none';
  more.textContent='Show more ('+(list.length-shown)+' left)';
}
var timer;
function go(){clearTimeout(timer);timer=setTimeout(function(){load(render)},120)}
q.addEventListener('input',go);g.addEventListener('change',function(){load(render)});
more.addEventListener('click',next);
document.querySelectorAll('[data-group]').forEach(function(b){b.addEventListener('click',function(){
  g.value=b.getAttribute('data-group');load(render);window.scrollTo({top:document.getElementById('inv-top').offsetTop-12,behavior:'smooth'});
})});
q.addEventListener('focus',function(){load(function(){})},{once:true});
var p=new URLSearchParams(location.search);
if(p.get('q'))q.value=p.get('q');
if(p.get('group')!==null&&/^\d+$/.test(p.get('group'))&&+p.get('group')<g.options.length-1)g.value=p.get('group');
if(q.value||g.value!=='')load(render);
})();
"""

def inventory_page(vids, by_cat, nav, foot):
    total = len(vids)
    known = set(by_cat)
    groups, used = [], set()
    for name, blurb, cats in GROUPS:
        cs = [c for c in cats if c in known]
        used.update(cs)
        groups.append([name, blurb, cs])
    leftover = sorted(known - used)
    if leftover: groups[-1][2] += leftover          # a new topic is never dropped from the page
    canon = HOST + '/videos/inventory/'
    desc = trim(f'Search {total} horse training videos by title, channel or topic, or browse {len(groups)} groups from groundwork to roping.', 160)
    bc = [('Home', '/'), ('Videos', '/videos/'), ('Video Inventory', None)]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': 'Horse Training Video Inventory', 'description': desc, 'url': canon}, bc_ld(bc)]}
    h = head('Horse Training Video Inventory — Search All Videos', desc, canon, ld, INV_CSS) + nav
    h += f'\n<section class="page-header"><div class="container">{crumbs(bc)}\n<h1>Horse Training Video Inventory</h1>\n'
    h += f'<p class="lead">Search all {total} videos, or browse by group. Every video links to the questions it helps answer.</p></div></section>\n'
    h += '<section class="section-sm" style="padding-top:0;"><div class="container" id="inv-top">\n'
    h += '<form class="inv-search" role="search" onsubmit="return false">\n'
    h += '<label for="inv-q" class="sr-only" style="position:absolute;left:-9999px">Search videos</label>\n'
    h += '<input type="search" id="inv-q" placeholder="Search by title, channel or topic, e.g. “flying lead change”" autocomplete="off">\n'
    h += '<label for="inv-g" class="sr-only" style="position:absolute;left:-9999px">Group</label>\n<select id="inv-g"><option value="">All groups</option>'
    for i, (name, _, _) in enumerate(groups):
        h += f'<option value="{i}">{E(name)}</option>'
    h += '</select>\n</form>\n<div class="inv-status" id="inv-status" role="status" aria-live="polite"></div>\n'
    h += '<div class="inv-results" id="inv-results"><div class="vp-grid wide" id="inv-grid"></div><button type="button" class="inv-more" id="inv-more" style="display:none">Show more</button></div>\n'
    h += '<div id="inv-browse"><h2 class="vp-h2" style="margin-top:.5rem">Browse by group</h2>\n<div class="inv-groups">\n'
    for i, (name, blurb, cs) in enumerate(groups):
        n = sum(len(by_cat[c]) for c in cs)
        h += f'<div class="inv-group"><h3>{E(name)}</h3><div class="n">{n} videos · {len(cs)} topics</div><p>{E(blurb)}</p>\n<ul class="inv-topics">'
        for c in sorted(cs, key=lambda c: (-len(by_cat[c]), c)):
            h += f'<li><a href="/videos/library/{c}/">{E(cat_name(c))} <b>{len(by_cat[c])}</b></a></li>'
        h += f'</ul>\n<button type="button" data-group="{i}">Search this group</button></div>\n'
    h += '</div>\n<p style="margin-top:1.5rem;"><a href="/videos/library/">Prefer a plain list? Open the full library by topic →</a></p></div>\n'
    h += '<noscript><p>Search needs JavaScript. <a href="/videos/library/">Browse the library by topic</a> instead.</p></noscript>\n'
    h += '</div></section>\n' + foot + '<script>' + INV_JS + '</script>\n</body></html>\n'
    cats_map = {c: cat_name(c) for c in known}
    gdata = [{'name': name, 'cats': cs} for name, _, cs in groups]
    rows = [[v['slug'], v['title'], v['channel'] or '', v['cat'], v['id']] for v in vids]
    data = {'cats': cats_map, 'groups': gdata, 'videos': rows}
    return h, json.dumps(data, ensure_ascii=False, separators=(',', ':'))

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)

def main():
    vids = load()
    assign_slugs(vids)
    by_cat = collections.defaultdict(list)
    for v in vids: by_cat[v['cat']].append(v)
    nav, foot = shell()
    for d in ('videos/watch', 'videos/library'):
        if os.path.isdir(d): shutil.rmtree(d)
    for v in vids:
        write(f'videos/watch/{v["slug"]}/index.html', video_page(v, nav, foot, by_cat, {x['id']: x for x in vids}))
    write('videos/library/index.html', library_index(by_cat, len(vids), nav, foot))
    for c, vs in by_cat.items():
        write(f'videos/library/{c}/index.html', category_page(c, vs, nav, foot))
    page, data = inventory_page(vids, by_cat, nav, foot)
    write('videos/inventory/index.html', page)
    write('videos/inventory/data.json', data)
    print(f'{len(vids)} video pages, {len(by_cat)} category pages, inventory page + data.json')
    print('with channel:', sum(1 for v in vids if v['channel']), '| no qa page:', sum(1 for v in vids if not any(p["path"].startswith("qa/") for p in v["pages_info"])))

if __name__ == '__main__':
    main()
