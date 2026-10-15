#!/usr/bin/env python3
"""Crawl kb.mautic.org (PHPKB) English categories -> markdown-ish text files with source URL headers."""
import re, html, urllib.request, urllib.parse, os, sys, time
OUT = sys.argv[1]
BASE = "https://kb.mautic.org"
seen_cats, articles = set(), {}
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (skills-harvest)"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
def crawl_cat(u):
    if u in seen_cats: return
    seen_cats.add(u)
    try: h = get(u)
    except Exception as e: print("ERR", u, e); return
    for m in re.findall(r'href="(https://kb\.mautic\.org/article/[^"]+)"', h):
        articles.setdefault(html.unescape(m), None)
    for m in re.findall(r'href="(https://kb\.mautic\.org/category/[^"]+)"', h):
        m = html.unescape(m)
        # English categories only: skip obvious non-English slugs
        if re.search(r'anleitungen|gu%c3%adas|guias|guides-d|tutoriels|fehlerbehebung|soluci|resolu|probl', m, re.I): continue
        crawl_cat(m.split('?')[0])
for c in ["how-to-guides/4/", "troubleshooting-mautic/11/", "tutorials/2/"]:
    crawl_cat(f"{BASE}/category/{c}")
    for p in (2,3,4): crawl_cat(f"{BASE}/category/{c}?page={p}")
def strip(h):
    h = re.sub(r'(?is)<(script|style|nav|header|footer).*?</\1>', ' ', h)
    h = re.sub(r'(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>', '\n', h)
    h = re.sub(r'(?i)<h1[^>]*>', '\n# ', h); h = re.sub(r'(?i)<h2[^>]*>', '\n## ', h); h = re.sub(r'(?i)<h3[^>]*>', '\n### ', h)
    h = re.sub(r'(?i)<li[^>]*>', '- ', h)
    h = re.sub(r'(?i)<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'\2 (\1)', h)
    h = re.sub(r'<[^>]+>', '', h)
    h = html.unescape(h)
    h = re.sub(r'\n\s*\n\s*\n+', '\n\n', h)
    return h.strip()
n = 0
for u in sorted(articles):
    try: h = get(u)
    except Exception as e: print("ERR", u, e); continue
    title = re.search(r'<title>(.*?)</title>', h, re.S)
    title = html.unescape(title.group(1)).strip() if title else u
    # main article body: PHPKB uses div with id/class containing 'article'
    body = re.search(r'(?is)<div[^>]+(?:id="article-content"|class="[^"]*article-content[^"]*"|class="[^"]*article_body[^"]*")[^>]*>(.*)', h)
    text = strip(body.group(1) if body else h)
    slug = u.rsplit('/',1)[-1].replace('.html','')[:120]
    with open(os.path.join(OUT, slug + ".md"), "w") as f:
        f.write(f"---\nsource: {u}\ntitle: {title}\nfetched: {time.strftime('%Y-%m-%d')}\n---\n\n{text}\n")
    n += 1; time.sleep(0.5)
print("articles:", n, "categories:", len(seen_cats))
