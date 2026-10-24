#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 小小河工.html 里的内联内容迁移到飞书多维表格

用法：
  python3 migrate_content.py              # 全量迁移（建字段 + 灌数据）
  python3 migrate_content.py --fields     # 只建字段
  python3 migrate_content.py --records    # 只灌数据

依赖：lark-cli 已配置 profile cli_aa514a33fcf85d1e 且 user 身份已授权
"""
import json, re, subprocess, sys, os, tempfile

BASE = 'CACyb67OaaFXZPskQQtc6IDTnDc'
PROFILE = 'cli_aa514a33fcf85d1e'
CLI = '/Users/carachen/.workbuddy/binaries/node/cli-connector-packages/bin/lark-cli'
if not os.path.exists(CLI):
    CLI = 'lark-cli'
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), '小小河工.html')

def cli(args, check=True):
    """调 lark-cli，返回 (ok, data)"""
    cmd = [CLI, '--profile', PROFILE] + args
    env = dict(os.environ)
    env.pop('HTTPS_PROXY', None); env.pop('HTTP_PROXY', None)
    env['LARK_CLI_NO_PROXY'] = '1'
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    out = p.stdout.strip()
    # 去掉 WARN 行
    out = '\n'.join(l for l in out.split('\n') if not l.startswith('[lark-cli]'))
    try:
        d = json.loads(out)
    except Exception:
        return False, {'raw': out[-800:]}
    return bool(d.get('ok')), d

def extract():
    """从 HTML 抽出四块内容"""
    s = open(HTML, encoding='utf-8').read()

    def grab(name, open_ch, close_ch):
        i = s.find(f'const {name}={open_ch}')
        assert i > 0, f'找不到 {name}'
        # 括号配平
        depth = 0; j = i + len(f'const {name}=')
        start = j
        while j < len(s):
            c = s[j]
            if c == open_ch: depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    j += 1; break
            j += 1
        return s[start:j]

    gates_js = grab('GATES', '[', ']')
    hunts_js = grab('HUNTS', '{', '}')
    kb_js    = grab('KB', '[', ']')
    # MOTIF 太大且已在 HTML 里，不迁（图走 key 引用）
    return gates_js, hunts_js, kb_js

def js_eval(expr):
    """用 node 求值 JS 字面量，最可靠（能处理裸键、单双引号、尾逗号）"""
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write('const v = ' + expr + ';\n')
        f.write('process.stdout.write(JSON.stringify(v));\n')
        tmp = f.name
    node = '/Users/carachen/.workbuddy/binaries/node/versions/22.22.2-6/bin/node'
    p = subprocess.run([node, tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if p.returncode != 0:
        raise RuntimeError('node 求值失败: ' + p.stderr[:300])
    return json.loads(p.stdout)

def main():
    only_fields = '--fields' in sys.argv
    only_records = '--records' in sys.argv

    print('读取 HTML 内容…')
    gates_js, hunts_js, kb_js = extract()
    gates = js_eval(gates_js)
    hunts = js_eval(hunts_js)
    kb    = js_eval(kb_js)
    print(f'  十闸 {len(gates)} / 四宫格点位 {len(hunts)} / 词条 {len(kb)}')

    # ---------- 表清单 ----------
    ok, d = cli(['base', '+table-list', '--base-token', BASE, '--as', 'user'])
    if not ok:
        print('列不出表：', d); return 1
    tables = {t['name']: t['id'] for t in d['data']['tables']}
    print('现有表：', tables)

    # 十座闸表：优先「十座闸」，否则用第一张（默认表）
    T_GATES = tables.get('十座闸') or (list(tables.values())[0] if tables else None)
    print('十座闸表 id =', T_GATES)

    # ---------- 建字段 ----------
    if not only_records:
        want = [
            ('编号', {'type': 'number'}),
            ('名称', {'type': 'text'}),
            ('段位', {'type': 'text'}),
            ('类型', {'type': 'text'}),
            ('来源', {'type': 'text'}),
            ('公里', {'type': 'number'}),
            ('纬度', {'type': 'number'}),
            ('经度', {'type': 'number'}),
            ('故事', {'type': 'text'}),
            ('题目', {'type': 'text'}),
            ('选项A', {'type': 'text'}),
            ('选项B', {'type': 'text'}),
            ('选项C', {'type': 'text'}),
            ('选项D', {'type': 'text'}),
            ('答案', {'type': 'number'}),
            ('提示', {'type': 'text'}),
            ('知识卡', {'type': 'text'}),
            ('奖励', {'type': 'text'}),
            ('任务', {'type': 'text'}),
            ('任务说明', {'type': 'text'}),
            ('任务A', {'type': 'text'}),
            ('任务B', {'type': 'text'}),
            ('任务C', {'type': 'text'}),
            ('观测A', {'type': 'text'}),
            ('观测B', {'type': 'text'}),
            ('观测C', {'type': 'text'}),
            ('回执A', {'type': 'text'}),
            ('回执B', {'type': 'text'}),
            ('回执C', {'type': 'text'}),
        ]
        ok, d = cli(['base', '+field-list', '--base-token', BASE,
                     '--table-id', T_GATES, '--as', 'user'])
        have = {f['name'] for f in d['data']['fields']} if ok else set()
        print(f'  已有字段 {len(have)} 个')

        for name, prop in want:
            if name in have:
                continue
            body = {'name': name}; body.update(prop)
            ok, d = cli(['base', '+field-create', '--base-token', BASE,
                         '--table-id', T_GATES, '--json', json.dumps(body, ensure_ascii=False),
                         '--as', 'user'])
            print(f'  字段 {name}: {"OK" if ok else "FAIL " + str(d.get("error",{}).get("message",""))[:60]}')

    if only_fields:
        print('仅建字段，结束。'); return 0

    # ---------- 灌数据：十座闸 ----------
    NUM = {'编号','公里','纬度','经度','答案'}
    fields = ['编号','名称','段位','类型','来源','公里','纬度','经度',
              '故事','题目','选项A','选项B','选项C','选项D','答案','提示','知识卡','奖励',
              '任务','任务说明','任务A','任务B','任务C','观测A','观测B','观测C',
              '回执A','回执B','回执C']
    rows = []
    for g in gates:
        o = g['opts']; t = g['task']['opts']
        def obs(i):
            if i >= len(t): return ''
            return '；'.join(f"{x['key']}={x.get('num')}{x['unit']}({x['txt']})" for x in t[i]['obs'])
        rows.append([
            g['id'], g['name'], g.get('seg',''), g.get('type',''), g.get('src',''),
            g.get('km',0), g.get('lat'), g.get('lng'),
            g.get('story',''), g.get('q',''),
            o[0], o[1], o[2], o[3] if len(o)>3 else '', g.get('ans',0),
            g.get('hint',''), g.get('k',''), g.get('reward',''),
            g['task']['q'] if g.get('task') else '', g['task'].get('sub',''),
            t[0]['t'] if len(t)>0 else '', t[1]['t'] if len(t)>1 else '', t[2]['t'] if len(t)>2 else '',
            obs(0), obs(1), obs(2),
            t[0]['r'] if len(t)>0 else '', t[1]['r'] if len(t)>1 else '', t[2]['r'] if len(t)>2 else '',
        ])

    # 数字列强转（该版本对字符串写 number 字段会静默失败）
    for r in rows:
        for i, f in enumerate(fields):
            if f in NUM:
                v = r[i]
                if v is None or v == '':
                    r[i] = None
                else:
                    try:
                        r[i] = int(v) if float(v) == int(v) else round(float(v), 4)
                    except Exception:
                        r[i] = None
    ok, d = cli(['base', '+record-batch-create', '--base-token', BASE,
                 '--table-id', T_GATES,
                 '--json', json.dumps({'fields': fields, 'rows': rows}, ensure_ascii=False),
                 '--as', 'user'])
    print(f'十座闸写入：{"OK" if ok else "FAIL"} {d.get("error",{}).get("message","")[:100] if not ok else str(len(rows))+" 行"}')

    # ---------- 四宫格 ----------
    T_H = tables.get('四宫格')
    if not T_H:
        ok, d = cli(['base', '+table-create', '--base-token', BASE, '--name', '四宫格', '--as', 'user'])
        print('建四宫格表:', 'OK' if ok else str(d)[:120])
        if ok:
            T_H = d['data']['table']['id']
    if T_H:
            for n, p in [('点位编号',{'type':'number'}),('点位',{'type':'text'}),
                         ('格序',{'type':'number'}),('格子ID',{'type':'text'}),
                         ('名称',{'type':'text'}),('提示',{'type':'text'}),
                         ('拓印图',{'type':'text'}),('印章字',{'type':'text'})]:
                body={'name':n}; body.update(p)
                cli(['base','+field-create','--base-token',BASE,'--table-id',T_H,
                     '--json',json.dumps(body,ensure_ascii=False),'--as','user'])
            hrows=[]
            for gid, h in hunts.items():
                for i, c in enumerate(h['cells']):
                    hrows.append([int(gid), h['name'], i+1, c['id'], c['nm'], c.get('hint',''),
                                  c.get('motif',''), c.get('badge','')])
            for r in hrows:
                r[0] = int(r[0]); r[2] = int(r[2])
            ok2, d2 = cli(['base','+record-batch-create','--base-token',BASE,'--table-id',T_H,
                           '--json',json.dumps({'fields':['点位编号','点位','格序','格子ID','名称','提示','拓印图','印章字'],'rows':hrows},ensure_ascii=False),
                           '--as','user'])
            print('四宫格写入:', 'OK' if ok2 else str(d2)[:120])

    # ---------- 自然笔记 ----------
    T_K = tables.get('自然笔记')
    if not T_K:
        ok, d = cli(['base', '+table-create', '--base-token', BASE, '--name', '自然笔记', '--as', 'user'])
        print('建自然笔记表:', 'OK' if ok else str(d)[:120])
        if ok:
            T_K = d['data']['table']['id']
    if T_K:
            for n in ['名称','标签','形态','作用','值得记']:
                cli(['base','+field-create','--base-token',BASE,'--table-id',T_K,
                     '--json',json.dumps({'name':n,'type':'text'},ensure_ascii=False),'--as','user'])
            krows=[[x['n'],x['tag'],x['f1'],x['f2'],x['f3']] for x in kb]
            ok2,d2 = cli(['base','+record-batch-create','--base-token',BASE,'--table-id',T_K,
                          '--json',json.dumps({'fields':['名称','标签','形态','作用','值得记'],'rows':krows},ensure_ascii=False),
                          '--as','user'])
            print('自然笔记写入:', 'OK' if ok2 else str(d2)[:120])

    print('\n完成。Base:', f'https://my.feishu.cn/base/{BASE}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
