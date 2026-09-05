#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
정적 HTML 생성기.

**배포에는 빌드 스텝이 없다.** 이 스크립트는 로컬에서만 돌리고, 결과물인
평범한 .html 파일을 저장소에 커밋한다. GitHub Pages 는 아무것도 하지 않는다.
(.nojekyll 참고)

이렇게 하는 이유: 페이지가 30개가 넘는데 헤더·GNB·푸터를 파일마다 복사해 두면
메뉴 하나 고칠 때 30곳을 고쳐야 한다. 네비게이션의 원본은 tools/sitemap_def.py 하나다.

    python3 tools/build_site.py
"""
import html, json, os, re, sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(__file__))
from sitemap_def import SECTIONS, EN_SECTIONS, ALL_LABELS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LEGACY = os.path.join(ROOT, 'data', 'legacy')

E = lambda s: html.escape(s or '', quote=True)


def load(name):
    p = os.path.join(LEGACY, name + '.json')
    return json.load(open(p)) if os.path.exists(p) else None


TABSTRIP_RE = re.compile(
    r'^(?:시대별|연도별)?\s*(?:\d{4}\s*년?\s*[~\-]\s*\d{4}\s*년?\s*){2,}')


def blocks_of(page_key, drop=0):
    """수집한 본문 블록에서 메뉴 텍스트를 걷어내고 문단만 남긴다."""
    d = load('page_' + page_key) or {}
    raw = d.get('blocks', [])

    # 상위 컨테이너가 하위 항목들을 통째로 이어붙인 블록을 버린다.
    # (구 사이트의 표/목록이 부모 div 의 직접 텍스트로도 한 번 더 잡히는 탓에
    #  같은 내용이 '한 덩어리 + 항목별'로 두 번 나온다.)
    parts_pool = [x.strip() for x in raw if len(x.strip()) >= 12]
    def is_concat(b):
        if len(b) < 200:
            return False
        covered = sum(1 for p in parts_pool if p != b and p in b)
        return covered >= 3

    out = []
    for b in [x for x in raw if not is_concat(x)]:
        # 구 사이트 DB 에 저장된 본문에는 HTML 조각이 문자 그대로 들어 있는
        # 경우가 있다 ('<span class="tit">교통편</span> : ...'). 태그를 걷어낸다.
        t = re.sub(r'<[^>]{1,200}>', ' ', b)
        t = html.unescape(t)
        t = re.sub(r'\s+', ' ', t).strip()
        if not t or t in ALL_LABELS or len(t) < 3:
            continue
        # 브레드크럼이 한 줄로 뭉쳐 들어온 경우 ('연구소소개 설립목적 취지')
        parts = [p for p in re.split(r'[\s>·]+', t) if p]
        if len(parts) > 1 and all(p in ALL_LABELS for p in parts):
            continue
        # 시대 탭 라벨이 본문 '앞에 붙어' 들어오는 경우.
        # ('시대별 1927~1947 1948~1960 … 1927년 9월 29일 …')
        # 블록을 버리면 본문까지 날아가므로 접두사만 떼어낸다.
        t = TABSTRIP_RE.sub('', t).strip()
        if len(t) < 3:
            continue
        if re.fullmatch(r'[0-9.\-/ ]+', t):
            continue
        out.append(t)
    return out[drop:]


MIN_W, MIN_H = 240, 70


def _too_small(rel_path):
    """구 사이트는 소제목('연구소개', '전문성')과 아이콘도 이미지로 만들어 두었다.
    이런 것들을 본문 폭으로 늘리면 흐릿하게 뭉개진다. 내용이 아니라 장식이므로
    아예 싣지 않는다. (필요한 제목은 텍스트로 따로 넣는다.)"""
    try:
        from PIL import Image
        w, h = Image.open(os.path.join(ROOT, rel_path)).size
        return w < MIN_W or h < MIN_H
    except Exception:
        return False


def imgs_of(page_key):
    d = load('page_' + page_key) or {}
    loc = d.get('images_local', {})
    paths = [loc[k] for k in sorted(loc, key=int)] if loc else []
    return [p for p in paths if not _too_small(p)]


# ─────────────────────────────────────────────────────────── 공통 조각
def rel(depth):
    """현재 문서에서 '사이트 루트'까지 올라가는 상대경로."""
    return '../' * depth


def base(depth, lang='ko'):
    """현재 문서에서 '그 언어판의 루트'까지 가는 상대경로.

    한국어는 사이트 루트가 곧 언어 루트지만, 영문은 /en/ 이 언어 루트다.
    이걸 구분하지 않으면 영문 페이지의 메뉴가 전부 한국어 페이지를 가리킨다.
    """
    return rel(depth) + ('en/' if lang == 'en' else '')


def gnb(depth, active=None, lang='ko'):
    secs = SECTIONS if lang == 'ko' else EN_SECTIONS
    b = base(depth, lang)
    li = []
    for key, label, _en, d, kids in secs:
        sub = ''.join(f'<a href="{b}{d}/{f}">{E(cl)}</a>' for f, cl, _s in kids)
        cls = ' class="on"' if key == active else ''
        li.append(
            f'<li{cls}><a href="{b}{d}/index.html">{E(label)}</a>'
            f'<div class="mega">{sub}</div></li>')
    return '<ul class="gnb">' + ''.join(li) + '</ul>'


def header(depth, active=None, lang='ko', alt_href=None):
    """lang='en' 이면 라벨과 언어 토글이 영문 기준이 된다.
    alt_href 는 '같은 내용의 반대 언어 페이지' 경로 — 언어 토글이 홈이 아니라
    지금 보던 페이지의 짝으로 가야 한다."""
    r = rel(depth)
    if lang == 'ko':
        brand_sub, related = '박태준미래전략연구소', '관련사이트'
        toggle = (f'<a href="{r}index.html" class="on">KOR</a><span>|</span>'
                  f'<a href="{alt_href or (r + "en/index.html")}">ENG</a>')
        sites = [('https://www.postech.ac.kr/', '포항공과대학교'),
                 ('https://www.posco.co.kr/', '포스코'),
                 ('https://www.postf.org/', '포스코청암재단'),
                 ('http://museum.posco.co.kr/', '포스코박물관')]
    else:
        brand_sub, related = 'Tae-Joon Park Institute', 'Related Sites'
        toggle = (f'<a href="{alt_href or (r + "index.html")}">KOR</a><span>|</span>'
                  f'<a href="{base(depth, "en")}index.html" class="on">ENG</a>')
        sites = [('https://www.postech.ac.kr/eng/', 'POSTECH'),
                 ('https://www.posco.co.kr/', 'POSCO'),
                 ('https://www.postf.org/', 'POSCO TJ Park Foundation'),
                 ('http://museum.posco.co.kr/', 'POSCO Museum')]
    opts = ''.join(f'<option value="{u}">{E(n)}</option>' for u, n in sites)
    return f'''<div class="util">
  <div class="wrap">
    <select aria-label="{E(related)}" onchange="if(this.value)window.open(this.value)">
      <option value="">{E(related)}</option>{opts}
    </select>
    <span class="lang">{toggle}</span>
  </div>
</div>
<header class="hd">
  <div class="wrap">
    <a class="brand" href="{base(depth, lang)}index.html">
      <span class="mark">tjpi</span>
      <span class="txt"><b>POSTECH</b><span>{E(brand_sub)}</span></span>
    </a>
    <nav aria-label="main">{gnb(depth, active, lang)}</nav>
    <button class="burger" aria-label="menu"><span></span></button>
  </div>
</header>'''


def footer(depth, lang='ko'):
    r = rel(depth)
    secs = SECTIONS if lang == 'ko' else EN_SECTIONS
    b = base(depth, lang)
    links = ''.join(f'<li><a href="{b}{d}/index.html">{E(l)}</a></li>'
                    for _k, l, _e, d, _c in secs)
    if lang == 'ko':
        privacy = '개인정보처리방침'
        addr = ('경상북도 포항시 남구 청암로 77 포항공과대학교 박태준학술정보관 6층<br>'
                'TEL 054-279-0053~6 &nbsp;·&nbsp; FAX 054-279-0059 '
                '&nbsp;·&nbsp; E-mail tj-park@postech.ac.kr')
        rel_sites = [('https://www.postech.ac.kr/', '포항공과대학교'),
                     ('https://www.posco.co.kr/', '포스코'),
                     ('https://www.postf.org/', '포스코청암재단'),
                     ('http://museum.posco.co.kr/', '포스코박물관')]
    else:
        privacy = 'Privacy Policy'
        addr = ('6F, Tae-Joon Park Digital Library, POSTECH, 77 Cheongam-ro, '
                'Nam-gu, Pohang, Gyeongbuk, Republic of Korea<br>'
                'Tel +82-54-279-0053~6 &nbsp;·&nbsp; Fax +82-54-279-0059 '
                '&nbsp;·&nbsp; E-mail tj-park@postech.ac.kr')
        rel_sites = [('https://www.postech.ac.kr/eng/', 'POSTECH'),
                     ('https://www.posco.co.kr/', 'POSCO'),
                     ('https://www.postf.org/', 'POSCO TJ Park Foundation'),
                     ('http://museum.posco.co.kr/', 'POSCO Museum')]
    brand_sub = '박태준미래전략연구소' if lang == 'ko' else 'Tae-Joon Park Institute'
    rl = ''.join(f'<li><a href="{u}" target="_blank" rel="noopener">{E(n)}</a></li>'
                 for u, n in rel_sites)
    return f'''<footer class="ft">
  <div class="wrap">
    <div class="ft-top">
      <div class="brand"><span class="mark">tjpi</span>
        <span class="txt"><b>POSTECH</b><span>{E(brand_sub)}</span></span></div>
      <ul class="ft-links">{links}
        <li><a href="https://www.postech.ac.kr/kor/usage-guide/privacy_policy.do" target="_blank" rel="noopener">{E(privacy)}</a></li>
      </ul>
    </div>
    <div class="ft-bot">
      <address>
        {addr}
        <span class="cr" style="display:block;margin-top:14px">© POSTECH Tae-Joon Park Institute for Future Strategy. All rights reserved.</span>
      </address>
      <ul class="ft-rel">{rl}</ul>
    </div>
  </div>
</footer>'''


def lnb(section, current_file, depth, lang='ko'):
    key, label, en, d, kids = section
    b = base(depth, lang)
    parts = []
    for f, cl, _s in kids:
        on = ' class="on"' if f == current_file else ''
        parts.append(f'<li{on}><a href="{b}{d}/{f}">{E(cl)}</a></li>')
    items = ''.join(parts)
    return f'<nav class="lnb" aria-label="{E(label)} 하위 메뉴"><p class="lnb-t">{E(label)}<span>{E(en)}</span></p><ul>{items}</ul></nav>'


def shell(title, desc, depth, section, current_file, body, canonical,
          lang='ko', alt_href=None, alt_canonical=None, article_title=None):
    """article_title 이 주어지면 개별 글 페이지로 취급한다.
    이때 h1 은 글 제목이어야 한다 — 목록 이름을 h1 으로 두면 461개 글이
    전부 같은 제목을 갖게 되어 검색에도 스크린리더에도 불리하다."""
    key, label, en, d, kids = section
    cur_label = next((cl for f, cl, _s in kids if f == current_file), label)
    r = rel(depth)
    home = 'HOME'
    b = base(depth, lang)
    crumb = (f'<a href="{b}index.html">{home}</a><span>›</span>'
             f'<a href="{b}{d}/index.html">{E(label)}</a><span>›</span>')
    if article_title:
        crumb += f'<a href="{b}{d}/{current_file}">{E(cur_label)}</a><span>›</span><em>{E(article_title[:40])}</em>'
    else:
        crumb += f'<em>{E(cur_label)}</em>'
    hero_kicker = cur_label if article_title else en
    hero_h1 = article_title if article_title else cur_label
    site = ('POSTECH 박태준미래전략연구소' if lang == 'ko'
            else 'POSTECH Tae-Joon Park Institute')
    skip = '본문 바로가기' if lang == 'ko' else 'Skip to content'
    ko_url = canonical if lang == 'ko' else alt_canonical
    en_url = alt_canonical if lang == 'ko' else canonical
    alts = ''
    if ko_url and en_url:
        alts = (f'<link rel="alternate" hreflang="ko" href="https://tjpark-research.github.io/{ko_url}">\n'
                f'<link rel="alternate" hreflang="en" href="https://tjpark-research.github.io/{en_url}">\n'
                f'<link rel="alternate" hreflang="x-default" href="https://tjpark-research.github.io/{ko_url}">')
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — {E(site)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="https://tjpark-research.github.io/{canonical}">
{alts}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{E(site)}">
<meta property="og:title" content="{E(title)} — {E(site)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="https://tjpark-research.github.io/{canonical}">
<link rel="stylesheet" href="{r}assets/fonts/pretendard-dynamic-subset.css">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">{E(skip)}</a>
{header(depth, key, lang, alt_href)}
<div class="sub-hero">
  <div class="wrap">
    <p class="eyebrow">{E(hero_kicker)}</p>
    <h1{' class="h1-art"' if article_title else ''}>{E(hero_h1)}</h1>
    <p class="crumb">{crumb}</p>
  </div>
</div>
<div class="sub-wrap wrap">
  {lnb(section, current_file, depth, lang)}
  <main id="main" class="sub-main">
{body}
  </main>
</div>
{footer(depth, lang)}
<script src="{r}assets/js/main.js"></script>
</body>
</html>
'''


# ─────────────────────────────────────────────────────── 본문 렌더러
def fig(src, depth, cap=None):
    c = f'<figcaption>{E(cap)}</figcaption>' if cap else ''
    return f'<figure class="fig"><img src="{rel(depth)}{src}" alt="{E(cap or "")}" loading="lazy">{c}</figure>'


def render_prose(blocks, images, depth, lead=True):
    out = []
    for i, b in enumerate(blocks):
        # 리드 문단(크고 강조되는 도입 문장)은 '첫 문단이라서'가 아니라
        # '짧아서' 리드다. 900자짜리 본문 덩어리에 리드를 씌우면
        # 페이지 전체가 도입부처럼 보인다.
        is_lead = lead and i == 0 and len(b) <= 120
        cls = ' class="lead"' if is_lead else ''
        out.append(f'<p{cls}>{E(b)}</p>')
    for im in images:
        out.append(fig(im, depth))
    return '<div class="prose">' + '\n'.join(out) + '</div>'


def render_image_page(images, depth, note):
    """구 사이트에서 본문 전체가 이미지로 만들어진 페이지.

    원본을 그대로 보여주되, 이미지 안의 글자는 검색도 확대도 스크린리더도
    안 되므로 텍스트로 다시 쓸 대상임을 명시해 둔다.
    """
    body = '\n'.join(fig(im, depth) for im in images)
    return (f'<div class="prose"><p class="lead">{E(note)}</p>{body}'
            f'<p class="todo-note">※ 이 페이지는 구 홈페이지에서 이미지 한 장으로 제작되어 '
            f'있었습니다. 내용을 텍스트로 다시 옮기면 검색·확대·스크린리더 이용이 '
            f'가능해집니다.</p></div>')


YEAR_RE = re.compile(r'^(\d{4})\s*년$')
DATE_RE = re.compile(r'^(\d{1,2})\s*[.]\s*(\d{1,2})\s+(.*)$')


def render_timeline(blocks):
    """'2013년' / '2. 15 연구소 개소' 형태의 블록을 연도별 타임라인으로 묶는다."""
    groups, cur = [], None
    for b in blocks:
        m = YEAR_RE.match(b)
        if m:
            cur = {'year': m.group(1), 'items': []}
            groups.append(cur)
            continue
        if cur is None:
            continue
        d = DATE_RE.match(b)
        if d:
            cur['items'].append((f'{int(d.group(1))}.{int(d.group(2))}', d.group(3)))
        else:
            cur['items'].append(('', b))
    out = ['<ol class="chrono">']
    for g in groups:
        rows = ''.join(
            f'<li><span class="d">{E(d)}</span><span class="t">{E(t)}</span></li>'
            for d, t in g['items'])
        out.append(f'<li class="chrono-y"><h3>{g["year"]}</h3><ul>{rows}</ul></li>')
    out.append('</ol>')
    return '\n'.join(out)


def render_eras(specs, depth):
    """시대별 탭 (생애). JS 없이도 전부 읽히도록 섹션을 모두 출력하고,
    JS 가 있으면 탭으로 접어 준다."""
    tabs, panes = [], []
    for i, (label, key) in enumerate(specs):
        on = ' class="on"' if i == 0 else ''
        tabs.append(f'<button type="button"{on} data-era="{i}">{E(label)}</button>')
        blocks = [b for b in blocks_of(key) if len(b) > 60]
        imgs = imgs_of(key)[:1]
        body = ''.join(f'<p>{E(b)}</p>' for b in blocks)
        body += ''.join(fig(im, depth) for im in imgs)
        panes.append(f'<section class="era-pane" data-era="{i}">'
                     f'<h2 class="era-h">{E(label)}</h2>{body}</section>')
    return (f'<div class="eras"><div class="era-tabs">{"".join(tabs)}</div>'
            f'<div class="prose">{"".join(panes)}</div></div>')


def render_board(name, depth, style='cards', empty='등록된 자료가 없습니다.',
                 detail_base=None):
    """detail_base 가 주어지면 각 항목을 개별 글 페이지로 링크한다.
    (예: 'research/books' → /research/books/<idx>.html)"""
    items = load('board_' + name) or []
    if not items:
        return f'<div class="prose"><p>{E(empty)}</p></div>'
    have_detail = {d['idx'] for d in (load('detail_' + name) or [])
                   if d.get('idx') and d.get('sections')}
    cards = []
    for it in items:
        href = None
        if detail_base and it.get('idx') in have_detail:
            href = f'{rel(depth)}{detail_base}/{it["idx"]}.html'
        t = it.get('title') or ''
        meta = ' · '.join(x for x in [it.get('author'), it.get('publisher'), it.get('date')] if x)
        summ = (it.get('summary') or '')[:150]
        key = E((t + ' ' + (it.get('author') or '')).lower())
        if style == 'cards':
            img = (f'<img src="{rel(depth)}{it["local"]}" alt="" loading="lazy">'
                   if it.get('local') else '<span class="noimg">TJPI</span>')
            inner = (f'<div class="bcard-cov">{img}</div>'
                     f'<div class="bcard-b"><h3>{E(t)}</h3>'
                     + (f'<p class="m">{E(meta)}</p>' if meta else '')
                     + (f'<p class="s">{E(summ)}</p>' if summ else '')
                     + '</div>')
            body_html = f'<a href="{href}">{inner}</a>' if href else inner
            cards.append(f'<li class="bcard" data-k="{key}">{body_html}</li>')
        else:
            inner = (f'<span class="tt">{E(t)}</span>'
                     f'<span class="dt">{E(it.get("date") or "")}</span>')
            body_html = f'<a href="{href}">{inner}</a>' if href else inner
            cards.append(f'<li class="brow" data-k="{key}">{body_html}</li>')
    cls = 'bgrid' if style == 'cards' else 'blist'
    return f'''<div class="board" data-page-size="{12 if style=="cards" else 20}">
  <div class="board-top">
    <p class="cnt">전체 <b>{len(items)}</b>건</p>
    <label class="board-search"><span class="sr">검색</span>
      <input type="search" placeholder="제목·저자 검색" data-board-search></label>
  </div>
  <ul class="{cls}">{''.join(cards)}</ul>
  <div class="board-more"><button type="button" data-board-more>더 보기</button></div>
</div>'''


# ─────────────────────────────────────────────────────── 페이지 정의
def people_page(depth):
    """연구소사람들 — 구 사이트의 표 구조가 본문 추출에서 뭉개져서
    수집 데이터 대신 확인된 명단을 직접 구성한다."""
    staff = [
        ('송민석', '소장', '054-279-2387', ''),
        ('정기준', '연구부교수', '054-279-5631', ''),
        ('백태헌', '책임연구원', '054-279-0057', '연구 총괄, 연구과제 수행'),
        ('박보미', '연구원', '054-279-0054', '기획·홍보·인사·예산 관리, 연구 지원'),
    ]
    rows = ''.join(
        f'<tr><th scope="row">{E(n)}</th><td>{E(r)}</td><td>{E(t)}</td><td>{E(w)}</td></tr>'
        for n, r, t, w in staff)
    committee = (
        '위원장 이진우(포스텍 석좌교수). 위원 최광웅, 김병현·김승환·류성호·정성모(포스텍), '
        '김병연·방민호·전상인(서울대), 김왕배(연세대), 박길성(고려대), 백기복(국민대), '
        '최진덕(한국학중앙연구원), 박성빈(Translink Capital), 전영기(시사저널), 조윤제(서강대).')
    return f'''<div class="prose">
  <p class="lead">연구소는 소수의 상근 인력이 기획·관리·평가를 맡고, 연구는 외부 전문가 네트워크와의 협업으로 수행합니다.</p>
  <h2>연구기획실</h2>
  <table class="tbl">
    <thead><tr><th scope="col">성명</th><th scope="col">직급</th><th scope="col">연락처</th><th scope="col">주요 업무</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <h2>미래전략연구위원회</h2>
  <p>미래전략연구 관련 기본정책을 설정하고, 연구소의 연구과제를 선정·기획합니다. 학자 중심으로 구성됩니다.</p>
  <p class="sub">{E(committee)}</p>
  <h2>박태준미래전략아카데미</h2>
  <p>미래전략 연구에 참여하거나 그 취지에 공감하는 교수·지식인의 모임으로, 교수·전문가 네트워크를 통해 연구 활동에 참여하고 연대합니다. 국내 주요 대학과 연구기관의 연구자 100여 분이 회원으로 참여하고 있습니다.</p>
  <p class="todo-note">※ 위원·회원 명단은 구 홈페이지 기준입니다. 최신 명단으로 갱신이 필요합니다.</p>
</div>'''


def location_page(depth):
    return '''<div class="prose">
  <p class="lead">포항공과대학교 박태준학술정보관 6층에 있습니다.</p>
  <table class="tbl">
    <tbody>
      <tr><th scope="row">주소</th><td>경상북도 포항시 남구 청암로 77<br>포항공과대학교 박태준학술정보관 6층</td></tr>
      <tr><th scope="row">전화</th><td>054-279-0053~6</td></tr>
      <tr><th scope="row">팩스</th><td>054-279-0059</td></tr>
      <tr><th scope="row">이메일</th><td><a href="mailto:tj-park@postech.ac.kr">tj-park@postech.ac.kr</a></td></tr>
    </tbody>
  </table>
  <p><a class="btn btn-p" href="https://map.kakao.com/?q=포항공과대학교 박태준학술정보관" target="_blank" rel="noopener">지도에서 보기</a></p>
</div>'''


def PAGES(depth):
    """(섹션키, 파일) → (제목, 설명, 본문HTML)"""
    d = depth
    P = {}
    # ── 미래전략연구
    P[('research', 'index.html')] = ('연구소개', '‘박태준 정신’을 기반으로 미래 핵심문제를 조망하고 대응 방향을 제안합니다.',
        research_intro_page(d))
    P[('research', 'longterm.html')] = ('중장기 연구주제', '연구소가 중장기적으로 붙들고 있는 세 갈래 질문.',
        longterm_page(d, 'ko'))
    P[('research', 'themes.html')] = ('연도별 연구주제', '연도별로 선정한 미래전략 연구주제와 세부 과제입니다.',
        render_eras([('2018~2020', 'research_theme_18_20'), ('2017~2018', 'research_theme_17_18'),
                     ('2016~2017', 'research_theme_16_17'), ('2015~2016', 'research_theme_15_16'),
                     ('2014~2015', 'research_theme_14_15')], d))
    P[('research', 'books.html')] = ('연구총서', '미래전략연구총서 — 미래 핵심 의제에 대한 학제적 연구 성과.',
        render_board('books_future', d, 'cards', detail_base='research/books'))
    P[('research', 'reports.html')] = ('연구보고서', '연구논문·전문가 에세이·여론조사 보고서.',
        render_board('reports_future', d, 'cards', detail_base='research/reports'))
    P[('research', 'contest.html')] = ('대학(원)생 공모전 수상작', '전국 대학생·대학원생 에세이 공모전 수상작.',
        render_board('contest_winners', d, 'cards', detail_base='research/contest'))
    # ── 박태준연구
    P[('tjpark', 'index.html')] = ('연구소개', '박태준의 정신과 리더십을 체계적으로 연구하고 사회적 자산으로 전파합니다.',
        render_prose(blocks_of('tj_research_intro'), imgs_of('tj_research_intro'), d))
    P[('tjpark', 'themes.html')] = ('연구분야', '박태준연구의 연도별 주제입니다.',
        render_prose(blocks_of('tj_research_theme'), imgs_of('tj_research_theme'), d))
    P[('tjpark', 'books.html')] = ('연구총서', '박태준 연구총서와 관련 단행본.',
        render_board('books_tj', d, 'cards', detail_base='tjpark-research/books'))
    P[('tjpark', 'reports.html')] = ('연구보고서', '박태준연구 보고서.',
        render_board('reports_tj', d, 'cards', detail_base='tjpark-research/reports'))
    # ── 박태준의 삶
    P[('life', 'index.html')] = ('생애', '청암 박태준이 걸어온 길을 시대별로 살펴봅니다.',
        render_eras([('1927~1947', 'life_bio_1'), ('1948~1960', 'life_bio_2'),
                     ('1961~1967', 'life_bio_3'), ('1968~1992', 'life_bio_4'),
                     ('1993~2000', 'life_bio_5'), ('2001~2011', 'life_bio_6')], d))
    P[('life', 'chronology.html')] = ('연보', '1927년부터 2011년까지의 연보.',
        render_timeline(blocks_of('life_chron_all')))
    P[('life', 'statue.html')] = ('청암 조각상', '우웨이산이 만든 전신상과 흉상, 그리고 받침돌의 건립문.',
        statue_page(d, 'ko'))
    P[('life', 'who.html')] = ('박태준을 말한다', '동시대인이 남긴 박태준에 대한 기록.',
        render_prose([b for b in blocks_of('life_who') if len(b) > 25], imgs_of('life_who'), d))
    # ── 청년사업
    # 구 사이트는 '현재 진행중인 공모전이 없습니다'라는 안내마저 이미지였다.
    # 상태 안내는 자주 바뀌는 문구이므로 텍스트여야 고치기도 쉽다.
    P[('youth', 'index.html')] = ('대학(원)생 공모전', '전국 대학생·대학원생을 대상으로 한 에세이 공모전.',
        render_prose(blocks_of('youth_contest'), [], d)
        + '<div class="prose"><h2>진행중 공모전</h2>'
          '<p class="empty-state">현재 진행중인 공모전이 없습니다.</p>'
          '<p>공모전이 열리면 이 자리와 <a href="../news/index.html">공지사항</a>에 안내합니다. '
          '지난 수상작은 <a href="winners.html">수상작 보기</a>에서 볼 수 있습니다.</p></div>')
    P[('youth', 'winners.html')] = ('수상작 보기', '역대 공모전 수상작.',
        render_board('contest_winners', d, 'cards', detail_base='research/contest'))
    P[('youth', 'camp.html')] = ('포스텍 청년비전캠프', '스스로의 비전을 설계하는 캠프.',
        render_prose(blocks_of('youth_camp'), imgs_of('youth_camp'), d))
    P[('youth', 'camp-guide.html')] = ('캠프 안내', '청년비전캠프 참가 안내.',
        render_prose(blocks_of('youth_camp_guide'), imgs_of('youth_camp_guide'), d))
    P[('youth', 'faq.html')] = ('FAQ', '자주 묻는 질문.',
        '<div class="prose"><p class="lead">공모전과 캠프에 관해 자주 묻는 질문입니다.</p>'
        '<p>문의: <a href="mailto:tj-park@postech.ac.kr">tj-park@postech.ac.kr</a> · 054-279-0053~6</p>'
        '<p class="todo-note">※ 구 홈페이지의 FAQ 항목이 비어 있어 옮길 내용이 없습니다. 문항을 정리해 주시면 채우겠습니다.</p></div>')
    # ── 포럼 & 세미나
    P[('forum', 'index.html')] = ('포럼', '산학연관 전문가와 석학이 모여 국가의 미래를 논의하는 자리.',
        render_board('forum', d, 'cards', detail_base='forum/forums'))
    P[('forum', 'seminar.html')] = ('세미나', '연구소가 개최한 세미나.',
        render_board('seminar', d, 'cards', detail_base='forum/seminars'))
    P[('forum', 'multimedia.html')] = ('멀티미디어', '포럼·세미나 영상과 미디어 자료.',
        render_board('multimedia', d, 'cards', detail_base='forum/media'))
    # ── 연구소소식
    P[('news', 'index.html')] = ('공지사항', '연구소 공지사항.', render_board('news_notice', d, 'rows', detail_base='news/notices'))
    P[('news', 'press.html')] = ('보도자료', '언론에 보도된 연구소 소식.', render_board('news_press', d, 'rows', detail_base='news/press-items'))
    P[('news', 'column.html')] = ('TJ미래전략 칼럼', '연구소가 전하는 미래전략 칼럼.', render_board('news_column', d, 'cards', detail_base='news/columns'))
    # ── 연구소소개
    P[('about', 'index.html')] = ('인사말', '박태준미래전략연구소 소장 인사말.',
        render_prose(blocks_of('lab_greeting'), [], d) + greeting_photos(d, 'ko'))
    P[('about', 'purpose.html')] = ('설립목적', '연구소 설립의 취지.',
        render_prose(blocks_of('lab_purpose'), [], d))
    P[('about', 'mission.html')] = ('미션', '박태준미래전략연구소의 미션.', mission_page(d, 'ko'))
    P[('about', 'history.html')] = ('연혁', '2013년 개소 이후의 연혁.',
        render_timeline(blocks_of('lab_history')))
    P[('about', 'logo.html')] = ('로고 소개', '연구소 로고의 의미.',
        render_prose([b for b in blocks_of('lab_logo') if len(b) > 15], imgs_of('lab_logo'), d))
    P[('about', 'projects.html')] = ('주요사업', '연구소의 중점사업과 사업원칙.', projects_page(d, 'ko'))
    P[('about', 'people.html')] = ('연구소사람들', '연구기획실과 연구위원회 구성.', people_page(d))
    P[('about', 'location.html')] = ('오시는 길', '연구소 위치와 연락처.', location_page(d))
    P[('about', 'brochure.html')] = ('E-카다로그', '연구소 소개 책자를 PDF로 내려받을 수 있습니다.',
        brochure_page(d, 'ko'))
    return P


def sync_main_nav():
    """메인 페이지(index.html, en/index.html)의 GNB 를 생성된 것으로 교체.

    메인은 손으로 쓴 페이지지만 네비게이션만은 sitemap_def.py 를 따라야 하므로
    해당 블록만 정규식으로 갈아끼운다."""
    for path, depth, lang in [('index.html', 0, 'ko'),
                              (os.path.join('en', 'index.html'), 1, 'en')]:
        p = os.path.join(ROOT, path)
        s = open(p, encoding='utf-8').read()
        new = gnb(depth, None, lang)
        s2 = re.sub(r'<ul class="gnb">.*?</ul>\s*</nav>', new + '</nav>', s, flags=re.S)
        if s2 != s:
            open(p, 'w', encoding='utf-8').write(s2)
            print(f'  nav 갱신: {path}')


def main():
    # ── 한국어: /<section>/<file>   (depth 1)
    ko_spec = PAGES(1)
    n = 0
    for section in SECTIONS:
        key, label, en, d, kids = section
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
        for f, cl, _s in kids:
            item = ko_spec.get((key, f))
            if item is None:
                continue
            title, desc, body = item
            out = shell(title, desc, 1, section, f, body,
                        canonical=f'{d}/{f}', lang='ko',
                        alt_href=f'../en/{d}/{f}', alt_canonical=f'en/{d}/{f}')
            open(os.path.join(ROOT, d, f), 'w', encoding='utf-8').write(out)
            n += 1
    print(f'한국어 {n}개 페이지')

    # ── 영문: /en/<section>/<file>   (depth 2)
    en_spec = EN_PAGES(2)
    m = 0
    for section in EN_SECTIONS:
        key, label, en, d, kids = section
        os.makedirs(os.path.join(ROOT, 'en', d), exist_ok=True)
        for f, cl, _s in kids:
            item = en_spec.get((key, f))
            if item is None:
                continue
            title, desc, body = item
            out = shell(title, desc, 2, section, f, body,
                        canonical=f'en/{d}/{f}', lang='en',
                        alt_href=f'../../{d}/{f}', alt_canonical=f'{d}/{f}')
            open(os.path.join(ROOT, 'en', d, f), 'w', encoding='utf-8').write(out)
            m += 1
    print(f'영문 {m}개 페이지')

    sync_main_nav()


# ─────────────────────────────────────────────────────── 영문 페이지
REVIEW = ('<p class="todo-note">※ This page was translated from the Korean edition '
          'for this renewal and has not yet been reviewed by the Institute. '
          'The Korean page is authoritative.</p>')

SRC_KO = ('<p class="todo-note">※ The publications and records listed here are in Korean. '
          'Titles are shown as published.</p>')


EN_DETAIL = {'books_future': 'research/books', 'reports_future': 'research/reports',
             'contest_winners': 'research/contest', 'books_tj': 'tjpark-research/books',
             'reports_tj': 'tjpark-research/reports', 'forum': 'forum/forums',
             'seminar': 'forum/seminars', 'multimedia': 'forum/media',
             'news_notice': 'news/notices', 'news_press': 'news/press-items',
             'news_column': 'news/columns'}


def en_board(name, depth, style='cards'):
    # 상세 글은 한국어판 하나만 둔다. 내용 자체가 한국어라 영문 사본을 만들면
    # 같은 글이 두 벌 생기고 검색엔진에는 중복으로 잡힌다.
    # detail_base 는 사이트 루트 기준 경로다. render_board 가 rel(depth) 를
    # 앞에 붙이므로 여기서 '../' 를 더하면 한 단계 더 올라가 버린다.
    return render_board(name, depth, style,
                        detail_base=EN_DETAIL.get(name)) + SRC_KO


def EN_PAGES(depth):
    d = depth
    P = {}
    # ── Future Strategy Research
    P[('research', 'index.html')] = ('Background', 'Researching differentiated future strategies based on the TJ Park Spirit.',
        render_prose([b for b in blocks_of('en_research_bg') if len(b) > 30], [], d))
    P[('research', 'longterm.html')] = ('Long-term Agenda', 'Three lines of enquiry pursued over the long term.',
        longterm_page(d, 'en'))
    P[('research', 'themes.html')] = ('Annual Research Themes', 'Research themes selected each year.',
        '<div class="prose"><p class="lead">Each year the Institute selects a set of themes and '
        'commissions studies on them.</p><p>Recent cycles have addressed the arrival of artificial '
        'intelligence and its consequences for the brain and cognition, for biotechnology, and for the '
        'economy and society (2018–2020); and the philosophical, economic and social challenges posed by '
        'the COVID-19 pandemic (2019–2020).</p>'
        '<p class="todo-note">※ Detailed theme descriptions are available on the Korean page. '
        'An English edition is being prepared.</p></div>')
    P[('research', 'books.html')] = ('Research Series', 'The Future Strategy Research Series.',
        en_board('books_future', d))
    P[('research', 'reports.html')] = ('Research Reports', 'Papers, expert essays and survey reports.',
        en_board('reports_future', d))
    P[('research', 'contest.html')] = ('Student Essay Contest', 'Award-winning essays from the national student contest.',
        en_board('contest_winners', d))
    # ── TJ Park Research
    P[('tjpark', 'index.html')] = ('Background', 'Studying the spirit and leadership of Tae-Joon Park.',
        render_prose([b for b in blocks_of('en_tj_bg') if len(b) > 40], [], d))
    P[('tjpark', 'themes.html')] = ('Fields of Research', 'Programmes carried out under TJ Park Research.',
        render_prose([b for b in blocks_of('en_tj_fields') if 40 < len(b) < 1200], [], d))
    P[('tjpark', 'books.html')] = ('Research Series', 'The TJ Park Research Series and related books.',
        en_board('books_tj', d))
    P[('tjpark', 'reports.html')] = ('Research Reports', 'Reports from TJ Park Research.',
        en_board('reports_tj', d))
    # ── The Life of TJ Park
    P[('life', 'index.html')] = ('Biography', 'The life of Chungam Park Tae-Joon, period by period.',
        render_prose([b for b in blocks_of('en_life_bio') if len(b) > 120], [], d))
    P[('life', 'chronology.html')] = ('Chronology', 'A year-by-year chronology, 1927–2011.',
        render_prose([b for b in blocks_of('en_life_chron') if len(b) > 40], [], d)
        + '<div class="prose"><p class="todo-note">※ The full chronology is available on the Korean page. '
          'An English edition is being prepared.</p></div>')
    P[('life', 'statue.html')] = ('TJ Park Statue', 'The full-length statue and bust by Wu Weishan.',
        statue_page(d, 'en'))
    P[('life', 'who.html')] = ('Who is TJ Park', 'What his contemporaries said of him.',
        render_prose([b for b in blocks_of('en_life_who') if len(b) > 25], [], d))
    # ── Youth Programmes
    P[('youth', 'index.html')] = ('Student Essay Contest', 'A national essay contest for undergraduate and graduate students.',
        '<div class="prose"><p class="lead">The Institute runs a national essay contest for undergraduate '
        'and graduate students, inviting young people to set out their own view of the future.</p>'
        '<p>Winning essays are published in the Institute’s report series and, in several years, collected '
        'into a volume of the Future Strategy Research Series.</p>'
        '<p>Enquiries: <a href="mailto:tj-park@postech.ac.kr">tj-park@postech.ac.kr</a> · +82-54-279-0053~6</p>'
        + REVIEW + '</div>')
    P[('youth', 'winners.html')] = ('Award-winning Essays', 'Essays awarded in past contests.',
        en_board('contest_winners', d))
    P[('youth', 'camp.html')] = ('POSTECH Vision Camp', 'A camp where students design their own vision.',
        '<div class="prose"><p class="lead">The POSTECH Vision Camp gives students a few summer days to '
        'work out what they want their own future to look like.</p>' + REVIEW + '</div>')
    P[('youth', 'camp-guide.html')] = ('Camp Guide', 'How to take part in the Vision Camp.',
        '<div class="prose"><p class="lead">Programme details, eligibility and how to apply.</p>'
        '<p>Enquiries: <a href="mailto:tj-park@postech.ac.kr">tj-park@postech.ac.kr</a> · +82-54-279-0053~6</p>'
        '<p class="todo-note">※ Full details are on the Korean page. An English guide is being prepared.</p></div>')
    P[('youth', 'faq.html')] = ('FAQ', 'Frequently asked questions.',
        '<div class="prose"><p class="lead">Questions about the contest and the camp.</p>'
        '<p>Enquiries: <a href="mailto:tj-park@postech.ac.kr">tj-park@postech.ac.kr</a> · +82-54-279-0053~6</p>'
        '<p class="todo-note">※ No FAQ entries have been carried over yet.</p></div>')
    # ── Forums & Seminars
    P[('forum', 'index.html')] = ('Forums', 'Where experts and scholars debate the nation’s future.',
        en_board('forum', d))
    P[('forum', 'seminar.html')] = ('Seminars', 'Seminars held by the Institute.', en_board('seminar', d))
    P[('forum', 'multimedia.html')] = ('Multimedia', 'Video and media from forums and seminars.',
        en_board('multimedia', d))
    # ── News
    P[('news', 'index.html')] = ('Notices', 'Announcements from the Institute.', en_board('news_notice', d, 'rows'))
    P[('news', 'press.html')] = ('Press', 'The Institute in the press.', en_board('news_press', d, 'rows'))
    P[('news', 'column.html')] = ('TJ Columns', 'Future-strategy columns from the Institute.', en_board('news_column', d))
    # ── About
    # 구 영문 인사말은 전임 소장의 글에 현 소장 서명이 붙어 있어 그대로 쓸 수 없다.
    # 한국어 현행 인사말을 옮기고 검토 필요를 명시한다.
    P[('about', 'index.html')] = ('Greetings', 'A message from the Director.',
        '<div class="prose">'
        '<p class="lead">I am Minseok Song, Director of the POSTECH Tae-Joon Park Institute.</p>'
        '<p>The Institute was founded to carry forward the spirit of the late Chairman Tae-Joon Park and '
        'to realise the vision of POSTECH. Chairman Park held that industry and education are the core of '
        'national development. He founded POSCO and POSTECH, and led a renaissance in both the Korean '
        'economy and Korean scholarship.</p>'
        '<p>Believing that “education is the most important investment a nation can make in its future”, he '
        'insisted that practical scholarship and creative research must go together, and that the task of a '
        'university is to let students build the capacity to solve real problems rather than merely acquire '
        'knowledge.</p>'
        '<p>Inheriting that conviction, the Institute analyses the challenges that universities and society '
        'will face, and pursues two central goals: to formulate POSTECH’s medium- and long-term development '
        'strategy, and to study the spirit and leadership of Tae-Joon Park so that they may be taught to the '
        'next generation.</p>'
        '<p>Amid rapid change in science, technology and social structure, the Institute will set a strategic '
        'direction for POSTECH’s growth as a world-class university and open a path toward a sustainable future.</p>'
        '<p class="sign">Director, POSTECH Tae-Joon Park Institute <b>Minseok Song</b></p>' + REVIEW + '</div>'
        + greeting_photos(d, 'en'))
    P[('about', 'purpose.html')] = ('Founding Purpose', 'Why the Institute was founded.',
        render_prose([b for b in blocks_of('en_lab_purpose') if len(b) > 80], [], d))
    P[('about', 'mission.html')] = ('Mission', 'The mission of the TJ Park Institute.', mission_page(d, 'en'))
    P[('about', 'history.html')] = ('History', 'The Institute since its founding in 2013.',
        render_timeline(blocks_of('en_lab_history')))
    P[('about', 'logo.html')] = ('Our Logo', 'The meaning of the Institute’s logo.',
        render_prose([], imgs_of('lab_logo'), d)
        + '<div class="prose"><p class="todo-note">※ The explanation of the logo is on the Korean page. '
          'An English version is being prepared.</p></div>')
    P[('about', 'projects.html')] = ('Major Programmes', 'Key projects and the principles behind them.',
        projects_page(d, 'en'))
    P[('about', 'people.html')] = ('People', 'The research office and the research committee.',
        '<div class="prose">'
        '<p class="lead">A small permanent staff plans, manages and evaluates the work; the research itself '
        'is carried out with a network of scholars from across Korea.</p>'
        '<h2>Research Office</h2>'
        '<table class="tbl"><thead><tr><th scope="col">Name</th><th scope="col">Position</th>'
        '<th scope="col">Tel</th></tr></thead><tbody>'
        '<tr><th scope="row">Minseok Song</th><td>Director</td><td>+82-54-279-2387</td></tr>'
        '<tr><th scope="row">Ki-Jun Jeong</th><td>Research Associate Professor</td><td>+82-54-279-5631</td></tr>'
        '<tr><th scope="row">Tae-Heon Baek</th><td>Senior Researcher</td><td>+82-54-279-0057</td></tr>'
        '<tr><th scope="row">Bo-Mi Park</th><td>Researcher</td><td>+82-54-279-0054</td></tr>'
        '</tbody></table>'
        '<h2>Future Strategy Research Committee</h2>'
        '<p>The committee sets research policy and selects and plans the Institute’s projects. '
        'It is chaired by Professor Jin-Woo Lee (POSTECH) and draws its members from POSTECH, '
        'Seoul National University, Yonsei, Korea University, Sogang and other institutions.</p>'
        '<h2>TJ Park Future Strategy Academy</h2>'
        '<p>An association of professors and public intellectuals who take part in, or share the aims of, '
        'the Institute’s research. Around one hundred researchers from major Korean universities and '
        'research institutes are members.</p>'
        '<p class="todo-note">※ Names follow the previous website and need updating.</p></div>')
    P[('about', 'location.html')] = ('Location', 'How to find us.',
        '<div class="prose"><p class="lead">The Institute is on the 6th floor of the Tae-Joon Park Digital '
        'Library at POSTECH.</p>'
        '<table class="tbl"><tbody>'
        '<tr><th scope="row">Address</th><td>6F, Tae-Joon Park Digital Library, POSTECH<br>'
        '77 Cheongam-ro, Nam-gu, Pohang, Gyeongbuk 37673, Republic of Korea</td></tr>'
        '<tr><th scope="row">Tel</th><td>+82-54-279-0053~6</td></tr>'
        '<tr><th scope="row">Fax</th><td>+82-54-279-0059</td></tr>'
        '<tr><th scope="row">E-mail</th><td><a href="mailto:tj-park@postech.ac.kr">tj-park@postech.ac.kr</a></td></tr>'
        '</tbody></table><h2>Getting here</h2>'
        + ''.join(f'<p>{E(b)}</p>' for b in blocks_of('en_lab_location') if len(b) > 90)
        + '<p><a class="btn btn-p" href="https://map.kakao.com/?q=POSTECH" target="_blank" rel="noopener">Open in map</a></p></div>')
    P[('about', 'brochure.html')] = ('Brochure', 'Download the Institute’s brochure as a PDF.',
        brochure_page(d, 'en'))
    return P


# ─────────────────────────────────────────────────────── 개별 글 상세
# 게시판 → (섹션키, 목록파일, 상세 디렉터리, 목록 라벨)
BOARD_MAP = {
    'books_future':    ('research', 'books.html',   'research/books',            '연구총서'),
    'reports_future':  ('research', 'reports.html', 'research/reports',          '연구보고서'),
    'contest_winners': ('research', 'contest.html', 'research/contest',          '공모전 수상작'),
    'books_tj':        ('tjpark',   'books.html',   'tjpark-research/books',     '연구총서'),
    'reports_tj':      ('tjpark',   'reports.html', 'tjpark-research/reports',   '연구보고서'),
    'forum':           ('forum',    'index.html',   'forum/forums',              '포럼'),
    'seminar':         ('forum',    'seminar.html', 'forum/seminars',            '세미나'),
    'multimedia':      ('forum',    'multimedia.html', 'forum/media',            '멀티미디어'),
    'news_notice':     ('news',     'index.html',   'news/notices',              '공지사항'),
    'news_press':      ('news',     'press.html',   'news/press-items',          '보도자료'),
    'news_column':     ('news',     'column.html',  'news/columns',              'TJ미래전략 칼럼'),
}

META_LABEL = {'author': '저자', 'publisher': '출판사', 'published': '발간일',
              'posted': '등록일', 'date': '일자'}


# 옛 공지 본문에는 구 홈페이지 주소가 그대로 적혀 있다("자세히 보기: http://...").
# 구 사이트가 내려가면 그 주소는 죽는다. 문구를 지우면 공지의 기록이 훼손되므로,
# 같은 내용이 있는 새 주소로 바꿔 준다. (주소만 갈아끼우는 것이지 내용은 그대로다.)
LEGACY_URL = re.compile(r'https?://tjpark\.postech\.ac\.kr(/[0-9A-Za-z_./%-]*)?(?:\?[^\s"\'<]*)?')
LEGACY_MAP = [
    ('/08_youth/01', 'youth/index.html', '대학(원)생 공모전'),
    ('/08_youth/02', 'youth/camp.html', '포스텍 청년비전캠프'),
    ('/08_youth', 'youth/index.html', '청년사업'),
    ('/03_research/03_1', 'research/reports.html', '연구보고서'),
    ('/03_research/03', 'research/books.html', '연구총서'),
    ('/03_research/04', 'research/contest.html', '공모전 수상작'),
    ('/03_research', 'research/index.html', '미래전략연구'),
    ('/04_research_park', 'tjpark-research/index.html', '박태준연구'),
    ('/05_news/03', 'news/press.html', '보도자료'),
    ('/05_news/04', 'news/column.html', 'TJ미래전략 칼럼'),
    ('/05_news', 'news/index.html', '공지사항'),
    ('/09_forum', 'forum/index.html', '포럼 & 세미나'),
    ('/02_lab', 'about/index.html', '연구소소개'),
    ('/01_about', 'life/index.html', '박태준의 삶'),
]


def rewrite_legacy_urls(text, depth):
    """본문에 적힌 구 홈페이지 주소를 새 사이트의 같은 자리로 바꾼다.
    날것의 경로가 아니라 사람이 읽을 수 있는 링크로 만든다."""
    def sub(m):
        path = m.group(1) or '/'
        for old, new, label in LEGACY_MAP:
            if path.startswith(old):
                return f'<a href="{rel(depth)}{new}">{E(label)}</a>'
        return f'<a href="{rel(depth)}index.html">박태준미래전략연구소 홈페이지</a>'
    return LEGACY_URL.sub(sub, text)


def detail_body(d, depth, list_href, list_label, prev_item, next_item):
    """개별 글 본문. 원문 그대로 옮기되 출처를 밝힌다."""
    title = d.get('title') or d.get('list_title') or ''
    meta = d.get('meta') or {}
    order = ['author', 'publisher', 'published', 'posted', 'date']
    seen, bits = set(), []
    for k in order:
        v = meta.get(k)
        if not v or v in seen:
            continue
        seen.add(v)
        bits.append(f'<span><b>{E(META_LABEL.get(k, k))}</b> {E(v)}</span>')

    cover = ''
    if d.get('image_local'):
        cover = (f'<figure class="art-cover"><img src="{rel(depth)}{d["image_local"]}" '
                 f'alt="" loading="lazy"></figure>')

    secs = []
    for s in d.get('sections', []):
        h = f'<h2>{E(s["heading"])}</h2>' if s.get('heading') else ''
        ps = ''.join(f'<p>{rewrite_legacy_urls(E(p), depth)}</p>'
                     for p in s.get('paragraphs', []))
        secs.append(h + ps)

    # 본문에 딸린 이미지 중 내려받기에 성공한 것만 싣는다.
    # (외부 언론사 서버 링크는 HTTPS 에서 어차피 막히고 원본도 자주 사라진다.)
    gal = ''
    locals_ = [v for _k, v in sorted((d.get('images_local') or {}).items(), key=lambda x: int(x[0]))]
    locals_ = [v for v in locals_ if v != d.get('image_local')]
    if locals_:
        gal = ('<div class="art-gal">'
               + ''.join(f'<img src="{rel(depth)}{v}" alt="" loading="lazy">' for v in locals_)
               + '</div>')

    files = ''
    if d.get('files'):
        li = ''.join(f'<li><a href="{E(f["href"])}" target="_blank" rel="noopener">{E(f["name"])}</a></li>'
                     for f in d['files'])
        files = f'<div class="art-files"><h2>첨부</h2><ul>{li}</ul></div>'

    nav = []
    if prev_item:
        nav.append(f'<a class="pn prev" href="{prev_item[0]}"><span>이전 글</span>{E(prev_item[1])}</a>')
    if next_item:
        nav.append(f'<a class="pn next" href="{next_item[0]}"><span>다음 글</span>{E(next_item[1])}</a>')
    navhtml = f'<nav class="art-nav">{"".join(nav)}</nav>' if nav else ''

    # 구 홈페이지 '원문 보기' 링크는 두지 않는다.
    # 구 사이트가 곧 내려가므로 링크를 남기면 461개의 죽은 링크가 된다.
    # 원문 URL 은 data/legacy/detail_*.json 에 그대로 보관되어 있다.
    src = ''

    return f'''<article class="art">
  <header class="art-hd">
    {f'<p class="art-m">{"".join(bits)}</p>' if bits else ''}
  </header>
  {cover}
  <div class="prose art-body">{''.join(secs)}</div>
  {gal}
  {files}
  {src}
  {navhtml}
  <p class="art-back"><a class="btn btn-g" href="{list_href}">{E(list_label)} 목록으로</a></p>
</article>'''


def build_details():
    made = 0
    for board, (skey, lfile, ddir, llabel) in BOARD_MAP.items():
        items = load('detail_' + board) or []
        items = [d for d in items if d.get('idx') and d.get('sections')]
        if not items:
            continue
        section = next(s for s in SECTIONS if s[0] == skey)
        outdir = os.path.join(ROOT, *ddir.split('/'))
        os.makedirs(outdir, exist_ok=True)
        depth = len(ddir.split('/'))            # 예: research/books → 2
        list_href = f'{rel(depth)}{section[3]}/{lfile}'
        for i, d in enumerate(items):
            title = d.get('title') or d.get('list_title') or ''
            prev_item = next_item = None
            if i > 0:
                p = items[i - 1]
                prev_item = (f'{p["idx"]}.html', p.get('title') or p.get('list_title') or '')
            if i < len(items) - 1:
                nx = items[i + 1]
                next_item = (f'{nx["idx"]}.html', nx.get('title') or nx.get('list_title') or '')
            first = ''
            for s in d.get('sections', []):
                if s.get('paragraphs'):
                    first = s['paragraphs'][0][:150]
                    break
            body = detail_body(d, depth, list_href, llabel, prev_item, next_item)
            out = shell(title[:70] or llabel, first or title, depth, section, lfile, body,
                        canonical=f'{ddir}/{d["idx"]}.html', lang='ko',
                        article_title=title or llabel)
            open(os.path.join(outdir, f'{d["idx"]}.html'), 'w', encoding='utf-8').write(out)
            made += 1
    print(f'개별 글 {made}개 페이지')


# ────────────────────────────────── 이미지로만 있던 페이지의 텍스트판
#
# 구 사이트의 미션·주요사업·중장기 연구주제는 본문 전체가 이미지 한 장이었다.
# 이미지 속 글자는 검색도, 확대도, 스크린리더도, 번역도 되지 않는다.
# 아래 내용은 그 이미지를 그대로 옮겨 적은 것이다(문구를 바꾸지 않았다).

def _matrix(rows):
    out = ['<div class="matrix">']
    for tone, key, val in rows:
        out.append(f'<div class="mrow"><div class="mkey {tone}">{key}</div>'
                   f'<div class="mval">{val}</div></div>')
    out.append('</div>')
    return ''.join(out)


def _ul(items):
    return '<ul>' + ''.join(f'<li>{E(x)}</li>' for x in items) + '</ul>'


def mission_page(depth, lang='ko'):
    if lang == 'ko':
        return f'''<div class="mission">
  <p class="who">박태준미래전략연구소는</p>
  <p>인류와 국가의 더 나은 내일을 위하여<br>미래사회를 조망하고 대응전략을 연구하며,</p>
  <p class="hi">박태준 정신과 리더십을<br>체계적으로 탐구하고 사회에 전파한다.</p>
</div>
<div class="prose"><p class="todo-note">※ 이 문안은 구 홈페이지에서 이미지로 제작되어 있던 것을
텍스트로 옮긴 것입니다. 문구는 원본 그대로이며, 이제 검색·확대·스크린리더 이용이 가능합니다.</p></div>'''
    return f'''<div class="mission">
  <p class="who">The TJ Park Institute aims to</p>
  <p>provide new insights into the future society,<br>and to develop future strategies.</p>
  <p class="hi">It explores Tae-Joon Park’s spirit and his leadership systematically,<br>
  and shares those findings with society for the betterment of humanity<br>
  as well as the advancement of Korea.</p>
</div>
<div class="prose"><p class="todo-note">※ Transcribed from the image used on the previous website,
wording unchanged, so that it can now be searched, zoomed and read by screen readers.</p></div>'''


def projects_page(depth, lang='ko'):
    if lang == 'ko':
        grid = ('<div class="mgrid">'
                '<div><h3>미래전략연구</h3>' + _ul(['미래 조망과 대응전략 연구',
                                                '연구결과의 사회적 공유']) + '</div>'
                '<div><h3>박태준연구</h3>' + _ul(['리더십 교재개발',
                                               '박태준 학술연구']) + '</div></div>')
        rows = [('t1', '중점사업', grid),
                ('t2', '사업원칙', _ul([
                    '지식네트워크를 통한 미래조망과 대응전략 연구',
                    '박태준 창의 · 도전 · 사회공헌정신의 체계화 및 사회전파',
                    '사회적 수용성과 영향력이 큰 사업의 우선 수행']))]
        note = ('※ 구 홈페이지에서 이미지로 제작되어 있던 표를 텍스트로 옮긴 것입니다. '
                '문구는 원본 그대로입니다.')
        lead = '연구소가 힘을 싣는 사업과, 사업을 고를 때의 원칙입니다.'
    else:
        grid = ('<div class="mgrid">'
                '<div><h3>Future Strategy Research</h3>' + _ul([
                    'Researching future society',
                    'Prospects and strategies, and sharing results with society']) + '</div>'
                '<div><h3>TJ Park Research</h3>' + _ul([
                    'Developing leadership teaching materials',
                    'Conducting academic research on TJ Park']) + '</div></div>')
        rows = [('t1', 'Key Projects', grid),
                ('t2', 'Principles', _ul([
                    'Prospect and research through a knowledge network',
                    'Systematisation and spreading of TJ Park’s spirit — creativity, '
                    'challenge and social contribution',
                    'Priority on work with larger social influence and acceptance']))]
        note = ('※ Transcribed from the image used on the previous website, wording unchanged.')
        lead = 'Where the Institute concentrates its work, and how it chooses that work.'
    return (f'<div class="prose"><p class="lead">{E(lead)}</p></div>'
            + _matrix(rows)
            + f'<div class="prose"><p class="todo-note">{E(note)}</p></div>')


def longterm_page(depth, lang='ko'):
    if lang == 'ko':
        rows = [
            ('t1', '바람직한<br>미래사회의 모습', _ul([
                '국가 엘리트(지도자)는 어떻게 만들어지는가?',
                '21세기의 새로운 리더의 유형과 역할',
                '한국적 상황과 바람직한 리더십',
                '미래사회의 윤리',
                '일류(선진)사회의 모습과 그 실현 방안',
                '미래사회에 통용될 수 있는 한국적 가치의 발견'])),
            ('t2', '국가와 기업의<br>지속적 성장모델 탐구', _ul([
                '21세기의 일류국가의 조건은 무엇인가?',
                '국가 성장의 모멘텀과 리더십',
                '바람직한 국가와 기업의 지배구조',
                '한국 경제 근대화 성공모델의 글로벌 전파',
                '국가, 기업의 의사결정과정에서의 리스크 커뮤니케이션',
                '한국산업의 새로운 먹거리',
                '한국경제가 저성장 기조에 적응하기 위한 전략',
                '한국 기업이 ‘빠른 추종자’에서 ‘혁신 선도자’로 전환하기 위한 방안'])),
            ('t3', '동북아<br>공존공영의 길', _ul([
                '한반도 평화통일 준비 연구 : 북한의 개방체제 연착륙 방안',
                '동북아 3국의 바람직한 리더십',
                '한 · 중 · 일의 공존공영 방안'])),
        ]
        lead = '연구소가 중장기적으로 붙들고 있는 세 갈래 질문입니다.'
        note = ('※ 구 홈페이지에서 이미지로 제작되어 있던 표를 텍스트로 옮긴 것입니다. '
                '문구는 원본 그대로입니다.')
    else:
        rows = [
            ('t1', 'Desirable<br>future society', _ul([
                'How are the elite group (leaders) of a nation made?',
                'Types and roles of a new leadership in the 21st century',
                'The unique situation of Korea and the desirable leadership',
                'Ethics of the future society',
                'Depicting the first-class (developed) society and planning how to realise it',
                'Discovering Korean values applicable in the future society'])),
            ('t2', 'A sustainable<br>growth model for<br>nations and enterprises', _ul([
                'What are the conditions of a first-class nation in the 21st century?',
                'Creating momentum and leadership for another national growth',
                'Ideal governing structure of nations and companies',
                'Spreading Korea’s success model of modernisation throughout the world',
                'Risk communication in decision-making in nations and enterprises',
                'New growth engines in Korean industry',
                'Strategies for the Korean economy to adapt to low growth',
                'Ways Korean enterprises can switch from “fast follower” to “innovative leader”'])),
            ('t3', 'Northeast Asia’s path<br>toward coexistence<br>and prosperity', _ul([
                'Preparatory studies on the unification of the Korean peninsula: ways to help '
                'open up North Korea for a soft landing as a new system',
                'Desirable leadership of the three Northeast Asian nations: Korea, China and Japan',
                'Ways Korea, China and Japan can coexist and prosper'])),
        ]
        lead = 'Three lines of enquiry the Institute pursues over the long term.'
        note = '※ Transcribed from the image used on the previous website, wording unchanged.'
    return (f'<div class="prose"><p class="lead">{E(lead)}</p></div>'
            + _matrix(rows)
            + f'<div class="prose"><p class="todo-note">{E(note)}</p></div>')


def research_intro_page(depth):
    """미래전략연구 > 연구소개.

    구 사이트에서는 '연구소개 / 전문성 / 네트워킹' 세 소제목이 각각 작은
    글자 이미지였다. 본문 폭으로 늘리면 뭉개지고, 검색도 되지 않는다.
    같은 문단 구성을 유지하되 소제목을 진짜 제목으로 되살렸다.
    """
    b = blocks_of('research_intro')
    def pick(idx):
        return b[idx] if idx < len(b) else ''
    intro = [x for x in b[:2] if x]
    expert = [x for x in b[2:3] if x]
    network = [x for x in b[3:5] if x]
    out = ['<div class="prose">']
    out += [f'<p class="lead">{E(intro[0])}</p>' if intro else '']
    out += [f'<p>{E(x)}</p>' for x in intro[1:]]
    if expert:
        out.append('<h2>전문성</h2>')
        out += [f'<p>{E(x)}</p>' for x in expert]
    if network:
        out.append('<h2>네트워킹</h2>')
        out += [f'<p>{E(x)}</p>' for x in network]
    out.append('</div>')
    return ''.join(out)


def brochure_page(depth, lang='ko'):
    """E-카다로그.

    구 홈페이지에만 있던 소개 책자 PDF 두 종을 저장소로 옮겨 왔다.
    구 사이트가 내려가면 사라질 자료였다. 원본이 71MB / 50MB 여서
    웹에서 열기 어려웠던 것을 페이지 수와 화질을 유지한 채 재압축했다.
    """
    r = rel(depth)
    items = [
        ('tjpi-brochure-2022.pdf', '박태준미래전략연구소 브로슈어',
         'TJPI Brochure', '2022', '11쪽 · 1.5MB', '11 pages · 1.5 MB'),
        ('tjpi-pamphlet-2020.pdf', '박태준미래전략연구소 팸플릿',
         'TJPI Pamphlet', '2020', '11쪽 · 1.0MB', '11 pages · 1.0 MB'),
    ]
    if lang == 'ko':
        lead = '연구소 소개 책자입니다. 눌러서 바로 보거나 내려받을 수 있습니다.'
        note = ('※ 구 홈페이지에 있던 원본(각각 71MB, 50MB)을 그대로 옮기면 열기 어려워, '
                '쪽수와 내용을 유지한 채 웹에서 볼 수 있는 크기로 다시 압축했습니다.')
        verb = '보기 · 내려받기'
    else:
        lead = 'Introductory booklets. Open them in the browser or download.'
        note = ('※ The originals on the previous website were 71 MB and 50 MB. '
                'They have been recompressed for the web with all pages and content intact.')
        verb = 'View · download'
    cards = []
    for fn, ko_t, en_t, year, ko_m, en_m in items:
        title = ko_t if lang == 'ko' else en_t
        meta = f'{year} · ' + (ko_m if lang == 'ko' else en_m)
        cards.append(
            f'<li class="dl-item"><div><h3>{E(title)}</h3><p class="m">{E(meta)}</p></div>'
            f'<a class="btn btn-p" href="{r}assets/files/{fn}" target="_blank" '
            f'rel="noopener">{E(verb)}</a></li>')
    return (f'<div class="prose"><p class="lead">{E(lead)}</p></div>'
            f'<ul class="dl-list">{"".join(cards)}</ul>'
            f'<div class="prose"><p class="todo-note">{E(note)}</p></div>')


# ───────────────────────── CSS 배경으로만 있던 사진 ─────────────────────────
#
# 구 사이트는 사진 일부를 <img> 가 아니라 CSS background 로 깔았다.
# (예: .chungam1 { background:url(../01_about/img/img4.jpg) })
# 태그만 훑던 수집기가 그것을 통째로 놓쳐, 조각상 사진이 새 사이트에 없었다.
# 여러 장을 한 파일에 합쳐 두었기에 잘라서 각각 제자리에 넣는다.

def _photo(src, depth, cap, cls=''):
    c = f'<figcaption>{E(cap)}</figcaption>' if cap else ''
    k = f' class="{cls}"' if cls else ''
    return (f'<figure class="fig{" " + cls if cls else ""}">'
            f'<img src="{rel(depth)}{src}" alt="{E(cap)}" loading="lazy">{c}</figure>')


def statue_page(depth, lang='ko'):
    P = 'assets/img/legacy/'
    if lang == 'ko':
        body = [b for b in blocks_of('life_statue') if len(b) > 20]
        caps = ('노벨동산의 전신 조각상과 받침돌', '박태준학술정보관의 흉상',
                '받침돌 뒷면에 새긴 건립문')
        h2 = '건립문'
        lead_note = ''
    else:
        body = [b for b in blocks_of('en_life_statue') if len(b) > 60]
        caps = ('The full-length statue and its pedestal, Nobel Hill',
                'The bust, Tae-Joon Park Digital Library',
                'The dedication inscribed on the back of the pedestal')
        h2 = 'Dedication'
    lead = f'<p class="lead">{E(body[0])}</p>' if body else ''
    rest = ''.join(f'<p>{E(b)}</p>' for b in body[1:-1]) if len(body) > 2 else ''
    dedication = f'<h2>{h2}</h2><p>{E(body[-1])}</p>' if len(body) > 1 else ''
    return (f'<div class="prose">{lead}{rest}</div>'
            f'<div class="statue-grid">'
            + _photo(P + 'statue-full.jpg', depth, caps[0], 'tall')
            + _photo(P + 'statue-bust.jpg', depth, caps[1])
            + '</div>'
            f'<div class="prose">{dedication}</div>'
            + _photo(P + 'statue-plaque.jpg', depth, caps[2]))


def greeting_photos(depth, lang='ko'):
    P = 'assets/img/legacy/'
    caps = (('2010 포스코청암상 시상식', '연구소 행사')
            if lang == 'ko' else
            ('2010 POSCO TJ Park Prize ceremony', 'An Institute event'))
    return ('<div class="statue-grid">'
            + _photo(P + 'greeting-award-2010.jpg', depth, caps[0])
            + _photo(P + 'greeting-group.jpg', depth, caps[1])
            + '</div>')


if __name__ == '__main__':
    main()
    build_details()
