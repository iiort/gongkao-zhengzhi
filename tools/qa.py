# -*- coding: utf-8 -*-
"""题库质量检查 + 抽样"""
import io, json, os, re, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
js = io.open(os.path.join(ROOT, "web", "data.js"), encoding="utf-8").read()
js = js[js.index("=") + 1:].strip().rstrip(";")
data = json.loads(js)

items = []
def walk(n, path):
    p = path + [n["title"]]
    if "items" in n:
        for it in n["items"]:
            it["_path"] = p
            items.append(it)
    for c in n.get("children", []):
        walk(c, p)

for p in data["parts"]:
    walk(p, [])

print("总题数:", len(items))
per_part = collections.Counter(it["_path"][0] for it in items)
for k, v in per_part.items():
    print("  ", k, v)

# 结构检查
bad_opts = [it for it in items if len(set(it["opts"])) != 4 or it["a"] not in it["opts"]]
print("选项异常:", len(bad_opts))
n_shi = sum(1 for it in items if ("是" in it["q"] or "指" in it["q"] or "标志着" in it["q"]))
print("含判断词的句子:", n_shi, "/", len(items))
print("答案长度分布:", collections.Counter(min(len(it["a"]) // 4 * 4, 20) for it in items).most_common())
print("题目长度(min/avg/max):", min(len(it["q"]) for it in items),
      round(sum(len(it["q"]) for it in items) / len(items), 1), max(len(it["q"]) for it in items))

dups = collections.Counter(re.sub(r"[，。；：、]", "", it["q"]) for it in items)
print("完全重复:", sum(1 for k, v in dups.items() if v > 1))

rnd = random.Random(7)
print("\n===== 抽样 24 题 =====")
for it in rnd.sample(items, 24):
    print("·", " / ".join(it["_path"][-2:]))
    print("  Q:", it["q"])
    print("  A:", it["a"], " | 选项:", it["opts"])
