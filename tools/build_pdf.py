"""Build Yoav_Dabas_Portfolio.pdf from index.html.

Generates a print layout (A4 landscape) from the site's own content, then
renders it with Chromium via Playwright:  python3 tools/build_pdf.py
Requires: beautifulsoup4, playwright (Chromium).
"""
import html, os, subprocess, sys, urllib.parse
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_PER_PAGE = 6
# Lead image for a project's intro page (default: first image of its last stage)
KEY = {
    'Fertile City': 'thumbs/FertileCity_FertileCity1.webp',
    'MyBriX': 'thumbs/Mybrix_wall8.webp',
    'Hareshet 17': 'thumbs/Hareshet17_ViewFromStreet.webp',
}
CACHE = os.path.join(os.environ.get('SCRATCH', '/tmp'), 'pdf_jpg')
os.makedirs(CACHE, exist_ok=True)

def jpg(src, size=1400):
    # Chromium embeds JPEG as-is but inflates WebP/PNG, so hand it JPEGs
    from PIL import Image
    path = os.path.join(ROOT, urllib.parse.unquote(src))
    out = os.path.join(CACHE, os.path.basename(path).rsplit('.', 1)[0] + f'_{size}.jpg')
    if not os.path.exists(out):
        im = Image.open(path)
        if im.mode in ('RGBA', 'LA', 'P'):
            im = im.convert('RGBA'); bg = Image.new('RGB', im.size, 'white'); bg.paste(im, mask=im.getchannel('A')); im = bg
        im = im.convert('RGB'); im.thumbnail((size, size))
        im.save(out, quality=78, optimize=True, progressive=True)
    return 'file://' + urllib.parse.quote(out)

soup = BeautifulSoup(open(os.path.join(ROOT, 'index.html'), encoding='utf-8'), 'html.parser')
e = html.escape

def items_of(gallery):
    out = []
    for a in gallery.select('a.gallery-item'):
        img = a.find('img')
        if not img or img['src'].lower().endswith('.gif'):
            continue  # videos and GIF animations don't print
        cap = a.select_one('.caption')
        out.append((img['src'], cap.get_text(strip=True) if cap else ''))
    return out

pages = []

# Cover
lede = soup.select_one('.hero-lede').get_text(' ', strip=True)
pages.append(f'''<section class="page cover">
  <img class="cover-img" src="{jpg("thumbs/hero.webp", 2000)}">
  <div class="cover-text">
    <p class="eyebrow">Yoav Dabas — Architect &amp; Researcher</p>
    <h1>Architecture of Things</h1>
    <p class="lede">{e(lede)}</p>
    <p class="meta">Portfolio · dabasy8.github.io/portfolio · dabasy8@gmail.com</p>
  </div>
</section>''')

# About + contents + awards
about = ''.join(f'<p>{e(p.get_text(" ", strip=True))}</p>' for p in soup.select('#about p'))
groups = ''
for g in soup.select('.project-index .index-group'):
    label = g.select_one('.index-label').get_text(strip=True)
    names = ''.join(f'<li>{e(a.get_text(strip=True))}</li>' for a in g.select('a'))
    groups += f'<div class="toc-group"><h4>{e(label)}</h4><ul>{names}</ul></div>'
awards = ''.join(f'<li>{e(li.get_text(" ", strip=True))}</li>' for li in soup.select('#awards .awards-block')[0].select('li'))
pages.append(f'''<section class="page about">
  <div class="col"><h2>About</h2>{about}<h2>Awards</h2><ul class="awards">{awards}</ul></div>
  <div class="col"><h2>Contents</h2>{groups}</div>
</section>''')

