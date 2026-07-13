#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает статический журнальный сайт из meta.json + articles/*.md + pages/*.md."""
import json, os, re, html, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
if os.path.exists(SITE):
    shutil.rmtree(SITE)
os.makedirs(os.path.join(SITE, "a"))
os.makedirs(os.path.join(SITE, "assets"))
shutil.copy(os.path.join(HERE, "assets", "style.css"), os.path.join(SITE, "assets", "style.css"))

meta = json.load(open(os.path.join(HERE, "meta.json"), encoding="utf-8"))
esc = lambda s: html.escape(s, quote=True)

def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    return t

def read_article(m):
    p = os.path.join(HERE, "articles", f"{m['idx']+1:02d}-{m['id']}.md")
    raw = open(p, encoding="utf-8").read()
    wb = ""
    mm = re.search(r"Wayback Machine:\s*(\S+)", raw)
    if mm: wb = mm.group(1)
    lines = raw.split("\n")
    body = "\n".join(l for l in lines if not l.startswith("#") and not l.startswith(">"))
    paras = [re.sub(r"\s*\n\s*", " ", b).strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    return wb, paras

def base(title, inner, active, depth=0):
    up = "../" * depth
    def cls(t): return ' class="on"' if t == active else ""
    return f"""<!doctype html><html lang="ru"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="Архив колонки Виктора Меламеда об иллюстрации, журнал «Как)», kak.ru, 2006–2009.">
<link rel="stylesheet" href="{up}assets/style.css">
</head><body>
<div class="ribbon"><div class="wrap"><div><b>[кАк)</b> · колонка об иллюстрации</div><div class="r">Виктор Меламед · 2006–2009</div></div></div>
<nav class="tabs"><div class="wrap" style="display:flex">
<a href="{up}index.html"{cls('index')}>Выпуски</a>
<a href="{up}ideas.html"{cls('ideas')}>Идеи</a>
<a href="{up}illustrators.html"{cls('names')}>Имена</a>
</div></nav>
<main class="wrap">{inner}</main>
<footer class="pagefoot"><div class="wrap">
<div>Архив спасён из Wayback Machine. Оригинал kak.ru закрыт.</div>
<div>69 выпусков · октябрь 2006 — июль 2009</div>
</div></footer>
</body></html>"""

# ——— index ———
mast = f"""<header class="mast">
<div class="kicker"><b>Виктор Меламед</b> · практик и теоретик иллюстрации</div>
<h1>Колонка<br>об<br>иллюстрации</h1>
<p class="lede">Легендарная авторская колонка на сайте журнала «[кАк)» — три года еженедельных разборов ремесла, метода и имён. Сайт закрыт; тексты спасены из веб-архива и собраны здесь целиком.</p>
<div class="stats"><span><b>69</b> выпусков</span><span><b>2006–2009</b></span><span><b>~130</b> художников</span><span>kak.ru / illumination</span></div>
</header>"""

rows = []
cur_year = None
for i, m in enumerate(meta):
    year = m["date"].split(".")[-1]
    if year != cur_year:
        cur_year = year
        rows.append(f'<div class="sect-h">{year}</div>')
    sub = f'<span class="s">{esc(m["sub"])}</span>' if m["sub"] else ""
    dd = ".".join(m["date"].split(".")[:2])
    rows.append(
        f'<a class="row" href="a/{m["idx"]+1:02d}.html">'
        f'<span class="n">{m["idx"]+1:02d}</span>'
        f'<span class="d">{dd}.{year}</span>'
        f'<span class="t">{esc(m["title"])}{sub}</span></a>'
    )
index_inner = mast + '<section class="contents">' + "\n".join(rows) + "</section>"
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(base("Виктор Меламед · Колонка об иллюстрации", index_inner, "index"))

# ——— articles ———
n = len(meta)
for i, m in enumerate(meta):
    wb, paras = read_article(m)
    body = "\n".join(f"<p>{inline(p)}</p>" for p in paras)
    deck = f'<p class="deck">{esc(m["sub"])}</p>' if m["sub"] else ""
    yr = m["date"].split(".")[-1]
    prev_a = f'<a class="pv" href="{meta[i-1]["idx"]+1:02d}.html"><span class="lab">← Предыдущий</span>{esc(meta[i-1]["title"])}</a>' if i>0 else "<span></span>"
    next_a = f'<a class="nx" href="{meta[i+1]["idx"]+1:02d}.html"><span class="lab">Следующий →</span>{esc(meta[i+1]["title"])}</a>' if i<n-1 else "<span></span>"
    inner = f"""<article class="art">
<div class="head">
<div class="meta"><span class="no">Выпуск <b>{m['idx']+1:02d}</b> / {n}</span><span>{esc(m['date'])}</span></div>
<h1>{esc(m['title'])}</h1>{deck}
</div>
<div class="body">{body}</div>
<div class="foot">
<div class="src">Источник: <a href="{esc(wb)}" target="_blank" rel="noopener">оригинал в Wayback Machine ↗</a></div>
<div class="pager">{prev_a}{next_a}</div>
</div>
</article>"""
    open(os.path.join(SITE, "a", f"{m['idx']+1:02d}.html"), "w", encoding="utf-8").write(base(f"{m['date']} · {m['title']} — Меламед", inner, "index", depth=1))

# ——— prose pages ———
def render_prose(mdpath):
    out = []
    for block in re.split(r"\n\s*\n", open(mdpath, encoding="utf-8").read()):
        b = block.strip()
        if not b: continue
        if b.startswith("## "):
            out.append(f"<h2>{inline(b[3:].strip())}</h2>")
        elif b.startswith("# "):
            out.append(f"<h1>{esc(b[2:].strip())}</h1>")
        else:
            b = re.sub(r"\s*\n\s*", " ", b)
            out.append(f"<p>{inline(b)}</p>")
    return "<section class=\"prose\">" + "\n".join(out) + "</section>"

open(os.path.join(SITE, "ideas.html"), "w", encoding="utf-8").write(
    base("Ключевые идеи — Меламед", render_prose(os.path.join(HERE, "pages", "ideas.md")), "ideas"))
open(os.path.join(SITE, "illustrators.html"), "w", encoding="utf-8").write(
    base("Имена — Меламед", render_prose(os.path.join(HERE, "pages", "illustrators.md")), "names"))

print("built:", len(os.listdir(os.path.join(SITE, "a"))), "articles + index/ideas/illustrators")
