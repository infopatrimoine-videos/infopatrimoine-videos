"""Bento-widget motion style (light grey canvas, white/black tiles, coral neon pills, camera punch-ins).
Example: PEA. Scenes come from SPEC with sentence-synced triggers."""
import sys, math, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/claude/motion")
from motion import F, rot, place, project, FOC, W, H, clamp, ease, ease_io, lerp, fr, encode
import motion_tmpl as MT

S = 2                       # tile supersampling
BLACK = (13, 13, 16); WHITE_T = (242, 242, 244); INK = (20, 20, 24); GREY = (128, 130, 138)
LIME = (190, 230, 20); RED = (226, 45, 35); ORANGE = (240, 92, 38); CORAL = (255, 96, 92)

# ---------------- layout (canvas = 1080 x 1920) ----------------
TILES = {
    "A1": (60, 240, 680, 860, "white"),
    "A2": (710, 240, 1020, 560, "black"),
    "A3": (710, 590, 1020, 860, "white"),
    "B":  (60, 890, 1020, 1240, "green"),
    "C1": (60, 1270, 360, 1550, "white"),
    "C2": (60, 1580, 360, 1860, "white"),
    "C3": (390, 1270, 1020, 1860, "black"),
}

def rr_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); return m

_base = {}
def tile_base(name):
    if name not in _base:
        x0, y0, x1, y1, kind = TILES[name]; w, h = (x1 - x0) * S, (y1 - y0) * S
        if kind == "white":
            y = np.linspace(0, 1, h)[:, None, None]
            arr = (np.array([248, 248, 250]) * (1 - y) + np.array([232, 233, 236]) * y) * np.ones((h, w, 3))
        elif kind == "black":
            y = np.linspace(0, 1, h)[:, None, None]
            arr = (np.array([24, 24, 28]) * (1 - y) + np.array([8, 8, 10]) * y) * np.ones((h, w, 3))
        else:  # green gradient like the reference car card
            x = np.linspace(0, 1, w)[None, :, None]
            arr = (np.array([24, 120, 30]) * (1 - x) + np.array([8, 12, 9]) * x) * np.ones((h, w, 3))
        g = Image.fromarray(arr.astype(np.uint8), "RGB")
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); img.paste(g, (0, 0), rr_mask(w, h, 64 * S))
        ImageDraw.Draw(img).rounded_rectangle([1, 1, w - 2, h - 2], 64 * S,
                                              outline=(255, 255, 255, 60 if kind != "white" else 255), width=2 * S)
        _base[name] = img
    return _base[name].copy()

def T(d, xy, s, w, size, col, a=1.0, anchor="la"):
    if a <= 0.01: return
    d.text((xy[0] * S, xy[1] * S), s, font=F(w, size * S), fill=tuple(col) + (int(255 * a),), anchor=anchor)

def neon_pill(img, box, text_s, a=1.0, size=64):
    """glowing coral pill like the reference clip."""
    if a <= 0.01: return
    x0, y0, x1, y1 = [v * S for v in box]; r = (y1 - y0) // 2
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([x0, y0, x1, y1], r, fill=CORAL + (int(200 * a),))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16 * S)))
    w, h = x1 - x0, y1 - y0
    yy = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array([170, 44, 48]) * (1 - yy) + np.array([70, 14, 18]) * yy) * np.ones((h, w, 3))
    pill = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    m = rr_mask(w, h, r).point(lambda v: int(v * a)); img.paste(pill, (x0, y0), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], r, outline=(255, 140, 136, int(255 * a)), width=3 * S)
    d.rounded_rectangle([x0 + 6 * S, y0 + 5 * S, x1 - 6 * S, y0 + h * 0.45], r, fill=(255, 255, 255, int(12 * a)))
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), text_s, font=F("B", size * S), fill=(255, 255, 255, int(255 * a)), anchor="mm")

# ---------------- tile widgets (content comes from the spec: C = SPEC_T[name]) ----------------
SPEC_T = {}
def cnt(c, g):
    v = c["value"] * g; return fr(v, c.get("dec", 0)) + (" " + c["unit"] if c.get("unit") else "")

