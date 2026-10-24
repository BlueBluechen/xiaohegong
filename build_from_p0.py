#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把飞书「P0实测记录」导出成 p0.js，并内联回 小小河工.html

用法：
  python3 build_from_p0.py            # 只导出 p0.js
  python3 build_from_p0.py --inline   # 同时内联进 HTML
  python3 build_from_p0.py --check    # 只校验，不写文件

设计（和 build_from_feishu.py 同一套原则）：
  - 拉取失败不能让页面白屏：出错就保留现有 p0.js，退出码 1
  - 只导出「注入产品 = 是」的记录
  - 照片不入 HTML（体积），只带 has 标记 + file_token；要显示图请用真后端
  - 时间用飞书的 ISO 字符串转成毫秒时间戳

这几条是刻意为之，改动前先想清楚：
  - P0 记录是「真实发生的」证据，不是演示数据，所以单独一个 P0 常量，
    和 demo 的 SEED 分开，避免混淆来源
  - observer 只写昵称，不写真实姓名；license 固定匿名
"""
import subprocess, json, os, sys
from datetime import datetime

CLI = '/Users/carachen/.workbuddy/binaries/node/cli-connector-packages/bin/lark-cli'
BASE = 'CACyb67OaaFXZPskQQtc6IDTnDc'
PROFILE = 'cli_aa514a33fcf85d1e'
T_P0 = 'tblrhQacJg8onRkh'

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'p0.js')
HTML = os.path.join(ROOT, '小小河工.html')

NEED = ['记录ID', '点位编号', '时间', '孩子昵称', '任务类型',
        '观测数值', '观测文本', '照片', '分级', '注入产品', '备注']


def cli(args):
    env = dict(os.environ)
    env.pop('HTTPS_PROXY', None); env.pop('HTTP_PROXY', None)
    env['LARK_CLI_NO_PROXY'] = '1'
    p = subprocess.run([CLI, '--profile', PROFILE] + args,
                       capture_output=True, text=True, env=env)
    out = '\n'.join(l for l in p.stdout.split('\n') if not l.startswith('[lark-cli]'))
    try:
        return json.loads(out)
    except Exception:
        return {'ok': False, 'error': {'message': out[-400:]}}


def fetch():
    d = cli(['base', '+record-list', '--base-token', BASE, '--table-id', T_P0,
             '--as', 'user', '--format', 'json'])
    if not d.get('ok'):
        return None, d.get('error', {}).get('message', '未知错误')

    data = d['data']
    fields = data['fields']
    rows = data['data']
    rids = data.get('record_id_list', [])

    miss = [n for n in NEED if n not in fields]
    if miss:
        return None, f'P0 表缺字段: {miss}'

    idx = {n: i for i, n in enumerate(fields)}

    def cell(r, name):
        v = r[idx[name]] if idx[name] < len(r) else None
        # select 字段返回数组
        if isinstance(v, list):
            if v and isinstance(v[0], dict):
                return v          # attachment
            return v[0] if v else None
        return v

    out = []
    for i, r in enumerate(rows):
        inject = cell(r, '注入产品')
        if inject != '是':
            continue

        rid = cell(r, '记录ID') or f'P0-{i+1:04d}'
        gid = cell(r, '点位编号')
        if gid is None:
            continue

        # 时间：飞书给 ISO 字符串
        ts_raw = cell(r, '时间')
        try:
            ts = int(datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00')).timestamp() * 1000)
        except Exception:
            ts = None
        if not ts:
            continue

        # 照片：attachment 数组
        atts = cell(r, '照片') or []
        if isinstance(atts, dict):
            atts = [atts]
        has_photo = bool(atts)
        tokens = [a.get('file_token') for a in atts if isinstance(a, dict) and a.get('file_token')]

        grade = cell(r, '分级') or ('A · 有照片' if has_photo else 'B · 无照片')

        out.append({
            'id': rid,
            'gateId': int(gid),
            'ts': ts,
            'type': cell(r, '任务类型') or '水文观测',
            'obs': cell(r, '观测数值') or '',
            'note': cell(r, '观测文本') or '',
            'observer': cell(r, '孩子昵称') or '匿名河工',
            'grade': 'A' if grade.startswith('A') else 'B',
            'hasPhoto': has_photo,
            'tokens': tokens,
            'memo': cell(r, '备注') or ''
        })

    out.sort(key=lambda x: x['ts'], reverse=True)

    # 记录ID 重复会让产品里两条记录撞同一个 id，点详情会错。
    # 人工填表很容易重复编号（尤其复制粘贴），所以这里强制查一遍。
    seen = {}
    for r in out:
        seen.setdefault(r['id'], []).append(r)
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    if dup:
        lines = ['记录ID 重复：']
        for k, v in dup.items():
            who = '、'.join(x['observer'] for x in v)
            lines.append(f'  {k} → {who}')
        lines.append('请在飞书表里改成不同编号后重跑。')
        return None, '\n'.join(lines)

    return out, None


def emit(recs, inline=False):
    text = ('/* 自动生成 · 请勿手改\n'
            '   来源：飞书 Base ' + BASE + ' / P0实测记录 ' + T_P0 + '\n'
            '   生成：build_from_p0.py\n'
            '   —— 要改数据，改飞书表格，然后重跑脚本 ——\n'
            '   这些都是真实发生的记录，不是演示数据。 */\n'
            'const P0=' + json.dumps(recs, ensure_ascii=False) + ';\n')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'✅ 已写 {OUT}（{len(recs)} 条，{len(text):,} 字节）')

    if not inline:
        return

    html = open(HTML, encoding='utf-8').read()
    body = json.dumps(recs, ensure_ascii=False)
    anchor = 'const P0='
    if anchor in html:
        i = html.index(anchor)
        j = len(html)
        for mark in ('\nconst ', '\n\nconst ', '</script>'):
            k = html.find(mark, i + len(anchor))
            if k > 0 and k < j:
                j = k
        tail = '\n' if html[i:j].endswith('\n') else ''
        html = html[:i] + anchor + body + ';' + tail + html[j:]
    else:
        # 第一次：插在 const SEED= 之后
        seat = 'const SEED=['
        i = html.index(seat)
        j = len(html)
        for mark in ('\nconst ', '\n\nconst ', '</script>'):
            k = html.find(mark, i + len(seat))
            if k > 0 and k < j:
                j = k
        html = html[:j] + '\nconst P0=' + body + ';\n' + html[j:]

    open(HTML, 'w', encoding='utf-8').write(html)
    print(f'✅ 已内联回 HTML（{len(html):,} 字节）')


def main():
    recs, err = fetch()
    if recs is None:
        print(f'❌ 拉取失败：{err}')
        print('   p0.js 未改。')
        return 1

    print(f'P0 记录 {len(recs)} 条（仅「注入产品=是」）')
    if '--check' in sys.argv:
        print('✅ 校验通过（未写文件）')
        return 0

    emit(recs, '--inline' in sys.argv)
    return 0


if __name__ == '__main__':
    sys.exit(main())
