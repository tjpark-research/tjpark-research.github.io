# -*- coding: utf-8 -*-
"""
사이트 구조 정의 — 이 파일이 네비게이션의 유일한 원본이다.

구 사이트의 메뉴 체계를 계승하되 두 가지를 바꿨다.
1. `박태준의 삶`을 최상위 메뉴로 승격 (구 영문 사이트에서는 이미 최상위였고,
   연구소 정체성의 핵심이라 하위에 묻어둘 이유가 없다).
2. URL 을 .php 쿼리스트링에서 의미가 드러나는 경로로 바꿨다.
   예) 03_research/03.php?bid=future  →  /research/books.html
"""

# (섹션키, 라벨, 영문라벨, 디렉터리, [(파일, 라벨, 페이지스펙키), ...])
SECTIONS = [
    ('research', '미래전략연구', 'Future Strategy Research', 'research', [
        ('index.html',    '연구소개',            'research_intro'),
        ('longterm.html', '중장기 연구주제',      'research_longterm'),
        ('themes.html',   '연도별 연구주제',      'research_themes'),
        ('books.html',    '연구총서',            'research_books'),
        ('reports.html',  '연구보고서',          'research_reports'),
        ('contest.html',  '대학(원)생 공모전 수상작', 'research_contest'),
    ]),
    ('tjpark', '박태준연구', 'TJ Park Research', 'tjpark-research', [
        ('index.html',   '연구소개',   'tj_intro'),
        ('themes.html',  '연구분야',   'tj_themes'),
        ('books.html',   '연구총서',   'tj_books'),
        ('reports.html', '연구보고서', 'tj_reports'),
    ]),
    ('life', '박태준의 삶', 'The Life of TJ Park', 'life', [
        ('index.html',      '생애',        'life_bio'),
        ('chronology.html', '연보',        'life_chronology'),
        ('statue.html',     '청암 조각상',  'life_statue'),
        ('who.html',        '박태준을 말한다', 'life_who'),
    ]),
    ('youth', '청년사업', 'Youth Programs', 'youth', [
        ('index.html',     '대학(원)생 공모전', 'youth_contest'),
        ('winners.html',   '수상작 보기',      'youth_winners'),
        ('camp.html',      '포스텍 청년비전캠프', 'youth_camp'),
        ('camp-guide.html','캠프 안내',        'youth_camp_guide'),
        ('faq.html',       'FAQ',            'youth_faq'),
    ]),
    ('forum', '포럼 & 세미나', 'Forums & Seminars', 'forum', [
        ('index.html',      '포럼',      'forum_forum'),
        ('seminar.html',    '세미나',    'forum_seminar'),
        ('multimedia.html', '멀티미디어', 'forum_multimedia'),
    ]),
    ('news', '연구소소식', 'News', 'news', [
        ('index.html',   '공지사항',        'news_notice'),
        ('press.html',   '보도자료',        'news_press'),
        ('column.html',  'TJ미래전략 칼럼',  'news_column'),
    ]),
    ('about', '연구소소개', 'About the Institute', 'about', [
        ('index.html',     '인사말',       'lab_greeting'),
        ('purpose.html',   '설립목적',     'lab_purpose'),
        ('mission.html',   '미션',        'lab_mission'),
        ('history.html',   '연혁',        'lab_history'),
        ('logo.html',      '로고 소개',    'lab_logo'),
        ('projects.html',  '주요사업',     'lab_projects'),
        ('people.html',    '연구소사람들',  'lab_people'),
        ('location.html',  '오시는 길',    'lab_location'),
    ]),
]

# 좌측 메뉴에서 걸러낼 라벨 (본문 추출 시 메뉴 텍스트가 섞여 들어오는 것을 제거)
ALL_LABELS = set()
for _k, _l, _e, _d, _kids in SECTIONS:
    ALL_LABELS.add(_l)
    for _f, _cl, _s in _kids:
        ALL_LABELS.add(_cl)
ALL_LABELS |= {
    '연구소개', '연구분야', '연구결과물', '연구총서', '연구보고서', '연구논문',
    '전문가에세이', '여론조사 보고서', '중장기 연구주제', '연도별 주제',
    '대학(원)생 공모전 수상작', '설립목적', '미션', '연혁', '로고소개', '주요사업',
    '연구소사람들', '오시는 길', '오시는길', '참여마당', '발전기금', 'E-카다로그',
    '인사말', '걸어온길', '생애', '연보', '청암조각상', '멀티미디어', '영상',
    '언론자료', '박태준을 말한다', '쇳물은 멈추지않는다', '박태준 어록 DB',
    '위대한 만남 - 박정희와 박태준', '공모전소개', '수상작 보기', '수상후기',
    '캠프소개', '캠프안내', '캠프후기', '갤러리', '서식&자료실', 'FAQ',
    '공지사항', '보도자료', 'TJ미래전략 칼럼', '메일링서비스', '포럼', '세미나',
    'HOME', '인쇄', '글자크기', '확대', '초기화', '축소', '게시판 List',
    '제목', '저자', '발행일', '내용', '미래전략연구', '박태준연구', '박태준의 삶',
    '박태준의삶', '박태준 연구', '청년사업', '포럼&세미나', '연구소소식', '연구소소개',
    'RESEARCH', 'INTRODUCE', "LIFE'S CHUNGAM", 'RESEARCH CHUNGAM',
}