def draw_A1(p, t):   # "big": label, value, unit, dec, note ; orange growing bars
    c = SPEC_T["A1"]; img = tile_base("A1"); d = ImageDraw.Draw(img); a = ease(p)
    T(d, (44, 52), c["label"], "M", 38, GREY, a)
    s = cnt(c, ease(clamp((t - 0.2) / 1.3)))
    T(d, (40, 120), s, "S", 104 if len(s) < 10 else (92 if len(s) < 12 else 76), INK, a)
    for i in range(6):
        k = ease(clamp((t - 0.6 - i * 0.12) / 0.5)); hh = (60 + i * 38) * k; x = 44 + i * 92
        d.rounded_rectangle([x * S, (520 - hh) * S, (x + 70) * S, 520 * S], 16 * S, fill=(220, 221, 226, int(255 * a)))
        if hh > 10: d.rounded_rectangle([x * S, (520 - hh * 0.55) * S, (x + 70) * S, 520 * S], 16 * S, fill=ORANGE + (int(255 * a),))
    T(d, (44, 560), c.get("note", ""), "M", 32, GREY, ease(clamp((t - 1.4) / 0.5)) * a)
    return img

def draw_A2(p, t):   # "pill": label, label2, start, value, unit, dec, note ; neon counter start -> value
    c = SPEC_T["A2"]; img = tile_base("A2"); d = ImageDraw.Draw(img); a = ease(p)
    T(d, (34, 40), c["label"], "M", 30, (170, 170, 180), a)
    T(d, (34, 80), c.get("label2", ""), "M", 30, (110, 110, 120), a)
    g = ease(clamp((t - 0.6) / 1.4)); v = c.get("start", 0) + (c["value"] - c.get("start", 0)) * g
    dec = 0 if (g >= 0.999 and abs(c["value"] - round(c["value"])) < 1e-6) else c.get("dec", 0)
    s = fr(v, dec) + (" " + c["unit"] if c.get("unit") else "")
    neon_pill(img, (34, 150, 276, 250), s, a, 56 if len(s) < 7 else 44)
    T(d, (155, 288), c.get("note", ""), "M", 28, LIME, ease(clamp((t - 1.9) / 0.4)) * a, "ma")
    return img

def draw_A3(p, t):   # "stat": label, label2, value, unit, dec, note
    c = SPEC_T["A3"]; img = tile_base("A3"); d = ImageDraw.Draw(img); a = ease(p)
    T(d, (30, 36), c["label"], "M", 30, GREY, a); T(d, (30, 72), c.get("label2", ""), "M", 30, GREY, a)
    s = cnt(c, ease(clamp((t - 0.2) / 1.0)))
    T(d, (26, 120), s, "S", 80 if len(s) < 7 else 60, INK, a)
    T(d, (30, 222), c.get("note", ""), "M", 28, ORANGE, ease(clamp((t - 1.0) / 0.4)) * a)
    return img

def draw_B(p, t):    # "compare" (green): label, value, unit, dec, suffix, ratio (0-1 bar), note
    c = SPEC_T["B"]; img = tile_base("B"); d = ImageDraw.Draw(img); a = ease(p)
    T(d, (52, 44), c["label"], "M", 38, (170, 255, 170), a)
    g = ease(clamp((t - 0.3) / 1.3)); s = cnt(c, g)
    T(d, (48, 104), s, "S", 120 if len(s) < 10 else 96, (205, 255, 205), a)
    T(d, (52 + d.textlength(s, font=F("S", (120 if len(s) < 10 else 96) * S)) / S + 18, 196), c.get("suffix", ""), "M", 40, (150, 220, 150), a)
    x0, x1, y0, y1 = 52, 908, 268, 300
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], 16 * S, fill=(255, 255, 255, int(30 * a)))
    xe = x0 + (x1 - x0) * c.get("ratio", 0.6) * g
    if xe > x0 + 20: d.rounded_rectangle([x0 * S, y0 * S, xe * S, y1 * S], 16 * S, fill=(40, 235, 40, int(255 * a)))
    T(d, (52, 318), c.get("note", ""), "M", 28, (150, 200, 150), ease(clamp((t - 1.2) / 0.4)) * a)
    return img

