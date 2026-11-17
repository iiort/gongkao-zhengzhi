# -*- coding: utf-8 -*-
"""导出 v3：知识体系（树）+ 题库（含答案与解析），Markdown"""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
js = io.open(os.path.join(ROOT, "web", "data.js"), encoding="utf-8").read()
js = js[js.index("=") + 1:].strip().rstrip(";")
data = json.loads(js)

L = []
L.append("# 政治理论 · 常识判断 知识体系与题库")
L.append("")
L.append("> 按 部分 → 篇 → 章 → 节 → 知识点 排列，每个知识点先给**知识体系树**（框架与展开），"
         "再给**辨析题**（答案加粗，附解析）。共 %d 道题。" % data["total"])
L.append("")
L.append("> 配套练习网页：`政治理论挖空填词.html`")
L.append("")

def emit_tree(nodes, depth, out):
    for n in nodes:
        t = n.get("t", "")
        d = n.get("d", "")
        pad = "  " * depth
        line = pad + "- " + t
        if d:
            line += "　—— " + d
        out.append(line)
        if n.get("ch"):
            emit_tree(n["ch"], depth + 1, out)

LETTER = ["A", "B", "C", "D"]
counter = [0]

def render(node, depth):
    title = node["title"]
    if depth == 0:
        L.append("\n---\n")
        L.append("# " + title)
    elif depth == 1:
        L.append("\n## " + title)
    elif depth == 2:
        L.append("\n### " + title)
    elif depth == 3:
        L.append("\n#### " + title)
    else:
        L.append("\n##### " + title)

    if "qs" in node:
        if node.get("tree"):
            L.append("")
            L.append("**【知识体系】**")
            L.append("")
            emit_tree(node["tree"], 0, L)
        if node["qs"]:
            L.append("")
            L.append("**【辨析题】**")
            L.append("")
            for q in node["qs"]:
                counter[0] += 1
                L.append("%d. %s" % (counter[0], q["q"]))
                for i, o in enumerate(q["o"]):
                    mark = " **✓**" if i == q["a"] else ""
                    L.append("   %s. %s%s" % (LETTER[i], o, mark))
                if q.get("why"):
                    L.append("   > 解析：%s" % q["why"])
                if q.get("at"):
                    L.append("   > 体系位置：%s" % q["at"])
                L.append("")
        return
    for c in node.get("children", []):
        render(c, depth + 1)

for p in data["parts"]:
    render(p, 0)

out = os.path.join(ROOT, "知识点总表.md")
io.open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("written", out, len(L), "lines", counter[0], "questions")
