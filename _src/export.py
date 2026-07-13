#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тянет 69 статей колонки Меламеда из Wayback и пишет markdown-файлы."""
import json, re, os, sys, urllib.request, urllib.parse
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "articles")
os.makedirs(ART, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
DELIM = re.compile(r'^.*?\sОт\s+\d{1,2}\s+(январ|феврал|март|апрел|ма|июн|июл|август|сентябр|октябр|ноябр|декабр)\S*\s+\d{4}\s*$')

# хвостовой сайдбарный промо-мусор kak.ru — обрезаем с первого совпадения
PROMO = [
    "Open!Design", "Десятая доля несметной коллекции", "Подделка ещё", "Подделка еще",
    "Коллекция изделий, подвергнутых редизайну", "Клоны есть не только", "Даже при допущении",
    "Одноразовые порционные пакетики", "Самые «угоняемые»", "Работы, присланные на конкурс",
    "Дело о сбежавшем кенгуру", "Фотограф, путешественница", "VibroPower и X-Project",
    "Светлана Татарникова", "27 календарей", "Конкурс РАО", "Свежая обложка журнала",
    "Даешь тренд", "часть коллекции Екатерины",
]

def fetch(ts, aid):
    url = f"https://web.archive.org/web/{ts}id_/http://kak.ru/columns/illumination/{aid}/"
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=45).read().decode("windows-1251", "replace")

def sanitize(s):
    s = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '', s)
    s = re.sub(r'https?://\S+', '', s)
    s = re.sub(r'\bwww\.\S+', '', s)
    s = re.sub(r'\b[A-Za-z0-9-]+\.(ru|com|net|org|info|name)\b/?\S*', '', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r' *\n *', '\n', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def extract(html, title):
    soup = BeautifulSoup(html, "html.parser")
    cc = soup.select_one(".columnContent")
    if cc and len(cc.get_text().strip()) > 150:
        body = cc.get_text("\n")
    else:
        ps = []
        for p in soup.find_all("p"):
            cls = " ".join(p.get("class") or []).lower()
            if cls and cls != "para1":
                continue
            t = re.sub(r"\s+", " ", p.get_text()).strip()
            if len(t) < 12:
                continue
            if "Дискуссия" in t or "@" in t or "е-почта" in t:
                continue
            ps.append(t)
        dpos = [i for i, t in enumerate(ps) if DELIM.match(t)]
        if len(dpos) >= 2:
            seg = ps[dpos[0] + 1:dpos[1]]
        elif len(dpos) == 1:
            seg = ps[dpos[0] + 1:]
        else:
            seg = ps
        body = "\n\n".join(seg)
    lines = [l.strip() for l in body.split("\n")]
    while lines and (lines[0] == "" or lines[0].upper() == title.upper()):
        lines.pop(0)
    body = sanitize("\n".join(lines))
    # обрезаем хвостовой промо-мусор
    low = body
    cut = len(body)
    for marker in PROMO:
        i = low.find(marker)
        if i != -1:
            cut = min(cut, i)
    body = body[:cut].strip()
    return body

def slug(s):
    s = s.lower()
    s = re.sub(r"[«»\"'`]", "", s)
    s = re.sub(r"[^a-zа-я0-9]+", "-", s, flags=re.I)
    return s.strip("-")[:48]

def main():
    meta = json.load(open(os.path.join(HERE, "meta.json"), encoding="utf-8"))
    fails = []
    for m in meta:
        num = f"{m['idx']+1:02d}"
        fname = f"{num}-{m['id']}.md"
        try:
            html = fetch(m["ts"], m["id"])
            body = extract(html, m["title"])
        except Exception as e:
            body, err = "", str(e)
            print(f"  ! {fname}: {err}")
        if len(body) < 100:
            fails.append(m["idx"])
            if not body:
                body = "*(Текст не удалось извлечь автоматически — см. оригинал в Wayback по ссылке выше.)*"
        wb = f"https://web.archive.org/web/{m['ts']}/http://kak.ru/columns/illumination/{m['id']}/"
        title = f"{m['date']} · {m['title']}" + (f" — {m['sub']}" if m['sub'] else "")
        md = f"# {title}\n\n> Оригинал в Wayback Machine: {wb}\n>\n> Колонка Виктора Меламеда об иллюстрации, журнал «Как)», kak.ru\n\n{body}\n"
        open(os.path.join(ART, fname), "w", encoding="utf-8").write(md)
        print(f"  ok {fname}  ({len(body)} симв.)")
    print(f"\nГотово: {len(meta)} файлов. Короткие/пустые (idx): {fails}")

if __name__ == "__main__":
    main()
