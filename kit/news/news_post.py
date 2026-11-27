"""Info Patrimoine — visuels « actu éco » pour Instagram (carrousel 4:5) et story (9:16).
Style : fond bleu nuit, accent or (couleurs du logo IP), titre blanc gras en bas, barre or, logo en haut à gauche.
Usage : python3 news_post.py spec.json outdir      (spec : voir EXAMPLE en bas)"""
import sys, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/claude/motion")
from motion import F
import motion_tmpl as MT

S = 2                                     # supersampling
NAVY0 = (6, 10, 26); NAVY1 = (16, 26, 58)
GOLD = (214, 172, 84); GOLD_HI = (255, 214, 130)
WHITE = (246, 246, 248); MUTED = (170, 176, 196)

def bg(w, h, glow=(0.5, 0.42)):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - glow[0] * w) / w) ** 2 + ((yy - glow[1] * h) / h) ** 2)
    t = np.clip(1 - d * 1.6, 0, 1)[..., None]
    arr = np.array(NAVY0) * (1 - t) + np.array(NAVY1) * t
    noise = np.random.default_rng(1).normal(0, 2.2, (h, w, 1))
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

def glow_layer(size, draw_fn, blur, strength=1.0):
    lay = Image.new("RGBA", size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(lay))
    g = lay.filter(ImageFilter.GaussianBlur(blur))
    if strength != 1.0:
        a = np.asarray(g).astype(np.float32); a[..., 3] = np.clip(a[..., 3] * strength, 0, 255); g = Image.fromarray(a.astype(np.uint8))
    return g, lay

def arrow(img, pts, width, color=GOLD, head=None):
    """zig-zag arrow with neon glow; pts in px; direction given by last segment."""
    W, H = img.size
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1); hl = head or width * 2.6
    tip = (x2 + math.cos(ang) * hl * 0.9, y2 + math.sin(ang) * hl * 0.9)
    left = (x2 + math.cos(ang + math.pi / 2) * hl * 0.75, y2 + math.sin(ang + math.pi / 2) * hl * 0.75)
    right = (x2 + math.cos(ang - math.pi / 2) * hl * 0.75, y2 + math.sin(ang - math.pi / 2) * hl * 0.75)
    def body(d, c, wd):
        d.line(pts, fill=c, width=wd, joint="curve"); d.polygon([tip, left, right], fill=c)
    for blur, a in ((60 * S, 0.9), (22 * S, 1.0)):
        g, _ = glow_layer(img.size, lambda d: body(d, color + (255,), width), blur, a); img.alpha_composite(g)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); body(d, color + (255,), width)
    # bevel highlight
    hi = Image.new("RGBA", img.size, (0, 0, 0, 0)); dh = ImageDraw.Draw(hi)
    dh.line([(x, y - width * 0.22) for x, y in pts], fill=GOLD_HI + (150,), width=max(2, int(width * 0.18)), joint="curve")
    lay.alpha_composite(hi.filter(ImageFilter.GaussianBlur(3 * S)))
    img.alpha_composite(lay)

import re
def keep_units(text):
    """non-breaking space between a number and its unit / between digit groups (12,4 %, 100 000 €)."""
    text = re.sub(r"(\d) (?=\d{3}\b)", "\\1\u00a0", text)
    return re.sub(r"(\d) (?=(%|€|\$|Md|M€|Md€|Md\$|ans?|mois|points?)\b|%|€)", "\\1\u00a0", text)

def wrap(d, text, font, maxw):
    words = keep_units(text).split(" "); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def headline(img, text, x, y_bottom, maxw, size, bar=True, align_bottom=True):
    d = ImageDraw.Draw(img); f = F("S", size * S)
    lines = wrap(d, text, f, maxw * S); lh = size * S * 1.12
    y0 = y_bottom * S - len(lines) * lh - (70 * S if bar else 0) if align_bottom else y_bottom * S
    for i, ln in enumerate(lines): d.text((x * S, y0 + i * lh), ln, font=f, fill=WHITE + (255,))
    if bar:
        yb = y0 + len(lines) * lh + 28 * S
        d.rectangle([x * S, yb, (x + 72) * S, yb + 16 * S], fill=GOLD + (255,))
    return y0 / S

def logo(img, x, y, size):
    lg = MT.logo(size * S)
    if lg is not None: img.alpha_composite(lg, (int(x * S), int(y * S)))
    d = ImageDraw.Draw(img)
    d.text(((x + size + 20) * S, (y + size / 2) * S), "INFO PATRIMOINE", font=F("B", int(size * 0.24) * S), fill=WHITE + (235,), anchor="lm")
    d.text(((x + size + 20) * S, (y + size / 2 + size * 0.24) * S), "L'ACTU ÉCO", font=F("M", int(size * 0.17) * S), fill=GOLD + (255,), anchor="lm")

def counter_tag(img, x, y, txt):
    d = ImageDraw.Draw(img); f = F("M", 30 * S); tw = d.textlength(txt, font=f)
    d.rounded_rectangle([x * S, y * S, x * S + tw + 44 * S, (y + 56) * S], 28 * S, fill=(255, 255, 255, 40))
    d.text((x * S + 22 * S, (y + 28) * S), txt, font=f, fill=WHITE + (230,), anchor="lm")

