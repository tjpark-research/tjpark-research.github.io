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


def fetch(url, dest):
    r = S.get(url, timeout=30)
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
    ok = skip = fail = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'legacy', '*.json'))):
        data = json.load(open(path))
        items = data if isinstance(data, list) else [data]
        changed = False
        for it in items:
            urls = []
            if isinstance(it, dict):
                if it.get('image'):
                    urls.append(('image', it['image']))
                for i, u in enumerate(it.get('images', []) or []):
                    urls.append((('images', i), u))
            for key, url in urls:
                if not url or not url.startswith('http'):
                    continue
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
                    except Exception as e:
                        fail += 1
                        print(f'  FAIL {url} — {e}')
                        continue
                if key == 'image':
                    it['local'] = rel
                else:
                    it.setdefault('images_local', {})[str(key[1])] = rel
                changed = True
        if changed:
            json.dump(data, open(path, 'w'), ensure_ascii=False, indent=1)
        print(f'{os.path.basename(path):34s} 처리')
    print(f'\n내려받음 {ok} / 이미 있음 {skip} / 실패 {fail}')


if __name__ == '__main__':
    main()
