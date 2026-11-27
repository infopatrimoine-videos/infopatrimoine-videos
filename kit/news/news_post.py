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


# ---------------- extra visuals ----------------
def _translucent(img, fn):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); fn(ImageDraw.Draw(lay)); img.alpha_composite(lay)

def _gold_glow(img, fn, blur=30, strength=0.9):
    g, _ = glow_layer(img.size, fn, blur * S, strength); img.alpha_composite(g)

def bars(img, x0, y0, w, h, values, labels, hi=-1, fmt=None):
    """bar chart around a zero line; highlighted bar in gold with glow, others white/muted."""
    d = ImageDraw.Draw(img); n = len(values); vmax = max(abs(v) for v in values) or 1
    pos = any(v > 0 for v in values); neg = any(v < 0 for v in values)
    zero = y0 + h * (0.5 if pos and neg else (1.0 if pos else 0.0))
    scale = h * (0.45 if pos and neg else 0.9) / vmax; bw = w / n * 0.56
    hi = hi % n
    for i, v in enumerate(values):
        cx = x0 + w / n * (i + 0.5); top = zero - v * scale
        box = [(cx - bw / 2) * S, min(zero, top) * S, (cx + bw / 2) * S, max(zero, top) * S + (2 * S if v == 0 else 0)]
        if i == hi:
            _gold_glow(img, lambda dd: dd.rounded_rectangle(box, 12 * S, fill=GOLD + (255,)), 28)
            d.rounded_rectangle(box, 12 * S, fill=GOLD + (255,))
        else:
            _translucent(img, lambda dd, b=box: dd.rounded_rectangle(b, 12 * S, fill=(255, 255, 255, 70)))
        val = fmt(v) if fmt else (("+" if v > 0 else "") + f"{v:.1f}".replace(".", ",") + " %")
        ty = (top - 34) if v >= 0 else (top + 34)
        d.text((cx * S, ty * S), val, font=F("B", 34 * S), fill=(GOLD if i == hi else WHITE) + (255,), anchor="mm")
        d.text((cx * S, (y0 + h + 95) * S), labels[i], font=F("M", 30 * S), fill=MUTED + (255,), anchor="mm")
    _translucent(img, lambda dd: dd.line([x0 * S, zero * S, (x0 + w) * S, zero * S], fill=(255, 255, 255, 120), width=2 * S))

def line_chart(img, x0, y0, w, h, values, labels=None, value_txt=None):
    d = ImageDraw.Draw(img); lo, hi_ = min(values), max(values); rng = (hi_ - lo) or 1
    pts = [((x0 + w * i / (len(values) - 1)) * S, (y0 + h - (v - lo) / rng * h) * S) for i, v in enumerate(values)]
    _translucent(img, lambda dd: [dd.line([x0 * S, (y0 + h * k / 4) * S, (x0 + w) * S, (y0 + h * k / 4) * S], fill=(255, 255, 255, 28), width=2 * S) for k in range(5)])
    poly = pts + [(pts[-1][0], (y0 + h) * S), (pts[0][0], (y0 + h) * S)]
    area = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(area).polygon(poly, fill=GOLD + (45,)); img.alpha_composite(area)
    _gold_glow(img, lambda dd: dd.line(pts, fill=GOLD + (255,), width=10 * S, joint="curve"), 22)
    d.line(pts, fill=GOLD + (255,), width=8 * S, joint="curve")
    x, y = pts[-1]; r = 18 * S
    _gold_glow(img, lambda dd: dd.ellipse([x - r * 2, y - r * 2, x + r * 2, y + r * 2], fill=GOLD_HI + (255,)), 20)
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE + (255,), outline=GOLD + (255,), width=6 * S)
    if value_txt:
        d.text(((x0 + w) * S, (y0 - 30) * S), value_txt, font=F("XB", 72 * S), fill=GOLD + (255,), anchor="rb")
    if labels:
        for i, lb in enumerate(labels):
            if lb: d.text(((x0 + w * i / (len(values) - 1)) * S, (y0 + h + 40) * S), lb, font=F("M", 28 * S), fill=MUTED + (255,), anchor="mm")

