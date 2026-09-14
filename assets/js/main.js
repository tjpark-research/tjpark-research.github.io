/* TJPI renewal prototype — minimal vanilla JS (no dependencies) */
(function () {
  'use strict';

  /* Asset root, derived from this script's own URL so that /en/ resolves too. */
  var BASE = (function () {
    var el = document.currentScript;
    if (!el) { var all = document.getElementsByTagName('script'); el = all[all.length - 1]; }
    return el && el.src ? el.src.replace(/assets\/js\/main\.js.*$/, '') : '';
  })();

  /* ---------- Featured slider (hero) ---------- */
  /* 영문 메인에도 같은 스크립트가 실린다. 배열이 하나뿐이면 영문 페이지의
     슬라이드가 한국어로 바뀌어 버리므로 문서 언어로 갈라 쓴다. */
  var EN = (document.documentElement.lang || '').slice(0, 2) === 'en';
  var slides = EN ? [
    {
      tag: 'CENTENNIAL',
      img: '' + BASE + 'assets/img/main/centennial.jpg',
      href: '' + BASE + 'news/press-items/100004.html',
      title: 'Toward the Centenary of Chungam Park Tae-Joon',
      desc: 'Pohang has begun preparing the programme marking one hundred years since his birth.',
      meta: '27 Aug 2026 \u00b7 Press'
    },
    {
      tag: 'FUTURE STRATEGY SERIES 15',
      img: '' + BASE + 'assets/img/books/9791191383690.jpg',
      href: '' + BASE + 'research/books/100015.html',
      title: 'Becoming MIT — Moments of Decision',
      desc: 'Volume 15 of the Future Strategy Research Series: how MIT was shaped by the choices it made at each turning point.',
      meta: 'Published 23 Apr 2026 \u00b7 Ppalgansogeum'
    },
    {
      tag: 'FUTURE STRATEGY SERIES 14',
      img: '' + BASE + 'assets/img/books/fs14-jiseong-jeguk.jpg',
      href: '' + BASE + 'research/books/64.html',
      title: 'Empire of Intellect — A World History of the Modern Research University',
      desc: 'Volume 14 follows the research university from Humboldt’s Berlin to the present, and asks where it goes next.',
      meta: 'Published 25 Feb 2026 \u00b7 Ppalgansogeum'
    }
  ] : [
    {
      tag: '탄생 100주년',
      img: '' + BASE + 'assets/img/main/centennial.jpg',
      href: '' + BASE + 'news/press-items/100004.html',
      title: '청암 박태준 탄생 100주년을 앞두고',
      desc: '포항시가 청암 박태준 탄생 100주년을 앞두고 기념사업 준비에 본격 착수했다.',
      meta: '2026.08.27 · 보도자료'
    },
    {
      tag: '미래전략연구총서 15',
      img: '' + BASE + 'assets/img/books/9791191383690.jpg',
      href: '' + BASE + 'research/books/100015.html',
      title: 'MIT가 MIT가 되기까지 — 비전, 위기, 선택의 순간들',
      desc: 'MIT의 운명을 가른 결정의 순간들을 담은 미래전략연구총서 15권. 데이비드 카이저 엮음, 노태복 옮김.',
      meta: '발간 2026.04.23 · 빨간소금'
    },
    {
      tag: '미래전략연구총서 14',
      img: '' + BASE + 'assets/img/books/fs14-jiseong-jeguk.jpg',
      href: '' + BASE + 'research/books/64.html',
      title: '지성의 제국 — 현대 연구중심대학의 세계사',
      desc: '훔볼트의 베를린에서 오늘에 이르기까지, 연구중심대학이 걸어온 길과 그 앞날을 묻는 미래전략연구총서 14권.',
      meta: '발간 2026.02.25 · 빨간소금'
    }
  ];

  var box = document.getElementById('feat');
  if (box) {
    var q = function (k) { return box.querySelector('[data-f="' + k + '"]'); };
    var i = 0;

    var render = function () {
      var s = slides[i];
      q('tag').textContent = s.tag;
      q('img').src = s.img;
      q('img').alt = s.title;
      q('title').textContent = s.title;
      q('desc').textContent = s.desc;
      q('meta').textContent = s.meta;
      if (q('link') && s.href) { q('link').href = s.href; }
      q('cur').textContent = i + 1;
    };

    q('tot').textContent = slides.length;
    q('prev').addEventListener('click', function () { i = (i - 1 + slides.length) % slides.length; render(); stop(); });
    q('next').addEventListener('click', function () { i = (i + 1) % slides.length; render(); stop(); });

    var timer = setInterval(function () { i = (i + 1) % slides.length; render(); }, 6500);
    function stop() { clearInterval(timer); }
    box.addEventListener('mouseenter', stop);

    render();
  }

  /* ---------- Mobile menu (prototype stub) ---------- */
  var burger = document.querySelector('.burger');
  var gnb = document.querySelector('.gnb');
  if (burger && gnb) {
    // 좁은 화면에서는 머리말의 검색창이 숨는다. 메뉴를 열 때 그 검색창을
    // 통째로 메뉴 안으로 옮겨 넣고, 닫을 때 제자리로 돌려놓는다.
    var hs = document.querySelector('.hd-search');
    var hsHome = hs && hs.parentNode, hsNext = hs && hs.nextSibling, hsLi = null;
    function stow() {
      if (!hs || hsLi) return;
      hsLi = document.createElement('li');
      hsLi.className = 'gnb-search';
      hsLi.appendChild(hs);
      gnb.insertBefore(hsLi, gnb.firstChild);
    }
    function unstow() {
      if (!hsLi) return;
      hsHome.insertBefore(hs, hsNext);
      hsLi.parentNode.removeChild(hsLi);
      hsLi = null;
    }
    burger.addEventListener('click', function () {
      var open = gnb.style.display === 'flex';
      if (open) {
        unstow();
        gnb.style.display = '';
      } else {
        gnb.style.cssText =
          'display:flex;flex-direction:column;position:absolute;top:100%;left:0;right:0;' +
          'background:#fff;border-bottom:1px solid var(--line);padding:12px 24px 20px;gap:0;height:auto;z-index:99';
        gnb.querySelectorAll('li').forEach(function (li) {
          li.style.padding = '12px 0';
          li.style.borderBottom = '1px solid var(--line)';
        });
        stow();
      }
    });
  }


  /* ---------- 하위 페이지: 시대별 탭 ----------
     JS 가 없으면 모든 시대가 그냥 이어서 보이도록 HTML 은 전부 출력해 두고,
     여기서 <html class="js"> 를 붙여 첫 탭만 남긴다. */
  var eras = document.querySelector('.eras');
  if (eras) {
    document.documentElement.classList.add('js');
    var panes = eras.querySelectorAll('.era-pane');
    var tabs = eras.querySelectorAll('.era-tabs button');
    var show = function (i) {
      panes.forEach(function (p, n) { p.classList.toggle('on', n === i); });
      tabs.forEach(function (t, n) { t.classList.toggle('on', n === i); });
    };
    tabs.forEach(function (t, i) { t.addEventListener('click', function () { show(i); }); });
    show(0);
  }

  /* ---------- 하위 페이지: 게시판 '더 보기' ----------
     항목은 전부 HTML 에 들어 있다(JS 없이도 전체가 보인다).
     JS 가 있을 때만 접어서 조금씩 펼쳐 준다. */
  document.querySelectorAll('.board').forEach(function (board) {
    var size = parseInt(board.getAttribute('data-page-size') || '12', 10);
    var list = board.querySelector('ul');
    var all = Array.prototype.slice.call(list.children);
    var moreWrap = board.querySelector('.board-more');
    var moreBtn = board.querySelector('[data-board-more]');
    var shown = size;

    function apply() {
      all.forEach(function (li, i) { li.hidden = i >= shown; });
      if (moreWrap) moreWrap.hidden = all.length <= shown;
    }

    if (moreBtn) {
      moreBtn.addEventListener('click', function () { shown += size; apply(); });
    }
    apply();
  });


  /* ---------- 영상: 눌렀을 때만 재생기를 붙인다 ----------
     썸네일만 먼저 보여 주고, 재생 버튼을 눌러야 유튜브(또는 mp4)를 불러온다.
     페이지를 열기만 해도 유튜브가 로드되면 느리고, 보는 사람의 접속 기록이
     유튜브로 새어 나간다. */
  document.querySelectorAll('.v-play').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var yt = btn.getAttribute('data-yt');
      var file = btn.getAttribute('data-file');
      var wrap = document.createElement('div');
      wrap.className = 'v-frame';
      if (yt) {
        var f = document.createElement('iframe');
        f.src = 'https://www.youtube-nocookie.com/embed/' + yt +
                '?autoplay=1&rel=0&modestbranding=1';
        f.title = btn.getAttribute('aria-label') || '';
        f.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture';
        f.allowFullscreen = true;
        f.setAttribute('loading', 'lazy');
        wrap.appendChild(f);
      } else if (file) {
        var v = document.createElement('video');
        v.src = file;
        v.poster = btn.getAttribute('data-poster') || '';
        v.controls = true;
        v.autoplay = true;
        v.playsInline = true;
        v.preload = 'metadata';
        wrap.appendChild(v);
      } else {
        return;
      }
      btn.parentNode.replaceChild(wrap, btn);
    });
  });

  /* ---------- Reveal on scroll ---------- */
  if ('IntersectionObserver' in window) {
    var targets = document.querySelectorAll('.p-card,.book,.tl li,.y-card,.stats li');
    targets.forEach(function (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(14px)';
      el.style.transition = 'opacity .6s ease, transform .6s ease';
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e, n) {
        if (!e.isIntersecting) return;
        setTimeout(function () {
          e.target.style.opacity = '1';
          e.target.style.transform = 'none';
        }, n * 55);
        io.unobserve(e.target);
      });
    }, { threshold: 0.12 });
    targets.forEach(function (el) { io.observe(el); });
  }
})();

