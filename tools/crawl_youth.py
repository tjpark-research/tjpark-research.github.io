#!/usr/bin/env python3
"""청년사업 게시판 세 개(수상후기·캠프후기·갤러리)의 본문을 받아 온다.

이 셋은 다른 게시판과 상세 페이지 구조가 다르다. 본문이 `dl.comp-wrap-view`
(dt=제목, dd=본문) 안에 있고, 갤러리 사진은 `a.group` 링크로 따로 붙는다.
일반 수집기(crawl_details.py)는 이 구조를 못 읽고 SNS 공유 버튼 세 개만
본문으로 집어 온다. 그래서 이 셋만 따로 받는다.

  python3 tools/crawl_youth.py youth_gallery
"""
import json, os, re, sys, time, urllib.request
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY = os.path.join(ROOT, 'data', 'legacy')
# 공유 버튼·아이콘은 본문 사진이 아니다.
SKIP = ('/images/sns/', '/images/common/', '/images/board/', '/images/main/')
# 구 CMS 의 편집자 메모가 본문에 섞여 있다. 방문자에게 보일 글이 아니다.
NOISE_P = re.compile(r'^<?\s*본문에 이미지 삽입')


def clean(t):
    return re.sub(r'[ \t ]+', ' ', (t or '')).strip()


def fetch(url):
    r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(r, timeout=25).read().decode('utf-8', 'replace')


def paras_of(dd):
    """<dd> 안의 글을 문단으로 나눈다. <br> 은 줄바꿈으로 바꾼 뒤 자른다."""
    for br in dd.find_all('br'):
        br.replace_with('\n')
    out = []
    for blk in dd.find_all(['p', 'div']) or [dd]:
        if blk.find(['p', 'div']):
            continue
        for line in clean(blk.get_text('')).split('\n'):
            line = clean(line)
            if line and line not in out:
                out.append(line)
    if not out:
        for line in clean(dd.get_text('')).split('\n'):
            line = clean(line)
            if line:
                out.append(line)
    return out


def one(url, bid):
    s = BeautifulSoup(fetch(url), 'html.parser')
    scope = s.select_one('dl.comp-wrap-view')
    title = None
    paras = []
    imgs = []
    if scope is not None:
        dt = scope.find('dt')
        if dt is not None:
            title = clean(dt.get_text(' '))
        for im in scope.find_all('img'):
            u = im.get('src') or ''
            if u and not any(k in u for k in SKIP):
                imgs.append(urllib.parse.urljoin(url, u))
        for dd in scope.find_all('dd'):
            paras += [x for x in paras_of(dd) if not NOISE_P.match(x)]
    # 갤러리 사진은 원본 크기 링크(a.group)로 붙는다.
    for a in s.select('a.group'):
        h = a.get('href') or ''
        if h and not any(k in h for k in SKIP):
            u = urllib.parse.urljoin(url, h)
            if u not in imgs:
                imgs.append(u)
    yt = None
    fr = s.find('iframe', src=re.compile(r'youtube'))
    if fr is not None:
        yt = fr.get('src')
    posted = None
    m = re.search(r'(\d{4}-\d{2}-\d{2})', s.get_text(' '))
    if m:
        posted = m.group(1)
    return title, paras, imgs, yt, posted


def main():
    import urllib.parse                      # one() 안에서 쓴다
    globals()['urllib'].parse = urllib.parse
    board = sys.argv[1]
    bid = board.replace('youth_', 'y_')
    rows = json.load(open(os.path.join(LEGACY, f'board_{board}.json'), encoding='utf-8'))
    # idx=0 은 목록에 섞여 있는 헛 링크다(맨 앞 글과 내용이 같다).
    rows = [x for x in rows if str(x.get('idx') or '') not in ('', '0', 'None')]
    out = []
    for it in rows:
        try:
            title, paras, imgs, yt, posted = one(it['href'], bid)
        except Exception as e:
            print(f"  실패 {it['idx']}: {e}")
            continue
        meta = {}
        if posted:
            meta['posted'] = posted
            meta['date'] = posted
        rec = {'url': it['href'],
               'title': title or it['title'],
               'meta': meta,
               'sections': [{'heading': None, 'paragraphs': paras}],
               'images': imgs,
               'files': [],
               'idx': it['idx'],
               'list_title': it['title'],
               'image_local': None}
        if yt:
            rec['youtube'] = yt
        out.append(rec)
        time.sleep(0.3)
    p = os.path.join(LEGACY, f'detail_{board}.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n = sum(len(''.join(p_ for s in r['sections'] for p_ in s['paragraphs'])) for r in out)
    print(f'{board}: {len(out)}건, 본문 {n}자, 사진 {sum(len(r["images"]) for r in out)}장')


if __name__ == '__main__':
    main()