def gauge(img, cx, cy, r, frac, value, label, lo_txt="", hi_txt=""):
    d = ImageDraw.Draw(img); box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
    _translucent(img, lambda dd: dd.arc(box, 180, 360, fill=(255, 255, 255, 45), width=46 * S))
    end = 180 + 180 * max(0, min(1, frac))
    _gold_glow(img, lambda dd: dd.arc(box, 180, end, fill=GOLD + (255,), width=46 * S), 26)
    d.arc(box, 180, end, fill=GOLD + (255,), width=46 * S)
    a = math.radians(end); nx, ny = cx + math.cos(a) * (r - 80), cy + math.sin(a) * (r - 80)
    d.line([cx * S, cy * S, nx * S, ny * S], fill=WHITE + (255,), width=10 * S)
    d.ellipse([(cx - 22) * S, (cy - 22) * S, (cx + 22) * S, (cy + 22) * S], fill=WHITE + (255,))
    d.text((cx * S, (cy + 110) * S), value, font=F("XB", 120 * S), fill=GOLD + (255,), anchor="mm")
    d.text((cx * S, (cy + 200) * S), label, font=F("M", 34 * S), fill=MUTED + (255,), anchor="mm")
    d.text(((cx - r) * S, (cy + 50) * S), lo_txt, font=F("M", 28 * S), fill=MUTED + (255,), anchor="mm")
    d.text(((cx + r) * S, (cy + 50) * S), hi_txt, font=F("M", 28 * S), fill=MUTED + (255,), anchor="mm")

def versus(img, y, left, right):
    """two figures side by side: left = (value, label) muted, right = (value, label) gold."""
    d = ImageDraw.Draw(img)
    for (val, lab), cx, col in ((left, 290, WHITE), (right, 790, GOLD)):
        if col == GOLD: _gold_glow(img, lambda dd: dd.text((cx * S, y * S), val, font=F("XB", 120 * S), fill=GOLD + (255,), anchor="mm"), 30, 0.7)
        d.text((cx * S, y * S), val, font=F("XB", 120 * S), fill=col + (255,), anchor="mm")
        for k, ln in enumerate(lab.split("\n")):
            d.text((cx * S, (y + 100 + k * 44) * S), ln, font=F("M", 34 * S), fill=MUTED + (255,), anchor="mm")
    d.text((540 * S, y * S), "→", font=F("B", 90 * S), fill=GOLD + (255,), anchor="mm")

