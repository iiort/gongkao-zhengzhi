# -*- coding: utf-8 -*-
"""Split extracted text of 理论讲练 into per-知识点 UTF-8 files with full hierarchy."""
import os, re, json

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(SRC, "text")
OUT = os.path.join(SRC, "sections")
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.startswith("消化清单_") or f.startswith("理论讲练_"):
        os.remove(os.path.join(OUT, f))

CN = "一二三四五六七八九十"

def clean(raw):
    out = []
    for ln in raw.split("\n"):
        s = ln.strip()
        if not s or s.startswith("===== PAGE") or s.startswith("抖音关注公考小黑老师"):
            continue
        out.append(s)
    return "\n".join(out)

HEAD = re.compile(r"^(第[" + CN + r"]+部分|第[" + CN + r"]+篇|第[" + CN + r"]+章|第[" + CN + r"]+节|知识点\s*\d+)\s*[:：]?\s*(.*)$")

def split_file(path, start_marker):
    raw = open(path, encoding="utf-8").read()
    idx = raw.find(start_marker)
    if idx > 0:
        raw = raw[idx:]
    txt = clean(raw)
    sections = []
    cur = {"part": "", "pian": "", "zhang": "", "jie": "", "kp": "", "body": []}
    for ln in txt.split("\n"):
        m = HEAD.match(ln) if len(ln) < 70 else None
        if m:
            kind = m.group(1)
            if kind.endswith("部分"):
                cur = {"part": ln, "pian": "", "zhang": "", "jie": "", "kp": "", "body": []}
            elif kind.endswith("篇"):
                cur = {"part": cur["part"], "pian": ln, "zhang": "", "jie": "", "kp": "", "body": []}
            elif kind.endswith("章"):
                cur = {"part": cur["part"], "pian": cur["pian"], "zhang": ln, "jie": "", "kp": "", "body": []}
            elif kind.endswith("节"):
                cur = {"part": cur["part"], "pian": cur["pian"], "zhang": cur["zhang"], "jie": ln, "kp": "", "body": []}
            else:
                cur = {"part": cur["part"], "pian": cur["pian"], "zhang": cur["zhang"], "jie": cur["jie"], "kp": ln, "body": []}
            sections.append(cur)
        else:
            cur["body"].append(ln)
    res = []
    for s in sections:
        body = "\n".join(s["body"]).strip()
        if len(body) < 60 or "......." in s["kp"]:
            continue
        s["body"] = body
        res.append(s)
    return res

secs = split_file(os.path.join(TEXT, "【理论讲练】政治理论&常识判断.txt"), "第一部分\n政治理论")
meta = []
for i, s in enumerate(secs):
    hdr = " / ".join([x for x in [s["part"], s["pian"], s["zhang"], s["jie"], s["kp"]] if x])
    dst = os.path.join(OUT, "kp_%03d.txt" % i)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(hdr + "\n\n" + s["body"])
    meta.append({"file": os.path.basename(dst), "header": hdr, "part": s["part"], "pian": s["pian"],
                 "zhang": s["zhang"], "jie": s["jie"], "kp": s["kp"], "chars": len(s["body"])})

with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)

print("sections:", len(meta), "chars:", sum(m["chars"] for m in meta))
for m in meta:
    print(m["file"], m["chars"], m["header"][:80])
