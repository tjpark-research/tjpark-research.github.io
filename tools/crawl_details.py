#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
게시판 개별 글의 상세(View) 페이지를 수집한다.

목록만 있고 개별 글 페이지가 없으면 방문자가 제목만 보고 끝난다.
data/legacy/board_*.json 의 각 항목 href 를 따라가 본문을 긁어
data/legacy/detail_<board>.json 으로 저장한다.

    python3 tools/crawl_details.py                # 전체 (오래 걸림)
    python3 tools/crawl_details.py books_future   # 게시판 하나만
    python3 tools/crawl_details.py --resume       # 아직 못 받은 것만

상세 페이지는 두 가지 마크업이 섞여 있다.
  (a) dl.semiTitle + dl.semiSummary  — 총서·보고서. 소제목이 있는 구조
  (b) 표 한 칸에 본문이 통째로       — 공지·보도자료
둘 다 처리하고, 결과는 [{heading, paragraphs}] 형태의 섹션 목록으로 통일한다.
"""
import json, os, re, sys, time
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(__file__))
from crawl_legacy import soup, clean, BASE

ROOT = os.path.join(os.path.dirname(__file__), '..')
LEGACY = os.path.join(ROOT, 'data', 'legacy')

SKIP_IMG = ('/images/common/', '/images/board/', '/images/main/',
            '/01_about/img/')   # 페이지 상단 배너(제목 이미지)
FILE_EXT = ('.pdf', '.hwp', '.hwpx', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')
NOISE = re.compile(r'^(목록|이전글|다음글|프린트|인쇄|첨부파일|조회수|등록일|작성자|글쓰기|수정|삭제)\s*[:：]?\s*$')


def split_paras(text):
    parts = [clean(p) for p in re.split(r'\n{1,}', text)]
    return [p for p in parts if len(p) > 1 and not NOISE.match(p)]


def table_to_rows(box):
    """상자 안의 표를 [[ROW|칸||칸]] 줄로 바꾼다.

    표를 그냥 글로 풀면 '인원 / 담당업무 / 지원자격 / 0명 …' 처럼 칸이 한
    줄씩 떨어져 무슨 표였는지 알 수 없게 된다. 줄 단위로 묶어 두면 빌더가
    그 자리에 표를 되살린다. dl 을 품은 표는 건드리지 않는다 — 그쪽은
    소제목이 있는 (a) 구조다.
    """
    for tbl in box.find_all('table'):
        if tbl.find('table') or tbl.find('dl'):
            continue
        # 사진 자리표시자가 든 표는 건드리지 않는다. 칸 안의 '|' 를 '/' 로
        # 바꾸는 통에 [[IMG|url|캡션]] 이 [[IMG/url/캡션]] 이 되어 사진이
        # 되살아나지 못한다. 사진이 든 표는 대개 자료표가 아니라 판짜기다.
        if '[[IMG|' in tbl.get_text(''):
            continue
        rows = []
        for tr in tbl.find_all('tr'):
            # 칸 안의 <br> 은 이미 개행으로 바뀌어 있다. 개행이 남으면
            # 자리표시자가 여러 문단으로 쪼개져 표로 되살아나지 못한다.
            cells = [clean(td.get_text('').replace('\n', ' '))
                     for td in tr.find_all(['th', 'td'])]
            if any(cells):
                # 칸 구분은 '||'. clean() 이 공백을 하나로 줄이므로 탭이나
                # 공백을 구분자로 쓰면 칸 경계가 사라진다.
                rows.append('||'.join(c.replace('|', '/') for c in cells))
        # 줄이 하나뿐이거나 칸이 하나뿐인 것은 자료표가 아니라 판짜기다.
        if len(rows) < 2 or not any('||' in r for r in rows):
            continue
        tbl.replace_with('\n' + '\n'.join(f'[[ROW|{r}]]' for r in rows) + '\n')
    return box


def extract(url):
    sp = soup(url)
    scope = sp.select_one('.s_cont') or sp.select_one('#Board') or sp.body
    if scope is None:
        return None

    for n in scope.select('script, style, .paging'):
        n.decompose()


    # 본문이 <br><br> 로만 문단을 나눈 글이 많다(에디터로 붙여 넣은 글).
    # get_text 는 <br> 을 빈 문자열로 흘려보내므로 문단이 통째로 붙어 버린다.
    for br in scope.find_all('br'):
        br.replace_with('\n')

    # 문단은 아래에서 get_text('') 로 뽑는다. get_text('\n') 을 쓰면 <span>,
    # <b>, <font> 같은 인라인 태그 경계마다 줄이 끊겨 "올해로 / 6 / 회째
    # 개최되는" 처럼 한 문장이 조각난다(구 에디터가 숫자·강조를 태그로
    # 감싸 놓았다). 그래서 줄바꿈은 <br> 과 아래의 블록 태그에서만 만든다.
    for blk in scope.find_all(['p', 'div', 'li', 'tr', 'dt', 'dd', 'td',
                               'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                               'blockquote', 'pre']):
        blk.append('\n')

    # 본문 사진은 <div class="center_img"><dl><dd><img></dd><dt>캡션</dt></dl></div>
    # 꼴로 글 중간에 놓여 있다. 사진을 그냥 걷어내면 캡션만 본문에 남아
    # 무엇을 설명하는 문장인지 알 수 없게 된다. 자리를 지킨 채 자리표시자로
    # 바꿔 두고, 빌더가 그 자리에 사진+캡션을 되살린다.
    inline = []
    for box in scope.select('div.center_img'):
        im = box.find('img')
        if im is None:
            box.decompose()
            continue
        src = urljoin(url, im.get('src') or '')
        dt = box.find('dt')
        cap = clean(dt.get_text(' ')) if dt else clean(im.get('alt') or '')
        inline.append(src)
        box.replace_with(f'\n[[IMG|{src}|{cap.replace("|", " ")}]]\n')

    # 초기 연재분은 center_img 없이 <dd><img></dd><dt>캡션</dt> 꼴이다.
    # 다행히 img 의 alt 에 같은 캡션이 들어 있으므로 그것을 쓰고,
    # 뒤따르는 <dt> 는 같은 문구가 두 번 나오지 않도록 지운다.
    for im in scope.select('img'):
        # SKIP_IMG 는 절대경로 기준이다. './img/txt2.jpg' 같은 상대경로를
        # 그대로 대조하면 배너가 걸러지지 않는다 — 먼저 URL 을 완성한다.
        src = urljoin(url, im.get('src') or '')
        if not src or any(k in src for k in SKIP_IMG):
            continue
        cap = clean(im.get('alt') or '')
        # <dd><img></dd><dt>캡션</dt> 꼴이면 dd 째로 자리표시자로 바꾼다.
        # 다만 dd 가 본문을 통째로 담고 있는 글도 있다(공모전 수상작은
        # '내 용' dd 하나에 에세이 전문이 들어 있고 그 안에 사진이 섞여
        # 있다). 그런 dd 를 바꿔 버리면 본문 2만 자가 사진 한 장으로
        # 사라진다. 사진만 든 짧은 dd 일 때만 dd 를 쓴다.
        holder = im
        dd = im.find_parent('dd')
        if dd is not None and len(dd.find_all('img')) == 1 \
                and len(clean(dd.get_text(' '))) < 120:
            holder = dd
        nxt = holder.find_next_sibling('dt')
        if nxt is not None:
            dt_text = clean(nxt.get_text(' '))
            if not cap:
                cap = dt_text
            if dt_text and dt_text == cap:
                nxt.decompose()
        if holder.parent is None:
            continue          # 이미 떨어져 나간 노드는 바꿀 수 없다
        inline.append(src)
        holder.replace_with(f'\n[[IMG|{src}|{cap.replace("|", " ")}]]\n')

    out = {'url': url, 'title': None, 'meta': {}, 'sections': [],
           'images': [], 'files': []}

    # ── 제목
    t = scope.select_one('dl.semiTitle dt') or scope.select_one('.boardtit')
    if t:
        out['title'] = clean(t.get_text(' '))

    # ── 메타 (저자 / 출판사 / 발간일 / 등록일 / 조회수)
    whole = clean(scope.get_text(' '))
    for label, key in [('저자', 'author'), ('출판사', 'publisher'),
                       ('발간일', 'published'), ('발행일', 'published'),
                       ('등록일', 'posted')]:
        m = re.search(label + r'\s*[:：]\s*([^|\n]{1,80}?)(?=\s{2,}|\s*(?:저자|출판사|발간일|발행일|등록일|조회|$))', whole)
        if m and key not in out['meta']:
            v = clean(m.group(1))
            if v:
                out['meta'][key] = v

    # ── (a) 소제목이 있는 구조
    for dl in scope.select('dl.semiSummary'):
        dt = dl.find('dt')
        dd = dl.find('dd')
        if dd is None:
            continue
        # 소제목이 있는 구조에도 표가 들어간다(포럼 프로그램표 따위).
        # 표를 그냥 풀면 '구분 / 시간 / 세부내용 / 1부 / 15:00~15:05 …'
        # 처럼 칸이 한 줄씩 떨어져 시간표를 읽을 수 없다.
        paras = split_paras(table_to_rows(dd).get_text(''))
        if paras:
            out['sections'].append({'heading': clean(dt.get_text(' ')) if dt else None,
                                    'paragraphs': paras})

    # ── (b) 표 한 칸에 본문이 들어 있는 구조
    if not out['sections']:
        # 구 CMS 는 본문을 td.contentbox 에 담는다. 이것을 먼저 쓴다.
        # '표를 품지 않은 가장 큰 칸' 만 찾으면, 본문이 표로 짜인 글(채용
        # 공고·전형 일정 따위)에서 안쪽 칸 하나만 건져 올려 본문 대부분을
        # 잃는다. 실제로 993 채용공고가 여섯 줄로 줄어 있었다.
        #
        # 표를 자리표시자로 바꾸는 일은 반드시 여기서 — 쓸 상자를 정한
        # 뒤에 — 한다. 위에서 미리 바꾸면 dl.semiSummary 구조((a) 분기)를
        # 품은 표까지 헐어 버려 포럼·세미나 본문이 통째로 날아간다.
        box = scope.select_one('td.contentbox') or scope.select_one('.contentbox')
        best, best_len = None, 0
        if box is not None and len(clean(box.get_text(''))) >= 40:
            best = table_to_rows(box).get_text('')
            best_len = len(clean(best))
        if best_len < 40:
            for cell in scope.select('td, div'):
                if cell.find(['td', 'table']):
                    continue
                txt = cell.get_text('')
                if len(clean(txt)) > best_len:
                    best, best_len = txt, len(clean(txt))
        if best and best_len > 40:
            paras = split_paras(best)
            # 제목이 본문 첫 줄로 다시 들어오는 경우 제거
            if paras and out['title'] and paras[0].startswith(out['title'][:12]):
                paras = paras[1:]
            if paras:
                out['sections'].append({'heading': None, 'paragraphs': paras})

    # 제목을 못 찾았으면 본문 앞에서 유추하지 않고 비워 둔다(목록 제목을 쓴다)
    out['images'].extend(inline)
    for im in scope.select('img'):
        u = urljoin(url, im.get('src') or '')
        if u and not any(k in u for k in SKIP_IMG) and u not in out['images']:
            out['images'].append(u)
    for a in scope.select('a[href]'):
        h = a.get('href') or ''
        # 구 CMS 의 첨부 링크는 '../02_board/fileDown.php?idx=820' 꼴이다.
        # 'download' 만 찾으면 'fileDown' 이 걸리지 않아 첨부가 통째로
        # 빠진다(실제로 공지·보도자료의 첨부가 전부 누락되어 있었다).
        if (h.lower().endswith(FILE_EXT) or 'download' in h.lower()
                or 'filedown' in h.lower()):
            # 첨부 링크의 이름이 이미지 버튼인 경우가 있다. 위에서 이미지를
            # 자리표시자로 바꿔 두었으므로 그 표시자가 이름에 섞이지 않게 한다.
            nm = clean(a.get_text(' '))
            nm = re.sub(r'\[\[IMG\|[^|]*\|([^\]]*)\]\]', r'\1', nm).strip()
            out['files'].append({'href': urljoin(url, h),
                                 'name': nm or os.path.basename(h)})
    return out


def run(board, resume=False):
    src = os.path.join(LEGACY, f'board_{board}.json')
    if not os.path.exists(src):
        print(f'  board_{board}.json 없음'); return
    items = json.load(open(src))
    dst = os.path.join(LEGACY, f'detail_{board}.json')
    have = {}
    if resume and os.path.exists(dst):
        have = {d['idx']: d for d in json.load(open(dst)) if d.get('idx')}

    out, done, failed = [], 0, 0
    for it in items:
        idx = it.get('idx')
        if idx and idx in have:
            out.append(have[idx]); continue
        try:
            d = extract(it['href']) or {}
            d['idx'] = idx
            d['list_title'] = it.get('title')
            d['image_local'] = it.get('local')
            for k in ('author', 'publisher', 'date'):
                if it.get(k) and k not in d.get('meta', {}):
                    d.setdefault('meta', {})[k] = it[k]
            out.append(d); done += 1
            time.sleep(0.15)
        except Exception as e:
            failed += 1
            out.append({'idx': idx, 'list_title': it.get('title'),
                        'url': it.get('href'), 'error': str(e)[:80]})
        # 중간 저장. 오래 걸리는 게시판은 중간에 끊길 수 있는데, 끝에서만
        # 저장하면 그때까지 받은 것이 통째로 날아가고 처음부터 다시 받아야
        # 한다. --resume 이 이어받을 수 있도록 스무 건마다 적어 둔다.
        if done and done % 20 == 0:
            json.dump(out, open(dst, 'w'), ensure_ascii=False, indent=1)
    json.dump(out, open(dst, 'w'), ensure_ascii=False, indent=1)
    withbody = sum(1 for d in out if d.get('sections'))
    print(f'{board:18s} {len(out):4d}건 (신규 {done}, 실패 {failed}, 본문있음 {withbody})')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    resume = '--resume' in sys.argv
    boards = args or [f[6:-5] for f in sorted(os.listdir(LEGACY))
                      if f.startswith('board_') and f.endswith('.json')]
    for b in boards:
        run(b, resume)


if __name__ == '__main__':
    main()
