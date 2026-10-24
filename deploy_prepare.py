#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准备部署目录：把仓库里的 HTML 同步为 deploy/ 下的部署副本

为什么需要这一步：
  火山 veFaaS 的函数根目录必须有一个 index.html，
  但仓库里的主文件叫「小小河工.html」（中文名，便于人读）。
  用脚本同步，避免手工复制后忘记更新。

  拓印页也一样要进 deploy/，否则线上访问不到。
  之前是手动 cp，容易漏 —— 现在统一由这个脚本管。

用法：
  python3 deploy_prepare.py          # 同步文件
  python3 deploy_prepare.py --check  # 只检查是否一致（CI 用）
"""
import hashlib
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DEPLOY = os.path.join(ROOT, 'deploy')

# (源文件, 部署副本名, 是否重命名)
# 主文件要改名成 index.html；拓印页保持原名（前端用中文名跳转）
SYNC = [
    ('小小河工.html', 'index.html', 'index'),
    ('小小河工-拓印体验.html', '小小河工-拓印体验.html', 'stamp'),
]

# 部署必需的静态文件（server.js / bootstrap 保持手写，不参与同步）
REQUIRED = ['server.js', 'bootstrap']


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    check_only = '--check' in sys.argv

    missing_src = [s for s, _, _ in SYNC if not os.path.exists(os.path.join(ROOT, s))]
    if missing_src:
        print(f'❌ 找不到源文件：{missing_src}')
        return 1

    # 部署骨架完整性
    missing = [f for f in REQUIRED if not os.path.exists(os.path.join(DEPLOY, f))]
    if missing:
        print(f'❌ deploy/ 缺少文件：{missing}')
        return 1

    stale = []
    for src, dst_name, tag in SYNC:
        s = os.path.join(ROOT, src)
        d = os.path.join(DEPLOY, dst_name)

        if not os.path.exists(d):
            stale.append((s, d, tag, 'missing'))
            continue
        if md5(s) != md5(d):
            stale.append((s, d, tag, 'old'))

    if check_only:
        if not stale:
            print('✅ 部署副本与源文件一致')
            return 0
        print('❌ 以下部署副本已过期：')
        for s, d, tag, why in stale:
            print(f'   {os.path.basename(s)} → deploy/{os.path.basename(d)}（{why}）')
        print('   请运行 python3 deploy_prepare.py')
        return 1

    if not stale:
        print('✅ 已是最新，无需同步')
        return 0

    for s, d, tag, why in stale:
        shutil.copy2(s, d)
        kb = os.path.getsize(s) / 1024
        print(f'✅ 已同步 {os.path.basename(s)} → deploy/{os.path.basename(d)}（{kb:.0f} KB）')
        print(f'   md5: {md5(d)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
