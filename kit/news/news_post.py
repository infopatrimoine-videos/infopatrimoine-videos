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
    if name in ICON_EXTRA:
        draw = lambda dd, col: icon_extra(dd, name, cx, cy, s, col + (255,))
    _gold_glow(img, lambda dd: draw(dd, GOLD), 40, 0.8)
    draw(ImageDraw.Draw(img), GOLD)


# ---------------- visuels supplémentaires (27/11) ----------------
RED = (232, 112, 112)

def _txt(d, xy, t, size, col=WHITE, w="M", anchor="mm"):
    d.text((xy[0] * S, xy[1] * S), t, font=F(w, size * S), fill=col + (255,), anchor=anchor)

def _gold_text(img, xy, t, size, anchor="mm", glow=True):
    if glow: _gold_glow(img, lambda dd: dd.text((xy[0] * S, xy[1] * S), t, font=F("XB", size * S), fill=GOLD + (255,), anchor=anchor), 30, 0.7)
    ImageDraw.Draw(img).text((xy[0] * S, xy[1] * S), t, font=F("XB", size * S), fill=GOLD + (255,), anchor=anchor)

def _lines(d, cx, y, text, size=34, col=MUTED, step=44):
    for k, ln in enumerate(text.split("\n")): _txt(d, (cx, y + k * step), ln, size, col)

def donut(img, cx, cy, r, frac, value, label):
    """anneau : une part d'un tout (part des ménages, part de marché…)"""
    box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]; wd = 74 * S
    _translucent(img, lambda dd: dd.ellipse(box, outline=(255, 255, 255, 40), width=wd))
    end = -90 + 360 * max(0.0, min(1.0, frac))
    _gold_glow(img, lambda dd: dd.arc(box, -90, end, fill=GOLD + (255,), width=wd), 26)
    d = ImageDraw.Draw(img); d.arc(box, -90, end, fill=GOLD + (255,), width=wd)
    _gold_text(img, (cx, cy), value, 104, glow=False)
    _lines(d, cx, cy + r + 70, label)

def hbars(img, x0, y0, w, items, hi=0):
    """classement horizontal : items = [[étiquette, nombre, texte affiché], …]"""
    d = ImageDraw.Draw(img); n = len(items); step = min(140, 660 / n); vmax = max(abs(it[1]) for it in items) or 1
    bx = x0 + 270; bw_max = w - 270 - 170
    for i, (lab, v, txt) in enumerate(items):
        y = y0 + i * step; bw = max(14, bw_max * abs(v) / vmax); box = [bx * S, (y - 28) * S, (bx + bw) * S, (y + 28) * S]
        _txt(d, (x0, y), lab, 34, WHITE if i == hi else MUTED, "B" if i == hi else "M", "lm")
        if i == hi:
            _gold_glow(img, lambda dd: dd.rounded_rectangle(box, 14 * S, fill=GOLD + (255,)), 24)
            d.rounded_rectangle(box, 14 * S, fill=GOLD + (255,))
        else:
            _translucent(img, lambda dd, b=box: dd.rounded_rectangle(b, 14 * S, fill=(255, 255, 255, 70)))
        _txt(d, (bx + bw + 22, y), txt, 36, GOLD if i == hi else WHITE, "XB" if i == hi else "B", "lm")

def thermo(img, cx, y0, frac, value, label):
    """thermomètre : un niveau qui chauffe (inflation, prix de l'énergie, tension)"""
    d = ImageDraw.Draw(img); h = 520; tw = 74; br = 78; by = y0 + h + br - 20
    _translucent(img, lambda dd: (dd.rounded_rectangle([(cx - tw / 2) * S, y0 * S, (cx + tw / 2) * S, by * S], tw / 2 * S, fill=(255, 255, 255, 45)),
                                  dd.ellipse([(cx - br) * S, (by - br) * S, (cx + br) * S, (by + br) * S], fill=(255, 255, 255, 45))))
    top = y0 + h * (1 - max(0.0, min(1.0, frac))) + 16; iw = tw - 30; ir = br - 18
    def f(dd):
        dd.rounded_rectangle([(cx - iw / 2) * S, top * S, (cx + iw / 2) * S, by * S], iw / 2 * S, fill=GOLD + (255,))
        dd.ellipse([(cx - ir) * S, (by - ir) * S, (cx + ir) * S, (by + ir) * S], fill=GOLD + (255,))
    _gold_glow(img, f, 26); f(d)
    for k in range(6):
        yy = y0 + 40 + k * (h - 60) / 5
        _translucent(img, lambda dd, yy=yy: dd.line([(cx + tw / 2 + 14) * S, yy * S, (cx + tw / 2 + 44) * S, yy * S], fill=(255, 255, 255, 110), width=3 * S))
    _gold_text(img, (cx + 170, top + 10), value, 120, anchor="lm")
    _lines(d, cx + 330, top + 110, label)

