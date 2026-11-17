# -*- coding: utf-8 -*-
"""Extract text from the political-theory PDFs into per-file .txt (per page)."""
import os, sys, glob, io
from pypdf import PdfReader

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SRC, "text")
os.makedirs(OUT, exist_ok=True)

pdfs = sorted(glob.glob(os.path.join(SRC, "*.pdf")))
for p in pdfs:
    name = os.path.splitext(os.path.basename(p))[0]
    dst = os.path.join(OUT, name + ".txt")
    if os.path.exists(dst):
        print("skip", name)
        continue
    try:
        r = PdfReader(p)
    except Exception as e:
        print("FAIL open", name, e)
        continue
    parts = []
    for i, page in enumerate(r.pages):
        try:
            t = page.extract_text() or ""
        except Exception as e:
            t = ""
        parts.append("\n===== PAGE %d =====\n" % (i + 1) + t)
    txt = "".join(parts)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt)
    print("ok", name, len(r.pages), "pages", len(txt), "chars")
