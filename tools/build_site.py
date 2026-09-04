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
from sitemap_def import SECTIONS, ALL_LABELS

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
        t = re.sub(r'\s+', ' ', b).strip()
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


def imgs_of(page_key):
    d = load('page_' + page_key) or {}
    loc = d.get('images_local', {})
    return [loc[k] for k in sorted(loc, key=int)] if loc else []


# ─────────────────────────────────────────────────────────── 공통 조각
def rel(depth):
    return '../' * depth


def gnb(depth, active=None):
    li = []
    for key, label, _en, d, kids in SECTIONS:
        sub = ''.join(
            f'<a href="{rel(depth)}{d}/{f}">{E(cl)}</a>' for f, cl, _s in kids)
        cls = ' class="on"' if key == active else ''
        li.append(
            f'<li{cls}><a href="{rel(depth)}{d}/index.html">{E(label)}</a>'
            f'<div class="mega">{sub}</div></li>')
    return '<ul class="gnb">' + ''.join(li) + '</ul>'


def header(depth, active=None):
    r = rel(depth)
    return f'''<div class="util">
  <div class="wrap">
    <select aria-label="관련 사이트" onchange="if(this.value)window.open(this.value)">
      <option value="">관련사이트</option>
      <option value="https://www.postech.ac.kr/">포항공과대학교</option>
      <option value="https://www.posco.co.kr/">포스코</option>
      <option value="https://www.postf.org/">포스코청암재단</option>
      <option value="http://museum.posco.co.kr/">포스코박물관</option>
    </select>
    <span class="lang"><a href="{r}index.html" class="on">KOR</a><span>|</span><a href="{r}en/index.html">ENG</a></span>
  </div>
</div>
<header class="hd">
  <div class="wrap">
    <a class="brand" href="{r}index.html">
      <span class="mark">tjpi</span>
      <span class="txt"><b>POSTECH</b><span>박태준미래전략연구소</span></span>
    </a>
    <nav aria-label="주 메뉴">{gnb(depth, active)}</nav>
    <button class="burger" aria-label="메뉴 열기"><span></span></button>
  </div>
</header>'''


def footer(depth):
    r = rel(depth)
    links = ''.join(
        f'<li><a href="{r}{d}/index.html">{E(l)}</a></li>'
        for _k, l, _e, d, _c in SECTIONS)
    return f'''<footer class="ft">
  <div class="wrap">
    <div class="ft-top">
      <div class="brand"><span class="mark">tjpi</span>
        <span class="txt"><b>POSTECH</b><span>박태준미래전략연구소</span></span></div>
      <ul class="ft-links">{links}
        <li><a href="https://www.postech.ac.kr/kor/usage-guide/privacy_policy.do" target="_blank" rel="noopener">개인정보처리방침</a></li>
      </ul>
    </div>
    <div class="ft-bot">
      <address>
        경상북도 포항시 남구 청암로 77 포항공과대학교 박태준학술정보관 6층<br>
        TEL 054-279-0053~6 &nbsp;·&nbsp; FAX 054-279-0059 &nbsp;·&nbsp; E-mail tj-park@postech.ac.kr
        <span class="cr" style="display:block;margin-top:14px">© POSTECH Tae-Joon Park Institute for Future Strategy. All rights reserved.</span>
      </address>
      <ul class="ft-rel">
        <li><a href="https://www.postech.ac.kr/" target="_blank" rel="noopener">포항공과대학교</a></li>
        <li><a href="https://www.posco.co.kr/" target="_blank" rel="noopener">포스코</a></li>
        <li><a href="https://www.postf.org/" target="_blank" rel="noopener">포스코청암재단</a></li>
        <li><a href="http://museum.posco.co.kr/" target="_blank" rel="noopener">포스코박물관</a></li>
      </ul>
    </div>
  </div>
</footer>'''


def lnb(section, current_file, depth):
    key, label, en, d, kids = section
    parts = []
    for f, cl, _s in kids:
        on = ' class="on"' if f == current_file else ''
        parts.append(f'<li{on}><a href="{rel(depth)}{d}/{f}">{E(cl)}</a></li>')
    items = ''.join(parts)
    return f'<nav class="lnb" aria-label="{E(label)} 하위 메뉴"><p class="lnb-t">{E(label)}<span>{E(en)}</span></p><ul>{items}</ul></nav>'


