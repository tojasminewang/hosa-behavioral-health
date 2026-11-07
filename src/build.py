#!/usr/bin/env python3
"""Build the HOSA Behavioral Health study site.

  python3 build.py           check everything, then write ../index.html
  python3 build.py --check   only check the questions against the notes

Inputs (all in this folder):
  notes/<topic>.md        study notes (custom markdown, see parse_notes)
  questions/<topic>.txt   practice questions (see parse_questions)
  template.html           page shell with {{ARTICLES}} and {{DATA}} slots
"""
import html
import json
import pathlib
import re
import sys
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
NOTES, QDIR, TEMPLATE, OUT = HERE / 'notes', HERE / 'questions', HERE / 'template.html', HERE.parent / 'index.html'

PARTS = [
    dict(n=1, weight=25, short='The Mind', title='The Mind',
         events=['biological', 'sensation', 'perception', 'consciousness', 'motivation', 'emotion', 'learning', 'memory']),
    dict(n=2, weight=25, short='Disorders & Treatments',
         title='Psychology and Behavioral Health Disorders, Treatments, Therapies & Services',
         events=['disorders-basics', 'autism', 'adhd', 'schizophrenia', 'bipolar', 'depression', 'anxiety', 'ocd', 'ptsd',
                 'personality', 'dissociative', 'eating', 'therapies', 'services']),
    dict(n=3, weight=25, short='Prevention & Recovery',
         title='Prevention, Identification, Recovery, and Management of Substance Abuse and Mental Illness',
         events=['substances', 'prevention', 'identification', 'treatment-sud', 'recovery']),
    dict(n=4, weight=15, short='Wellness, Stress & Coping', title='Wellness, Stress, Coping',
         events=['stress', 'coping', 'wellness', 'trauma']),
    dict(n=5, weight=5, short='Careers & Laws', title='Workforce/Careers and Laws, Regulations and Guidelines',
         events=['careers', 'laws']),
    dict(n=6, weight=5, short='History & Integration', title='History and Health Systems Integration',
         events=['history', 'integration']),
]
TITLES = {
    'biological': 'Biological Psychology', 'sensation': 'Sensation', 'perception': 'Perception',
    'consciousness': 'Consciousness & Sleep', 'motivation': 'Motivation', 'emotion': 'Emotion', 'learning': 'Learning',
    'memory': 'Memory', 'disorders-basics': 'Understanding Mental Disorders', 'autism': 'Autism Spectrum Disorder',
    'adhd': 'ADHD', 'schizophrenia': 'Schizophrenia', 'bipolar': 'Bipolar Disorder', 'depression': 'Depression',
    'anxiety': 'Anxiety Disorders', 'ocd': 'OCD & Related Disorders', 'ptsd': 'PTSD',
    'personality': 'Personality Disorders', 'dissociative': 'Dissociative Disorders', 'eating': 'Eating Disorders',
    'therapies': 'Therapies & Treatments', 'services': 'Services, Care & Helplines',
    'substances': 'Substance Use & Addiction', 'prevention': 'Prevention', 'identification': 'Identification & Crisis Care',
    'treatment-sud': 'SUD Treatment & Overdose', 'recovery': 'Recovery', 'stress': 'Stress',
    'coping': 'Coping & Resilience', 'wellness': 'Wellness & Health Psychology', 'trauma': 'Trauma & Disaster Mental Health',
    'careers': 'Careers & Workforce', 'laws': 'Laws, Regulations & Guidelines',
    'history': 'History of Psychology & SAMHSA', 'integration': 'Health Systems Integration',
}
ORDER = [s for p in PARTS for s in p['events']]
PART_OF = {s: p['n'] for p in PARTS for s in p['events']}


def norm(s):
    """Same as the page's norm(): lowercase, accents folded, letters and digits only."""
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', str(s).lower()))


def slugify(s):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', norm_keep(s))).strip('-')


def norm_keep(s):
    return unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()


# ---------- notes ----------
LINK = re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)')
BOLD = re.compile(r'\*\*(.+?)\*\*')
PAGES = re.compile(r'\s*\{(pp?\.[^}]*)\}\s*$')


