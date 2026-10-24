#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片 → 拓印卡（火山方舟 Seedream）

用法：
  export ARK_API_KEY=xxx
  python3 render_stamp.py 输入照片.jpg                    # 出一张
  python3 render_stamp.py 照片.jpg --subject swan          # 指定题材墨色
  python3 render_stamp.py 照片.jpg -o out.png --size 2K

为什么要走服务端而不是纯前端：
  - 浏览器里没法安全放 ARK key（谁都能扒）
  - 这个脚本的产物是「预生成素材」，跑一次内联进 HTML，
    现场断网也能用 —— 保住「断网双击能跑」这条硬约束

关键参数 watermark=false：这是官方支持的关闭水印，比事后修补干净。
"""
import os, sys, json, argparse, base64, pathlib, urllib.request

ARK_URL = 'https://ark.cn-beijing.volces.com/api/v3/images/generations'
DEFAULT_MODEL = 'doubao-seedream-5-0-flash-260915'

# 候选模型：账号开通哪个就填哪个（见 --probe）
# 5-0-flash 是当前账号实际开通的；其余留作备选，报 404 就说明没开这个
CANDIDATES = [
    'doubao-seedream-5-0-flash-260915',
    'doubao-seedream-5-0-lite-260128',
    'doubao-seedream-4-0-250828',
    'doubao-seedream-4-5-251128',
]

# 按 skill 的配色规范，给不同题材不同的墨色倾向
INK_HINT = {
    'swan':   '深色羽毛禁用死黑，用炭灰、墨蓝灰、深褐灰层层半透明叠印',
    'bridge': '墙体用赭红、陶土赤褐半透明叠印，屋顶用灰蓝',
    'sluice': '墙体用灰蓝、鼠尾草青，孔洞保留纸底留白',
    'reed':   '浅色花穗以暖白米白为主，茎叶用橄榄绿、浅抹茶绿干刷',
}

PROMPT_TMPL = '''请基于参考图制作一张纯拓印插画，1:1 方形构图。
画面整张都是干净的拓印插画风格，不出现任何文字、字母、数字、水印。

1. 主体与构图：参考图中最有记忆点的单一主体位于画面正中央，水平垂直均居中；
主体约占画面 55%~65%，四周保留舒展的暖白或浅米白艺术纸底留白，呼吸感充足。
2. 主体提取：只保留核心主体与少量必要陪体，省略背景杂物（栏杆、人物、多余建筑等）；
外轮廓呈手工剪纸或版画刀刻般干净利落的弧线与几何切面，完全不使用黑色勾线描边，
边界与纸底清晰分明，不晕成模糊水渍。
3. 拓印质感：内部采用孔版丝网半透明叠印与海绵拓包干压结合的弥散颗粒质感；
{ink}；受光处保留干擦飞白，色块内部由浓到淡形成海绵拓包颗粒弥散渐变，
明快干净、透气，避免厚重浑浊与 neon 艳色。
4. 整体去繁就简、主体居中、外轮廓利落现代、配色低饱和通透清新、留白舒展、简约高级。'''


def b64_data_url(path):
    ext = pathlib.Path(path).suffix.lower().lstrip('.')
    mime = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'webp': 'webp'}.get(ext, 'jpeg')
    raw = open(path, 'rb').read()
    return 'data:image/%s;base64,%s' % (mime, base64.b64encode(raw).decode())


def gen(photo, prompt, size, model, key, out):
    body = json.dumps({
        'model': model,
        'prompt': prompt,
        'image': [b64_data_url(photo)],
        'size': size,
        'response_format': 'url',
        'watermark': False,          # 关水印：官方参数，别去掉
    }).encode()

    req = urllib.request.Request(ARK_URL, data=body, method='POST', headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read().decode())

    url = d['data'][0]['url']
    with urllib.request.urlopen(url, timeout=120) as r:
        img = r.read()
    pathlib.Path(out).write_bytes(img)
    print('✅ %s（%d KB）' % (out, len(img) // 1024))
    return out


def probe(key):
    """逐个试候选模型，告诉你账号实际能用哪个。
       返回 (ok_list, limited_list, detail)"""
    ok, limited, detail = [], [], []
    for m in CANDIDATES:
        body = json.dumps({'model': m, 'prompt': 'a black swan on water',
                           'size': '1K', 'watermark': False}).encode()
        req = urllib.request.Request(ARK_URL, data=body, method='POST', headers={
            'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                r.read()
            ok.append(m)
            detail.append((m, '✅ 可用'))
        except urllib.error.HTTPError as e:
            t = e.read().decode()
            try:
                code = json.loads(t)['error']['code']
            except Exception:
                code = t[:50]
            # 429 = 模型开通了，但撞到用量/额度限制。这和 404 是两回事
            if code == 'SetLimitExceeded' or e.code == 429:
                limited.append(m)
                detail.append((m, '⚠️  %s（已开通，但被额度限制拦住）' % code))
            else:
                detail.append((m, '%s %s' % (e.code, code)))
        except Exception as e:
            detail.append((m, 'ERR ' + str(e)[:50]))
    return ok, limited, detail


def center_subject(path, out, target_ratio=0.58):
    """把主体裁到画面正中。

    为什么需要：模型出图不保证居中，实测黑天鹅明显偏右上。
    skill 规范要求「主体水平垂直均居中、约占 55%~65%」，
    靠 prompt 求不来，只能算。

    做法：把「非纸底」像素当作主体，求包围盒，再以包围盒中心
    为锚点裁一个正方形，使主体占比约为 target_ratio。
    """
    try:
        from PIL import Image
    except ImportError:
        print('⚠️  没装 Pillow，跳过居中。pip install pillow')
        return path

    im = Image.open(path).convert('RGB')
    W, H = im.size
    px = im.load()

    # 纸底是暖白，阈值取 235：低于它的算「有墨」
    step = 2
    xs, ys = [], []
    for y in range(0, H, step):
        for x in range(0, W, step):
            r, g, b = px[x, y]
            if (r + g + b) / 3 < 235:
                xs.append(x); ys.append(y)

    if not xs:
        print('⚠️  没找到主体，保持原图')
        return path

    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)

    # 让主体占 target_ratio：边长 = 主体较长边 / ratio
    side = int(max(bw, bh) / target_ratio)
    side = min(side, W, H)

    left = int(cx - side / 2)
    top = int(cy - side / 2)
    left = max(0, min(W - side, left))
    top = max(0, min(H - side, top))

    im.crop((left, top, left + side, top + side)).save(out, quality=95)
    print('   居中裁切：主体 %dx%d → %d 见方' % (bw, bh, side))
    return out


def make_web_asset(path, out, size=480, quality=82):
    """导一张可内联的小图（保持单文件、断网可用的前提）"""
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(path).convert('RGB').resize((size, size), Image.LANCZOS)
    im.save(out, quality=quality, optimize=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('photo', nargs='?', default=None)
    ap.add_argument('-o', '--out', default=None)
    ap.add_argument('--subject', default='swan', choices=list(INK_HINT))
    ap.add_argument('--size', default='2K')
    ap.add_argument('--model', default=DEFAULT_MODEL)
    ap.add_argument('--probe', action='store_true', help='只检测账号能用哪些模型')
    ap.add_argument('--no-center', action='store_true', help='跳过主体居中裁切')
    ap.add_argument('--web', default=None, help='同时导一张可内联的小图，给这个路径')
    a = ap.parse_args()

    key = os.environ.get('ARK_API_KEY')
    if not key:
        print('❌ 缺 ARK_API_KEY')
        print('   export ARK_API_KEY=你的key   # 火山方舟控制台 → API Key 管理')
        return 1

    if a.probe:
        ok, limited, detail = probe(key)
        for m, s in detail:
            print('  %-36s %s' % (m, s))
        if ok:
            print('\n✅ 可用：' + ', '.join(ok))
            print('   用它：python3 render_stamp.py 照片.jpg --model ' + ok[0])
            return 0
        if limited:
            print('\n⚠️  模型已开通，但被用量限制拦住：' + ', '.join(limited))
            print('   去方舟控制台 → 模型开通页，把「安全体验模式」的用量上限调高或关闭：')
            print('   https://console.volcengine.com/ark')
            print('   这不是 key 或模型名的问题，是额度。')
            return 2
        print('\n❌ 没有一个可用。两种可能：')
        print('   1) 账号还没在方舟控制台「开通」这些模型（最常见）')
        print('   2) 需要先在控制台创建「推理接入点」(endpoint)，')
        print('      然后把 endpoint id（形如 ep-xxxxx）传给 --model')
        print('   控制台：https://console.volcengine.com/ark  → 模型广场 / 在线推理')
        return 1

    if not a.photo:
        print('❌ 缺照片路径。用 --probe 可以先检测模型可用性')
        return 1
    if not os.path.exists(a.photo):
        print('❌ 找不到照片: ' + a.photo)
        return 1

    out = a.out or (str(pathlib.Path(a.photo).with_suffix('')) + '-stamp.png')
    prompt = PROMPT_TMPL.format(ink=INK_HINT[a.subject])
    try:
        gen(a.photo, prompt, a.size, a.model, key, out)
    except urllib.error.HTTPError as e:
        t = e.read().decode()
        print('❌ HTTP %s: %s' % (e.code, t[:400]))
        if 'SetLimitExceeded' in t or e.code == 429:
            print('\n额度问题，不是 key 也不是模型名：')
            print('  方舟控制台的「安全体验模式」给这个模型设了用量上限，')
            print('  去模型开通页调高或关闭它：https://console.volcengine.com/ark')
        elif 'InvalidEndpointOrModel' in t:
            print('\n提示：模型没开通或名字不对。跑一下自检：')
            print('   python3 render_stamp.py --probe')
        return 1
    except Exception as e:
        print('❌ ' + str(e)[:400])
        return 1

    # 模型不保证居中，后处理裁到画面正中（skill 要求主体居中占 55%~65%）
    if not a.no_center:
        try:
            center_subject(out, out)
        except Exception as e:
            print('⚠️  居中处理失败，保留原图：' + str(e)[:120])

    if a.web:
        w = make_web_asset(out, a.web)
        if w:
            print('   网页用小图：%s（%d KB）' % (w, os.path.getsize(w) // 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
