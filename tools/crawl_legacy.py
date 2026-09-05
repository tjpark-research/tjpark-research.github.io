#!/usr/bin/env python3
"""
구 사이트(tjpark.postech.ac.kr) 콘텐츠 수집기.

리뉴얼 작업용 일회성 도구가 아니라, 이관이 끝날 때까지 반복해서 돌릴 수 있게
만들어 두었다. 결과는 data/legacy/*.json 으로 떨어지고, 페이지 빌더가 그걸 읽는다.

    python3 tools/crawl_legacy.py            # 전체
    python3 tools/crawl_legacy.py boards     # 게시판만
    python3 tools/crawl_legacy.py pages      # 본문 페이지만
"""
import json, os, re, sys, time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE = 'http://tjpark.postech.ac.kr/'
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'legacy')
S = requests.Session()
S.headers['User-Agent'] = 'Mozilla/5.0 (TJPI site migration)'

# 구 사이트는 meta charset 에 euc-kr 이 남아 있지만 실제 바이트는 UTF-8 이다
# (템플릿 일부에만 옛 인코딩의 잔재가 섞여 있어 몇 글자가 깨진다).
# 따라서 무조건 UTF-8 로 읽고, 깨지는 글자만 버린다.
def soup(url):
    r = S.get(url, timeout=30)
    return BeautifulSoup(r.content.decode('utf-8', 'replace'), 'lxml')


def clean(s):
    return re.sub(r'[ \t\xa0]+', ' ', (s or '')).strip()


# ---------------------------------------------------------------- 본문 페이지
def body_text(url):
    """정적 본문 페이지에서 좌측 메뉴/공통 UI를 걷어내고 본문만 남긴다."""
    sp = soup(url)
    node = sp.select_one('#Contentbody') or sp.select_one('#cBody') or sp.body
    if node is None:
        return {'url': url, 'error': 'no body'}
    for sel in ('script', 'style', '#Board', '.lnb', '.snb'):
        for n in node.select(sel):
            n.decompose()
    # 요소의 '직접 텍스트'만 뽑는다.
    #
    # 단순히 "자식 블록태그가 있으면 컨테이너이므로 건너뛴다"고 하면 안 된다.
    # 구 사이트의 설립목적 페이지는 <dd> 안에 본문 전체가 <br> 로 이어져 있고
    # 그 끝에 날짜 <p> 하나가 들어 있다. 그 <p> 때문에 <dd> 전체가 컨테이너로
    # 오인되어 가장 중요한 글이 통째로 사라졌다.
    # 그래서 자식 블록태그의 텍스트는 빼고 그 요소가 직접 갖고 있는 텍스트만 취한다.
    # (자식 블록태그는 순회 과정에서 따로 잡힌다.)
    TAGS = ['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td', 'dt', 'dd', 'div']

    def own_text(el):
        parts = []
        for child in el.children:
            name = getattr(child, 'name', None)
            if name in TAGS:
                continue
            parts.append(child.get_text(' ') if name else str(child))
        return clean(' '.join(parts))

    blocks, seen = [], set()
    for el in node.find_all(TAGS):
        t = own_text(el)
        if len(t) < 2 or t in seen:
            continue
        if '//' in t:                       # 스크립트 잔재
            continue
        seen.add(t)
        blocks.append(t)

    # 중첩된 div 때문에 같은 글이 길이만 조금 다르게 두 번 잡히는 일이 있다.
    # 다만 '포함되면 무조건 버리기'는 위험하다 — 연보의 '1927년' 같은 짧은 항목이
    # 어딘가 긴 블록에 우연히 포함되어 통째로 사라진다.
    # 그래서 길이가 거의 같을 때(90% 이상)만 중복으로 본다.
    longest = sorted(blocks, key=len, reverse=True)
    kept = []
    for t in longest:
        if any(t in k and len(t) >= 0.9 * len(k) for k in kept):
            continue
        kept.append(t)
    keep = set(kept)
    blocks = [t for t in blocks if t in keep]

    imgs = [urljoin(url, i['src']) for i in node.find_all('img') if i.get('src')
            and '/images/common/' not in i['src']]
    return {'url': url, 'blocks': blocks, 'images': imgs}


# ------------------------------------------------------------------ 게시판
VIEW = re.compile(r'(?:pgMode|pg_mode)=View', re.I)


