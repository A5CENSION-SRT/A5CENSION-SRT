#!/usr/bin/env python3
"""Local preview of README.md that mimics GitHub's rendering (dark/light)."""
import re, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r = open(os.path.join(root, "README.md"), encoding="utf-8").read()
r = re.sub(r"<!--.*?-->", "", r, flags=re.S)
r = re.sub(r"`([^`]+)`", r"<code>\1</code>", r)
r = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", r)
r = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" style="color:#4493f8">\1</a>', r)
def wrap(src):
    out = []
    for chunk in re.split(r"\n\s*\n", src.strip()):
        t = chunk.strip()
        out.append(t if t.startswith(("<picture", "<img", "<p", "<br", "<a ")) else f"<p>{t}</p>")
    return "\n".join(out)
r = wrap(r)
page = f'''<!doctype html><meta charset="utf-8"><meta name="color-scheme" content="light dark"><title>Profile preview</title>
<style>:root{{--bg:#fff;--fg:#1f2328;--bd:#d1d9e0;--mu:#59636e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--fg:#e6edf3;--bd:#30363d;--mu:#8b949e}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 -apple-system,"Segoe UI",sans-serif}}
.w{{max-width:910px;margin:24px auto;padding:0 16px}}.h{{color:var(--mu);font:12px ui-monospace,monospace;margin:0 0 6px 4px}}
.b{{border:1px solid var(--bd);border-radius:6px;padding:32px}}img{{max-width:100%}}
.b p{{margin:0 0 16px}}
code{{background:color-mix(in srgb,var(--fg) 10%,transparent);padding:.2em .4em;border-radius:6px;font:85% ui-monospace,monospace}}p[align=center]{{text-align:center}}</style>
<div class="w"><p class="h">A5CENSION-SRT / README.md</p><div class="b">{r}</div></div>'''
open(os.path.join(root, "preview.html"), "w", encoding="utf-8").write(page)