def shell(title, desc, depth, section, current_file, body, canonical):
    key, label, en, d, kids = section
    cur_label = next((cl for f, cl, _s in kids if f == current_file), label)
    r = rel(depth)
    crumb = (f'<a href="{r}index.html">HOME</a><span>›</span>'
             f'<a href="{r}{d}/index.html">{E(label)}</a><span>›</span><em>{E(cur_label)}</em>')
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — POSTECH 박태준미래전략연구소</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="https://tjpark-research.github.io/{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="POSTECH 박태준미래전략연구소">
<meta property="og:title" content="{E(title)} — POSTECH 박태준미래전략연구소">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="https://tjpark-research.github.io/{canonical}">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">본문 바로가기</a>
{header(depth, key)}
<div class="sub-hero">
  <div class="wrap">
    <p class="eyebrow">{E(en)}</p>
    <h1>{E(cur_label)}</h1>
    <p class="crumb">{crumb}</p>
  </div>
</div>
<div class="sub-wrap wrap">
  {lnb(section, current_file, depth)}
  <main id="main" class="sub-main">
{body}
  </main>
</div>
{footer(depth)}
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


def render_board(name, depth, style='cards', empty='등록된 자료가 없습니다.'):
    items = load('board_' + name) or []
    if not items:
        return f'<div class="prose"><p>{E(empty)}</p></div>'
    cards = []
    for it in items:
        t = it.get('title') or ''
        meta = ' · '.join(x for x in [it.get('author'), it.get('publisher'), it.get('date')] if x)
        summ = (it.get('summary') or '')[:150]
        key = E((t + ' ' + (it.get('author') or '')).lower())
        if style == 'cards':
            img = (f'<img src="{rel(depth)}{it["local"]}" alt="" loading="lazy">'
                   if it.get('local') else '<span class="noimg">TJPI</span>')
            cards.append(
                f'<li class="bcard" data-k="{key}"><div class="bcard-cov">{img}</div>'
                f'<div class="bcard-b"><h3>{E(t)}</h3>'
                + (f'<p class="m">{E(meta)}</p>' if meta else '')
                + (f'<p class="s">{E(summ)}</p>' if summ else '')
                + '</div></li>')
        else:
            cards.append(
                f'<li class="brow" data-k="{key}"><span class="tt">{E(t)}</span>'
                f'<span class="dt">{E(it.get("date") or "")}</span></li>')
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
        render_prose(blocks_of('research_intro'), imgs_of('research_intro'), d))
    P[('research', 'longterm.html')] = ('중장기 연구주제', '연구소가 설정한 중장기 연구 방향입니다.',
        render_image_page(imgs_of('research_longterm'), d, '연구소의 중장기 연구 방향입니다.'))
    P[('research', 'themes.html')] = ('연도별 연구주제', '연도별로 선정한 미래전략 연구주제와 세부 과제입니다.',
        render_eras([('2018~2020', 'research_theme_18_20'), ('2017~2018', 'research_theme_17_18'),
                     ('2016~2017', 'research_theme_16_17'), ('2015~2016', 'research_theme_15_16'),
                     ('2014~2015', 'research_theme_14_15')], d))
    P[('research', 'books.html')] = ('연구총서', '미래전략연구총서 — 미래 핵심 의제에 대한 학제적 연구 성과.',
        render_board('books_future', d, 'cards'))
    P[('research', 'reports.html')] = ('연구보고서', '연구논문·전문가 에세이·여론조사 보고서.',
        render_board('reports_future', d, 'cards'))
    P[('research', 'contest.html')] = ('대학(원)생 공모전 수상작', '전국 대학생·대학원생 에세이 공모전 수상작.',
        render_board('contest_winners', d, 'cards'))
    # ── 박태준연구
    P[('tjpark', 'index.html')] = ('연구소개', '박태준의 정신과 리더십을 체계적으로 연구하고 사회적 자산으로 전파합니다.',
        render_prose(blocks_of('tj_research_intro'), imgs_of('tj_research_intro'), d))
    P[('tjpark', 'themes.html')] = ('연구분야', '박태준연구의 연도별 주제입니다.',
        render_prose(blocks_of('tj_research_theme'), imgs_of('tj_research_theme'), d))
    P[('tjpark', 'books.html')] = ('연구총서', '박태준 연구총서와 관련 단행본.',
        render_board('books_tj', d, 'cards'))
    P[('tjpark', 'reports.html')] = ('연구보고서', '박태준연구 보고서.',
        render_board('reports_tj', d, 'cards'))
    # ── 박태준의 삶
    P[('life', 'index.html')] = ('생애', '청암 박태준이 걸어온 길을 시대별로 살펴봅니다.',
        render_eras([('1927~1947', 'life_bio_1'), ('1948~1960', 'life_bio_2'),
                     ('1961~1967', 'life_bio_3'), ('1968~1992', 'life_bio_4'),
                     ('1993~2000', 'life_bio_5'), ('2001~2011', 'life_bio_6')], d))
    P[('life', 'chronology.html')] = ('연보', '1927년부터 2011년까지의 연보.',
        render_timeline(blocks_of('life_chron_all')))
    P[('life', 'statue.html')] = ('청암 조각상', '청암 박태준 조각상.',
        render_prose([b for b in blocks_of('life_statue') if len(b) > 20], imgs_of('life_statue'), d))
    P[('life', 'who.html')] = ('박태준을 말한다', '동시대인이 남긴 박태준에 대한 기록.',
        render_prose([b for b in blocks_of('life_who') if len(b) > 25], imgs_of('life_who'), d))
    # ── 청년사업
    P[('youth', 'index.html')] = ('대학(원)생 공모전', '전국 대학생·대학원생을 대상으로 한 에세이 공모전.',
        render_prose(blocks_of('youth_contest'), imgs_of('youth_contest'), d))
    P[('youth', 'winners.html')] = ('수상작 보기', '역대 공모전 수상작.',
        render_board('contest_winners', d, 'cards'))
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
        render_board('forum', d, 'cards'))
    P[('forum', 'seminar.html')] = ('세미나', '연구소가 개최한 세미나.',
        render_board('seminar', d, 'cards'))
    P[('forum', 'multimedia.html')] = ('멀티미디어', '포럼·세미나 영상과 미디어 자료.',
        render_board('multimedia', d, 'cards'))
    # ── 연구소소식
    P[('news', 'index.html')] = ('공지사항', '연구소 공지사항.', render_board('news_notice', d, 'rows'))
    P[('news', 'press.html')] = ('보도자료', '언론에 보도된 연구소 소식.', render_board('news_press', d, 'rows'))
    P[('news', 'column.html')] = ('TJ미래전략 칼럼', '연구소가 전하는 미래전략 칼럼.', render_board('news_column', d, 'cards'))
    # ── 연구소소개
    P[('about', 'index.html')] = ('인사말', '박태준미래전략연구소 소장 인사말.',
        render_prose(blocks_of('lab_greeting'), [], d))
    P[('about', 'purpose.html')] = ('설립목적', '연구소 설립의 취지.',
        render_prose(blocks_of('lab_purpose'), [], d))
    P[('about', 'mission.html')] = ('미션', '연구소의 미션.',
        render_image_page(imgs_of('lab_mission'), d, '연구소의 미션입니다.'))
    P[('about', 'history.html')] = ('연혁', '2013년 개소 이후의 연혁.',
        render_timeline(blocks_of('lab_history')))
    P[('about', 'logo.html')] = ('로고 소개', '연구소 로고의 의미.',
        render_prose([b for b in blocks_of('lab_logo') if len(b) > 15], imgs_of('lab_logo'), d))
    P[('about', 'projects.html')] = ('주요사업', '연구소의 주요 사업.',
        render_image_page(imgs_of('lab_projects'), d, '연구소가 수행하는 주요 사업입니다.'))
    P[('about', 'people.html')] = ('연구소사람들', '연구기획실과 연구위원회 구성.', people_page(d))
    P[('about', 'location.html')] = ('오시는 길', '연구소 위치와 연락처.', location_page(d))
    return P


