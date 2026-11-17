# -*- coding: utf-8 -*-
"""把 web/ 下的 index.html + style.css + app.js + data.js 打包成单文件 HTML"""
import os, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")


def read(name):
    # utf-8-sig 会自动去掉 BOM：BOM 跑到 <style>/<script> 中间会让第一条规则失效
    return io.open(os.path.join(WEB, name), encoding="utf-8-sig").read().lstrip("\ufeff")


html = read("index.html")
css = read("style.css")
app = read("app.js")
data = read("data.js")


def safe(s):
    return s.replace("</script", "<\\/script")


html = html.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + css + "\n</style>")
html = html.replace('<script src="data.js"></script>', "<script>\n" + safe(data) + "\n</script>")
html = html.replace('<script src="app.js"></script>', "<script>\n" + safe(app) + "\n</script>")

assert "\ufeff" not in html, "还有 BOM"
out = os.path.join(ROOT, "政治理论挖空填词.html")
io.open(out, "w", encoding="utf-8", newline="\n").write(html)
print("written", out, round(len(html.encode("utf-8")) / 1024), "KB")