def calendar(img, cx, cy, day, month, label):
    """date clé : une échéance, une entrée en vigueur"""
    d = ImageDraw.Draw(img); w, h = 420, 440; x0, y0 = cx - w / 2, cy - h / 2
    _gold_glow(img, lambda dd: dd.rounded_rectangle([x0 * S, y0 * S, (x0 + w) * S, (y0 + h) * S], 40 * S, fill=GOLD + (255,)), 40, 0.5)
    d.rounded_rectangle([x0 * S, y0 * S, (x0 + w) * S, (y0 + h) * S], 40 * S, fill=WHITE + (255,))
    d.rounded_rectangle([x0 * S, y0 * S, (x0 + w) * S, (y0 + 130) * S], 40 * S, fill=GOLD + (255,))
    d.rectangle([x0 * S, (y0 + 90) * S, (x0 + w) * S, (y0 + 130) * S], fill=GOLD + (255,))
    for xx in (x0 + 110, x0 + w - 110):
        d.rounded_rectangle([(xx - 14) * S, (y0 - 34) * S, (xx + 14) * S, (y0 + 40) * S], 14 * S, fill=NAVY1 + (255,))
    _txt(d, (cx, y0 + 70), month.upper(), 50, NAVY0, "XB")
    _txt(d, (cx, y0 + 285), day, 190, NAVY0, "XB")
    _lines(d, cx, y0 + h + 70, label, 36, WHITE)

def people(img, y, total, k, value, label=""):
    """k personnes sur total (1 Français sur 3…)"""
    d = ImageDraw.Draw(img); step = min(150, 860 / total); x0 = 540 - step * (total - 1) / 2; s = step * 0.42
    for i in range(total):
        cx = x0 + i * step
        def p(dd, col, cx=cx):
            dd.ellipse([(cx - s * 0.42) * S, (y - s * 1.55) * S, (cx + s * 0.42) * S, (y - s * 0.71) * S], fill=col)
            dd.rounded_rectangle([(cx - s * 0.75) * S, (y - s * 0.55) * S, (cx + s * 0.75) * S, (y + s * 1.2) * S], s * 0.5 * S, fill=col)
        if i < k:
            _gold_glow(img, lambda dd, p=p: p(dd, GOLD + (255,)), 22); p(d, GOLD + (255,))
        else:
            _translucent(img, lambda dd, p=p: p(dd, (255, 255, 255, 70)))
    _gold_text(img, (540, y + s * 1.2 + 140), value, 130)
    if label: _lines(d, 540, y + s * 1.2 + 250, label)

def stat3(img, y0, items):
    """2 à 3 chiffres clés empilés : items = [[valeur, étiquette], …]"""
    d = ImageDraw.Draw(img); step = 210
    for i, (val, lab) in enumerate(items):
        y = y0 + i * step
        _gold_text(img, (100, y), val, 92, anchor="lm", glow=(i == 0))
        for kk, ln in enumerate(lab.split("\n")):
            _txt(d, (650, y - (len(lab.split("\n")) - 1) * 22 + kk * 44), ln, 34, WHITE if kk == 0 else MUTED, "B" if kk == 0 else "M", "lm")
        if i < len(items) - 1:
            _translucent(img, lambda dd, y=y: dd.line([110 * S, (y + step / 2) * S, 970 * S, (y + step / 2) * S], fill=(255, 255, 255, 45), width=2 * S))