def big_figure(img, cx, cy, value, unit, label, size=230):
    d = ImageDraw.Draw(img)
    g, _ = glow_layer(img.size, lambda dd: dd.text((cx * S, cy * S), value, font=F("XB", size * S), fill=GOLD + (255,), anchor="mm"), 40 * S, 0.8)
    img.alpha_composite(g)
    d.text((cx * S, cy * S), value, font=F("XB", size * S), fill=GOLD + (255,), anchor="mm")
    if unit: d.text((cx * S, (cy + size * 0.68) * S), unit, font=F("B", int(size * 0.26) * S), fill=WHITE + (255,), anchor="mm")
    if label: d.text((cx * S, (cy + size * 0.68 + size * 0.3) * S), label, font=F("M", 34 * S), fill=MUTED + (255,), anchor="mm")

def icon_grid(img, x0, y0, cols, rows, cell, faded_from, missing_mark=True):
    """grid of small 'job ad' cards; the last ones are faded / dashed (= missing ads)."""
    d = ImageDraw.Draw(img); n = cols * rows
    for i in range(n):
        r, c = divmod(i, cols); x = (x0 + c * cell) * S; y = (y0 + r * cell) * S; w = (cell - 18) * S; h = (cell - 18) * S
        if i < faded_from:
            d.rounded_rectangle([x, y, x + w, y + h], 14 * S, fill=(255, 255, 255, 235))
            d.ellipse([x + w * 0.36, y + h * 0.16, x + w * 0.64, y + h * 0.44], fill=NAVY1 + (255,))
            d.rounded_rectangle([x + w * 0.24, y + h * 0.5, x + w * 0.76, y + h * 0.8], 10 * S, fill=NAVY1 + (255,))
        else:
            d.rounded_rectangle([x, y, x + w, y + h], 14 * S, outline=GOLD + (200,), width=3 * S)
            if missing_mark:
                d.line([x + w * 0.3, y + h * 0.3, x + w * 0.7, y + h * 0.7], fill=GOLD + (200,), width=4 * S)
                d.line([x + w * 0.7, y + h * 0.3, x + w * 0.3, y + h * 0.7], fill=GOLD + (200,), width=4 * S)

def page_tag(img, W, k, n):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle([(W - 150) * S, 60 * S, (W - 44) * S, 124 * S], 32 * S, fill=(255, 255, 255, 38))
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img); f = F("M", 32 * S); t = f"{k}/{n}"
    d.text(((W - 97) * S, 92 * S), t, font=f, fill=WHITE + (235,), anchor="mm")

def finish(img, out):
    W, H = img.size
    img.convert("RGB").resize((W // S, H // S), Image.LANCZOS).save(out, quality=95)

def render(spec, outdir):
    os.makedirs(outdir, exist_ok=True); outs = []
    n = len(spec["slides"])
    for k, sl in enumerate(spec["slides"], 1):
        W, H = 1080, 1350
        img = bg(W * S, H * S, glow=sl.get("glow", (0.55, 0.38)))
        if sl["visual"] == "arrow_down":
            P = [(x * S, y * S) for x, y in [(-40, 140), (190, 420), (380, 290), (640, 650), (780, 540), (960, 860)]]
            arrow(img, P, 64 * S)
        elif sl["visual"] == "arrow_up":
            P = [(x * S, y * S) for x, y in [(-40, 860), (190, 600), (380, 720), (640, 360), (780, 470), (960, 170)]]
            arrow(img, P, 64 * S)
        elif sl["visual"] == "figure":
            big_figure(img, W / 2, sl.get("fig_y", 430), sl["value"], sl.get("unit", ""), sl.get("label", ""))
        elif sl["visual"] == "grid":
            icon_grid(img, 150, 200, 6, 4, 130, sl.get("faded_from", 18))
            big_figure(img, W / 2, 790, sl["value"], sl.get("unit", ""), "", size=130)
        logo(img, 64, 48, 118)
        page_tag(img, W, k, n)
        headline(img, sl["title"], 80, 1270, 900, sl.get("size", 64))
        out = os.path.join(outdir, f"post_{k}.jpg"); finish(img, out); outs.append(out)
    if spec.get("story"):
        st = spec["story"]; W, H = 1080, 1920
        img = bg(W * S, H * S, glow=(0.55, 0.4))
        P = [(x * S, y * S) for x, y in [(-40, 330), (190, 620), (380, 490), (640, 860), (780, 750), (960, 1080)]]
        arrow(img, P, 64 * S) if st.get("visual", "arrow_down") == "arrow_down" else None
        logo(img, 64, 150, 130)
        y = headline(img, st["title"], 80, 1500, 920, st.get("size", 70))
        d = ImageDraw.Draw(img)
        for i, kf in enumerate(st.get("facts", [])):
            yy = 1560 + i * 62
            d.ellipse([84 * S, (yy - 8) * S, 100 * S, (yy + 8) * S], fill=GOLD + (255,))
            d.text((122 * S, yy * S), kf, font=F("M", 36 * S), fill=WHITE + (240,), anchor="lm")
        d.text((80 * S, 1790 * S), st.get("source", ""), font=F("M", 26 * S), fill=MUTED + (255,), anchor="lm")
        out = os.path.join(outdir, "story.jpg"); finish(img, out); outs.append(out)
    return outs

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); print(render(spec, sys.argv[2]))
