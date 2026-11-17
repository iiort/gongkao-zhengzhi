# -*- coding: utf-8 -*-
"""把 facts/*.json 合并成 web/data.js（含选项生成的题库）"""
import os, io, json, re, random, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC_DIR = os.path.join(ROOT, "sections")
FACT_DIR = os.path.join(ROOT, "facts")
WEB = os.path.join(ROOT, "web")

meta = json.load(io.open(os.path.join(SEC_DIR, "meta.json"), encoding="utf-8"))
secs = []
for i, m in enumerate(meta):
    m = dict(m)
    m["sid"] = "kp_%03d" % i
    m["items"] = []
    secs.append(m)
by_sid = {s["sid"]: s for s in secs}

def norm_q(q):
    q = q.replace("\u3000", " ")
    q = re.sub(r"_{2,}", "____", q)
    q = re.sub(r"\s+", "", q)
    return q

def clean_a(a):
    a = a.strip()
    a = a.strip("“”\"'「」《》 ")
    a = re.sub(r"[\s\u3000]+", "", a)
    return a

raw_facts = {}
bad = []
for fp in sorted(glob.glob(os.path.join(FACT_DIR, "*.json"))):
    base = os.path.basename(fp)[:-5]
    sids = base.split("+")
    try:
        data = json.load(io.open(fp, encoding="utf-8"))
    except Exception as e:
        bad.append((base, "JSON解析失败: %s" % e))
        continue
    facts = data.get("facts") if isinstance(data, dict) else data
    if not isinstance(facts, list):
        bad.append((base, "格式不对"))
        continue
    for f in facts:
        if not isinstance(f, dict):
            continue
        q = norm_q(str(f.get("q", "")))
        a = clean_a(str(f.get("a", "")))
        sec = str(f.get("sec", "")).strip()
        if sec not in sids:
            sec = sids[0]
        raw_facts.setdefault(sec, []).append((q, a, base))

# ---- 清洗 + 去重 ----
seen = set()
total_kept = 0
for s in secs:
    keep = []
    for q, a, base in raw_facts.get(s["sid"], []):
        if q.count("____") != 1:
            bad.append((base, "空位数量异常: " + q[:30]))
            continue
        if not a or len(a) > 24 or "____" in a:
            bad.append((base, "答案异常: " + a[:20]))
            continue
        if len(q) < 6 or len(q) > 130:
            bad.append((base, "句子长度异常: " + q[:30]))
            continue
        key = re.sub(r"[，。；：、,.;:“”\"'（）()《》]", "", q)
        if key in seen:
            continue
        seen.add(key)
        keep.append((q, a))
    s["items"] = keep
    total_kept += len(keep)

# ---- 选项生成 ----
rnd = random.Random(20260410)

all_answers = []
for s in secs:
    for q, a in s["items"]:
        all_answers.append(a)

# 章级别的池子
def chap_key(s):
    return (s["part"], s["pian"], s["zhang"])

pools_chap = {}
for s in secs:
    pools_chap.setdefault(chap_key(s), []).extend([a for q, a in s["items"]])

def pick_distractors(ans, s, q=""):
    cands = []
    local = [a for qq, a in s["items"] if a != ans]
    chap = [a for a in pools_chap.get(chap_key(s), []) if a != ans]
    glob_ = [a for a in all_answers if a != ans]
    for pool in (local, chap, glob_):
        c = [a for a in pool if a != ans and a not in cands and a not in q and abs(len(a) - len(ans)) <= 6]
        if len(c) >= 3:
            cands.extend(c)
            break
        cands.extend(c)
    # 去重保序
    out = []
    for a in cands:
        if a != ans and a not in out:
            out.append(a)
    if len(out) < 3:
        extra = [a for a in all_answers if a != ans and a not in out and a not in q]
        out.extend(extra)
    rnd.shuffle(out)
    return out[:3]

# ---- 组树 ----
def new_node(title):
    return {"title": title, "children": []}

parts = []
PART_NAMES = {"第一部分": "第一部分 政治理论", "第二部分": "第二部分 常识判断"}
for s in secs:
    if not s["items"]:
        continue
    levels = [x for x in [PART_NAMES.get(s["part"], s["part"]), s["pian"], s["zhang"], s["jie"], s["kp"]] if x]
    if not levels:
        continue
    cur = parts
    node = None
    for depth, title in enumerate(levels):
        found = None
        for n in cur:
            if n["title"] == title:
                found = n
                break
        if found is None:
            found = new_node(title)
            found["children"] = []
            cur.append(found)
        node = found
        cur = found["children"]
    if node is None:
        continue
    if "items" in node:
        node["children"] = []
    node["items"] = []
    for i, (q, a) in enumerate(s["items"]):
        opts = pick_distractors(a, s, q)
        opts = opts + [a]
        rnd.shuffle(opts)
        node["items"].append({
            "id": "%s_%02d" % (s["sid"], i),
            "q": q, "a": a, "opts": opts,
        })

def count_items(node):
    if "items" in node:
        return len(node["items"])
    return sum(count_items(c) for c in node["children"])

def prune(node):
    if "items" in node:
        return count_items(node) > 0
    node["children"] = [c for c in node["children"] if prune(c)]
    return len(node["children"]) > 0

parts = [p for p in parts if prune(p)]

total = sum(count_items(p) for p in parts)

out = {
    "generatedAt": "2026-04-10",
    "total": total,
    "parts": parts,
}

os.makedirs(WEB, exist_ok=True)
js = "window.QUIZ_DATA = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
io.open(os.path.join(WEB, "data.js"), "w", encoding="utf-8").write(js)

print("sections with items:", sum(1 for s in secs if s["items"]))
print("total items:", total)
print("bad:", len(bad))
for b in bad[:15]:
    print("  ", b)
io.open(os.path.join(ROOT, "tools", "merge_bad.json"), "w", encoding="utf-8").write(
    json.dumps(bad, ensure_ascii=False, indent=1))
