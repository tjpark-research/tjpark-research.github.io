/* TJPI renewal prototype — minimal vanilla JS (no dependencies) */
(function () {
  'use strict';

  /* ---------- Featured slider (hero) ---------- */
  var slides = [
    {
      tag: '미래전략연구총서 14',
      img: 'http://tjpark.postech.ac.kr/data/future/8383cfb3771776843453.jpg',
      title: '지성의 제국 — 현대 연구중심대학의 세계사',
      desc: '2026년 박태준미래전략연구소는 ‘현대 연구중심대학의 세계사’를 엮은 미래전략연구 총서 14권 『지성의 제국』을 발간했다.',
      meta: '발간 2026.02.25 · 빨간소금'
    },
    {
      tag: '미래전략포럼',
      img: 'http://tjpark.postech.ac.kr/data/mainvisual/316cfe2c051673917091.jpg',
      title: '『도시의 미래, 공간과 산업을 생각한다』 포럼',
      desc: '국가의 미래 발전을 모색하기 위해 산학연관 전문가, 석학 및 오피니언 리더들이 한자리에 모여 토론의 장을 마련합니다.',
      meta: '포스코 국제관 1층 국제회의장'
    },
    {
      tag: '미래전략 영상',
      img: 'http://tjpark.postech.ac.kr/data/mainvisual/a2dcf9a62f1673325810.jpg',
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
