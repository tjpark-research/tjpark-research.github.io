#!/usr/bin/env python3
"""
data/legacy/*.json 이 참조하는 구 사이트 이미지를 assets/img/legacy/ 로 내려받는다.

GitHub Pages 는 HTTPS 라 http:// hotlink 는 mixed-content 로 차단된다.
따라서 이관 대상 이미지는 전부 저장소 안으로 가져와야 한다.
내려받은 파일명은 원본 URL 해시 기반이라 재실행해도 안정적이며,
JSON 에 'local' 필드를 채워 넣어 빌더가 그대로 쓰게 한다.
"""
import hashlib, io, json, os, glob, sys, time
import requests
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUTDIR = os.path.join(ROOT, 'assets', 'img', 'legacy')
MAXW = 700          # 목록 썸네일 용도라 이 이상은 낭비
QUALITY = 82

S = requests.Session()
S.headers['User-Agent'] = 'Mozilla/5.0 (TJPI site migration)'


def local_name(url):
    h = hashlib.sha1(url.encode()).hexdigest()[:12]
    ext = os.path.splitext(url.split('?')[0])[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.gif'):
        ext = '.jpg'
    return f'{h}{ext}'


# 본문에는 외부 언론사 서버 이미지 링크가 섞여 있다. 남의 서버라 사라지기도 하고
# 응답이 느려 수집이 멈춘다. 우리가 가져올 수 있는 것은 연구소 자체 서버뿐이다.
OWN_HOSTS = ('tjpark.postech.ac.kr', 'postech1.dever-host.com',
             # 「위대한 만남」 연재에 실린 사진. 구 홈페이지가 조선일보 서버를
             # 직접 링크해 두어, 구 사이트를 내리면 함께 사라진다.
             # 저작권은 조선일보에 있으므로 게재 조건은 연구소가 확인해야 한다.
             'image.chosun.com')
DEADLINE = float(os.environ.get('FETCH_SECONDS', '150'))


# 광고·추적 픽셀. 기사 본문에 섞여 들어오지만 콘텐츠가 아니다.
AD_HOSTS = ('criteo.com', 'doubleclick.net', 'googlesyndication.com',
            'cad.chosun.com', 'ad.', 'analytics.')

# 이 파일들은 외부(언론사) 서버 이미지도 가져온다.
# 언론자료는 기사와 사진이 한 벌이라 사진 없이 캡션만 남으면 뜻이 통하지 않는다.
# 저작권은 각 언론사에 있으므로 게재 조건은 연구소가 확인해야 한다.
EXTERNAL_OK = {'detail_tj_media.json'}


def is_own(url, allow_external=False):
    if any(h in url for h in AD_HOSTS):
        return False
    if any(h in url for h in OWN_HOSTS):
        return True
    return allow_external and url.startswith('http')


def fetch(url, dest):
    r = S.get(url, timeout=8)
    if r.status_code != 200 or len(r.content) < 500:
        raise ValueError(f'HTTP {r.status_code}, {len(r.content)}B')
    data = r.content
    try:
        im = Image.open(io.BytesIO(data))
        if im.format == 'GIF' and getattr(im, 'is_animated', False):
            open(dest, 'wb').write(data)          # 애니메이션은 그대로
            return
        w, h = im.size
        if w > MAXW:
            im = im.resize((MAXW, int(h * MAXW / w)), Image.LANCZOS)
        if dest.endswith('.png'):
            im.save(dest, optimize=True)
        else:
            im.convert('RGB').save(dest, 'JPEG', quality=QUALITY,
                                   optimize=True, progressive=True)
    except Exception:
        open(dest, 'wb').write(data)              # 디코딩 실패 시 원본 보존


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    global T0
    T0 = time.time()
    ok = skip = fail = 0
    try:
      for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'legacy', '*.json'))):
        data = json.load(open(path))
        allow_external = os.path.basename(path) in EXTERNAL_OK
        items = data if isinstance(data, list) else [data]
        changed = False
        for it in items:
            urls = []
            if isinstance(it, dict):
                if it.get('image'):
                    urls.append(('image', it['image']))
                for i, u in enumerate(it.get('images', []) or []):
                    urls.append((('images', i), u))
                # 상세 페이지 본문 이미지. 외부 언론사 서버 링크가 섞여 있어
                # 실패가 나오는 게 정상이다(원본이 이미 사라진 것).
                for i, u in enumerate(it.get('images', []) or []):
                    pass
            for key, url in urls:
                if not url or not url.startswith('http'):
                    continue
                if not is_own(url, allow_external):
                    continue
                if time.time() - T0 > DEADLINE:
                    raise TimeoutError('deadline')
                name = local_name(url)
                dest = os.path.join(OUTDIR, name)
                rel = 'assets/img/legacy/' + name
                if os.path.exists(dest):
                    skip += 1
                else:
                    try:
                        fetch(url, dest)
                        ok += 1
                        time.sleep(0.1)
                    except TimeoutError:
                        raise
                    except Exception as e:
                        fail += 1
                        continue
                if key == 'image':
                    it['local'] = rel
                else:
                    it.setdefault('images_local', {})[str(key[1])] = rel
                changed = True
        if changed:
            json.dump(data, open(path, 'w'), ensure_ascii=False, indent=1)
        print(f'{os.path.basename(path):34s} 처리')
        if time.time() - T0 > DEADLINE:
            print('  (시간 제한 도달 — 다시 실행하면 이어서 받습니다)')
            break
    except TimeoutError:
        print('  (시간 제한 도달 — 다시 실행하면 이어서 받습니다)')
    print(f'\n내려받음 {ok} / 이미 있음 {skip} / 실패 {fail}')


if __name__ == '__main__':
    main()
