"""Build the standalone GitHub Pages copy of the demo from app/index.html.

app/index.html is written as a page fragment (the Claude artifact host adds the
doctype, charset and viewport). GitHub Pages serves files as-is, so this script wraps
the same fragment in a full HTML document and writes web/index.html plus web/data.json.
One source file, two hosts: edit app/index.html, then run this script.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "app" / "index.html"
OUT = ROOT / "web"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
"""


def main():
    frag = SRC.read_text()
    # split the fragment: everything before the first page element goes in <head>
    cut = frag.index('<div class="wrap">')
    head, body = frag[:cut], frag[cut:]
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(HEAD + head + "</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    shutil.copy(ROOT / "app" / "data.json", OUT / "data.json")
    print("written web/index.html and web/data.json")


if __name__ == "__main__":
    main()
