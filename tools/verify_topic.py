# -*- coding: utf-8 -*-
"""核对专题题目的数字是否都能在纲要原文里找到"""
import io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
js = io.open(os.path.join(ROOT, "web", "data.js"), encoding="utf-8").read()
data = json.loads(js[js.index("=") + 1:].strip().rstrip(";"))

topic = data["parts"][0]
print("专题:", topic["title"], len(topic["children"]), "节")

src = {}
for c in topic["children"]:
    pass

meta = json.load(io.open(os.path.join(ROOT, "sections_topic", "meta.json"), encoding="utf-8"))
text = {m["id"]: io.open(os.path.join(ROOT, "sections_topic", m["file"]), encoding="utf-8").read() for m in meta}

num = re.compile(r"\d+(?:\.\d+)?")
bad = []
checked = 0
# 遍历题目
for c in topic["children"]:
    for q in c["qs"]:
        sid = q["id"].split("_")[0]
        t = text.get(sid, "")
        t2 = re.sub(r"[\s\u3000]", "", t)
        blob = re.sub(r"[\s\u3000]", "", q["q"] + q["o"][q["a"]] + (q.get("why") or ""))
        for n in set(num.findall(q["q"] + q["o"][q["a"]])):
            checked += 1
            if n not in t2:
                bad.append((sid, n, q["q"][:34], q["o"][q["a"]][:30]))

print("核对数字", checked, "个，未在原文找到:", len(bad))
for b in bad[:20]:
    print("  ", b)