ICONS = {}
def icon(img, name, cx, cy, s):
    """large glowing gold pictogram: house, coins, factory, cart, globe, briefcase, percent, bank, chip, oil"""
    def draw(dd, col):
        c = col + (255,); X = lambda v: (cx + v * s) * S; Y = lambda v: (cy + v * s) * S
        if name == "house":
            dd.polygon([(X(-1), Y(-0.1)), (X(0), Y(-1)), (X(1), Y(-0.1))], fill=c)
            dd.rectangle([X(-0.75), Y(-0.15), X(0.75), Y(0.9)], fill=c)
            dd.rectangle([X(-0.2), Y(0.35), X(0.2), Y(0.9)], fill=NAVY0 + (255,))
            dd.rectangle([X(0.35), Y(-0.75), X(0.6), Y(-0.35)], fill=c)
        elif name == "coins":
            for k in range(4):
                dd.ellipse([X(-0.8), Y(0.55 - k * 0.42), X(0.8), Y(0.95 - k * 0.42)], fill=c, outline=NAVY0 + (255,), width=6 * S)
            dd.text((X(0), Y(-0.5)), "€", font=F("XB", int(s * 0.55) * S), fill=NAVY0 + (255,), anchor="mm")
        elif name == "factory":
            dd.polygon([(X(-1), Y(0.9)), (X(-1), Y(-0.1)), (X(-0.5), Y(-0.45)), (X(-0.5), Y(-0.1)), (X(0), Y(-0.45)), (X(0), Y(-0.1)), (X(0.5), Y(-0.45)), (X(0.5), Y(-1)), (X(0.8), Y(-1)), (X(0.8), Y(-0.1)), (X(1), Y(-0.1)), (X(1), Y(0.9))], fill=c)
            for k in range(3): dd.rectangle([X(-0.8 + k * 0.55), Y(0.25), X(-0.55 + k * 0.55), Y(0.5)], fill=NAVY0 + (255,))
        elif name == "cart":
            dd.line([X(-1), Y(-0.8), X(-0.7), Y(-0.8), X(-0.4), Y(0.4), X(0.8), Y(0.4)], fill=c, width=int(s * 0.12) * S, joint="curve")
            dd.polygon([(X(-0.6), Y(-0.5)), (X(1), Y(-0.5)), (X(0.8), Y(0.2)), (X(-0.45), Y(0.2))], fill=c)
            for xx in (-0.3, 0.65): dd.ellipse([X(xx - 0.15), Y(0.6), X(xx + 0.15), Y(0.9)], fill=c)
        elif name == "globe":
            dd.ellipse([X(-1), Y(-1), X(1), Y(1)], outline=c, width=int(s * 0.1) * S)
            dd.ellipse([X(-0.45), Y(-1), X(0.45), Y(1)], outline=c, width=int(s * 0.07) * S)
            for yy in (-0.45, 0, 0.45): dd.line([X(-0.92 if yy else -1), Y(yy), X(0.92 if yy else 1), Y(yy)], fill=c, width=int(s * 0.07) * S)
        elif name == "briefcase":
            dd.rounded_rectangle([X(-1), Y(-0.45), X(1), Y(0.85)], int(s * 0.15) * S, fill=c)
            dd.rounded_rectangle([X(-0.35), Y(-0.85), X(0.35), Y(-0.45)], int(s * 0.1) * S, outline=c, width=int(s * 0.1) * S)
            dd.rectangle([X(-1), Y(0.05), X(1), Y(0.12)], fill=NAVY0 + (255,))
        elif name == "percent":
            dd.text((X(0), Y(0)), "%", font=F("XB", int(s * 2.1) * S), fill=c, anchor="mm")
        elif name == "bank":
            dd.polygon([(X(-1), Y(-0.45)), (X(0), Y(-1)), (X(1), Y(-0.45))], fill=c)
            for k in range(4): dd.rectangle([X(-0.8 + k * 0.48), Y(-0.3), X(-0.62 + k * 0.48), Y(0.6)], fill=c)
            dd.rectangle([X(-1), Y(0.7), X(1), Y(0.9)], fill=c)
        elif name == "chip":
            dd.rounded_rectangle([X(-0.6), Y(-0.6), X(0.6), Y(0.6)], int(s * 0.1) * S, fill=c)
            for k in range(5):
                o = -0.48 + k * 0.24
                for a, b2 in (((o, -0.95), (o, -0.6)), ((o, 0.6), (o, 0.95)), ((-0.95, o), (-0.6, o)), ((0.6, o), (0.95, o))):
                    dd.line([X(a[0]), Y(a[1]), X(b2[0]), Y(b2[1])], fill=c, width=int(s * 0.07) * S)
            dd.text((X(0), Y(0)), "IA", font=F("XB", int(s * 0.5) * S), fill=NAVY0 + (255,), anchor="mm")
        elif name == "oil":
            dd.polygon([(X(0), Y(-1)), (X(0.62), Y(0.05)), (X(-0.62), Y(0.05))], fill=c)
            dd.ellipse([X(-0.66), Y(-0.4), X(0.66), Y(0.95)], fill=c)
    _gold_glow(img, lambda dd: draw(dd, GOLD), 40, 0.8)
    draw(ImageDraw.Draw(img), GOLD)

