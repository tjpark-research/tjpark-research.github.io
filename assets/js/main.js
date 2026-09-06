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
  var slides = [
    {
      tag: '미래전략연구총서 14',
      img: ''+BASE+'assets/img/books/fs14-jiseong-jeguk.jpg',
      title: '지성의 제국 — 현대 연구중심대학의 세계사',
      desc: '2026년 박태준미래전략연구소는 ‘현대 연구중심대학의 세계사’를 엮은 미래전략연구 총서 14권 『지성의 제국』을 발간했다.',
      meta: '발간 2026.02.25 · 빨간소금'
    },
    {
      tag: '미래전략포럼',
      img: ''+BASE+'assets/img/main/forum-city-future.jpg',
      title: '『도시의 미래, 공간과 산업을 생각한다』 포럼',
      desc: '국가의 미래 발전을 모색하기 위해 산학연관 전문가, 석학 및 오피니언 리더들이 한자리에 모여 토론의 장을 마련합니다.',
      meta: '포스코 국제관 1층 국제회의장'
    },
    {
      tag: '미래전략 영상',
      img: ''+BASE+'assets/img/main/pohang-pittsburgh.jpg',
      title: '포항–피츠버그, 두 철강도시의 평행이론',
      desc: '두 도시의 미래 비전을 제시하여 향후 도시 간 협력의 방향을 모색한 영상 콘텐츠입니다.',
      meta: 'YouTube · TJPI 채널'
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
    burger.addEventListener('click', function () {
      var open = gnb.style.display === 'flex';
      if (open) {
        gnb.style.display = '';
      } else {
        gnb.style.cssText =
          'display:flex;flex-direction:column;position:absolute;top:100%;left:0;right:0;' +
          'background:#fff;border-bottom:1px solid var(--line);padding:12px 24px 20px;gap:0;height:auto;z-index:99';
        gnb.querySelectorAll('li').forEach(function (li) {
          li.style.padding = '12px 0';
          li.style.borderBottom = '1px solid var(--line)';
        });
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