def draw_C1(p, t):   # "clock": label (e.g. "5 ans", "8 ans", "Délai")
    c = SPEC_T["C1"]; img = tile_base("C1"); d = ImageDraw.Draw(img); a = ease(p)
    cx, cy, R = 150 * S, 128 * S, 100 * S
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(226, 227, 231, int(255 * a)))
    for k in range(12):
        ang = k / 12 * 2 * math.pi; r0 = R * (0.82 if k % 3 else 0.74)
        d.line([(cx + r0 * math.sin(ang), cy - r0 * math.cos(ang)), (cx + R * 0.9 * math.sin(ang), cy - R * 0.9 * math.cos(ang))],
               fill=(150, 150, 158, int(255 * a)), width=3 * S)
    spin = t * 2.4 * math.pi * min(1, p * 2)
    for L, wdt, ang, col in [(0.55, 7, spin / 12, INK), (0.8, 5, spin, INK), (0.85, 3, spin * 3, RED)]:
        d.line([(cx, cy), (cx + R * L * math.sin(ang), cy - R * L * math.cos(ang))], fill=col + (int(255 * a),), width=wdt * S)
    d.ellipse([cx - 9 * S, cy - 9 * S, cx + 9 * S, cy + 9 * S], fill=RED + (int(255 * a),))
    T(d, (150, 262), c["label"], "S", 34, INK, a, "md")
    return img

def draw_C2(p, t):   # "mini": label, value, unit, dec, fill (0-1 of the 5 orange bars)
    c = SPEC_T["C2"]; img = tile_base("C2"); d = ImageDraw.Draw(img); a = ease(p)
    T(d, (150, 44), c["label"], "M", 28, GREY, a, "ma")
    s = cnt(c, ease(clamp((t - 0.2) / 1.0)))
    T(d, (150, 86), s, "S", 58 if len(s) < 8 else 44, (120, 122, 130), a, "ma")
    nb = round(5 * c.get("fill", 1.0))
    for i in range(5):
        k = ease(clamp((t - 0.4 - i * 0.1) / 0.4)) if i < nb else 0; x = 34 + i * 48
        d.rounded_rectangle([x * S, 178 * S, (x + 40) * S, 250 * S], 12 * S, fill=(222, 223, 228, int(255 * a)))
        if k > 0.02: d.rounded_rectangle([x * S, (250 - 72 * k) * S, (x + 40) * S, 250 * S], 12 * S, fill=ORANGE + (int(255 * a),))
    return img

