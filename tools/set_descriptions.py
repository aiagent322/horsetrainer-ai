#!/usr/bin/env python3
"""Hand-written meta descriptions (120-160 chars) built only from each page's own facts. Applies to meta + og:description. Run from repo root."""
import re, html, glob, itertools, json
M = {
'famous-trainers/bill-dorrance.html': 'Biography of Bill Dorrance (1906–1999), rancher and horseman whose philosophy of feel, timing and softness helped shape modern natural horsemanship.',
'famous-trainers/bobby-ingersoll.html': 'Biography of Bobby Ingersoll, co-founder of the NRCHA Snaffle Bit Futurity (1970) and the only rider to achieve its Triple Crown in 1975.',
'famous-trainers/buck-brannaman.html': 'Biography of Buck Brannaman, natural horsemanship clinician and author, an inspiration for The Horse Whisperer and subject of the 2011 documentary Buck.',
'famous-trainers/corey-cushing.html': "Biography of Corey Cushing, NRCHA's first Four Million Dollar Rider, four-time Snaffle Bit Futurity Open Champion and three-time World's Greatest Horseman.",
'famous-trainers/isabell-werth.html': 'Biography of Isabell Werth (b. 1969), German dressage rider and the most decorated equestrian in Olympic history, with team gold at all seven Games.',
'famous-trainers/lloyd-cox.html': 'Biography of Lloyd Cox, 2010 NCHA Futurity Open Champion (score 230 on One Time Royalty), NCHA Hall of Fame 2000 and Oklahoma cutting horse trainer.',
'famous-trainers/todd-bergen.html': 'Biography of Todd Bergen, two-time NRHA Futurity Open Champion and NRCHA Snaffle Bit Futurity Champion, first $2 Million Rider in both NRHA and NRCHA.',
'famous-trainers/tommy-garland.html': 'Biography of Tommy Garland, Arabian horse trainer, national western pleasure champion and USEF Equestrian of Honor based in Bristol, Tennessee.',
'famous-trainers/warwick-schiller.html': 'Biography of Warwick Schiller, NRHA Reserve World Champion, 2010 and 2018 World Equestrian Games rider (Team Australia), author and clinician.',
'famous-trainers/xenophon.html': 'Biography of Xenophon (c. 430–354 BC), ancient Greek soldier, historian and father of classical horsemanship, author of On Horsemanship.',
'famous-trainers/alois-podhajsky.html': 'Biography of Alois Podhajsky (1898–1973), Austrian cavalry colonel, 1936 Olympic dressage bronze medalist and director of the Spanish Riding School of Vienna.',
'barrel-racing/barrel-horse-fitness-program/index.html': 'A structured barrel horse fitness and conditioning program: long slow distance work, arena fitness, sparing speed work, rest days and monitoring fitness.',
'barrel-racing/pattern-fundamentals/index.html': 'The fundamentals of the barrel racing cloverleaf pattern: pocket position, the turn, rate and departure, plus walking the pattern and when to add speed.',
'barrel-racing/speed-control-and-rate/index.html': 'How to teach a barrel horse to rate: collect and prepare for the turn before reaching the barrel, with exercises for building rate and common problems.',
'barrel-racing/starting-a-young-barrel-horse/index.html': 'How to start a young barrel horse the right way: age and timing, the foundation needed before barrels, the pattern introduction sequence and anticipation.',
'colt-starting/developing-the-stop/index.html': 'How to develop a correct, reliable stop in a young horse. Seat cue first, voice second, rein last, from walk to trot, plus common mistakes to avoid.',
'colt-starting/first-60-days-under-saddle/index.html': "A week-by-week training plan for a horse's first 60 days under saddle: first rides and steering, gaits, the lope, and what done looks like at day 60.",
'colt-starting/first-ride-preparation/index.html': "The groundwork checklist before a colt's first ride: what the horse must know, how to check readiness, the day of the first ride and what success looks like.",
'colt-starting/when-to-start-a-young-horse/index.html': 'When is a horse old enough to start under saddle? Growth plate timelines, breed differences, readiness indicators beyond age and the groundwork window.',
'find-a-trainer/reining-trainers/index.html': 'Find verified NRHA-affiliated reining trainers near you in the HorseTrainer.ai directory. Get scored matches by location, level and specialty.',
'groundwork/round-pen-fundamentals/index.html': 'Complete round pen fundamentals guide: join-up, directional control, gait transitions and reading horse body language, step by step.',
'groundwork/trailer-loading-step-by-step/index.html': 'A proven pressure-and-release trailer loading method that works even for severely resistant horses, with step-by-step approach and retreat work.',
'list-your-training/index.html': 'Get listed in the HorseTrainer.ai trainer directory. Receive leads matched to your discipline, location and level. Free, Basic, VIP and Featured tiers.',
'mustang/mustang-gentling-techniques/index.html': 'Proven techniques for gentling an untouched BLM mustang: systematic touch introduction, reading fear vs. acceptance, and moving from touch to halter.',
'problem-horse/horse-that-bites/index.html': 'Why horses bite, how to tell playful mouthy behavior from true biting aggression, and a clear, consistent approach to establishing bite-free boundaries.',
'problem-horse/rearing/index.html': 'Rearing is one of the most dangerous horse behaviors. Learn why horses rear, what NOT to do, and why it needs a professional problem horse specialist.',
'problem-horse/spooky-horse-desensitizing/index.html': 'Why horses spook and a proven systematic desensitization approach that builds genuine confidence, not just tolerance, using approach and retreat.',
'reining/reining-circles-large-and-small/index.html': 'How to ride reining circles correctly: the large/fast and small/slow distinction, what makes a circle correct, the transitions between them and common problems.',
'reining/spinning-fundamentals/index.html': 'How to teach the reining spin step by step: prerequisites, pivot foot, lateral footfall pattern, adding speed once footfall is correct, and common problems.',
'tack/how-to-fit-a-bridle/index.html': 'Step-by-step guide to fitting a horse bridle correctly: crownpiece, browband, cheekpieces, throatlatch and noseband, and why bridle fit is a welfare issue.',
'tack/index.html': 'Tack and equipment guides: how to fit a saddle and a bridle, western and English bit selection, and protective boots for horses, step by step.',
'tack/protective-boots-for-horses/index.html': 'Complete guide to horse leg boots: splint, bell, sport, skid and tendon boots and polo wraps, plus fit, application and heat management.',
'trail/building-a-bombproof-trail-horse/index.html': 'How to build a genuinely confident, safe trail horse through systematic desensitization, not flooding or force, from ground work to mounted practice.',
'trail/trail-obstacles-training/index.html': 'How to train a horse to navigate trail obstacles, including bridges, tarps, water and gates, with a progression and a home obstacle course to practice on.',
'tv/index.html': 'Horse Genius TV: a full-screen, remote-friendly way to browse and watch horse training videos on your TV or any large display.',
'qa/training-principles-psychology/index.html': 'Expert answers to 13 horse training questions about Training Principles & Psychology, plus related training videos from HorseTrainer.ai.',
}
bad=[(len(d),p) for p,d in M.items() if not 120<=len(d)<=160]
if bad: raise SystemExit(f'length out of range: {bad}')
for p in glob.glob('qa/*/index.html'):
    s = open(p, encoding='utf-8').read(); m = re.search(r'name="description" content="([^"]*)"', s)
    cur = html.unescape(m.group(1)) if m else ''
    if 120 <= len(cur) <= 160 or p in M: continue
    mm = re.fullmatch(r'Expert answers to (\d+) horse training questions about (.*?)\. Learn from professional trainers\.', cur)
    if not mm: print('skip', p, len(cur)); continue
    qs = sorted({html.unescape(x).strip() for x in re.findall(r'<h2><a href="[^"]+">(.*?)</a></h2>', s)}, key=len)
    base = f'Expert answers to {mm.group(1)} horse training questions about {mm.group(2)}, including '
    best = None
    for k in (3, 2, 1):
        for c in itertools.combinations(qs[:12], k):
            q = ' and '.join(f'“{x}”' for x in c) if k < 3 else f'“{c[0]}”, “{c[1]}” and “{c[2]}”'
            d = base + q + '.'
            if 120 <= len(d) <= 160 and (best is None or len(d) > len(best)): best = d
        if best: break
    if best: M[p] = best
    else: print('no fit', p)
n = 0
for p, d in M.items():
    s = o = open(p, encoding='utf-8').read(); e = html.escape(d, quote=True)
    s = re.sub(r'(name="description"[^>]*content=")[^"]*(")', lambda m: m.group(1) + e + m.group(2), s, 1)
    s = re.sub(r'(property="og:description" content=")[^"]*(")', lambda m: m.group(1) + e + m.group(2), s, 1)
    s = re.sub(r'("@type": ?"(?:Article|WebPage|CollectionPage|AboutPage)".*?"description": ?)("(?:[^"\\]|\\.)*")', lambda m: m.group(1) + json.dumps(d, ensure_ascii=False), s, 1, flags=re.S) if '"description"' in s and 'application/ld+json' in s and '"@type": "FAQPage"' not in s and '"@type":"FAQPage"' not in s else s
    if s != o: open(p, 'w', encoding='utf-8').write(s); n += 1
print('updated', n, 'of', len(M))
