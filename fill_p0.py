#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 记录批量补全：把「只传了照片」的记录补齐成完整记录
=====================================================

为什么需要它：
  实际工作流是「先传照片，再补信息」。照片一传就是 2~3 张，
  但点位、时间、任务类型、观测值还得一条条填 —— 手工点太慢。
  这个脚本把「同一批照片」按指定参数一次性补齐。

用法：
  1) 先看有哪些记录没补齐
       python3 fill_p0.py --list

  2) 一次补一条（按记录ID或昵称）
       python3 fill_p0.py --nick 哼哼 --gate 3 --type 物种观察 \
              --obs "水鸟=2只" --text "湖面上有两只黑天鹅" --inject

  3) 批量：把某个昵称的所有未补全记录一起补
       python3 fill_p0.py --nick 阿布 --gate 3 --type 物种观察 \
              --obs "水鸟=3只" --text "芦苇边看到三只" --inject

  4) 补完写进产品
       python3 build_from_p0.py --inline

注意：
  --inject 才会设「注入产品=是」。不加就只补字段、不进产品，
  适合先整理再统一放行。
"""
import subprocess, json, os, sys, argparse
from datetime import datetime

CLI = '/Users/carachen/.workbuddy/binaries/node/cli-connector-packages/bin/lark-cli'
BASE = 'CACyb67OaaFXZPskQQtc6IDTnDc'
PROFILE = 'cli_aa514a33fcf85d1e'
T_P0 = 'tblrhQacJg8onRkh'

GATES = {1:'安河闸',2:'肖家河闸',3:'树村闸',4:'京包闸',5:'清河闸',
         6:'下清河闸',7:'羊坊闸',8:'外环跌水闸',9:'沈家闸',10:'沙子营闸'}

TYPES = ['水文观测','物种观察','岸线观察','异常通报']


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


def fetch_all():
    d = cli(['base', '+record-list', '--base-token', BASE, '--table-id', T_P0,
             '--as', 'user', '--format', 'json'])
    if not d.get('ok'):
        print('❌ 拉取失败：' + str(d.get('error', {}).get('message', ''))[:200])
        return None
    data = d['data']
    fields = data['fields']
    rows = data['data']
    ids = data['record_id_list']
    out = []
    for i, r in enumerate(rows):
        rec = dict(zip(fields, r))
        rec['_id'] = ids[i]
        out.append(rec)
    return out


def is_incomplete(rec):
    """照片有了但关键字段没填"""
    has_photo = bool(rec.get('照片'))
    return has_photo and (rec.get('点位编号') is None or rec.get('时间') is None)


def cmd_list():
    recs = fetch_all()
    if not recs:
        return 1
    inc = [r for r in recs if is_incomplete(r)]
    done = [r for r in recs if not is_incomplete(r)]
    print(f'共 {len(recs)} 条｜未补齐 {len(inc)}｜已完整 {len(done)}\n')

    if inc:
        print('未补齐（只传了照片）：')
        for r in inc:
            n = len(r.get('照片') or [])
            print(f"  {r['_id']}  {str(r.get('孩子昵称') or '—'):<8} 照片 {n} 张")
    if done:
        print('\n已完整：')
        for r in done:
            inj = r.get('注入产品')
            inj = inj[0] if isinstance(inj, list) and inj else '—'
            print(f"  {r['_id']}  {str(r.get('孩子昵称') or '—'):<8} "
                  f"点位{r.get('点位编号')}  {r.get('任务类型')}  注入={inj}")
    return 0


def cmd_fill(a):
    recs = fetch_all()
    if not recs:
        return 1

    # 支持按 record-id 精确指定（一个孩子的照片可能分属不同点位，得拆开填）
    if a.id:
        ids = [x.strip() for x in a.id.split(',')]
        targets = [r for r in recs if r['_id'] in ids]
        if not targets:
            print(f'❌ 没找到记录：{a.id}')
            return 1
    else:
        targets = [r for r in recs if r.get('孩子昵称') == a.nick]
        if not targets:
            print(f'❌ 没找到昵称「{a.nick}」的记录')
            return 1
        if a.only_incomplete:
            targets = [r for r in targets if is_incomplete(r)]
    if not targets:
        print('没有需要补的记录。')
        return 0

    if a.gate not in GATES:
        print('❌ 点位编号要在 1~10')
        return 1
    if a.type not in TYPES:
        print('❌ 任务类型要是：' + ' / '.join(TYPES))
        return 1

    now = a.time or datetime.now().strftime('%Y-%m-%d %H:%M')
    grade = 'A · 有照片' if any(r.get('照片') for r in targets) else 'B · 无照片'

    print(f'准备补 {len(targets)} 条：')
    for r in targets:
        print(f"  {r['_id']}  {r.get('孩子昵称')}  → 点位{a.gate}({GATES[a.gate]}) "
              f"{a.type} {a.obs or ''}")

    # record-batch-update 用 patch（字段→值 的映射），不是 fields+rows。
    # fields+rows 是 record-batch-create 的格式，混用会报 invalid_request。
    patch = {
        '点位编号': a.gate,
        '时间': now,
        '任务类型': a.type,
        '观测数值': a.obs or '',
        '观测文本': a.text or '',
        '分级': grade,
    }
    if a.memo:
        patch['备注'] = a.memo
    if a.inject:
        patch['注入产品'] = '是'

    payload = {
        'record_id_list': [r['_id'] for r in targets],
        'patch': patch,
    }

    d = cli(['base', '+record-batch-update', '--base-token', BASE,
             '--table-id', T_P0, '--as', 'user',
             '--json', json.dumps(payload, ensure_ascii=False)])
    if not d.get('ok'):
        print('❌ 更新失败：' + str(d.get('error', {}).get('message', ''))[:300])
        return 1

    print(f'\n✅ 已补 {len(targets)} 条' + ('，并设为「注入产品=是」' if a.inject else ''))
    if not a.inject:
        print('   要进产品，加 --inject 重跑，或去表里手动设「注入产品=是」')
    print('   下一步：python3 build_from_p0.py --inline')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true', help='列出未补齐的记录')
    ap.add_argument('--nick', help='孩子昵称')
    ap.add_argument('--id', help='按记录ID精确指定（逗号分隔多条）')
    ap.add_argument('--memo', default='', help='备注：素材来源、拍摄条件等')
    ap.add_argument('--gate', type=int, help='点位编号 1-10')
    ap.add_argument('--type', help='任务类型')
    ap.add_argument('--obs', default='', help='观测数值，如 水鸟=2只')
    ap.add_argument('--text', default='', help='观测文本：孩子自己的话')
    ap.add_argument('--time', default='', help='时间，默认现在')
    ap.add_argument('--inject', action='store_true', help='同时设为注入产品=是')
    ap.add_argument('--all', dest='only_incomplete', action='store_true',
                    default=True, help='该昵称下所有未补齐的都补（默认）')
    a = ap.parse_args()

    if a.list:
        return cmd_list()
    if not ((a.nick or a.id) and a.gate and a.type):
        ap.print_help()
        print('\n提示：先跑 --list 看看有哪些没补齐')
        return 1
    return cmd_fill(a)


if __name__ == '__main__':
    sys.exit(main())
