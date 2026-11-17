# -*- coding: utf-8 -*-
"""v3 题库体检 + 抽样"""
import io, json, os, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
js = io.open(os.path.join(ROOT, "web", "data.js"), encoding="utf-8").read()
js = js[js.index("=") + 1:].strip().rstrip(";")
data = json.loads(js)

items, trees = [], 0

def walk(n, path):
    global trees
    p = path + [n["title"]]
    if "qs" in n:
        if n.get("tree"):
            trees += 1
        for q in n["qs"]:
            q["_p"] = p
            items.append(q)
    for c in n.get("children", []):
        walk(c, p)

for p in data["parts"]:
    walk(p, [])

print("总题数:", len(items), " 有体系树的小节:", trees)
print("分部统计:", collections.Counter(q["_p"][0] for q in items).most_common())
print("题干长度 avg:", round(sum(len(q["q"]) for q in items) / len(items), 1))
print("选项数异常:", sum(1 for q in items if len(q["o"]) != 4 or len(set(q["o"])) != 4))
print("有解析:", sum(1 for q in items if q.get("why")), "/", len(items))
print("有体系位置:", sum(1 for q in items if q.get("at")), "/", len(items))

# 选项长度差异：越接近越难
import statistics
diffs = []
for q in items:
    ls = [len(o) for o in q["o"]]
    diffs.append(max(ls) - min(ls))
print("选项长度极差 中位数:", statistics.median(diffs), " 平均:", round(sum(diffs) / len(diffs), 1))

rnd = random.Random(11)
print("\n===== 抽样 14 题 =====")
for q in rnd.sample(items, 14):
    print("·", " / ".join(q["_p"][-1:]))
    print("  Q:", q["q"])
    for i, o in enumerate(q["o"]):
        print("    ", "ABCD"[i], ("✓ " if i == q["a"] else "  ") + o)
    print("    解析:", q.get("why", "")[:70])