def detail(url, stub=None):
    """상세(View) 페이지에서 전체 제목과 본문을 가져온다.

    목록의 제목은 '..'/'...' 로 잘려 있다. 상세 페이지 본문(div.s_cont) 안에서
    잘린 제목을 접두사로 갖는 줄을 찾아 전체 제목을 복원한다.
    """
    try:
        sp = soup(url)
        scope = sp.select_one('.s_cont') or sp.select_one('#Board') or sp.body
        lines = [clean(x) for x in scope.get_text('\n').split('\n')]
        lines = [x for x in lines if x]

        title = None
        if stub:
            head = stub.rstrip('\ufffd.… ')[:12]
            cands = [x for x in lines if head and x.startswith(head)]
            if cands:
                title = max(cands, key=len)
        if not title:
            n = scope.select_one('.boardtit')
            title = clean(n.get_text(' ')) if n else None

        body = [x for x in lines if len(x) > 60 and x != title]
        return {'title': title, 'body': max(body, key=len) if body else None}
    except Exception:
        return {}


def board(path, bid=None, max_pages=40, details=False):
    """목록형 게시판을 마지막 페이지까지 훑는다.

    주의 1: 이 사이트의 페이지 번호는 **0부터** 시작한다 (`?page=0` 이 1페이지).
            1부터 세면 첫 페이지를 통째로 놓친다. 페이지 수는 .paging 위젯에서 읽는다.
    주의 2: 목록 행은 li.tit(제목) / li.day(저자·출판사·발간일) / li.cont(요약) 구조다.
            클래스가 없는 게시판을 위해 일반 텍스트 파싱으로 폴백한다.
    """
    def page_url(n):
        q = f'?page={n}&pgMode=List'
        if bid:
            q += f'&bid={bid}'
        return urljoin(BASE, path) + q

    first = soup(page_url(0))
    last = 0
    pg = first.select_one('.paging')
    if pg:
        nums = [int(m.group(1)) for a in pg.find_all('a')
                for m in [re.search(r'page=(\d+)', a.get('href', ''))] if m]
        if nums:
            last = min(max(nums), max_pages - 1)

    items, seen = [], set()
    for n in range(0, last + 1):
        sp = first if n == 0 else soup(page_url(n))
        scope = sp.select_one('#Board') or sp.select_one('#Contentbody') or sp.body
        if scope is None:
            break
        for a in scope.find_all('a', href=VIEW):
            m = re.search(r'idx=(\d+)', a.get('href', ''))
            idx = m.group(1) if m else None
            if idx and idx in seen:
                continue
            row = a.find_parent('tr') or a.find_parent('li') or a.parent
            if row is None:
                continue
            def pick(cls):
                n_ = row.select_one('li.' + cls) if hasattr(row, 'select_one') else None
                return clean(n_.get_text(' ')) if n_ else None
            td_left = row.select_one('td.left') if hasattr(row, 'select_one') else None
            title = pick('tit') or (clean(td_left.get_text(' ')) if td_left else None) \
                    or clean(a.get_text(' '))
            if title in ('', '자세히보기'):
                continue
            if idx:
                seen.add(idx)
            meta = pick('day') or clean(row.get_text(' '))
            g = lambda p: (lambda mm: clean(mm.group(1)) if mm else None)(re.search(p, meta))
            img = row.find('img')
            items.append({
                'idx': idx,
                'title': title.rstrip('\ufffd. …'),
                # 서버가 제목을 '바이트' 단위로 자르기 때문에 멀티바이트 글자가
                # 반토막 나서 U+FFFD 로 끝나는 경우가 많다. 이것도 잘린 것으로 본다.
                'truncated': bool(re.search(r'\.\.+$|…$|\ufffd', title)),
                'href': urljoin(page_url(n), a['href']),
                'image': urljoin(page_url(n), img['src']) if img and img.get('src')
                         and '/images/common/' not in img['src'] else None,
                'author': g(r'저자\s*:\s*(.+?)(?:,\s*출판사|,\s*발간일|,\s*발행일|$)'),
                'publisher': g(r'출판사\s*:\s*([^,]+)'),
                'date': g(r'(?:발간일|발행일|등록일)\s*:\s*([0-9./\-년월일 ]+)')
                        or (lambda mm: mm.group(1) if mm else None)(
                            re.search(r'(\d{4}[-.]\d{1,2}[-.]\d{1,2})', clean(row.get_text(' ')))),
                'summary': pick('cont'),
            })
        time.sleep(0.25)

    if details:
        for it in items:
            if it.get('truncated'):
                d = detail(it['href'], stub=it['title'])
                if d.get('title') and len(d['title']) > len(it['title']):
                    it['title'] = d['title']
                    it['truncated'] = False
                if d.get('body') and not it.get('summary'):
                    it['summary'] = d['body'][:600]
                time.sleep(0.2)
    return items


