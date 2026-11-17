# -*- coding: utf-8 -*-
"""把 facts3/*.json（体系树 + 易混选择题）合并成 web/data.js"""
import os, io, json, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC_DIR = os.path.join(ROOT, "sections")
FACT_DIR = os.path.join(ROOT, "facts3")
WEB = os.path.join(ROOT, "web")

meta = json.load(io.open(os.path.join(SEC_DIR, "meta.json"), encoding="utf-8"))
PART_NAMES = {"第一部分": "第一部分 政治理论", "第二部分": "第二部分 常识判断"}

secs = []
for i, m in enumerate(meta):
    m = dict(m)
    m["sid"] = "kp_%03d" % i
    m["qs"] = []
    m["tree"] = []
    secs.append(m)
by_sid = {s["sid"]: s for s in secs}

bad = []
seen_q = set()

def norm_q(s):
    return re.sub(r"[\s\u3000，。；：、,.;:!?！？“”\"'（）()《》]", "", s)

for fp in sorted(glob.glob(os.path.join(FACT_DIR, "*.json"))):
    base = os.path.basename(fp)[:-5]
    try:
        data = json.load(io.open(fp, encoding="utf-8-sig"))
    except Exception as e:
        bad.append((base, "JSON 解析失败: %s" % e))
        continue
    sections = data.get("sections") if isinstance(data, dict) else data
    if not isinstance(sections, list):
        bad.append((base, "顶层格式不对"))
        continue
    for s in sections:
        sid = str(s.get("id", "")).strip()
        if sid not in by_sid:
            continue
        target = by_sid[sid]
        if not target["tree"] and isinstance(s.get("tree"), list):
            target["tree"] = s["tree"]
        qs = s.get("qs") or []
        for q in qs:
            if not isinstance(q, dict):
                continue
            text = str(q.get("q", "")).strip()
            opts = q.get("o")
            a = q.get("a")
            if not text or not isinstance(opts, list) or len(opts) != 4:
                bad.append((sid, "字段不全"))
                continue
            opts = [str(x).strip() for x in opts]
            if any(not x for x in opts) or len(set(opts)) != 4:
                bad.append((sid, "选项重复/为空: " + text[:16]))
                continue
            if not isinstance(a, int) or a < 0 or a > 3:
                bad.append((sid, "答案下标异常"))
                continue
            key = norm_q(text)
            if key in seen_q:
                continue
            seen_q.add(key)
            target["qs"].append({
                "q": text,
                "o": opts,
                "a": a,
                "why": str(q.get("why", "")).strip(),
                "at": str(q.get("at", "")).strip(),
            })

# 编号
for s in secs:
    for i, q in enumerate(s["qs"]):
        q["id"] = "%s_%02d" % (s["sid"], i)

# ---------------------------------------------------------------
# 打乱选项顺序：原始数据里正确答案严重偏向 A，这里统一重排，
# 并把解析里「A项 / B项 / 选项C」的指代同步改写。
# ---------------------------------------------------------------
import random
rnd = random.Random(20260411)
LETTERS = "ABCD"


def remap_letters(text, mapping):
    # 先保护不是「选项」的字母：维生素A、D、E、K / B族 / A型血 等
    protect = []

    def hold(m):
        protect.append(m.group(0))
        return "\x00%d\x00" % (len(protect) - 1)

    text = re.sub(r"维生素[A-Za-z0-9、\s]*", hold, text)
    text = re.sub(r"[ABCD]族", hold, text)
    text = re.sub(r"[ABCD]型", hold, text)

    def sub_ref(m):
        return mapping.get(m.group(1), m.group(1))

    # A项 / B、 / C是 / D为 —— 前瞻匹配，不吞掉后面的字
    text = re.sub(r"([ABCD])(?=(项|、|是|为|对应|属于|错|也|和|与))", sub_ref, text)
    # 选项A
    text = re.sub(r"(?<=选项)([ABCD])", lambda m: mapping.get(m.group(1), m.group(1)), text)

    def back(m):
        return protect[int(m.group(1))]

    return re.sub(r"\x00(\d+)\x00", back, text)


res = {"before": [0, 0, 0, 0], "after": [0, 0, 0, 0]}
for s in secs:
    for q in s["qs"]:
        res["before"][q["a"]] += 1
        order = [0, 1, 2, 3]
        rnd.shuffle(order)                       # order[new] = old
        old_opts, old_ans = q["o"], q["a"]
        q["o"] = [old_opts[i] for i in order]
        q["a"] = order.index(old_ans)
        mapping = {LETTERS[old]: LETTERS[order.index(old)] for old in range(4)}
        if q.get("why"):
            q["why"] = remap_letters(q["why"], mapping)
        res["after"][q["a"]] += 1