/* ── 사이트 검색 ──────────────────────────────────────────────
   서버가 없으므로 빌드 때 만들어 둔 색인 하나를 받아 브라우저에서 찾는다.
   색인은 처음 검색할 때 한 번만 받고(assets/search/index.json), 그 뒤로는
   브라우저 캐시에서 나온다. 한글은 부분 문자열로 찾는다 — '포스코'가
   '포스코와'에 걸리므로 어간을 떼어낼 일이 없다. */
(function () {
  var hd = document.querySelector('.hd-search');
  var page = document.getElementById('sr-results');
  var conf = hd || document.querySelector('.sr-form');
  if (!conf) return;
  var root = conf.getAttribute('data-root') || '';
  var lang = conf.getAttribute('data-lang') || 'ko';
  var ko = lang !== 'en';
  var idx = null, pending = null;

  function load() {
    if (idx) return Promise.resolve(idx);
    if (!pending) {
      pending = fetch(root + 'assets/search/index.json')
        .then(function (r) { return r.json(); })
        .then(function (j) {
          // 영문 쪽에서는 영문 페이지와, 두 언어가 함께 쓰는 개별 글을 찾는다.
          idx = j.d.filter(function (d) {
            return ko ? d[4] === 0 : (d[4] === 1 || d[5] === 1);
          }).map(function (d) {
            var hay = (d[1] + ' ' + d[2] + ' ' + d[3]).toLowerCase();
            return {
              u: d[0], t: d[1], w: d[2], x: d[3],
              h: hay, hs: hay.replace(/\s+/g, ''),
              ht: d[1].toLowerCase()
            };
          });
          return idx;
        })
        .catch(function () { idx = []; return idx; });
    }
    return pending;
  }

  function words(q) {
    return q.toLowerCase().split(/\s+/).filter(Boolean);
  }

  function search(q) {
    var terms = words(q);
    if (!terms.length) return [];
    var out = [];
    for (var i = 0; i < idx.length; i++) {
      var d = idx[i], sc = 0, ok = true;
      for (var j = 0; j < terms.length; j++) {
        var t = terms[j], s = 0;
        if (d.ht.indexOf(t) === 0) s = 120;
        else if (d.ht.indexOf(t) >= 0) s = 100;
        else if (d.h.indexOf(t) >= 0) s = 30;
        else if (d.hs.indexOf(t.replace(/\s+/g, '')) >= 0) s = 20;
        if (!s) { ok = false; break; }
        sc += s;
      }
      if (ok) out.push([sc, d]);
    }
    out.sort(function (a, b) {
      return b[0] - a[0] || a[1].t.length - b[1].t.length;
    });
    return out.map(function (o) { return o[1]; });
  }

  var ENT = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return ENT[c]; }); }

  function hi(s, terms) {
    var out = esc(s);
    terms.forEach(function (t) {
      var re = new RegExp(t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      out = out.replace(re, function (m) { return '\u0001' + m + '\u0002'; });
    });
    return out.split('\u0001').join('<mark>').split('\u0002').join('</mark>');
  }

  function snippet(d, terms) {
    var low = d.x.toLowerCase(), at = -1;
    for (var i = 0; i < terms.length && at < 0; i++) at = low.indexOf(terms[i]);
    if (at < 0) return hi(d.x.slice(0, 150), terms) + (d.x.length > 150 ? '…' : '');
    var from = Math.max(0, at - 50);
    var cut = d.x.slice(from, from + 160);
    return (from ? '…' : '') + hi(cut, terms) + (from + 160 < d.x.length ? '…' : '');
  }

  function row(d, terms, withText) {
    return '<a href="' + root + d.u + '">'
      + '<span class="sr-t">' + hi(d.t, terms) + '</span>'
      + (d.w ? '<span class="sr-w">' + esc(d.w) + '</span>' : '')
      + (withText && d.x ? '<span class="sr-x">' + snippet(d, terms) + '</span>' : '')
      + '</a>';
  }

  /* 머리말 검색창 — 치는 대로 후보를 떨군다 */
  if (hd) {
    var inp = hd.querySelector('input');
    var drop = document.createElement('div');
    drop.className = 'sr-drop';
    drop.hidden = true;
    hd.appendChild(drop);
    var timer;
    function suggest() {
      var q = inp.value.trim();
      if (!q) { drop.hidden = true; return; }
      load().then(function () {
        if (inp.value.trim() !== q) return;
        var r = search(q), terms = words(q);
        if (!r.length) {
          drop.innerHTML = '<p class="sr-no">' + (ko ? '결과가 없습니다' : 'No results') + '</p>';
        } else {
          var all = '';
          if (r.length > 8) {
            all = '<a class="sr-all" href="' + root + (ko ? '' : 'en/') + 'search.html?q='
              + encodeURIComponent(q) + '">'
              + (ko ? r.length + '건 모두 보기' : 'All ' + r.length + ' results') + '</a>';
          }
          drop.innerHTML = r.slice(0, 8).map(function (d) {
            return row(d, terms, false);
          }).join('') + all;
        }
        drop.hidden = false;
      });
    }
    // 좁은 화면에서는 입력칸이 돋보기 뒤로 접힌다. 아무 데나 눌러도 펼치게.
    hd.addEventListener('click', function () { inp.focus(); });
    inp.addEventListener('focus', load);
    inp.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(suggest, 120);
    });
    inp.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { drop.hidden = true; inp.blur(); }
    });
    document.addEventListener('click', function (e) {
      if (!hd.contains(e.target)) drop.hidden = true;
    });
  }

  /* 검색 결과 쪽 */
  if (page) {
    var form = document.querySelector('.sr-form');
    var box = document.getElementById('sr-q');
    var cnt = document.getElementById('sr-count');
    var more = document.getElementById('sr-more');
    var res = [], shown = 0, terms = [], SIZE = 20;

    function render() {
      page.innerHTML = res.slice(0, shown).map(function (d) {
        return '<li>' + row(d, terms, true) + '</li>';
      }).join('');
      more.hidden = shown >= res.length;
    }

    function run(q) {
      q = (q || '').trim();
      if (!q) {
        cnt.textContent = ko ? '찾을 말을 넣어 주세요.' : 'Type something to search for.';
        page.innerHTML = ''; more.hidden = true;
        return;
      }
      load().then(function () {
        terms = words(q);
        res = search(q);
        shown = Math.min(SIZE, res.length);
        cnt.textContent = res.length
          ? (ko ? '‘' + q + '’ — ' + res.length + '건' : '“' + q + '” — ' + res.length + ' results')
          : (ko ? '‘' + q + '’ 이 든 쪽이 없습니다.' : 'Nothing matched “' + q + '”.');
        render();
      });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var q = box.value.trim();
      if (history.replaceState) {
        history.replaceState(null, '', location.pathname + (q ? '?q=' + encodeURIComponent(q) : ''));
      }
      run(q);
    });
    more.addEventListener('click', function () {
      shown = Math.min(shown + SIZE, res.length);
      render();
    });

    var q0 = '';
    var m = location.search.match(/[?&]q=([^&]*)/);
    if (m) { try { q0 = decodeURIComponent(m[1].replace(/\+/g, ' ')); } catch (err) { q0 = ''; } }
    box.value = q0;
    run(q0);
  }
})();