PAGES = {
    # 미래전략연구
    'research_intro':        '03_research/01.php',
    'research_longterm':     '03_research/02.php',
    'research_theme_18_20':  '03_research/02_1_4.php',
    'research_theme_17_18':  '03_research/02_1_3.php',
    'research_theme_16_17':  '03_research/02_1_1.php',
    'research_theme_15_16':  '03_research/02_1_2.php',
    'research_theme_14_15':  '03_research/02_1.php',
    # 박태준연구
    'tj_research_intro':     '04_research_park/01.php',
    'tj_research_theme':     '04_research_park/04.php',
    # 연구소소개
    'lab_greeting':          '02_lab/01.php',
    'lab_purpose':           '02_lab/02.php',
    'lab_mission':           '02_lab/02_1.php',
    'lab_history':           '02_lab/02_2.php',
    'lab_logo':              '02_lab/02_3.php',
    'lab_projects':          '02_lab/03.php',
    'lab_people':            '02_lab/04.php',
    'lab_location':          '02_lab/05.php',
    # 박태준의 삶
    'life_bio':              '01_about/01.php',
    'life_chronology':       '01_about/01_1.php',
    'life_statue':           '01_about/01_2.php',
    'life_who':              '01_about/03.php',
    # 박태준의 삶 — 생애/연보는 시대별 탭이 각각 별도 페이지다
    'life_bio_1': '01_about/01.php',
    'life_bio_2': '01_about/01_01.php',
    'life_bio_3': '01_about/01_02.php',
    'life_bio_4': '01_about/01_03.php',
    'life_bio_5': '01_about/01_04.php',
    'life_bio_6': '01_about/01_05.php',
    'life_chron_all': '01_about/01_1_6.php',
    # ── 구 영문 사이트 (eng_site). 분량이 적지만 '원문'이라 번역보다 우선한다.
    'en_lab_greeting':  'eng_site/02_lab/01.php',
    'en_lab_purpose':   'eng_site/02_lab/02.php',
    'en_lab_mission':   'eng_site/02_lab/02_1.php',
    'en_lab_history':   'eng_site/02_lab/02_2.php',
    'en_lab_fields':    'eng_site/02_lab/03.php',
    'en_lab_people':    'eng_site/02_lab/04.php',
    'en_lab_location':  'eng_site/02_lab/05.php',
    'en_research_bg':   'eng_site/03_research/01.php',
    'en_research_fields':'eng_site/03_research/02.php',
    'en_tj_bg':         'eng_site/04_research_park/01.php',
    'en_tj_fields':     'eng_site/04_research_park/04.php',
    'en_life_bio':      'eng_site/01_about/01.php',
    'en_life_chron':    'eng_site/01_about/01_1.php',
    'en_life_statue':   'eng_site/01_about/01_2.php',
    'en_life_who':      'eng_site/01_about/03.php',
    # 청년사업
    'youth_contest':         '08_youth/01.php',
    'youth_camp':            '08_youth/02.php',
    'youth_camp_guide':      '08_youth/02_2.php',
    'youth_faq':             '08_youth/04.php',
}

BOARDS = {
    'books_future':      ('03_research/03.php',       'future'),
    'reports_future':    ('03_research/03_1.php',     None),
    'contest_winners':   ('03_research/04.php',       None),
    'books_tj':          ('04_research_park/02.php',  'kor'),
    'reports_tj':        ('04_research_park/02_1.php', None),
    'news_notice':       ('05_news/01.php',           'notice'),
    'news_press':        ('05_news/03.php',           'etc'),
    'news_column':       ('05_news/04.php',           'tj_culumn'),
    'forum':             ('09_forum/01.php',          None),
    'seminar':           ('09_forum/02.php',          None),
    'multimedia':        ('09_forum/03.php',          None),
    # 박태준의 삶 › 쇳물은 멈추지 않는다 — 2004년 중앙일보 연재 회고. 게시판(bid=steel).
    'steel':             ('01_about/04.php',          'steel'),
    # 박태준의 삶 › 위대한 만남 · 박정희와 박태준 — 연재. 게시판(bid=meet).
    'meet':              ('01_about/06.php',          'meet'),
}


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    os.makedirs(OUT, exist_ok=True)

    if what in ('all', 'pages'):
        for name, path in PAGES.items():
            try:
                data = body_text(urljoin(BASE, path))
                json.dump(data, open(f'{OUT}/page_{name}.json', 'w'),
                          ensure_ascii=False, indent=1)
                print(f'page  {name:24s} blocks={len(data.get("blocks", []))} imgs={len(data.get("images", []))}')
            except Exception as e:
                print(f'page  {name:24s} FAIL {e}')

    only = sys.argv[2] if len(sys.argv) > 2 else None
    if what in ('all', 'boards'):
        for name, (path, bid) in BOARDS.items():
            if only and name != only:
                continue
            try:
                items = board(path, bid, details=True)
                json.dump(items, open(f'{OUT}/board_{name}.json', 'w'),
                          ensure_ascii=False, indent=1)
                print(f'board {name:24s} items={len(items)}')
            except Exception as e:
                print(f'board {name:24s} FAIL {e}')


if __name__ == '__main__':
    main()
