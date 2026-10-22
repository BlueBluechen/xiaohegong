# -*- coding: utf-8 -*-
"""把 demo.template.html 里的 GATES / META 数据注入 demo-m.template.html，
   生成最终可直接打开的 demo.html（单文件、无外部依赖）。"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "demo.template.html")      # 数据源（旧 16:9 版本，持有规范的十闸数据）
TPL = os.path.join(HERE, "demo-m.template.html")    # 竖版模板，含 /*__DATA__*/ 占位符
OUT = os.path.join(HERE, "demo.html")


def slice_block(src, start, end):
    i = src.index(start)
    j = src.index(end, i) + len(end)
    return src[i:j]


def main():
    src = open(SRC, encoding="utf-8").read()
    gates = slice_block(src, "const GATES=[", "\n];")
    meta = slice_block(src, "const META=[", "];")
    assign = "\nGATES.forEach((g,idx)=>Object.assign(g,META[idx]));\n"

    tpl = open(TPL, encoding="utf-8").read()
    out = tpl.replace("/*__DATA__*/", gates + "\n" + meta + assign)

    # 版式微调（模板里没固化、每次构建时施加）
    out = out.replace(
        ".coach{position:absolute;right:24px;z-index:6;",
        ".coach{position:absolute;right:24px;top:250px;z-index:6;",
    )
    open(OUT, "w", encoding="utf-8").write(out)
    print("built %s (%d KB)" % (OUT, os.path.getsize(OUT) // 1024))


if __name__ == "__main__":
    main()