def timeline(img, y, items, hi=-1):
    """frise : items = [[date, étiquette (\\n possible)], …], hi = étape en or"""
    d = ImageDraw.Draw(img); n = len(items); x0, x1 = 140, 940; hi = hi % n
    _translucent(img, lambda dd: dd.line([x0 * S, y * S, x1 * S, y * S], fill=(255, 255, 255, 90), width=6 * S))
    for i, (date, lab) in enumerate(items):
        x = x0 + (x1 - x0) * i / (n - 1); r = 30 if i == hi else 20
        if i == hi:
            _gold_glow(img, lambda dd, x=x: dd.ellipse([(x - 46) * S, (y - 46) * S, (x + 46) * S, (y + 46) * S], fill=GOLD + (255,)), 22)
            d.line([x0 * S, y * S, x * S, y * S], fill=GOLD + (255,), width=6 * S)
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(GOLD if i <= hi else WHITE) + (255,))
        _txt(d, (x, y - 80), date, 50 if i == hi else 40, GOLD if i == hi else WHITE, "XB" if i == hi else "B")
        _lines(d, x, y + 90, lab, 36, WHITE if i == hi else MUTED, 46)

def ticker(img, y0, rows):
    """tableau de marché : rows = [[nom, niveau, variation, hausse(true/false)], …]"""
    d = ImageDraw.Draw(img); step = 128
    for i, (name, lvl, chg, up) in enumerate(rows):
        y = y0 + i * step
        _translucent(img, lambda dd, y=y: dd.rounded_rectangle([90 * S, (y - 50) * S, 990 * S, (y + 50) * S], 24 * S, fill=(255, 255, 255, 22)))
        _txt(d, (130, y), name, 38, WHITE, "B", "lm")
        _txt(d, (640, y), lvl, 38, WHITE, "M", "rm")
        col = GOLD if up else RED
        pill = [690 * S, (y - 32) * S, 960 * S, (y + 32) * S]
        _translucent(img, lambda dd, pill=pill, col=col: dd.rounded_rectangle(pill, 32 * S, fill=col + (60,)))
        tri = [(718, y + 10), (742, y + 10), (730, y - 12)] if up else [(718, y - 10), (742, y - 10), (730, y + 12)]
        d.polygon([(a * S, b * S) for a, b in tri], fill=col + (255,))
        _txt(d, (942, y), chg, 36, col, "XB", "rm")

def balance(img, cy, left, right, tilt=0.5):
    """balance : left/right = [valeur, étiquette] ; tilt > 0 = penche à droite"""
    d = ImageDraw.Draw(img); cx = 540; L = 290; a = math.radians(14 * max(-1, min(1, tilt)))
    top = cy - 220
    d.polygon([((cx - 120) * S, (cy + 300) * S), ((cx + 120) * S, (cy + 300) * S), (cx * S, (cy + 250) * S)], fill=GOLD + (255,))
    d.rectangle([(cx - 10) * S, top * S, (cx + 10) * S, (cy + 270) * S], fill=GOLD + (255,))
    pL = (cx - L * math.cos(a), top - L * math.sin(a)); pR = (cx + L * math.cos(a), top + L * math.sin(a))
    _gold_glow(img, lambda dd: dd.line([pL[0] * S, pL[1] * S, pR[0] * S, pR[1] * S], fill=GOLD + (255,), width=16 * S), 20)
    d.line([pL[0] * S, pL[1] * S, pR[0] * S, pR[1] * S], fill=GOLD + (255,), width=16 * S)
    d.ellipse([(cx - 26) * S, (top - 26) * S, (cx + 26) * S, (top + 26) * S], fill=GOLD_HI + (255,))
    for (val, lab), (px, py), col in ((left, pL, WHITE), (right, pR, GOLD)):
        ph = py + 150
        for sx in (-110, 110): d.line([px * S, py * S, (px + sx) * S, ph * S], fill=GOLD + (200,), width=4 * S)
        d.chord([(px - 140) * S, (ph - 60) * S, (px + 140) * S, (ph + 60) * S], 0, 180, fill=GOLD + (255,))
        if col == GOLD: _gold_text(img, (px, ph + 120), val, 70)
        else: _txt(d, (px, ph + 120), val, 70, WHITE, "XB")
        _lines(d, px, ph + 190, lab, 32)

