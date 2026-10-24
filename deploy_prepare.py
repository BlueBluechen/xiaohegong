#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准备部署目录：把 小小河工.html 同步为 deploy/index.html

为什么需要这一步：
  火山 veFaaS 的函数根目录必须有一个 index.html，
  但仓库里的主文件叫「小小河工.html」（中文名，便于人读）。
  用脚本同步，避免手工复制后忘记更新。

用法：
  python3 deploy_prepare.py          # 同步文件
  python3 deploy_prepare.py --check  # 只检查是否一致（CI 用）
"""
import hashlib
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, '小小河工.html')
DST = os.path.join(ROOT, 'deploy', 'index.html')

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

    if not os.path.exists(SRC):
        print(f'❌ 找不到源文件：{SRC}')
        return 1

    # 部署骨架完整性
    missing = [f for f in REQUIRED
               if not os.path.exists(os.path.join(ROOT, 'deploy', f))]
    if missing:
        print(f'❌ deploy/ 缺少文件：{missing}')
        return 1

    if not os.path.exists(DST):
        print('⚠️  deploy/index.html 不存在，将创建')
        if not check_only:
            shutil.copy2(SRC, DST)
        return 0

    same = md5(SRC) == md5(DST)

    if check_only:
        if same:
            print('✅ 部署副本与主文件一致')
            return 0
        print('❌ 部署副本已过期，请运行 python3 deploy_prepare.py')
        return 1

    if same:
        print('✅ 已是最新，无需同步')
        return 0

    size = os.path.getsize(SRC)
    shutil.copy2(SRC, DST)
    print(f'✅ 已同步 小小河工.html → deploy/index.html（{size / 1024:.0f} KB）')
    print(f'   md5: {md5(DST)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