print("答案分布 打乱前", res["before"], "打乱后", res["after"])

def new_node(title):
    return {"title": title, "children": []}


# 组树
def count_qs(node):
    if "qs" in node:
        return len(node["qs"])
    return sum(count_qs(c) for c in node["children"])

def prune(node):
    if "qs" in node:
        return len(node["qs"]) > 0
    node["children"] = [c for c in node["children"] if prune(c)]
    return len(node["children"]) > 0

parts = []
for s in secs:
    if not s["qs"]:
        continue
    levels = [PART_NAMES.get(s["part"], s["part"]), s["pian"], s["zhang"], s["jie"], s["kp"]]
    levels = [x for x in levels if x]
    cur_list = parts
    node = None
    for title in levels:
        found = None
        for n in cur_list:
            if n["title"] == title:
                found = n
                break
        if found is None:
            found = {"title": title, "children": []}
            cur_list.append(found)
        node = found
        cur_list = found["children"]
    if node is None:
        continue
    node["qs"] = s["qs"]
    node["tree"] = s["tree"]

parts = [p for p in parts if prune(p)]

# ---------------------------------------------------------------
# 专题：十五五规划（来自 facts_topic，独立成一棵树，放在最前面）
# ---------------------------------------------------------------
TOPIC_DIR = os.path.join(ROOT, "facts_topic")
TOPIC_META = os.path.join(ROOT, "sections_topic", "meta.json")
if os.path.isdir(TOPIC_DIR):
    tmeta = json.load(io.open(TOPIC_META, encoding="utf-8"))
    tby = {m["id"]: m for m in tmeta}
    topic = {}
    for fp in sorted(glob.glob(os.path.join(TOPIC_DIR, "*.json"))):
        base = os.path.basename(fp)[:-5]
        try:
            data = json.load(io.open(fp, encoding="utf-8-sig"))
        except Exception as e:
            print("专题文件解析失败", base, e)
            continue
        for s in data.get("sections", []):
            sid = str(s.get("id", "")).strip()
            if sid not in tby:
                continue
            qs = []
            for q in s.get("qs") or []:
                text = str(q.get("q", "")).strip()
                opts = q.get("o")
                a = q.get("a")
                if not text or not isinstance(opts, list) or len(opts) != 4:
                    continue
                opts = [str(x).strip() for x in opts]
                if any(not x for x in opts) or len(set(opts)) != 4:
                    continue
                if not isinstance(a, int) or a < 0 or a > 3:
                    continue
                qs.append({"q": text, "o": opts, "a": a,
                           "why": str(q.get("why", "")).strip(),
                           "at": str(q.get("at", "")).strip()})
            topic[sid] = {"tree": s.get("tree") or [], "qs": qs}

    # 打乱专题题目的选项（与教材题同样处理）
    for sid, t in topic.items():
        for q in t["qs"]:
            order = [0, 1, 2, 3]
            rnd.shuffle(order)
            old_opts, old_ans = q["o"], q["a"]
            q["o"] = [old_opts[i] for i in order]
            q["a"] = order.index(old_ans)
            mapping = {LETTERS[old]: LETTERS[order.index(old)] for old in range(4)}
            if q.get("why"):
                q["why"] = remap_letters(q["why"], mapping)

    tchildren = []
    for m in tmeta:
        t = topic.get(m["id"])
        if not t or not t["qs"]:
            continue
        for i, q in enumerate(t["qs"]):
            q["id"] = "%s_%02d" % (m["id"], i)
        tchildren.append({"title": m["title"], "children": [], "qs": t["qs"], "tree": t["tree"]})
    if tchildren:
        parts.insert(0, {"title": "专题·十五五规划（2026—2030）", "children": tchildren})
        print("专题小节:", len(tchildren), "题数:", sum(len(c["qs"]) for c in tchildren))

total = sum(count_qs(p) for p in parts)

out = {"generatedAt": "2026-11-17", "total": total, "parts": parts}
js = "window.QUIZ_DATA = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
io.open(os.path.join(WEB, "data.js"), "w", encoding="utf-8").write(js)

secs_with_q = sum(1 for s in secs if s["qs"])
print("有题小节:", secs_with_q, "/", len(secs))
print("总题数:", total)
print("异常:", len(bad))
for b in bad[:12]:
    print("  ", b)
io.open(os.path.join(ROOT, "tools", "merge3_bad.json"), "w", encoding="utf-8").write(
    json.dumps(bad, ensure_ascii=False, indent=1))