def inline(s):
    """Markdown-ish inline text -> (html, plain text)."""
    out, plain, pos = [], [], 0
    for m in LINK.finditer(s):
        out.append(fmt(s[pos:m.start()])); plain.append(strip(s[pos:m.start()]))
        out.append(f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">{fmt(m.group(1))}</a>')
        plain.append(strip(m.group(1)))
        pos = m.end()
    out.append(fmt(s[pos:])); plain.append(strip(s[pos:]))
    return ''.join(out), ''.join(plain)


def fmt(s):
    return BOLD.sub(lambda m: f'<b>{m.group(1)}</b>', html.escape(s, quote=False))


def strip(s):
    return BOLD.sub(lambda m: m.group(1), s)


class Block:
    """One searchable element of the notes (li, p, tr, h2, h3), mirroring what the page searches."""
    def __init__(self, kind, own, full=None, heading=''):
        self.kind, self.own, self.full, self.heading = kind, own, full if full is not None else own, heading


def parse_notes(slug, text):
    """Returns (html, blocks, cards).

    Format: '@ text' = source line; '## Heading {pp. 1–2}' = section with textbook pages; '### Sub';
    '- item' / '  - sub-item' = bullets ('- **Term:** definition' also becomes a flashcard);
    '| a | b |' rows = table (first row = header, second = ---); anything else = paragraph.
    """
    lines = text.rstrip('\n').split('\n')
    out, blocks, cards = [], [], []
    heading = ''
    i = 0
    used_ids = set()

    def hid(t):
        base = f'{slug}--{slugify(t)}' or slug
        k, n = base, 2
        while k in used_ids:
            k, n = f'{base}-{n}', n + 1
        used_ids.add(k)
        return k

    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith('@ '):
            h_, p_ = inline(ln[2:].strip())
            out.append(f'<p class="srcline"><span class="k">Source</span> {h_}</p>')
            blocks.append(Block('p', 'Source ' + p_, heading=heading))
            i += 1
        elif ln.startswith('## ') or ln.startswith('### '):
            level = 2 if ln.startswith('## ') else 3
            t = ln[level + 1:].strip()
            m = PAGES.search(t)
            pg = m.group(1) if m else None
            if m:
                t = t[:m.start()].rstrip()
            h_, p_ = inline(t)
            chip = f' <span class="pg" title="Textbook pages">{html.escape(pg)}</span>' if pg else ''
            out.append(f'<h{level} id="{hid(p_)}">{h_}{chip}</h{level}>')
            blocks.append(Block(f'h{level}', p_ + (' ' + pg if pg else ''), heading=heading))
            if level == 2:
                heading = p_
            i += 1
        elif ln.lstrip().startswith('- '):
            items = []          # (depth, text)
            while i < len(lines) and lines[i].lstrip().startswith('- '):
                raw = lines[i]
                depth = (len(raw) - len(raw.lstrip(' '))) // 2
                items.append((depth, raw.lstrip()[2:].strip()))
                i += 1
            out.append(render_list(items, heading, blocks, cards, slug))
        elif ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            if len(rows) > 1 and all(re.fullmatch(r':?-{2,}:?', c) for c in rows[1]):
                head, body = rows[0], rows[2:]
            else:
                head, body = None, rows
            out.append(render_table(head, body, heading, blocks, cards, slug))
        else:
            h_, p_ = inline(ln.strip())
            out.append(f'<p>{h_}</p>')
            blocks.append(Block('p', p_, heading=heading))
            i += 1
    return '\n'.join(out), blocks, cards


def render_list(items, heading, blocks, cards, slug):
    # build a tree
    root = []
    stack = [(-1, root)]
    for depth, t in items:
        node = {'t': t, 'kids': []}
        while stack[-1][0] >= depth:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((depth, node['kids']))

    def plain_of(node):
        return inline(node['t'])[1] + ''.join(plain_of(k) for k in node['kids'])

    def emit(nodes):
        parts = ['<ul>']
        for nd in nodes:
            h_, p_ = inline(nd['t'])
            sub = emit(nd['kids']) if nd['kids'] else ''
            parts.append(f'<li>{h_}{sub}</li>')
            blocks.append(Block('li', p_, plain_of(nd), heading))
            m = re.match(r'\*\*(.+?):\*\*\s*(.+)$', nd['t'])
            if m:
                back = f'<p>{inline(m.group(2))[0]}</p>' + sub
                cards.append({'event': slug, 'ctx': heading, 'front': strip(m.group(1)), 'back': back, 'src': p_[:90]})
        parts.append('</ul>')
        return ''.join(parts)

    return emit(root)


def render_table(head, body, heading, blocks, cards, slug):
    parts = ['<div class="tbl"><table>']
    if head:
        parts.append('<thead><tr>' + ''.join(f'<th>{inline(c)[0]}</th>' for c in head) + '</tr></thead>')
    parts.append('<tbody>')
    for row in body:
        cells = [inline(c) for c in row]
        parts.append('<tr>' + ''.join(f'<td>{h_}</td>' for h_, _ in cells) + '</tr>')
        own = ' — '.join(p_ for _, p_ in cells)
        blocks.append(Block('tr', own, ''.join(p_ for _, p_ in cells), heading))
        if head and len(cells) >= 2 and cells[0][1]:
            back = ''.join(f'<p><b>{inline(head[k])[0] if k < len(head) else ""}:</b> {cells[k][0]}</p>'
                           for k in range(1, len(cells)) if cells[k][1])
            cards.append({'event': slug, 'ctx': heading, 'front': cells[0][1], 'back': back,
                          'src': ' '.join(p_ for _, p_ in cells)[:90]})
    parts.append('</tbody></table></div>')
    return ''.join(parts)


# ---------- questions ----------
def parse_questions(slug, text, path):
    """Blocks separated by blank lines: '? question', '+ correct', '- wrong' x3, '@ text from the notes',
    optional '! explanation' and '~ group'. A line '## hard' marks every later question as hard."""
    qs, level, cur, errs = [], 'normal', None, []

    def close():
        nonlocal cur
        if cur:
            qs.append(cur)
        cur = None

    for no, ln in enumerate(text.split('\n'), 1):
        s = ln.rstrip()
        if not s.strip():
            close()
            continue
        if s.strip().lower() == '## hard':
            close()
            level = 'hard'
            continue
        tag, _, val = s.partition(' ')
        val = val.strip()
        if tag == '?':
            close()
            cur = {'q': val, 'right': None, 'wrong': [], 'src': None, 'explain': '', 'grp': None, 'level': level, 'line': no}
        elif cur is None:
            errs.append(f'{path.name}:{no}: text outside a question: {s[:60]}')
        elif tag == '+':
            cur['right'] = val
        elif tag == '-':
            cur['wrong'].append(val)
        elif tag == '@':
            cur['src'] = val
        elif tag == '!':
            cur['explain'] = (cur['explain'] + ' ' + val).strip()
        elif tag == '~':
            cur['grp'] = val
        else:
            errs.append(f'{path.name}:{no}: unknown line: {s[:60]}')
    close()
    return qs, errs


def find_block(blocks, src):
    want = norm(src)
    best, best_len = None, 10 ** 9
    for k, b in enumerate(blocks):
        t = norm(b.full)
        if want and want in t and len(t) < best_len:
            best, best_len = k, len(t)
    return best


PREFIX = {}


def build_data(check_only=False):
    problems, articles, all_q, all_cards, counts = [], [], [], [], {}
    for slug in ORDER:
        md = (NOTES / f'{slug}.md').read_text(encoding='utf-8')
        body, blocks, cards = parse_notes(slug, md)
        qpath = QDIR / f'{slug}.txt'
        qs, errs = parse_questions(slug, qpath.read_text(encoding='utf-8'), qpath) if qpath.exists() else ([], [])
        problems += errs
        n_norm = n_hard = 0
        seen_q = set()
        for q in qs:
            where = f'{qpath.name}:{q["line"]}'
            if not q['q'] or not q['right'] or len(q['wrong']) != 3 or not q['src']:
                problems.append(f'{where}: needs a question, 1 right answer, 3 wrong answers, and @ source '
                                f'(has {len(q["wrong"])} wrong)')
                continue
            choices = [q['right']] + q['wrong']
            if len({norm(c) for c in choices}) != 4:
                problems.append(f'{where}: duplicate answer choices')
            if norm(q['q']) in seen_q:
                problems.append(f'{where}: repeated question')
            seen_q.add(norm(q['q']))
            k = find_block(blocks, q['src'])
            if k is None:
                problems.append(f'{where}: source not found in notes/{slug}.md: "{q["src"]}"')
                continue
            if q['level'] == 'hard':
                n_hard += 1
                qid = f'{slug}-h{n_hard}'
            else:
                n_norm += 1
                qid = f'{slug}-{n_norm}'
            item = {'id': qid, 'event': slug, 'type': 'mc', 'q': q['q'], 'choices': choices,
                    'explain': q['explain'], 'src': q['src'], 'line': blocks[k].own,
                    'grp': f'{slug}:{q["grp"]}' if q['grp'] else f'{slug}:b{k}'}
            if q['level'] == 'hard':
                item['level'] = 'hard'
            all_q.append(item)
        counts[slug] = (n_norm, n_hard, len(cards))
        for c in cards:
            if find_block(blocks, c['src']) is None:
                problems.append(f'card source not found in {slug}: {c["src"]}')
        all_cards += cards
        articles.append((slug, body))
    return problems, articles, all_q, all_cards, counts


def article_html(slug, body, counts):
    p = next(x for x in PARTS if slug in x['events'])
    i = ORDER.index(slug)
    n, nh, nc = counts[slug]
    prev = ORDER[i - 1] if i else None
    nxt = ORDER[i + 1] if i + 1 < len(ORDER) else None
    esc = html.escape
    meta = f'<span>{n} questions</span>'
    if nh:
        meta += f'<span class="dot">•</span><span>{nh} hard</span>'
    meta += f'<span class="dot">•</span><span>{nc} flashcards</span>'
    nav = ''
    if prev:
        nav += (f'<a class="prev" href="#notes-{prev}" data-act="notes" data-arg="{prev}"><span class="lbl">← Previous</span>'
                f'<span>{esc(TITLES[prev])}</span></a>')
    if nxt:
        nav += (f'<a class="next" href="#notes-{nxt}" data-act="notes" data-arg="{nxt}"><span class="lbl">Next →</span>'
                f'<span>{esc(TITLES[nxt])}</span></a>')
    hard_btn = (f'<button class="btn" type="button" data-act="quiz-ev-hard" data-arg="{slug}"><svg class="ic" aria-hidden="true">'
                f'<use href="#i-flame"/></svg>Hard quiz</button>\n') if nh else ''
    return f'''<article class="event pc-{p["n"]}" id="ev-{slug}" aria-labelledby="h-{slug}" hidden>
<header class="event-head">
<p class="crumb"><span class="chip">Part {p["n"]} · {p["weight"]}%</span><span>{esc(p["title"])}</span></p>
<h1 class="page-title" id="h-{slug}">{esc(TITLES[slug])}</h1>
<p class="event-meta">{meta}</p>
<div class="head-row">
<button class="btn primary" type="button" data-act="quiz-ev" data-arg="{slug}"><svg class="ic" aria-hidden="true"><use href="#i-quiz"/></svg>Quiz this topic</button>
{hard_btn}<button class="btn" type="button" data-act="review-ev" data-arg="{slug}" data-review="{slug}" hidden><svg class="ic" aria-hidden="true"><use href="#i-redo"/></svg>Redo wrong answers<span class="count"></span></button>
<button class="btn" type="button" data-act="cards" data-arg="{slug}"><svg class="ic" aria-hidden="true"><use href="#i-cards"/></svg>Flashcards</button>
<span class="head-prog"><span class="meter" data-meter="{slug}" role="img"><i></i></span><span class="pct" data-pct="{slug}"></span></span>
</div>
<div class="qactions head-tools"><p class="hl-hint"><svg class="ic" aria-hidden="true"><use href="#i-marker"/></svg>Select any text in the notes to highlight it or add a note.</p><span class="ev-note" data-evnote="{slug}"></span></div>
</header>
<div class="card doc"><div class="prose">
{body}
</div></div>
<nav class="ev-nav" aria-label="Previous and next topic">{nav}</nav>
</article>'''


def main():
    check_only = '--check' in sys.argv
    problems, articles, qs, cards, counts = build_data(check_only)
    tot_n = sum(c[0] for c in counts.values())
    tot_h = sum(c[1] for c in counts.values())
    for slug in ORDER:
        n, nh, nc = counts[slug]
        print(f'  {slug:18} {n:3} normal {nh:3} hard {nc:4} cards')
    print(f'TOTAL {tot_n} normal + {tot_h} hard = {tot_n + tot_h} questions, {len(cards)} flashcards')
    if problems:
        print(f'\n{len(problems)} problem(s):')
        for p in problems:
            print('  -', p)
    if check_only:
        sys.exit(1 if problems else 0)
    if problems:
        sys.exit('Not building until the problems above are fixed.')
    data = {
        'parts': [{k: p[k] for k in ('n', 'title', 'short', 'weight', 'events')} for p in PARTS],
        'events': {s: {'title': TITLES[s], 'part': PART_OF[s]} for s in ORDER},
        'questions': qs, 'cards': cards,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    page = TEMPLATE.read_text(encoding='utf-8')
    page = page.replace('{{ARTICLES}}', '\n'.join(article_html(s, b, counts) for s, b in articles))
    page = page.replace('{{DATA}}', blob)
    OUT.write_text(page, encoding='utf-8')
    print(f'wrote {OUT} ({OUT.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
