# POSTECH 박태준미래전략연구소 — 홈페이지 리뉴얼

기존 `tjpark.postech.ac.kr` (PHP) 사이트를 대체할 정적 사이트.
배포 대상: https://github.com/tjpark-research/tjpark-research.github.io

## 현재 상태 — 메인 페이지 시안 (1차)

| 파일 | 설명 |
|---|---|
| `index.html` | 한국어 메인 |
| `en/index.html` | 영문 메인 |
| `assets/css/style.css` | 전체 스타일 (단일 파일, 빌드 도구 없음) |
| `assets/js/main.js` | 히어로 슬라이더 / 모바일 메뉴 / 스크롤 리빌 |
| `assets/img/` | (비어 있음) 이관 예정 이미지 자리 |

로컬 확인: `index.html`을 브라우저로 열기. 빌드·서버 불필요.

## 설계 결정

- **순수 정적 HTML/CSS/JS.** GitHub Pages에 그대로 배포. Jekyll/Hugo 미사용.
- **한/영 병행.** 루트 = 한국어, `/en/` = 영문. 상단 KOR/ENG 토글.
- **상단 메뉴 7개.** 기존 6개 + `박태준의 삶`을 최상위로 승격
  (구 영문 사이트에서는 이미 최상위였음. 연구소 정체성의 핵심이라 판단).
- **디자인 톤.** 잉크 블랙 + POSTECH 크림슨 + 브론즈/골드. 본문 산세리프,
  제목·인용 세리프(Noto Serif KR). 제철·기록·품격의 인상.
- **폰트.** Google Fonts CDN (Noto Sans KR / Noto Serif KR).

## 알려진 제약 (배포 전 반드시 처리)

1. **이미지가 아직 구 사이트 hotlink 상태** (`http://tjpark.postech.ac.kr/...`).
   GitHub Pages는 HTTPS라 mixed-content로 차단됨.
   → 이미지를 `assets/img/`로 내려받고 상대경로로 교체할 것.
2. 모든 내부 링크가 `#` placeholder. 하위 페이지 제작 시 연결.
3. 검색 폼은 UI만 존재. 정적 사이트용 검색(예: 클라이언트 인덱스) 별도 구현 필요.
4. 통계 수치(총서 14권 / 박태준 연구총서 8권)는 구 사이트 목록 기준. 확정 필요.

## 다음 단계

- [ ] 메인 시안 확정 (레이아웃·색·타이포)
- [ ] 이미지·PDF 등 자산 이관, 상대경로 전환
- [ ] 하위 페이지 템플릿 1종 제작 → 나머지 페이지 확장
- [ ] 연구총서/보고서/공지 목록을 JSON 데이터 + 렌더링으로 분리
- [ ] 접근성 점검, OG 태그, sitemap.xml, 404.html
- [ ] `tjpark-research/tjpark-research.github.io` 로 푸시 및 Pages 설정
