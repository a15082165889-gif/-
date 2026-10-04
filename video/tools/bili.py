"""Tiny Bilibili helper: search (via the SSR search page) and metadata lookups.

    python3 tools/bili.py search "五里河 国足 出线"
"""
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
COOKIES = "/tmp/bili_cookies.txt"


def _cookie_header():
    try:
        out = []
        for ln in open(COOKIES):
            p = ln.strip().split("\t")
            if len(p) == 7:
                out.append(f"{p[5]}={p[6]}")
        return "; ".join(out)
    except OSError:
        return ""


def get(url, referer="https://www.bilibili.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer, "Cookie": _cookie_header()})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def search(q, pages=1):
    seen, out = set(), []
    for page in range(1, pages + 1):
        html = get(f"https://search.bilibili.com/all?keyword={urllib.parse.quote(q)}&page={page}")
        for m in re.finditer(r'"bvid":"(BV[0-9A-Za-z]{10})".{0,1500}?"title":"(.*?)".{0,800}?"duration":"([0-9:]+)"',
                             html, re.S):
            bv, title, dur = m.group(1), re.sub(r"<.*?>", "", m.group(2)), m.group(3)
            if bv not in seen:
                seen.add(bv)
                out.append((bv, dur, title))
        if not out:  # fall back to bare ids
            for bv in dict.fromkeys(re.findall(r"BV[0-9A-Za-z]{10}", html)):
                if bv not in seen:
                    seen.add(bv)
                    out.append((bv, "?", ""))
    return out


def view(bv):
    d = json.loads(get(f"https://api.bilibili.com/x/web-interface/view?bvid={bv}"))
    return d.get("data") or {}


if __name__ == "__main__":
    if sys.argv[1] == "search":
        for bv, dur, title in search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1):
            print(f"{bv} | {dur} | {title}")