def draw_C3(p, t):   # "grid" (black): title, title2, tag, cells [[label, "red"|"lime"]]*8, legend_red, legend_lime
    c = SPEC_T["C3"]; img = tile_base("C3"); d = ImageDraw.Draw(img); a = ease(p)
    T(d, (48, 48), c["title"], "M", 52, (245, 245, 248), a); T(d, (48, 108), c.get("title2", ""), "M", 52, (245, 245, 248), a)
    s = c.get("tag", "")
    if s:
        tw = d.textlength(s, font=F("M", 26 * S)) / S
        d.rounded_rectangle([(560 - tw - 40) * S, 60 * S, 560 * S, 108 * S], 24 * S, outline=(80, 80, 90, int(255 * a)), width=2 * S)
        T(d, (540 - tw, 84), s, "M", 26, (200, 200, 210), a, "lm")
    for i, (lab, kind) in enumerate(c["cells"][:8]):
        cx, cy = 100 + (i % 4) * 140, 250 + (i // 4) * 140
        k = ease(clamp((t - 0.3 - i * 0.22) / 0.35)); R = 54; fs = 28 if len(lab) < 6 else 22
        if kind == "red":
            d.ellipse([(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S], outline=(RED if k > 0.5 else (60, 60, 68)) + (int(255 * a),), width=4 * S)
            T(d, (cx, cy), lab, "M", fs, (230, 230, 235) if k > 0.5 else (110, 110, 120), a, "mm")
        else:
            if k > 0.02: d.ellipse([(cx - R * k) * S, (cy - R * k) * S, (cx + R * k) * S, (cy + R * k) * S], fill=LIME + (int(255 * a),))
            else: d.ellipse([(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S], outline=(60, 60, 68, int(255 * a)), width=4 * S)
            T(d, (cx, cy), lab, "S", fs, (20, 30, 5) if k > 0.5 else (110, 110, 120), a, "mm")
    la = ease(clamp((t - 0.9) / 0.4)) * a; lb = ease(clamp((t - 2.0) / 0.4)) * a
    d.ellipse([48 * S, 488 * S, 72 * S, 512 * S], fill=RED + (int(255 * la),)); T(d, (86, 500), c.get("legend_red", ""), "M", 30, (220, 220, 228), la, "lm")
    d.ellipse([48 * S, 538 * S, 72 * S, 562 * S], fill=LIME + (int(255 * lb),)); T(d, (86, 550), c.get("legend_lime", ""), "M", 30, (220, 220, 228), lb, "lm")
    return img

DRAW = {"A1": draw_A1, "A2": draw_A2, "A3": draw_A3, "B": draw_B, "C1": draw_C1, "C2": draw_C2, "C3": draw_C3}

# ---------------- spec loading ----------------
FULL = (0, 0, 1080, 1920)
def R_(*names):
    xs0 = min(TILES[n][0] for n in names); ys0 = min(TILES[n][1] for n in names)
    xs1 = max(TILES[n][2] for n in names); ys1 = max(TILES[n][3] for n in names)
    return (xs0 - 30, ys0 - 30, xs1 + 30, ys1 + 30)
SPEC = []; REVEAL = {}; CAM = []; HOOK = {}; RECAP = {}
def load(spec):
    """spec = {"hook": {"title","sub"}, "recap": {"big","sub"}, "tiles": {A1..C3: {...}},
               "scenes": [...], "reveal": {tile: [scene, sentence, delay]}, "cam": [[scene, sentence, delay, [tiles] or "full"]]}"""
    global SPEC, REVEAL, CAM, HOOK, RECAP
    SPEC = spec["scenes"]; HOOK = spec["hook"]; RECAP = spec["recap"]
    SPEC_T.clear(); SPEC_T.update(spec["tiles"])
    REVEAL = {k: tuple(v) for k, v in spec["reveal"].items()}
    CAM = [(s_, i, dl, FULL if reg == "full" else R_(*reg)) for s_, i, dl, reg in spec["cam"]]
    _cache.clear()

def abs_time(timing, si, idx, delay=0.0):
    st, D, B = timing[si]; return st + (B[idx] if idx < len(B) else B[-1]) + delay

def camera(T_, timing):
    keys = [(abs_time(timing, s, i, dl), reg) for s, i, dl, reg in CAM]
    MOVE = 1.1
    start = keys[0][1]; reg = keys[0][1]; k = 1.0
    for j in range(1, len(keys)):
        tk, rg = keys[j]
        if T_ < tk: break
        kp = ease_io(clamp((tk - keys[j - 1][0]) / MOVE)) if j > 1 else 1.0
        start = tuple(lerp(a, b, kp) for a, b in zip(start, reg)) if j > 1 else keys[0][1]
        reg = rg; k = ease_io(clamp((T_ - tk) / MOVE))
    x0, y0, x1, y1 = [lerp(a, b, k) for a, b in zip(start, reg)]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    zoom = min(1.55, 1000 / (x1 - x0), 1640 / (y1 - y0))
    move = math.sin(math.pi * clamp(k))          # tilt while moving, like the clip
    rx = 4 + 7 * move + 1.2 * math.sin(T_ * 0.7); ry = -3 - 6 * move + 1.2 * math.cos(T_ * 0.6)
    return cx, cy, zoom, rx, ry

_cache = {}
def tile_img(name, p, t):
    if name == "C1": return DRAW[name](p, t)               # clock keeps ticking
    tq = round(t * 30) / 30 if t < 3.6 else 3.6            # animations finish by ~3.5 s
    key = (name, round(p, 3), tq)
    if key not in _cache:
        if len(_cache) > 400: _cache.clear()
        _cache[key] = DRAW[name](p, tq)
    return _cache[key]

_bg = None
def bg():
    global _bg
    if _bg is None:
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.48) / (H * 0.62)) ** 2)
        v = np.clip(1 - 0.42 * r ** 2, 0.45, 1)
        arr = (np.array([222, 224, 227])[None, None, :] * v[..., None]).astype(np.uint8)
        _bg = Image.fromarray(arr, "RGB").convert("RGBA")
    return _bg.copy()

