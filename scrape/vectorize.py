"""Batch-trace all stamp GIFs to SVG with potrace.

Outputs:
  assets/stamps/svg/<same-stem>.svg   (viewBox only, fill=currentColor)
  scrape/vector-report.json           (per-image stats incl. grayscale flag)
  scrape/vector-qa.html               (contact sheet: original vs SVG)
"""

import json
from pathlib import Path

import numpy as np
import potrace
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "stamps"
OUT = SRC / "svg"
OUT.mkdir(exist_ok=True)

def otsu(px: np.ndarray) -> int:
    hist = np.bincount(px.ravel(), minlength=256).astype(float)
    total = px.size
    best_t, best_var = 128, -1.0
    w0 = 0.0
    sum_all = float(np.dot(np.arange(256), hist))
    sum0 = 0.0
    for t in range(256):
        w0 += hist[t]
        if w0 == 0 or w0 == total:
            continue
        sum0 += t * hist[t]
        m0 = sum0 / w0
        m1 = (sum_all - sum0) / (total - w0)
        var = w0 * (total - w0) * (m0 - m1) ** 2
        if var > best_var:
            best_var, best_t = var, t
    return int(min(max(best_t, 60), 210))


def trace(im_l: Image.Image) -> tuple[str, int]:
    # upscale before tracing so antialiased thin strokes survive thresholding
    scale = 3 if max(im_l.size) < 400 else 2
    big = im_l.resize((im_l.width * scale, im_l.height * scale), Image.LANCZOS)
    px = np.array(big)
    # potracer's convention: False pixels are foreground — so ink must be False
    data = px >= otsu(px)
    bmp = potrace.Bitmap(data)
    path = bmp.trace(turdsize=2 * scale * scale, opttolerance=0.4)
    parts = []
    n = 0
    for curve in path:
        n += 1
        s = curve.start_point
        parts.append(f"M{s.x:.0f},{s.y:.0f}")
        for seg in curve:
            if seg.is_corner:
                c, e = seg.c, seg.end_point
                parts.append(f"L{c.x:.0f},{c.y:.0f}L{e.x:.0f},{e.y:.0f}")
            else:
                c1, c2, e = seg.c1, seg.c2, seg.end_point
                parts.append(f"C{c1.x:.0f},{c1.y:.0f} {c2.x:.0f},{c2.y:.0f} {e.x:.0f},{e.y:.0f}")
        parts.append("Z")
    return "".join(parts), n, scale

def load_flat(path: Path) -> Image.Image:
    """Open image and composite any transparency over white before grayscale."""
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert("L")


report = []
for gif in sorted(SRC.glob("*.gif")):
    im = load_flat(gif)
    px = np.array(im)
    # grayscale/halftone detector: fraction of pixels that are neither near-white nor near-black
    gray_frac = float(((px > 60) & (px < 195)).mean())
    d, curves, scale = trace(im)
    w, h = im.size
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w * scale} {h * scale}">'
           f'<path d="{d}" fill="currentColor" fill-rule="evenodd"/></svg>')
    out = OUT / (gif.stem + ".svg")
    out.write_text(svg, encoding="utf-8")
    report.append({
        "stem": gif.stem,
        "px": [w, h],
        "gif_bytes": gif.stat().st_size,
        "svg_bytes": len(svg),
        "curves": curves,
        "gray_frac": round(gray_frac, 4),
        "flag_gray": gray_frac > 0.08,
    })
    print(f"{gif.stem}: {w}x{h} curves={curves} gray={gray_frac:.3f}"
          + ("  <-- FLAG" if gray_frac > 0.08 else ""))

(ROOT / "scrape" / "vector-report.json").write_text(
    json.dumps(report, indent=1), encoding="utf-8")

# contact sheet for eyeball QA
rows = []
for r in report:
    stem = r["stem"]
    flag = ' style="outline:3px solid red;"' if r["flag_gray"] else ""
    rows.append(f"""
<div class="pair"{flag}>
  <div class="lbl">{stem} · {r['px'][0]}×{r['px'][1]} · curves {r['curves']} · gray {r['gray_frac']}</div>
  <div class="imgs">
    <img src="../assets/stamps/{stem}.gif" alt="">
    <img src="../assets/stamps/svg/{stem}.svg" alt="">
  </div>
</div>""")
html = ("<title>Vector QA</title><style>"
        "body{font-family:sans-serif;background:#fff;color:#111}"
        ".pair{margin:14px;padding:8px;border:1px solid #ccc;display:inline-block;vertical-align:top}"
        ".lbl{font-size:11px;color:#555;margin-bottom:6px}"
        ".imgs img{max-width:260px;max-height:200px;margin-right:10px;background:#fff;border:1px dashed #eee}"
        "</style>" + "".join(rows))
(ROOT / "scrape" / "vector-qa.html").write_text(html, encoding="utf-8")

flagged = [r["stem"] for r in report if r["flag_gray"]]
print(f"\n{len(report)} traced; flagged for review: {flagged or 'none'}")
