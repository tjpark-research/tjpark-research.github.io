#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""게시판 글의 첨부파일을 내려받아 저장소에 담는다.

구 CMS 의 첨부 링크는 '02_board/fileDown.php?idx=NNN' 이라 구 사이트가
내려가면 함께 사라진다. 파일을 assets/files/<board>/ 로 옮기고
detail_*.json 에 files_local 을 적어 둔다.

    python3 tools/fetch_files.py news_notice
"""
import json, os, re, sys, time
from urllib.parse import urlparse, unquote
import requests

ROOT = os.path.join(os.path.dirname(__file__), '..')
LEGACY = os.path.join(ROOT, 'data', 'legacy')
OUT = os.path.join(ROOT, 'assets', 'files')
UA = {'User-Agent': 'Mozilla/5.0 (compatible; TJPI-archive/1.0)'}
SAFE = re.compile(r'[^0-9A-Za-z가-힣._-]+')


def safe_name(name, href):
    n = unquote(name or '').strip()
    if not n or '.' not in n:
        n = os.path.basename(urlparse(href).path) or 'file'
    n = SAFE.sub('_', n).strip('_')
    return n[:90] or 'file'


def run(board):
    p = os.path.join(LEGACY, f'detail_{board}.json')
    data = json.load(open(p))
    d = os.path.join(OUT, board)
    os.makedirs(d, exist_ok=True)
    got = skip = fail = 0
    for x in data:
        loc = {}
        for i, f in enumerate(x.get('files') or []):
            nm = f'{x["idx"]}_{safe_name(f.get("name"), f["href"])}'
            path = os.path.join(d, nm)
            rel = f'assets/files/{board}/{nm}'
            if os.path.exists(path) and os.path.getsize(path) > 0:
                loc[str(i)] = rel; skip += 1; continue
            try:
                r = requests.get(f['href'], headers=UA, timeout=40)
                r.raise_for_status()
                if len(r.content) < 64:
                    raise ValueError(f'너무 작음 {len(r.content)}B')
                open(path, 'wb').write(r.content)
                loc[str(i)] = rel; got += 1
            except Exception as e:
                print(f'  실패 {x["idx"]} {f.get("name")}: {e}'); fail += 1
            time.sleep(0.2)
        if loc:
            x['files_local'] = loc
    json.dump(data, open(p, 'w'), ensure_ascii=False, indent=1)
    print(f'{board}: 새로 {got}, 이미 있음 {skip}, 실패 {fail}')


if __name__ == '__main__':
    for b in (sys.argv[1:] or ['news_notice']):
        run(b)
