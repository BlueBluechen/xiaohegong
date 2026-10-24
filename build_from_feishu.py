#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从飞书多维表格拉取内容，生成 content.js，注入 小小河工.html

用法：
  python3 build_from_feishu.py            # 拉取并写 content.js
  python3 build_from_feishu.py --check    # 只校验，不写文件
  python3 build_from_feishu.py --inline   # 同时把内容内联回 HTML（原地更新）

设计：内容出问题时不能让页面白屏。
  - 拉取失败 → 保留现有 content.js，退出码 1
  - 缺字段   → 报错并列出具体缺哪个字段
  - 数量不符 → 警告但不阻断（允许运营临时删几条）
"""
import subprocess, json, os, sys, re

CLI = '/Users/carachen/.workbuddy/binaries/node/cli-connector-packages/bin/lark-cli'
BASE = 'CACyb67OaaFXZPskQQtc6IDTnDc'
PROFILE = 'cli_aa514a33fcf85d1e'
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'content.js')
HTML = os.path.join(ROOT, '小小河工.html')

T_GATES = 'tblidU4Jukf9jCqA'
T_HUNTS = 'tbl2GDHUV725XRfV'
T_KB    = 'tblxhYA09sFht9zC'


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


def fetch(table_id):
    """返回 markdown 表格 → 解析成 [{字段: 值}]"""
    d = cli(['base', '+record-list', '--base-token', BASE,
             '--table-id', table_id, '--as', 'user', '--format', 'markdown'])
    raw = d.get('raw') if isinstance(d, dict) and 'raw' in d else None
    # --format markdown 时 CLI 直接输出表格文本，不走 json；用单独调用
    env = dict(os.environ)
    env.pop('HTTPS_PROXY', None); env.pop('HTTP_PROXY', None)
    env['LARK_CLI_NO_PROXY'] = '1'
    p = subprocess.run([CLI, '--profile', PROFILE, 'base', '+record-list',
                        '--base-token', BASE, '--table-id', table_id,
                        '--as', 'user', '--format', 'markdown'],
                       capture_output=True, text=True, env=env)
    md = p.stdout
    lines = [l for l in md.split('\n') if l.startswith('|')]
    if len(lines) < 2:
        return [], []
    hdr = [c.strip() for c in lines[0].split('|')[1:-1]]
    rows = []
    for l in lines[2:]:
        cells = [c.strip() for c in l.split('|')[1:-1]]
        if len(cells) != len(hdr):
            continue
        rows.append(dict(zip(hdr, cells)))
    return hdr, rows


def num(v, default=None):
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except Exception:
        return default


def build():
    errors = []

    # ---------- 十座闸 ----------
    hdr, rows = fetch(T_GATES)
    need = ['编号', '名称', '段位', '类型', '来源', '公里', '纬度', '经度',
            '故事', '题目', '选项A', '选项B', '选项C', '选项D', '答案', '提示',
            '知识卡', '奖励', '任务', '任务说明',
            '任务A', '任务B', '任务C', '观测A', '观测B', '观测C',
            '回执A', '回执B', '回执C']
    miss = [n for n in need if n not in hdr]
    if miss:
        errors.append(f'十座闸缺字段: {miss}')

    gates = []
    for r in rows:
        gid = num(r.get('编号'))
        if not gid:          # 脏数据行（无编号）直接跳过
            continue
        name = r.get('名称', '').strip()
        if not name:
            continue
        opts = [r.get('选项A', ''), r.get('选项B', ''), r.get('选项C', ''), r.get('选项D', '')]
        topts = []
        for i, key in enumerate(['A', 'B', 'C']):
            obs_raw = r.get(f'观测{key}', '')
            obs = parse_obs(obs_raw)
            topts.append({
                't': r.get(f'任务{key}', ''),
                'r': r.get(f'回执{key}', ''),
                'obs': obs
            })
        gates.append({
            'id': gid,
            'name': name,
            'lat': num(r.get('纬度'), 0),
            'lng': num(r.get('经度'), 0),
            'seg': r.get('段位', ''),
            'type': r.get('类型', ''),
            'src': r.get('来源', ''),
            'km': num(r.get('公里'), 0),
            'story': r.get('故事', ''),
            'q': r.get('题目', ''),
            'opts': opts,
            'ans': num(r.get('答案'), 0),
            'hint': r.get('提示', ''),
            'k': r.get('知识卡', ''),
            'reward': r.get('奖励', ''),
            'task': {'q': r.get('任务', ''), 'sub': r.get('任务说明', ''), 'opts': topts}
        })
    gates.sort(key=lambda g: g['id'])

    if len(gates) != 10:
        errors.append(f'十座闸数量 {len(gates)}，期望 10')

    # ---------- 四宫格 ----------
    hdr2, rows2 = fetch(T_HUNTS)
    hunts = {}
    for r in rows2:
        gid = num(r.get('点位编号'))
        if not gid: continue
        if gid not in hunts:
            hunts[gid] = {'name': r.get('点位', ''), 'sub': '', 'cells': []}
        hunts[gid]['cells'].append({
            '_seq': num(r.get('格序'), 0),
            'id': r.get('格子ID', ''),
            'motif': r.get('拓印图', ''),
            'nm': r.get('名称', ''),
            'hint': r.get('提示', ''),
            'badge': r.get('印章字', '')
        })
    for gid, h in hunts.items():
        h['cells'].sort(key=lambda c: c['_seq'])   # 按格序，不能按字母
        for c in h['cells']:
            c.pop('_seq', None)
        h['sub'] = f"在 {h['name'].split(' · ')[0]} 走一圈，这四样东西应该还在。"
    if len(hunts) != 10:
        errors.append(f'四宫格点位 {len(hunts)}，期望 10')

    # ---------- 自然笔记 ----------
    hdr3, rows3 = fetch(T_KB)
    kb = []
    for r in rows3:
        n = r.get('名称', '').strip()
        if not n: continue
        kb.append({'n': n, 'tag': r.get('标签', ''),
                   'f1': r.get('形态', ''), 'f2': r.get('作用', ''), 'f3': r.get('值得记', '')})
    if len(kb) != 8:
        errors.append(f'自然笔记 {len(kb)} 条，期望 8')

    # ---------- 汇总 ----------
    print(f'十座闸 {len(gates)} / 四宫格点位 {len(hunts)} ({sum(len(h["cells"]) for h in hunts.values())} 格) / 词条 {len(kb)}')
    if errors:
        print('\n⚠️  问题：')
        for e in errors: print('  -', e)
        return None, errors

    return {'gates': gates, 'hunts': hunts, 'kb': kb}, []


def parse_obs(s):
    """'透明度=3级(高（看得见水底）)' → [{key,num,unit,txt}]
       支持 '；' 分隔多个"""
    if not s: return []
    out = []
    for part in s.split('；'):
        part = part.strip()
        if not part: continue
        m = re.match(r'^(.+?)=([\d.]+|—|None|null)([^\(]*)\((.*)\)$', part)
        if m:
            key, val, unit, txt = m.groups()
            if val in ('—', 'None', 'null'):
                nv = None
            else:
                nv = int(float(val)) if float(val) == int(float(val)) else float(val)
            out.append({'key': key.strip(), 'num': nv,
                        'unit': unit.strip(), 'txt': txt.strip()})
        else:
            out.append({'key': part, 'num': None, 'unit': '', 'txt': ''})
    return out


def emit(data, inline=False):
    js_lines = ['/* 自动生成 · 请勿手改',
                '   来源：飞书 Base ' + BASE,
                '   生成：build_from_feishu.py',
                '   —— 要改内容，改飞书表格，然后重跑脚本 —— */',
                '']
    js_lines.append('const GATES=' + json.dumps(data['gates'], ensure_ascii=False, indent=0).replace('\n', '') + ';')
    js_lines.append('')
    js_lines.append('const HUNTS=' + json.dumps(data['hunts'], ensure_ascii=False, indent=0).replace('\n', '') + ';')
    js_lines.append('')
    js_lines.append('const KB=' + json.dumps(data['kb'], ensure_ascii=False, indent=0).replace('\n', '') + ';')
    text = '\n'.join(js_lines)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'✅ 已写 {OUT} ({len(text):,} 字节)')

    if inline:
        html = open(HTML, encoding='utf-8').read()
        blocks = [
            ('GATES', json.dumps(data['gates'], ensure_ascii=False).replace('\n', '')),
            ('HUNTS', json.dumps(data['hunts'], ensure_ascii=False).replace('\n', '')),
            ('KB',    json.dumps(data['kb'], ensure_ascii=False).replace('\n', '')),
        ]
        # 关键：从后往前替换，且用「下一个 const/ 或 </script>」做右边界，
        # 不靠括号配平（MOTIF 里的 base64 会干扰扫描）
        cnt = 0
        for name, body in blocks:
            anchor = f'const {name}='
            i = html.find(anchor)
            if i < 0:
                print(f'  ⚠️ 找不到 {name}')
                continue
            # 右边界：从 anchor 往后找下一个 "const " 或 "</script>"
            j = len(html)
            for mark in ('\nconst ', '\n\nconst ', '</script>'):
                k = html.find(mark, i + len(anchor))
                if k > 0 and k < j:
                    j = k
            seg = html[i:j]
            # 保留段尾的换行（如果有）
            tail = '\n' if seg.endswith('\n') else ''
            html = html[:i] + f'const {name}={body};' + tail + html[j:]
            cnt += 1

        if '内容源：飞书 Base' not in html:
            html = html.replace(
                '<script>',
                f'<script>\n/* 内容源：飞书 Base {BASE} · 由 build_from_feishu.py 生成，勿手改 */',
                1)

        open(HTML, 'w', encoding='utf-8').write(html)
        print(f'✅ 已内联回 HTML（{cnt} 块常量，{len(html):,} 字节）')


def main():
    data, errs = build()
    if not data:
        print('\n❌ 构建中止，content.js 未改。')
        return 1
    if '--check' in sys.argv:
        print('\n✅ 校验通过（未写文件）')
        return 0
    emit(data, '--inline' in sys.argv)
    return 0


if __name__ == '__main__':
    sys.exit(main())
