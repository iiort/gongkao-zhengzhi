# -*- coding: utf-8 -*-
"""把纲要全文切成 18 个专题小节"""
import io, os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sections_topic")
raw = io.open(os.path.join(OUT, "_raw.txt"), encoding="utf-8").read()

pat = re.compile(r"\*\*第([一二三四五六七八九十]+)篇")
marks = [m.start() for m in pat.finditer(raw)]
marks.append(len(raw))
pian = {}
for i in range(len(marks) - 1):
    chunk = raw[marks[i]:marks[i + 1]].strip()
    head = chunk.split("\n")[0].strip("* \t　")
    # 取「第X篇」
    key = head.split("　")[0].split(" ")[0]
    pian[key] = chunk
    pian[key.replace("第", "篇")] = chunk

print("keys:", list(pian.keys())[:6])

# 第一篇按章再切
p1 = pian["第一篇"]
i2 = p1.find("**第二章")
i3 = p1.find("**第三章")
ch1 = p1[:i2].strip()
ch2 = p1[i2:i3].strip()
ch3 = p1[i3:].strip()

def clean(t):
    t = re.sub(r"\*\*", "", t)
    t = re.sub(r"\n+", "\n", t)
    return t.strip()

SECTIONS = [
    ("s01", "第一篇 奋力开创中国式现代化建设新局面 / 第一章 发展环境（“十四五”成就与“十五五”发展环境）", clean(ch1)),
    ("s02", "第一篇 / 第二章 指导方针（指导思想与六条必须遵循的原则）", clean(ch2)),
    ("s03", "第一篇 / 第三章 主要目标（七个方面目标与关键指标）", clean(ch3)),
    ("s04", "第二篇 建设现代化产业体系　巩固壮大实体经济根基", clean(pian["第二篇"])),
    ("s05", "第三篇 加快高水平科技自立自强　引领发展新质生产力", clean(pian["第三篇"])),
    ("s06", "第四篇 深入推进数字中国建设　提升数智化发展水平", clean(pian["第四篇"])),
    ("s07", "第五篇 建设强大国内市场　加快构建新发展格局", clean(pian["第五篇"])),
    ("s08", "第六篇 加快构建高水平社会主义市场经济体制　增强高质量发展动力", clean(pian["第六篇"])),
    ("s09", "第七篇 扩大高水平对外开放　开创合作共赢新局面", clean(pian["第七篇"])),
    ("s10", "第八篇 加快农业农村现代化　扎实推进乡村全面振兴", clean(pian["第八篇"])),
    ("s11", "第九篇 优化区域经济布局　促进区域协调发展", clean(pian["第九篇"])),
    ("s12", "第十篇 激发全民族文化创新创造活力　繁荣发展社会主义文化", clean(pian["第十篇"])),
    ("s13", "第十一篇 完善人口发展战略　促进人口高质量发展", clean(pian["第十一篇"])),
    ("s14", "第十二篇 加大保障和改善民生力度　扎实推进全体人民共同富裕", clean(pian["第十二篇"])),
    ("s15", "第十三篇 加快经济社会发展全面绿色转型　建设美丽中国", clean(pian["第十三篇"])),
    ("s16", "第十四篇 推进国家安全体系和能力现代化　建设更高水平平安中国", clean(pian["第十四篇"])),
    ("s17", "第十五篇 如期实现建军一百年奋斗目标 与 第十七篇 坚持和完善“一国两制” 推进祖国统一",
     clean(pian["第十五篇"]) + "\n\n" + clean(pian["第十七篇"])),
    ("s18", "第十六篇 发展全过程人民民主　完善中国特色社会主义法治体系 与 第十八篇 加强规划实施保障",
     clean(pian["第十六篇"]) + "\n\n" + clean(pian["第十八篇"])),
]

meta = []
for sid, title, body in SECTIONS:
    dst = os.path.join(OUT, sid + ".txt")
    io.open(dst, "w", encoding="utf-8", newline="\n").write("专题·十五五规划 / " + title + "\n\n" + body)
    meta.append({"id": sid, "title": title, "file": sid + ".txt", "chars": len(body)})

json.dump(meta, io.open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for m in meta:
    print(m["id"], m["chars"], m["title"][:40])
print("total", sum(m["chars"] for m in meta))