# Projects
for divider in soup.select('section.category-divider'):
    category = divider.h3.get_text(strip=True)
    container = divider.find_next_sibling('div', class_='work-container')
    for art in container.select('article.project-block'):
        info = art.select_one('.project-info')
        title = info.h3.get_text(strip=True)
        tag = info.select_one('.tag').get_text(' ', strip=True)
        credits = info.select_one('.credits')
        desc = info.select_one('.desc')
        desc_txt = ''
        if desc:
            for a in desc.find_all('a'):
                a.decompose()
            for br in desc.find_all('br'):
                br.decompose()
            desc_txt = desc.get_text(' ', strip=True).rstrip(' ·')
        stages = art.select('.stage')
        all_items = [it for s in stages for g in s.select('.gallery') for it in items_of(g)]
        # Key image: prefer the last stage (finals/renders), first image
        key = next((items_of(g)[0] for s in reversed(stages) for g in s.select('.gallery') if items_of(g)), None)
        if title in KEY:
            key = (KEY[title], '')
        pages.append(f'''<section class="page intro">
  <div class="intro-text">
    <p class="eyebrow">{e(category)}</p>
    <h2 class="title">{e(title)}</h2>
    <p class="tag">{e(tag)}</p>
    {f'<p class="credits">{e(credits.get_text(" ", strip=True))}</p>' if credits else ''}
    <p class="desc">{e(desc_txt)}</p>
  </div>
  <div class="intro-img">{f'<img src="{jpg(key[0])}">' if key else ''}</div>
</section>''')
        for s in stages:
            h4 = s.find('h4'); sd = s.select_one('.stage-desc')
            for g in s.select('.gallery'):
                its = items_of(g)
                if not its:
                    continue
                compact = 'compact' in g.get('class', [])
                chunk = its if compact else its[:MAX_PER_PAGE]
                n = len(chunk)
                cls = 'compact' if compact else f'n{min(n, 6)}'
                cells = ''.join(f'<figure><div class="frame"><img src="{jpg(src, 500 if compact else 1100)}"></div>{f"<figcaption>{e(c)}</figcaption>" if c and not compact else ""}</figure>' for src, c in chunk)
                head = f'<h3>{e(title)}{" — " + e(h4.get_text(strip=True)) if h4 else ""}</h3>'
                pages.append(f'''<section class="page stage">
  <header>{head}{f'<p>{e(sd.get_text(" ", strip=True))}</p>' if sd else ''}</header>
  <div class="grid {cls}">{cells}</div>
</section>''')

# Contact
links = ' · '.join(e(a.get_text(strip=True)) + ': ' + e(a['href'].replace('https://', '')) for a in soup.select('#contact .links a'))
pages.append(f'''<section class="page contact">
  <h2 class="title">Yoav Dabas</h2>
  <p>dabasy8@gmail.com</p><p>{links}</p>
  <p>Full portfolio online: dabasy8.github.io/portfolio</p>
</section>''')