def page_tag(img, W, k, n):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle([(W - 150) * S, 60 * S, (W - 44) * S, 124 * S], 32 * S, fill=(255, 255, 255, 38))
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img); f = F("M", 32 * S); t = f"{k}/{n}"
    d.text(((W - 97) * S, 92 * S), t, font=f, fill=WHITE + (235,), anchor="mm")

def finish(img, out):
    W, H = img.size
    img.convert("RGB").resize((W // S, H // S), Image.LANCZOS).save(out, quality=95)

def draw_visual(img, sl, dy=0):
    """dy shifts the visual down (story)."""
    W = 1080
    sl = dict(sl)
    for k in ("y", "fig_y"):
        if k in sl: sl[k] += dy
    if sl["visual"] == "arrow_down":
        P = [(x * S, y * S) for x, y in [(-40, 140 + dy), (190, 420 + dy), (380, 290 + dy), (640, 650 + dy), (780, 540 + dy), (960, 860 + dy)]]
        arrow(img, P, 64 * S)
    elif sl["visual"] == "arrow_up":
        P = [(x * S, y * S) for x, y in [(-40, 860 + dy), (190, 600 + dy), (380, 720 + dy), (640, 360 + dy), (780, 470 + dy), (960, 170 + dy)]]
        arrow(img, P, 64 * S)
    elif sl["visual"] == "figure":
        big_figure(img, W / 2, sl.get("fig_y", 430 + dy), sl["value"], sl.get("unit", ""), sl.get("label", ""))
    elif sl["visual"] == "bars":
        bars(img, 120, sl.get("y", 230 + dy), 840, 520, sl["values"], sl["labels"], sl.get("hi", -1))
    elif sl["visual"] == "line":
        line_chart(img, 110, sl.get("y", 260 + dy), 860, 460, sl["values"], sl.get("labels"), sl.get("value_txt"))
    elif sl["visual"] == "gauge":
        gauge(img, 540, sl.get("y", 600 + dy), 330, sl["frac"], sl["value"], sl.get("label", ""), sl.get("lo", ""), sl.get("hi", ""))
    elif sl["visual"] == "versus":
        versus(img, sl.get("y", 480 + dy), sl["left"], sl["right"])
    elif sl["visual"] == "icon":
        icon(img, sl["icon"], 540, sl.get("y", 420 + dy), sl.get("s", 210))
        if sl.get("value"): big_figure(img, 540, sl.get("y", 420 + dy) + 330, sl["value"], "", "", size=120)
    elif sl["visual"] == "grid":
        icon_grid(img, 150, 200 + dy, 6, 4, 130, sl.get("faded_from", 18))
        big_figure(img, W / 2, 790 + dy, sl["value"], sl.get("unit", ""), "", size=130)


def render(spec, outdir):
    os.makedirs(outdir, exist_ok=True); outs = []
    n = len(spec["slides"])
    for k, sl in enumerate(spec["slides"], 1):
        W, H = 1080, 1350
        img = bg(W * S, H * S, glow=sl.get("glow", (0.55, 0.38)))
        draw_visual(img, sl)
        logo(img, 64, 48, 118)
        if spec.get("page_tag"): page_tag(img, W, k, n)   # désactivé par défaut (demande de Tomas, 27/11)
        headline(img, sl["title"], 80, 1270, 900, sl.get("size", 64))
        out = os.path.join(outdir, f"post_{k}.jpg"); finish(img, out); outs.append(out)
    if spec.get("story"):
        st = spec["story"]; W, H = 1080, 1920
        img = bg(W * S, H * S, glow=(0.55, 0.4))
        draw_visual(img, st.get("visual_spec", {"visual": st.get("visual", "arrow_down")}), dy=190)
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
