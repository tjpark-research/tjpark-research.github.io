#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/curated/*.json 이 제대로 적혀 있는지 본다.

연구소가 GitHub 웹에서 직접 고치는 파일이라, 쉼표 하나가 빠져도 홈페이지가
통째로 안 만들어진다. 무엇이 어디서 틀렸는지 한국어로 짚어 준다.

    python3 tools/check_curated.py
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
CURATED = os.path.join(ROOT, 'data', 'curated')

BOARDS = {'news_notice', 'news_press'}
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
SMART = '“”‘’'

errs = []


def bad(where, msg, hint=''):
    errs.append((where, msg, hint))


def load(name):
    p = os.path.join(CURATED, name)
    if not os.path.exists(p):
        return None
    raw = open(p, encoding='utf-8').read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        line = raw.split('\n')[e.lineno - 1] if e.lineno <= len(raw.split('\n')) else ''
        hint = ''
        if 'Expecting' in e.msg and ',' in e.msg:
            hint = '앞 줄 끝에 쉼표(,)가 빠졌거나, 마지막 항목 뒤에 쉼표가 남아 있습니다.'
        elif any(c in line for c in SMART):
            hint = '둥근 따옴표(“ ”)가 섞여 있습니다. 곧은 따옴표(")로 바꿔 주세요.'
        bad(f'{name} {e.lineno}번째 줄', e.msg, hint or f'그 줄: {line.strip()[:80]}')
        return False


def check_posts(data):
    seen = set()
    for i, a in enumerate(data, 1):
        w = f'posts.json {i}번째 글'
        if not isinstance(a, dict):
            bad(w, '항목이 { } 로 감싸여 있지 않습니다'); continue
        b = a.get('board', 'news_notice')
        if b not in BOARDS:
            bad(w, f'board 가 "{b}" 로 되어 있습니다',
                'news_notice(공지사항) 또는 news_press(보도자료) 여야 합니다')
        for k in ('date', 'title', 'body'):
            if not a.get(k):
                bad(w, f'{k} 가 비어 있습니다')
        d = a.get('date') or ''
        if d and not DATE.match(d):
            bad(w, f'date 가 "{d}" 입니다', '2026-09-10 처럼 적어 주세요')
        if not isinstance(a.get('body') or [], list):
            bad(w, 'body 는 문단 목록이어야 합니다', '["첫 문단", "둘째 문단"] 꼴')
        for f in (a.get('files') or []):
            if not f.get('path'):
                bad(w, '첨부에 path 가 없습니다')
            elif not os.path.exists(os.path.join(ROOT, f['path'])):
                bad(w, f'첨부 파일이 없습니다: {f["path"]}',
                    '먼저 그 경로에 파일을 올려 주세요')
        for im in (a.get('images') or []):
            if not os.path.exists(os.path.join(ROOT, im)):
                bad(w, f'사진 파일이 없습니다: {im}',
                    '먼저 그 경로에 사진을 올려 주세요')
        key = (b, d, (a.get('title') or '').strip())
        if key in seen:
            bad(w, '같은 날짜·제목의 글이 이미 있습니다')
        seen.add(key)


def check_books(data):
    for i, a in enumerate(data, 1):
        w = f'books.json {i}번째 책'
        for k in ('board', 'title', 'date'):
            if not a.get(k):
                bad(w, f'{k} 가 비어 있습니다')
        c = a.get('cover')
        if c and not os.path.exists(os.path.join(ROOT, c)):
            bad(w, f'표지 그림이 없습니다: {c}')


def check_history(data):
    seen = set()
    for i, y in enumerate(data, 1):
        w = f'history.json {i}번째 연도'
        year = str(y.get('year') or '')
        if not re.fullmatch(r'(19|20)\d{2}', year):
            bad(w, f'year 가 네 자리 연도가 아닙니다: {year!r}',
                '"year": "2025" 처럼 적습니다')
            continue
        if year in seen:
            bad(w, f'{year}년이 두 번 나옵니다',
                '한 연도의 항목은 한 덩어리에 모아 적습니다')
        seen.add(year)
        items = y.get('items')
        if not isinstance(items, list) or not items:
            bad(w, f'{year}년에 items 가 없습니다')
            continue
        for j, it in enumerate(items, 1):
            v = f'history.json {year}년 {j}번째 항목'
            d = str(it.get('date') or '')
            if d and not re.fullmatch(r'\d{2}\.\d{2}', d):
                bad(v, f'날짜 모양이 다릅니다: {d!r}',
                    '"date": "09.01" 처럼 월.일 두 자리씩 적습니다')
            if not it.get('ko'):
                bad(v, 'ko (한글 문구) 가 비어 있습니다')
            if not it.get('en'):
                bad(v, 'en (영문 문구) 가 비어 있습니다',
                    '영문 연혁 페이지에도 같이 실립니다. 책 제목은 '
                    '『』 대신 *제목* 으로 적으면 이탤릭이 됩니다')


def main():
    for name, fn in (('posts.json', check_posts), ('books.json', check_books),
                     ('history.json', check_history)):
        data = load(name)
        if data is False:
            continue
        if data is None:
            continue
        if not isinstance(data, list):
            bad(name, '맨 바깥이 [ ] 목록이어야 합니다')
            continue
        fn(data)
    for name in ('media_links.json', 'videos.json'):
        load(name)

    if not errs:
        print('data/curated 형식 이상 없음')
        return 0
    print('=' * 60)
    print('새 글 파일에 고칠 곳이 있습니다')
    print('=' * 60)
    for where, msg, hint in errs:
        print(f'\n[{where}]\n  {msg}')
        if hint:
            print(f'  → {hint}')
    print('\n쓰는 법: data/curated/README.md')
    return 1


if __name__ == '__main__':
    sys.exit(main())
