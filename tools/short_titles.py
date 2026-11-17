# -*- coding: utf-8 -*-
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "sections_topic", "meta.json")
m = json.load(io.open(p, encoding="utf-8"))

SHORT = {
    "s01": "发展环境与历史方位",
    "s02": "指导方针与六条原则",
    "s03": "主要目标与关键指标",
    "s04": "现代化产业体系",
    "s05": "科技自立自强",
    "s06": "数字中国与人工智能",
    "s07": "强大国内市场",
    "s08": "高水平社会主义市场经济体制",
    "s09": "高水平对外开放",
    "s10": "农业农村现代化",
    "s11": "区域协调与新型城镇化",
    "s12": "文化强国",
    "s13": "人口高质量发展",
    "s14": "民生与共同富裕",
    "s15": "绿色转型与美丽中国",
    "s16": "国家安全与平安中国",
    "s17": "国防军队与“一国两制”",
    "s18": "民主法治与规划实施",
}
for x in m:
    x["title"] = SHORT.get(x["id"], x["title"])

json.dump(m, io.open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("ok", [x["title"] for x in m[:4]])
