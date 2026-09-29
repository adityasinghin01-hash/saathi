"""Markdown docs -> PDF (A4). 03-SCREENSHOTS embeds each screenshot so the reader sees it."""
import os, re, markdown
import render as R
import diagrams as D

PACK = D.OUT
CSS = """@page{size:A4;margin:14mm} body{font-family:'IBM Plex Sans','Noto Sans Devanagari',Helvetica,Arial,sans-serif;color:#2e2119;font-size:12.5px;line-height:1.5}
h1{font-size:24px;color:#8f3a1b;margin:0 0 8px} h2{font-size:17px;border-bottom:2px solid #bf5630;padding-bottom:3px;margin-top:22px;page-break-after:avoid}
h3{font-size:14px;margin-top:14px} table{border-collapse:collapse;width:100%;margin:8px 0;font-size:11px} th,td{border:1px solid #e8d9c6;padding:5px 6px;vertical-align:top;text-align:left}
th{background:#f8e2d4} tr{page-break-inside:avoid} code{background:#f4e9da;padding:1px 4px;border-radius:3px} a{color:#8a3517}
img.shot{max-width:100%;max-height:520px;border:1px solid #e8d9c6;border-radius:8px;display:block;margin:6px 0 14px}
.foot{margin-top:20px;font-size:10px;color:#6a5444}"""

def link_fix(html):
    # make links to local files absolute so they work from the PDF
    return re.sub(r'href="(?!https?:|#|/)([^"]+)"', lambda m: f'href="file://{os.path.normpath(os.path.join(PACK, m.group(1)))}"', html)

for name in ["01-SLIDE-BY-SLIDE-BRIEF", "02-NUMBERS-AND-CLAIMS", "03-SCREENSHOTS", "04-JUDGE-QA", "05-BRAND-AND-LINKS"]:
    md = open(os.path.join(PACK, name + ".md"), encoding="utf-8").read()
    # Python-Markdown needs a blank line before a list that follows a paragraph line.
    md = re.sub(r"(?m)^(?!\s*[-*] |\s*\d+\. |\s*$)(.+)\n(?=\s*[-*] |\s*\d+\. )", r"\1\n\n", md)
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"])
    if name == "03-SCREENSHOTS":
        shots = sorted(f for f in os.listdir(os.path.join(PACK, "screens")) if f.endswith(".png") and not f.startswith("S21"))
        body += "<h2>All screenshots</h2>" + "".join(
            f"<h3>{f}</h3><img class=shot src='file://{os.path.join(PACK, 'screens', f)}'>" for f in shots)
    html = f"<!doctype html><html><head><meta charset=utf-8><style>{CSS}</style></head><body>{link_fix(body)}<div class=foot>Saathi · साथी — synthetic demo data · pack generated 29 Sep 2026</div></body></html>"
    R.pdf_from_html(html, os.path.join(PACK, name + ".pdf"))
    print("wrote", name)