def waffle(img, x0, y0, frac, value, label):
    """grille 10 × 10 : une proportion en %"""
    d = ImageDraw.Draw(img); c = 54; g = 10; k = round(frac * 100)
    def f(dd, col, only):
        for i in range(100):
            r, cc = divmod(i, 10)
            if (i < k) == only:
                x = x0 + cc * c; y = y0 + (9 - r) * c
                dd.rounded_rectangle([x * S, y * S, (x + c - g) * S, (y + c - g) * S], 8 * S, fill=col)
    _translucent(img, lambda dd: f(dd, (255, 255, 255, 45), False))
    _gold_glow(img, lambda dd: f(dd, GOLD + (255,), True), 20); f(d, GOLD + (255,), True)
    _gold_text(img, (x0 + 10 * c + 220, y0 + 220), value, 120, glow=False)
    _lines(d, x0 + 10 * c + 220, y0 + 330, label)

def progress(img, y, frac, value, label, target=None, target_txt=""):
    """barre de progression vers un objectif (target = position 0-1 du repère)"""
    d = ImageDraw.Draw(img); x0, x1, h = 110, 970, 70
    _translucent(img, lambda dd: dd.rounded_rectangle([x0 * S, y * S, x1 * S, (y + h) * S], h / 2 * S, fill=(255, 255, 255, 40)))
    xe = x0 + (x1 - x0) * max(0.04, min(1.0, frac))
    _gold_glow(img, lambda dd: dd.rounded_rectangle([x0 * S, y * S, xe * S, (y + h) * S], h / 2 * S, fill=GOLD + (255,)), 26)
    d.rounded_rectangle([x0 * S, y * S, xe * S, (y + h) * S], h / 2 * S, fill=GOLD + (255,))
    _gold_text(img, (x0, y - 120), value, 130, anchor="lm", glow=False)
    _txt(d, (x0, y + h + 60), label, 34, MUTED, "M", "lm")
    if target is not None:
        xt = x0 + (x1 - x0) * target
        d.line([xt * S, (y - 30) * S, xt * S, (y + h + 30) * S], fill=WHITE + (255,), width=6 * S)
        _txt(d, (xt, y + h + 120), target_txt, 30, WHITE, "B")

def quote(img, y, text, who):
    """citation officielle courte (moins de 15 mots, mot pour mot)"""
    d = ImageDraw.Draw(img)
    _gold_text(img, (130, y - 40), "«", 260, anchor="lm")
    f = F("B", 58 * S); lines = wrap(d, keep_units(text), f, 820 * S)
    for k, ln in enumerate(lines): d.text((130 * S, (y + 150 + k * 74) * S), ln, font=f, fill=WHITE + (255,), anchor="lm")
    yy = y + 150 + len(lines) * 74 + 30
    d.rectangle([130 * S, yy * S, 210 * S, (yy + 6) * S], fill=GOLD + (255,))
    _txt(d, (230, yy + 3), who, 32, MUTED, "M", "lm")

def receipt(img, y0, rows, total):
    """ticket de caisse : rows = [[article, prix], …], total = [libellé, prix]"""
    d = ImageDraw.Draw(img); x0, x1 = 230, 850; rh = 74; h = 110 + rh * len(rows) + 150
    paper = [(x0, y0), (x1, y0), (x1, y0 + h)]
    zz = [(x1 - i * 31, y0 + h + (0 if i % 2 == 0 else 22)) for i in range(int((x1 - x0) / 31) + 1)] + [(x0, y0 + h)]
    poly = [(a * S, b * S) for a, b in paper + zz]
    _gold_glow(img, lambda dd: dd.polygon(poly, fill=GOLD + (255,)), 40, 0.45)
    d.polygon(poly, fill=WHITE + (255,))
    _txt(d, (540, y0 + 60), "TICKET", 34, NAVY1, "XB")
    for i, (it, pr) in enumerate(rows):
        y = y0 + 130 + i * rh
        _txt(d, (x0 + 40, y), it, 34, NAVY1, "M", "lm"); _txt(d, (x1 - 40, y), pr, 34, NAVY1, "B", "rm")
    y = y0 + 130 + len(rows) * rh
    for xx in range(x0 + 40, x1 - 40, 22): d.line([xx * S, (y - 20) * S, (xx + 10) * S, (y - 20) * S], fill=NAVY1 + (150,), width=3 * S)
    _txt(d, (x0 + 40, y + 40), total[0], 40, NAVY0, "XB", "lm")
    d.text(((x1 - 40) * S, (y + 40) * S), total[1], font=F("XB", 48 * S), fill=(176, 128, 40, 255), anchor="rm")