_sh = {}
def shadow(name):
    if name not in _sh:
        x0, y0, x1, y1, _ = TILES[name]; w, h = x1 - x0, y1 - y0; m = 60
        s = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
        ImageDraw.Draw(s).rounded_rectangle([m, m, m + w, m + h], 64, fill=(40, 45, 55, 110))
        _sh[name] = s.filter(ImageFilter.GaussianBlur(26))
    return _sh[name]

def frame_at(T_, timing):
    img = bg()
    cx, cy, zoom, rx, ry = camera(T_, timing)
    R = rot(rx, ry, 0)
    Z = FOC / zoom - FOC
    hook_end = abs_time(timing, 1, 0)
    for name, (x0, y0, x1, y1, kind) in TILES.items():
        # tiles pop in during the hook (empty), staggered
        i = list(TILES).index(name)
        pop = ease((T_ - 0.15 - i * 0.12) / 0.5)
        if pop <= 0.01: continue
        tcx, tcy = (x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy
        Tr = R @ np.array([tcx, tcy + (1 - pop) * 80, 0.0]) + np.array([0, 0, Z])
        sc = 0.9 + 0.1 * pop
        place(img, shadow(name), R, Tr + R @ np.array([0, 22.0, 0]), pop * 0.9, scale=sc)
        s_, i_, dl = REVEAL[name]; tr = abs_time(timing, s_, i_, dl)
        p = clamp((T_ - tr) / 0.5); t_loc = max(0.0, T_ - tr)
        place(img, tile_img(name, p, t_loc), R, Tr, pop, scale=sc / S)
    # overlays
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    si = max(i for i in range(len(timing)) if T_ >= timing[i][0])
    st, D, B = timing[si]; u = T_ - st
    if si == 0:   # hook title card (neon glass) over dimmed bento
        a = ease((D - 0.3 - u) / 0.4)
        if a > 0.01:
            lay.alpha_composite(Image.new("RGBA", (W, H), (230, 231, 234, int(150 * a))))
            card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            neon_box = (140, 700, 940, 1060)
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(gl).rounded_rectangle(neon_box, 70, fill=CORAL + (int(170 * a),))
            card.alpha_composite(gl.filter(ImageFilter.GaussianBlur(40)))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle(neon_box, 70, fill=(14, 14, 18, int(250 * a)), outline=(255, 130, 126, int(255 * a)), width=4)
            sc = 1.0
            cd.text((W / 2, 830), HOOK["title"], font=F("B", int((150 if len(HOOK["title"]) < 9 else 1250 // max(9, len(HOOK["title"]))) * sc)), fill=(255, 255, 255, int(255 * a)), anchor="mm")
            cd.text((W / 2, 965), HOOK.get("sub", ""), font=F("M", 44), fill=(255, 150, 146, int(255 * a)), anchor="mm")
            lay.alpha_composite(card)
            lg = MT.logo(110)
            if lg is not None: lay.alpha_composite(lg, (W // 2 - 55, 1110))
    elif SPEC[si]["type"] == "step":
        a = min(ease((u - 0.1) / 0.4), ease((D - 0.2 - u) / 0.3))
        if a > 0.01:
            s = f"{SPEC[si]['num']} · {SPEC[si]['kicker']}"; f = F("S", 46); tw = d.textlength(s, font=f)
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(gl).rounded_rectangle([W / 2 - tw / 2 - 40, 140, W / 2 + tw / 2 + 40, 240], 40, fill=CORAL + (int(150 * a),))
            lay.alpha_composite(gl.filter(ImageFilter.GaussianBlur(14)))
            d.rounded_rectangle([W / 2 - tw / 2 - 36, 144, W / 2 + tw / 2 + 36, 236], 46, fill=(16, 16, 20, int(245 * a)), outline=(255, 130, 126, int(255 * a)), width=3)
            d.text((W / 2, 190), s, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    else:         # recap: saving pill + logo + CTA over the full bento
        a = ease((u - 0.6) / 0.5)
        if a > 0.01:
            lay.alpha_composite(Image.new("RGBA", (W, H), (228, 229, 233, int(225 * a))))
            pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            box = (170, 640, 910, 840)
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(gl).rounded_rectangle(box, 100, fill=CORAL + (int(190 * a),))
            pl.alpha_composite(gl.filter(ImageFilter.GaussianBlur(36)))
            pd = ImageDraw.Draw(pl)
            pd.rounded_rectangle(box, 100, fill=(120, 28, 32, int(255 * a)), outline=(255, 140, 136, int(255 * a)), width=4)
            g = ease((u - 0.6) / 1.2)
            pd.text((W / 2, 740), RECAP["big"], font=F("B", 110 if len(RECAP["big"]) < 11 else 80), fill=(255, 255, 255, int(255 * a)), anchor="mm")
            pd.text((W / 2, 885), RECAP.get("sub", ""), font=F("M", 42), fill=(30, 30, 36, int(255 * a)), anchor="mm")
            lay.alpha_composite(pl)
        ac = ease((u - B[-1]) / 0.5)
        if ac > 0.01:
            lg = MT.logo(170)
            if lg is not None:
                im = lg.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * ac))); lay.alpha_composite(im, (W // 2 - 85, 990))
            cl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(cl)
            s = "Abonne-toi à Info Patrimoine"; f = F("B", 44); tw = d.textlength(s, font=f)
            d.rounded_rectangle([W / 2 - tw / 2 - 44, 1200, W / 2 + tw / 2 + 44, 1300], 50, fill=(12, 12, 16, int(245 * ac)))
            d.text((W / 2, 1250), s, font=f, fill=(255, 255, 255, int(255 * ac)), anchor="mm")
            d.text((W / 2, 1350), "Une notion de patrimoine par jour · info pédagogique, pas un conseil",
                   font=F("R", 28), fill=(80, 82, 90, int(255 * ac)), anchor="mm")
            lay.alpha_composite(cl)
    img.alpha_composite(lay)
    tot = timing[-1][0] + timing[-1][1]
    ImageDraw.Draw(img).rectangle([0, 0, int(W * T_ / tot), 6], fill=CORAL + (255,))
    if T_ > tot - 0.5:
        img = Image.blend(Image.new("RGBA", (W, H), (222, 224, 227, 255)), img, clamp((tot - T_) / 0.5))
    return img

def est_timing(cps=14.0):
    out = []; st = 0.0
    for S_ in SPEC:
        B = []; t = 0.0
        for s in S_["say"]: B.append(t); t += len(s) / cps + 0.35
        out.append((st, t + 0.4, B)); st += t + 0.4
    return out

if __name__ == "__main__":
    # python3 bento.py stills <name> [timing.json|x] [t ...]
    sys.path.insert(0, os.getcwd()); import bento_specs
    load(bento_specs.BENTO[sys.argv[2]])
    timing = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and sys.argv[3].endswith(".json") else est_timing()
    ts = [float(x) for x in sys.argv[4:]] or [2.0, 6.0, 12.0, 17.0, 24.0, 30.0]
    ims = [frame_at(t, timing).convert("RGB").resize((270, 480)) for t in ts]
    c = Image.new("RGB", (270 * len(ims), 480))
    for i, im in enumerate(ims): c.paste(im, (i * 270, 0))
    c.save("stills.png"); print("stills.png")