css = '''
@page { size: 297mm 210mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: #1a1a1a; }
.page { width: 297mm; height: 210mm; padding: 14mm 16mm; position: relative; overflow: hidden; page-break-after: always; }
.eyebrow { text-transform: uppercase; letter-spacing: .14em; font-size: 8.5pt; color: #6b6b6b; margin: 0 0 4mm; }
.cover { padding: 0; background: #111; color: #fff; }
.cover-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 30% center; filter: grayscale(.45) brightness(.6) contrast(1.05); }
.cover-text { position: absolute; left: 16mm; right: 16mm; bottom: 16mm; }
.cover .eyebrow { color: rgba(255,255,255,.85); }
.cover h1 { font-size: 64pt; line-height: .95; letter-spacing: -.035em; margin: 0 0 8mm; font-weight: 600; }
.cover .lede { font-size: 13pt; max-width: 150mm; border-top: 1px solid rgba(255,255,255,.4); padding-top: 5mm; margin: 0 0 6mm; }
.cover .meta { font-size: 8.5pt; opacity: .75; margin: 0; }
.about { display: grid; grid-template-columns: 1.3fr 1fr; gap: 16mm; }
.about h2 { font-size: 9pt; text-transform: uppercase; letter-spacing: .1em; color: #6b6b6b; margin: 0 0 4mm; }
.about h2 + p, .about p { font-size: 10.5pt; line-height: 1.5; color: #333; margin: 0 0 3mm; }
.about .awards { list-style: none; padding: 0; margin: 8mm 0 0; font-size: 9pt; color: #444; }
.about .col > h2:nth-of-type(2) { margin-top: 10mm; }
.awards li { padding: 2mm 0; border-top: 1px solid #e5e5e5; }
.toc-group { margin-bottom: 6mm; }
.toc-group h4 { font-size: 8pt; text-transform: uppercase; letter-spacing: .08em; color: #6b6b6b; margin: 0 0 2mm; font-weight: 600; }
.toc-group ul { list-style: none; padding: 0; margin: 0; font-size: 12pt; line-height: 1.6; }
.intro { display: grid; grid-template-columns: 95mm 1fr; gap: 12mm; align-items: center; }
.title { font-size: 26pt; letter-spacing: -.02em; margin: 0 0 2mm; font-weight: 600; }
.intro .tag { font-size: 9.5pt; color: #6b6b6b; margin: 0 0 6mm; }
.intro .credits { font-size: 9pt; border-left: 2px solid #1a1a1a; padding-left: 3mm; margin: 0 0 6mm; }
.intro .desc { font-size: 10pt; line-height: 1.55; color: #444; margin: 0; }
.intro-img { height: 182mm; display: flex; align-items: center; justify-content: center; }
.intro-img img { max-width: 100%; max-height: 100%; object-fit: contain; }
.stage { display: flex; flex-direction: column; }
.stage header { margin-bottom: 6mm; }
.stage h3 { font-size: 11pt; margin: 0 0 1.5mm; font-weight: 600; }
.stage header p { font-size: 9pt; color: #6b6b6b; margin: 0; max-width: 170mm; line-height: 1.45; }
.grid { flex: 1; display: grid; gap: 6mm; min-height: 0; }
.grid { align-content: center; }
.grid.n1 { grid-template-columns: 1fr; --fh: 140mm; }
.grid.n2 { grid-template-columns: 1fr 1fr; --fh: 120mm; }
.grid.n3 { grid-template-columns: repeat(3, 1fr); --fh: 110mm; }
.grid.n4 { grid-template-columns: 1fr 1fr; --fh: 62mm; }
.grid.n5, .grid.n6 { grid-template-columns: repeat(3, 1fr); --fh: 62mm; }
.grid.compact { grid-template-columns: repeat(7, 1fr); gap: 3mm; --fh: 34mm; }
figure { margin: 0; display: flex; flex-direction: column; min-height: 0; }
.frame { height: var(--fh, 60mm); display: flex; align-items: flex-end; justify-content: center; }
.frame img { max-width: 100%; max-height: 100%; object-fit: contain; }
figcaption { font-size: 7.5pt; color: #6b6b6b; text-align: center; margin-top: 2mm; }
.contact { display: flex; flex-direction: column; justify-content: center; }
.contact p { font-size: 11pt; color: #444; margin: 0 0 2mm; }
'''
doc = f'<!doctype html><html><head><meta charset="utf-8"><title>Yoav Dabas — Portfolio</title><style>{css}</style></head><body>{"".join(pages)}</body></html>'
out_html = os.path.join(ROOT, '_print.html')
open(out_html, 'w', encoding='utf-8').write(doc)

js = f'''
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch({{ executablePath: process.env.CHROME || undefined }});
  const p = await b.newPage();
  await p.goto('file://{out_html}');
  await p.waitForFunction(() => [...document.images].every(i => i.complete));
  await p.pdf({{ path: '{os.path.join(ROOT, "Yoav_Dabas_Portfolio.pdf")}', width: '297mm', height: '210mm', printBackground: true }});
  await b.close();
}})();
'''
runner = os.path.join(os.environ.get('SCRATCH', '/tmp'), 'render_pdf.cjs')
open(runner, 'w').write(js)
subprocess.run(['node', runner], check=True, cwd=os.environ.get('NODE_DIR', ROOT))
os.remove(out_html)
print('pages:', len(pages))