ICON_EXTRA = ("piggy", "car", "bolt", "plane", "shield", "hourglass", "key", "note")
def icon_extra(dd, name, cx, cy, s, c):
    X = lambda v: (cx + v * s) * S; Y = lambda v: (cy + v * s) * S; N = NAVY0 + (255,)
    if name == "piggy":
        dd.ellipse([X(-0.95), Y(-0.6), X(0.75), Y(0.62)], fill=c)
        dd.rounded_rectangle([X(0.6), Y(-0.2), X(1.0), Y(0.22)], int(s * 0.12) * S, fill=c)
        dd.polygon([(X(0.05), Y(-0.45)), (X(0.3), Y(-0.92)), (X(0.48), Y(-0.4))], fill=c)
        for xx in (-0.62, 0.18): dd.rounded_rectangle([X(xx), Y(0.4), X(xx + 0.24), Y(0.92)], int(s * 0.06) * S, fill=c)
        dd.rounded_rectangle([X(-0.38), Y(-0.42), X(0.1), Y(-0.32)], int(s * 0.04) * S, fill=N)
        dd.ellipse([X(0.34), Y(-0.2), X(0.46), Y(-0.08)], fill=N)
        dd.ellipse([X(-0.32), Y(-1.12), X(0.04), Y(-0.6)], fill=c, outline=N, width=4 * S)
    elif name == "car":
        dd.polygon([(X(-0.6), Y(-0.05)), (X(-0.35), Y(-0.6)), (X(0.4), Y(-0.6)), (X(0.68), Y(-0.05))], fill=c)
        dd.polygon([(X(-0.42), Y(-0.1)), (X(-0.25), Y(-0.48)), (X(-0.03), Y(-0.48)), (X(-0.03), Y(-0.1))], fill=N)
        dd.polygon([(X(0.07), Y(-0.1)), (X(0.07), Y(-0.48)), (X(0.32), Y(-0.48)), (X(0.52), Y(-0.1))], fill=N)
        dd.rounded_rectangle([X(-1), Y(-0.12), X(1), Y(0.5)], int(s * 0.16) * S, fill=c)
        for xx in (-0.55, 0.55):
            dd.ellipse([X(xx - 0.3), Y(0.2), X(xx + 0.3), Y(0.8)], fill=N); dd.ellipse([X(xx - 0.19), Y(0.31), X(xx + 0.19), Y(0.69)], fill=c)
    elif name == "bolt":
        dd.polygon([(X(0.2), Y(-1)), (X(-0.6), Y(0.15)), (X(-0.05), Y(0.15)), (X(-0.25), Y(1)), (X(0.6), Y(-0.2)), (X(0.05), Y(-0.2))], fill=c)
    elif name == "plane":
        dd.rounded_rectangle([X(-1), Y(-0.13), X(1), Y(0.13)], int(s * 0.13) * S, fill=c)
        dd.polygon([(X(-0.1), Y(-0.1)), (X(0.25), Y(-0.1)), (X(-0.25), Y(-0.95)), (X(-0.5), Y(-0.95))], fill=c)
        dd.polygon([(X(-0.1), Y(0.1)), (X(0.25), Y(0.1)), (X(-0.25), Y(0.95)), (X(-0.5), Y(0.95))], fill=c)
        dd.polygon([(X(-0.9), Y(-0.1)), (X(-0.7), Y(-0.1)), (X(-0.85), Y(-0.48)), (X(-1.02), Y(-0.48))], fill=c)
    elif name == "shield":
        dd.polygon([(X(0), Y(-1)), (X(0.85), Y(-0.68)), (X(0.75), Y(0.25)), (X(0), Y(1)), (X(-0.75), Y(0.25)), (X(-0.85), Y(-0.68))], fill=c)
        dd.line([X(-0.36), Y(0), X(-0.08), Y(0.3), X(0.42), Y(-0.3)], fill=N, width=int(s * 0.14) * S, joint="curve")
    elif name == "hourglass":
        w = int(s * 0.1) * S
        dd.rounded_rectangle([X(-0.75), Y(-1), X(0.75), Y(-0.85)], 6 * S, fill=c); dd.rounded_rectangle([X(-0.75), Y(0.85), X(0.75), Y(1)], 6 * S, fill=c)
        dd.line([X(-0.6), Y(-0.85), X(0), Y(0), X(-0.6), Y(0.85)], fill=c, width=w); dd.line([X(0.6), Y(-0.85), X(0), Y(0), X(0.6), Y(0.85)], fill=c, width=w)
        dd.polygon([(X(-0.32), Y(-0.45)), (X(0.32), Y(-0.45)), (X(0), Y(-0.05))], fill=c)
        dd.polygon([(X(0), Y(0.4)), (X(0.5), Y(0.82)), (X(-0.5), Y(0.82))], fill=c)
    elif name == "key":
        dd.ellipse([X(-1), Y(-0.45), X(-0.1), Y(0.45)], outline=c, width=int(s * 0.18) * S)
        dd.rectangle([X(-0.15), Y(-0.09), X(1), Y(0.09)], fill=c)
        dd.rectangle([X(0.58), Y(0.05), X(0.72), Y(0.4)], fill=c); dd.rectangle([X(0.82), Y(0.05), X(0.96), Y(0.32)], fill=c)
    elif name == "note":
        dd.rounded_rectangle([X(-1), Y(-0.58), X(1), Y(0.58)], int(s * 0.1) * S, fill=c)
        dd.rounded_rectangle([X(-0.86), Y(-0.44), X(0.86), Y(0.44)], int(s * 0.06) * S, outline=N, width=4 * S)
        dd.ellipse([X(-0.3), Y(-0.3), X(0.3), Y(0.3)], outline=N, width=5 * S)
        dd.text((X(0), Y(0)), "€", font=F("XB", int(s * 0.42) * S), fill=N, anchor="mm")

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
    elif sl["visual"] == "donut":
        donut(img, 540, sl.get("y", 500 + dy), 270, sl["frac"], sl["value"], sl.get("label", ""))
    elif sl["visual"] == "ranking":
        hbars(img, 100, sl.get("y", 300 + dy), 880, sl["items"], sl.get("hi", 0))
    elif sl["visual"] == "thermo":
        thermo(img, 300, sl.get("y", 270 + dy), sl["frac"], sl["value"], sl.get("label", ""))
    elif sl["visual"] == "calendar":
        calendar(img, 540, sl.get("y", 450 + dy), sl["day"], sl["month"], sl.get("label", ""))
    elif sl["visual"] == "people":
        people(img, sl.get("y", 470 + dy), sl.get("total", 10), sl["k"], sl["value"], sl.get("label", ""))
    elif sl["visual"] == "stat3":
        stat3(img, sl.get("y", 330 + dy), sl["items"])
    elif sl["visual"] == "timeline":
        timeline(img, sl.get("y", 560 + dy), sl["items"], sl.get("hi", -1))
    elif sl["visual"] == "ticker":
        ticker(img, sl.get("y", 300 + dy), sl["rows"])
    elif sl["visual"] == "balance":
        balance(img, sl.get("y", 520 + dy), sl["left"], sl["right"], sl.get("tilt", 0.5))
    elif sl["visual"] == "waffle":
        waffle(img, 90, sl.get("y", 300 + dy), sl["frac"], sl["value"], sl.get("label", ""))
    elif sl["visual"] == "progress":
        progress(img, sl.get("y", 560 + dy), sl["frac"], sl["value"], sl.get("label", ""), sl.get("target"), sl.get("target_txt", ""))
    elif sl["visual"] == "quote":
        quote(img, sl.get("y", 360 + dy), sl["text"], sl.get("who", ""))
    elif sl["visual"] == "receipt":
        receipt(img, sl.get("y", 200 + dy), sl["rows"], sl["total"])
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