def sync_main_nav():
    """메인 페이지(index.html, en/index.html)의 GNB·푸터 링크를 생성된 것으로 교체.

    메인은 손으로 쓴 페이지지만 네비게이션만은 sitemap_def.py 를 따라야 하므로
    해당 블록만 정규식으로 갈아끼운다."""
    # 영문 하위 페이지가 아직 없으므로 en/index.html 은 건드리지 않는다.
    # (한글 라벨이 영문 페이지에 주입되는 것을 막기 위함)
    for path, depth in [('index.html', 0)]:
        p = os.path.join(ROOT, path)
        s = open(p, encoding='utf-8').read()
        new = gnb(depth)
        s2 = re.sub(r'<ul class="gnb">.*?</ul>\s*</nav>', new + '</nav>', s, flags=re.S)
        if s2 != s:
            open(p, 'w', encoding='utf-8').write(s2)
            print(f'  nav 갱신: {path}')


def main():
    n = 0
    for section in SECTIONS:
        key, label, en, d, kids = section
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
        spec = PAGES(1)
        for f, cl, _s in kids:
            item = spec.get((key, f))
            if item is None:
                continue
            title, desc, body = item
            html_out = shell(title, desc, 1, section, f, body, f'{d}/{f}')
            open(os.path.join(ROOT, d, f), 'w', encoding='utf-8').write(html_out)
            n += 1
    print(f'{n}개 페이지 생성')
    sync_main_nav()


if __name__ == '__main__':
    main()
