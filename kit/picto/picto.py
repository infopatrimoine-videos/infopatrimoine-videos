"""Style PICTO : fond noir, pictogrammes blancs, gros mots, transitions « whip » avec flou de mouvement.
Moteur générique piloté par une spec (picto_specs.py). Voir README_picto.md.
python3 picto.py stills <nom> timing.json voice.mp3 t1 t2 ...   (aperçu -> stills.png)"""
import sys, math, json, os, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/home/claude/motion")
import motion_tmpl as MT

W, H, FPS = 1080, 1920, 30
WH = (245, 245, 245); BK = (0, 0, 0); GR = (120, 120, 124); DG = (46, 46, 50); RED = (255, 70, 70)
FD = "/usr/share/fonts/opentype/inter/"
@functools.lru_cache(None)
def F(w, s):
    return ImageFont.truetype(FD + {"K": "InterDisplay-Black.otf", "XB": "InterDisplay-ExtraBold.otf", "B": "InterDisplay-Bold.otf",
                                    "S": "InterDisplay-SemiBold.otf", "M": "InterDisplay-Medium.otf", "R": "InterDisplay-Regular.otf",
                                    "L": "InterDisplay-Light.otf"}[w], int(s))

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x, k=1.7): x = clamp(x); x -= 1; return 1 + x * x * ((k + 1) * x + k)
def lerp(a, b, t): return a + (b - a) * t
def fr(v, dec=0): return f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")

TIMING = []; DUR = 1.0; SPEC = {}; PANELS = []
def at(s, i=0, d=0.0):
    st, D, B = TIMING[s]; return st + (B[i] if i < len(B) else B[-1]) + d
def AT(ref): return at(*ref)

# ---------------------------------------------------------------- drawing helpers (layer = RGBA W x H)
def mblur(img, dx, dy=0.0):
    L = int(abs(dx) + abs(dy))
    if L < 3: return img
    k = np.zeros((2 * L + 1, 2 * L + 1), np.float32)
    cv2.line(k, (L - int(dx / 2), L - int(dy / 2)), (L + int(dx / 2), L + int(dy / 2)), 1.0, 1)
    k /= k.sum()
    a = np.asarray(img).astype(np.float32); al = a[..., 3:4] / 255.0
    pm = np.concatenate([a[..., :3] * al, a[..., 3:4]], 2)
    pm = cv2.filter2D(pm, -1, k)
    out = np.zeros_like(pm); al2 = pm[..., 3:4] / 255.0
    out[..., :3] = np.where(al2 > 1e-3, pm[..., :3] / np.maximum(al2, 1e-3), 0); out[..., 3] = pm[..., 3]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")

def put(L, spr, cx, cy, sc=1.0, a=1.0, blur=(0, 0), rot=0.0):
    if a <= 0.01 or sc <= 0.01: return
    im = spr
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(sc - 1) > 1e-3: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    if blur != (0, 0):
        pad = int(abs(blur[0]) + abs(blur[1])) + 2
        big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); big.paste(im, (pad, pad)); im = mblur(big, *blur)
    if a < 0.999:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    L.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2))) if (0 <= int(cx - im.width / 2) and 0 <= int(cy - im.height / 2)
                      and int(cx - im.width / 2) + im.width <= W and int(cy - im.height / 2) + im.height <= H) else _paste_clip(L, im, int(cx - im.width / 2), int(cy - im.height / 2))

def _paste_clip(L, im, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + im.width), min(H, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    L.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

@functools.lru_cache(512)
def text_spr(s, w, size, col=WH, outline=0, track=0):
    f = F(w, size); bb = f.getbbox(s, stroke_width=outline)
    tw = bb[2] - bb[0] + 2 * outline + 8 + track * len(s); th = bb[3] - bb[1] + 2 * outline + 8
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if outline:
        m1 = Image.new("L", im.size, 0); ImageDraw.Draw(m1).text((4 - bb[0] + outline, 4 - bb[1] + outline), s, font=f, fill=255, stroke_width=outline, stroke_fill=255)
        m2 = Image.new("L", im.size, 0); ImageDraw.Draw(m2).text((4 - bb[0] + outline, 4 - bb[1] + outline), s, font=f, fill=255)
        m = Image.fromarray(np.clip(np.asarray(m1).astype(int) - np.asarray(m2).astype(int), 0, 255).astype(np.uint8))
        im.paste(Image.new("RGBA", im.size, col + (255,)), (0, 0), m)
    elif track:
        x = 4 - bb[0]
        for ch in s:
            d.text((x, 4 - bb[1]), ch, font=f, fill=col + (255,)); x += f.getlength(ch) + track
    else:
        d.text((4 - bb[0], 4 - bb[1]), s, font=f, fill=col + (255,))
    return im

def txt(L, s, cx, cy, size, w="K", col=WH, a=1.0, sc=1.0, blur=(0, 0), outline=0, track=0):
    put(L, text_spr(s, w, size, col, outline, track), cx, cy, sc, a, blur)

def fit(s, w, size, maxw):
    while F(w, size).getlength(s) > maxw and size > 20: size -= 4
    return size

# ---------------------------------------------------------------- pictograms (drawn 2x, white)
SS = 2
def canvas(w, h): im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def done(im): return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
def P(*v): return [x * SS for x in v]

@functools.lru_cache(None)
def coin(r=150, glyph="€", wings=False):
    ww = int(r * 4.6) if wings else 2 * r + 20; hh = 2 * r + 20
    im, d = canvas(ww, hh); cx, cy = ww / 2, hh / 2
    if wings:
        for side in (-1, 1):
            for k in range(4):
                L = r * (1.55 - k * 0.25); y = cy - r * 0.55 + k * r * 0.30; x0 = cx + side * r * 0.6
                x1 = x0 + side * L
                d.rounded_rectangle(P(min(x0, x1), y - r * 0.13, max(x0, x1), y + r * 0.13), radius=int(r * 0.13 * SS), fill=WH + (255,), outline=BK + (255,), width=5 * SS)
    d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill=WH + (255,))
    d.ellipse(P(cx - r * .8, cy - r * .8, cx + r * .8, cy + r * .8), outline=BK + (255,), width=int(r * .05 * SS))
    fs = int(r * 1.1 * SS)
    while F("K", fs).getlength(glyph) > r * 1.3 * SS: fs -= 4
    f = F("K", fs)
    d.text((cx * SS, cy * SS), glyph, font=f, fill=BK + (255,), anchor="mm")
    return done(im)

def stick(pose="walk", ph=0.0, h=420, lw=26):
    im, d = canvas(int(h * 0.9), h + 20); cx = im.width / SS / 2; c = WH + (255,)
    hr = h * 0.12
    if pose == "sad":
        hx, hy = cx + h * 0.12, h * 0.27; sh = (cx + h * 0.02, h * 0.36); hip = (cx - h * 0.03, h * 0.62)
        d.line(P(*sh, *hip), fill=c, width=lw * SS)
        d.line(P(*sh, sh[0] + h * 0.10, sh[1] + h * 0.22), fill=c, width=lw * SS, joint="curve")
        for s in (-1, 1): d.line(P(*hip, hip[0] + s * h * 0.07, h * 0.98), fill=c, width=lw * SS)
        d.ellipse(P(hx - hr, hy - hr, hx + hr, hy + hr), fill=c)
    else:
        sw = math.sin(ph); hx, hy = cx + h * 0.05, h * 0.13; sh = (cx + h * 0.02, h * 0.30); hip = (cx - h * 0.02, h * 0.60)
        d.line(P(*sh, *hip), fill=c, width=lw * SS)
        for s in (-1, 1):
            a = s * sw * 0.9
            kx, ky = hip[0] + math.sin(a) * h * 0.2, hip[1] + math.cos(a) * h * 0.2
            d.line(P(*hip, kx, ky, kx + math.sin(a - 0.5 * abs(a) - 0.2) * h * 0.2, ky + math.cos(a) * h * 0.2), fill=c, width=lw * SS, joint="curve")
            b = -s * sw * 0.8
            ex, ey = sh[0] + math.sin(b) * h * 0.15, sh[1] + math.cos(b) * h * 0.15
            d.line(P(*sh, ex, ey, ex + math.sin(b + 0.8) * h * 0.14, ey + math.cos(b + 0.8) * h * 0.14), fill=c, width=int(lw * 0.8) * SS, joint="curve")
        d.ellipse(P(hx - hr, hy - hr, hx + hr, hy + hr), fill=c)
    return done(im)

@functools.lru_cache(None)
def bust(h=200, col=WH):
    im, d = canvas(int(h * 0.9), h); cx = im.width / SS / 2; c = col + (255,)
    r = h * 0.22; d.ellipse(P(cx - r, 0, cx + r, 2 * r), fill=c)
    d.rounded_rectangle(P(cx - h * 0.4, h * 0.5, cx + h * 0.4, h * 1.25), radius=int(h * 0.3 * SS), fill=c)
    im = im.crop((0, 0, im.width, h * SS)); return done(im)

@functools.lru_cache(None)
def piggy(w=520):
    h = int(w * 0.8); im, d = canvas(w, h); c = WH + (255,); k = BK + (255,)
    bx0, by0, bx1, by1 = w * 0.1, h * 0.2, w * 0.86, h * 0.82
    for x in (w * 0.24, w * 0.62): d.rounded_rectangle(P(x, h * 0.7, x + w * 0.12, h * 0.98), radius=int(w * 0.03 * SS), fill=c)
    d.polygon(P(w * 0.62, h * 0.30, w * 0.70, h * 0.06, w * 0.78, h * 0.33), fill=c)
    d.ellipse(P(bx0, by0, bx1, by1), fill=c)
    d.rounded_rectangle(P(w * 0.82, h * 0.40, w * 0.97, h * 0.62), radius=int(w * 0.05 * SS), fill=c)
    for y in (0.47, 0.55): d.ellipse(P(w * 0.875, h * (y - 0.025), w * 0.905, h * (y + 0.025)), fill=k)
    d.ellipse(P(w * 0.70, h * 0.36, w * 0.74, h * 0.42), fill=k)
    d.rounded_rectangle(P(w * 0.38, h * 0.24, w * 0.56, h * 0.27), radius=6 * SS, fill=k)
    d.arc(P(w * 0.01, h * 0.36, w * 0.13, h * 0.5), 90, 360, fill=c, width=int(w * 0.022 * SS))
    return done(im)

@functools.lru_cache(None)
def target(r=200):
    im, d = canvas(2 * r + 10, 2 * r + 10); cx = cy = r + 5
    for i, rr in enumerate([1, .78, .56, .34, .14]):
        d.ellipse(P(cx - r * rr, cy - r * rr, cx + r * rr, cy + r * rr), fill=(WH if i % 2 == 0 else BK) + (255,))
    return done(im)

def arrow_spr(L=300, w=16):
    im, d = canvas(L + 40, 80); c = WH + (255,)
    d.line(P(0, 40, L - 20, 40), fill=c, width=w * SS); d.polygon(P(L - 40, 10, L + 30, 40, L - 40, 70), fill=c)
    for k in range(3): d.line(P(10 + k * 18, 40, k * 18 - 15, 10 + (k % 2) * 0), fill=c, width=6 * SS); d.line(P(10 + k * 18, 40, k * 18 - 15, 70), fill=c, width=6 * SS)
    return done(im)

def pie(r=220, cut=0.0):
    im, d = canvas(2 * r + 160, 2 * r + 160); cx = cy = r + 80; c = WH + (255,)
    d.pieslice(P(cx - r, cy - r, cx + r, cy + r), -40, 270, fill=c)
    ang = math.radians(-85); ox, oy = math.cos(ang) * cut * 70, math.sin(ang) * cut * 70
    d.pieslice(P(cx - r + ox, cy - r + oy, cx + r + ox, cy + r + oy), 270, 320, fill=c, outline=BK + (255,), width=6 * SS)
    return done(im)

@functools.lru_cache(None)
def building(h=360):
    w = int(h * 0.62); im, d = canvas(w, h); c = WH + (255,); k = BK + (255,)
    d.rectangle(P(0, h * 0.08, w, h), fill=c); d.rectangle(P(w * 0.1, 0, w * 0.9, h * 0.1), fill=c)
    for r in range(5):
        for q in range(3):
            x, y = w * (0.13 + q * 0.28), h * (0.17 + r * 0.14)
            d.rectangle(P(x, y, x + w * 0.18, y + h * 0.08), fill=k)
    d.rectangle(P(w * 0.38, h * 0.86, w * 0.62, h), fill=k)
    return done(im)

def padlock(h=360, close=1.0, col=WH):
    w = int(h * 0.8); im, d = canvas(w, h + 120); c = col + (255,); k = BK + (255,)
    lift = (1 - close) * 90
    d.arc(P(w * 0.2, 10 - lift + 30, w * 0.8, h * 0.62 - lift + 30), 180, 360, fill=c, width=int(h * 0.09 * SS))
    d.line(P(w * 0.2 + h * 0.045, h * 0.30 - lift + 30, w * 0.2 + h * 0.045, h * 0.48 + 30), fill=c, width=int(h * 0.09 * SS))
    d.line(P(w * 0.8 - h * 0.045, h * 0.30 - lift + 30, w * 0.8 - h * 0.045, h * 0.45 - lift + 30), fill=c, width=int(h * 0.09 * SS))
    d.rounded_rectangle(P(0, h * 0.45 + 30, w, h + 30), radius=int(h * 0.1 * SS), fill=c)
    d.ellipse(P(w * 0.42, h * 0.62 + 30, w * 0.58, h * 0.78 + 30), fill=k); d.polygon(P(w * 0.45, h * 0.72 + 30, w * 0.55, h * 0.72 + 30, w * 0.57, h * 0.9 + 30, w * 0.43, h * 0.9 + 30), fill=k)
    return done(im)

def hourglass(h=420, sand=0.5, rot=0.0):
    w = int(h * 0.62); im, d = canvas(w, h); c = WH + (255,); k = BK + (255,)
    d.rounded_rectangle(P(0, 0, w, h * 0.07), radius=8 * SS, fill=c); d.rounded_rectangle(P(0, h * 0.93, w, h), radius=8 * SS, fill=c)
    top = [(w * 0.1, h * 0.09), (w * 0.9, h * 0.09), (w * 0.53, h * 0.5), (w * 0.47, h * 0.5)]
    bot = [(w * 0.47, h * 0.5), (w * 0.53, h * 0.5), (w * 0.9, h * 0.91), (w * 0.1, h * 0.91)]
    for poly in (top, bot): d.polygon(P(*[v for p in poly for v in p]), outline=c, width=10 * SS)
    st = 1 - sand
    if st > 0.02:
        y = h * 0.5 - (h * 0.38) * st; hw = (w * 0.4) * st
        d.polygon(P(w / 2 - hw, y, w / 2 + hw, y, w / 2, h * 0.49), fill=c)
    if sand > 0.02:
        y = h * 0.9 - h * 0.3 * sand; d.polygon(P(w * 0.12, h * 0.9, w * 0.88, h * 0.9, w / 2 + w * 0.1, y, w / 2 - w * 0.1, y), fill=c)
        d.line(P(w / 2, h * 0.5, w / 2, y), fill=c, width=4 * SS)
    return done(im)

def clock(r=200, ang=0.0, col=WH):
    im, d = canvas(2 * r + 10, 2 * r + 10); cx = cy = r + 5; c = col + (255,)
    d.ellipse(P(cx - r, cy - r, cx + r, cy + r), outline=c, width=int(r * 0.1 * SS))
    for i in range(12):
        a = i / 12 * 2 * math.pi; r0 = r * 0.72
        d.line(P(cx + r0 * math.sin(a), cy - r0 * math.cos(a), cx + r * 0.82 * math.sin(a), cy - r * 0.82 * math.cos(a)), fill=c, width=6 * SS)
    d.line(P(cx, cy, cx + r * 0.6 * math.sin(ang), cy - r * 0.6 * math.cos(ang)), fill=c, width=12 * SS)
    d.line(P(cx, cy, cx + r * 0.4 * math.sin(ang / 12), cy - r * 0.4 * math.cos(ang / 12)), fill=c, width=16 * SS)
    d.ellipse(P(cx - 16, cy - 16, cx + 16, cy + 16), fill=c)
    return done(im)

@functools.lru_cache(None)
def warning(h=380, col=WH):
    w = int(h * 1.12); im, d = canvas(w, h); c = col + (255,)
    d.polygon(P(w / 2, 10, w - 10, h - 10, 10, h - 10), outline=c, width=int(h * 0.07 * SS))
    d.line(P(w / 2, h * 0.35, w / 2, h * 0.68), fill=c, width=int(h * 0.08 * SS)); d.ellipse(P(w / 2 - h * 0.05, h * 0.76, w / 2 + h * 0.05, h * 0.86), fill=c)
    return done(im)

def magnifier(r=150, inner=None):
    im, d = canvas(int(r * 3.2), int(r * 3.2)); c = WH + (255,); cx = cy = r * 1.2
    d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill=WH + (255,))
    d.line(P(cx + r * .7, cy + r * .7, cx + r * 1.9, cy + r * 1.9), fill=c, width=int(r * .28 * SS))
    im = done(im)
    if inner is not None:
        ii = inner.resize((int(r * 1.3), int(r * 1.3 * inner.height / inner.width)), Image.LANCZOS)
        blk = Image.new("RGBA", ii.size, BK + (255,)); blk.putalpha(ii.getchannel("A"))
        im.alpha_composite(blk, (int(cx - ii.width / 2), int(cy - ii.height / 2)))
    ring = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([cx - r, cy - r, cx + r, cy + r], outline=BK + (255,), width=10)
    im.alpha_composite(ring); return im

def balance(tilt=0.0, left=None, right=None, a=1.0):
    """tilt>0: right side down. returns RGBA ~ 1000x900"""
    w, h = 1000, 900; im, d = canvas(w, h); c = WH + (255,)
    cx, top = w / 2, 200
    d.rounded_rectangle(P(cx - 170, h - 60, cx + 170, h - 20), radius=14 * SS, fill=c)
    d.polygon(P(cx - 30, top, cx + 30, top, cx + 44, h - 60, cx - 44, h - 60), fill=c)
    d.ellipse(P(cx - 34, top - 34, cx + 34, top + 34), fill=c)
    ang = math.radians(tilt * 14); L = 330
    ends = []
    for s in (-1, 1):
        ex, ey = cx + s * L * math.cos(ang), top + s * L * math.sin(ang); ends.append((ex, ey))
    d.line(P(*ends[0], *ends[1]), fill=c, width=20 * SS)
    out = []
    for (ex, ey), lab in zip(ends, (left, right)):
        py = ey + 260
        for s in (-1, 1): d.line(P(ex, ey, ex + s * 130, py), fill=c, width=5 * SS)
        d.chord(P(ex - 160, py - 60, ex + 160, py + 60), 0, 180, fill=c)
        out.append((ex, py))
    im = done(im)
    dd = ImageDraw.Draw(im)
    for (ex, py), lab in zip(out, (left, right)):
        if lab:
            s, k = lab; f = F("K", 50); tw = f.getlength(s)
            y1 = py - 2 - (1 - k) * 220
            dd.rounded_rectangle([ex - tw / 2 - 24, y1 - 92, ex + tw / 2 + 24, y1 - 4], 18, fill=WH + (int(255 * min(1, k * 3)),), outline=BK + (255,), width=5)
            dd.text((ex, y1 - 48), s, font=f, fill=BK + (int(255 * min(1, k * 3)),), anchor="mm")
    return im

@functools.lru_cache(None)
def logo_spr(h):
    lg = MT.logo(h); return lg

# ---------------------------------------------------------------- background
@functools.lru_cache(None)
def background():
    im = Image.new("RGB", (W, H), BK); d = ImageDraw.Draw(im)
    hz = 1500
    for i in range(-14, 15):  # perspective floor grid
        d.line([(W / 2 + i * 40, hz), (W / 2 + i * 330, H)], fill=(26, 26, 28), width=2)
    y = hz; k = 0
    while y < H: d.line([(0, y), (W, y)], fill=(26, 26, 28), width=2); k += 1; y = hz + 12 * k * k
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / (H * 0.8)) ** 2)
    g = np.clip(1.0 - 0.9 * r, 0, 1)[..., None]
    arr = np.asarray(im).astype(np.float32) + 22 * g ** 2
    return np.clip(arr, 0, 255).astype(np.uint8)

GRAIN = [np.random.default_rng(i).normal(0, 5, (H // 2, W // 2)).astype(np.float32) for i in range(6)]

# ---------------------------------------------------------------- panels
def big_words(L, words, u, y0=820, gap=None, sizes=None):
    """words appear one by one (pop + blur), stacked."""
    n = len(words); sizes = sizes or [150] * n; gap = gap or [s * 1.02 for s in sizes]
    tot = sum(gap); y = y0 - tot / 2
    for i, (wd, sz) in enumerate(zip(words, sizes)):
        k = ease((u - i * 0.22) / 0.35)
        out = isinstance(wd, tuple); s = wd[0] if out else wd
        sz2 = fit(s, "K", sz, 960)
        txt(L, s, W / 2, y + gap[i] / 2, sz2, "K", WH, k, 0.85 + 0.15 * k, blur=(0, (1 - k) * 60), outline=6 if out else 0)
        y += gap[i]

def counter(L, v, dec, unit, u, cy, size=190, dur=1.4):
    g = ease(u / dur); s = fr(v * g, dec) + " " + unit
    sz = fit(fr(v, dec) + " " + unit, "K", size, 980)
    txt(L, s, W / 2, cy, sz, "K", WH, ease(u / 0.3))

def caption(L, s, u, cy, size=56, w="S", col=GR, delay=0.3):
    k = ease((u - delay) / 0.4); txt(L, s, W / 2, cy + (1 - k) * 30, fit(s, w, size, 980), w, col, k)

def label_pill(L, s, cx, cy, k, size=46, inv=False):
    if k <= 0.01: return
    f = F("K", size); tw = f.getlength(s)
    im = Image.new("RGBA", (int(tw + 70), int(size * 1.9)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, im.width - 3, im.height - 3], im.height // 2, fill=(WH if not inv else BK) + (255,), outline=WH + (255,), width=4)
    d.text((im.width / 2, im.height / 2), s, font=f, fill=(BK if not inv else WH) + (255,), anchor="mm")
    put(L, im, cx, cy, 0.7 + 0.3 * back(k), clamp(k * 2))

def chart_line(L, u, y0=1150, y1=600, a=0.35):
    pts = []; n = 26; rng = np.random.default_rng(3)
    for i in range(n):
        x = 80 + i * (920 / (n - 1)); y = y0 - (y0 - y1) * (i / (n - 1)) ** 1.6 + rng.normal(0, 28)
        pts.append((x, y))
    m = int(clamp(u / 1.6) * (n - 1)) + 1
    d = ImageDraw.Draw(L); d.line(pts[:m], fill=(70, 70, 76, int(255 * a * 2)), width=8, joint="curve")

# ================================================================ generic panels (driven by the spec)
def pop(k): return 0.6 + 0.4 * back(k), clamp(k * 2)

def icon_spr(name, size, u):
    """name: target, piggy, building, bust, padlock, hourglass, clock, warning, warning_red, pie, stick, coin:<txt>, coinw:<txt>"""
    if name.startswith("coin:"): return coin(int(size * 0.45), name[5:])
    if name.startswith("coinw:"): return coin(int(size * 0.3), name[6:], True)
    return {"target": lambda: target(int(size * 0.5)), "piggy": lambda: piggy(int(size * 1.25)), "building": lambda: building(int(size * 0.85)),
            "bust": lambda: bust(int(size * 0.8)), "padlock": lambda: padlock(int(size * 0.75), ease(clamp((u - 0.5) / 0.3))),
            "hourglass": lambda: hourglass(int(size * 1.05), clamp(u / 4.5)), "clock": lambda: clock(int(size * 0.45), u * 7),
            "warning": lambda: warning(int(size * 0.75)), "warning_red": lambda: warning(int(size * 0.75), RED),
            "pie": lambda: pie(int(size * 0.42), ease((u - 0.5) / 0.5)), "stick": lambda: stick("sad", h=int(size * 0.9))}[name]()

def pn_words(L, u, T, p): big_words(L, p["words"], u, p.get("y", 860), sizes=p.get("sizes"))

def pn_hook(L, u, T, p):
    txt(L, p.get("ghost", ""), W / 2, 470, fit(p.get("ghost", ""), "K", 210, 1000), "K", (60, 60, 64), 1.0, outline=5)
    u1 = at(0, 1) - p["_t0"]; cg = "coinw:" + p.get("coin", "€")
    if u < u1:
        kx = ease(u / 0.9); put(L, icon_spr(cg, 350, u), lerp(-500, W / 2, kx), 1330 + math.sin(u * 5) * 22, blur=((1 - kx) * 90, 0))
    else:
        ko = clamp((u - u1) / 0.45)
        if ko < 1: put(L, icon_spr(cg, 350, u), lerp(W / 2, W / 2 + 1400, ko * ko), 1330 - ko * 500, blur=(ko * 120, -ko * 40))
        k = ease((u - u1) / 0.4)
        txt(L, "?", 760, 1330, 520, "K", (90, 90, 96), k, outline=8)
        put(L, stick("sad", h=380), 470, 1350, 1.0, k, blur=(0, (1 - k) * 40))
    t = p["title"]; sz = min(fit(x, "K", 190, 990) for x in t); y = 865 - (len(t) - 1) * sz * 0.45
    for i, x in enumerate(t): txt(L, x, W / 2, y + i * sz * 0.9, sz, "K")
    txt(L, p.get("sub", ""), W / 2, 1100, fit(p.get("sub", ""), "XB", 62, 980), "XB", WH, ease((u - 0.8) / 0.4))
    lg = logo_spr(110)
    if lg is not None: put(L, lg, W / 2, 1640)

def pn_icon(L, u, T, p):
    """icon + title + caption + pill + note ; options: accent (coin glyph, with 'target' an arrow hits), icon_label (pie), figure (stick), people (n busts)"""
    ppl = p.get("people", 0); k = ease(u / 0.4); name = p["icon"]
    yi, yt = (560, 880) if ppl else (720, 1090)
    sc, a = pop(k); put(L, icon_spr(name, 420, u), W / 2 if not p.get("figure") else 330, yi, sc, a)
    if p.get("figure"): put(L, stick("sad", h=360), 760, yi + 40, 1.0, ease((u - 0.4) / 0.4))
    if name == "target":
        ka = clamp((u - 0.6) / 0.35); dist = lerp(900, 0, ease(ka)) + 190
        if ka > 0: put(L, arrow_spr(320), W / 2 + 15 + dist * 0.707, yi - 15 - dist * 0.707, 1.0, 1.0, blur=((1 - ka) * 60, -(1 - ka) * 60), rot=225)
    if p.get("accent"):
        kc = ease((u - 1.1) / 0.4); put(L, coin(80, p["accent"]), W / 2 - 230, yi - 200 - 60 * kc, 0.5 + 0.5 * back(kc), clamp(kc * 2))
    if p.get("icon_label"): txt(L, p["icon_label"], W / 2 + 230, yi - 200, 40, "XB", WH, ease((u - 0.5) / 0.5))
    tcol = RED if p.get("red") else WH
    txt(L, p["title"], W / 2, yt, fit(p["title"], "K", p.get("size", 150), 980), "K", tcol, ease((u - 0.2) / 0.4))
    y = yt + 105
    if p.get("caption"): caption(L, p["caption"], u, y, 52, "S", WH, 0.5); y += 110
    if ppl:
        b = bust(64); cols = 10
        for i in range(ppl):
            r, q = divmod(i, cols); kk = ease((u - 1.6 - i * 0.03) / 0.25)
            put(L, b, 150 + q * 87, y + 20 + r * 80, 0.4 + 0.6 * back(kk), clamp(kk * 2))
        y += 80 * ((ppl + cols - 1) // cols) + 60
    if p.get("pill"): label_pill(L, p["pill"], W / 2, y + 10, ease((u - p.get("pill_at", 1.4)) / 0.4), fit(p["pill"], "K", 48, 860)); y += 120
    if p.get("note"): caption(L, p["note"], u, y, 46, "M", GR, p.get("note_at", 2.4))

def pn_duo(L, u, T, p):
    """two icons side by side with labels; a coin (glyph) moves from right to left; title + caption"""
    k = ease(u / 0.4); sc, a = pop(k)
    put(L, icon_spr(p["left"][0], 380, u), 300, 720, sc, a); txt(L, p["left"][1], 300, 920, fit(p["left"][1], "XB", 50, 420), "XB", WH, k)
    put(L, icon_spr(p["right"][0], 380, u), 790, 700, sc, a); txt(L, p["right"][1], 790, 920, fit(p["right"][1], "XB", 50, 420), "XB", WH, k)
    k1 = ease((u - 0.5) / 0.4); k2 = clamp((u - 1.1) / 0.55)
    put(L, coin(85, p.get("coin_left", "€")), 300, 1080, back(k1), clamp(k1 * 2))
    if k2 > 0: put(L, coin(85, p.get("coin_right", "+")), lerp(790, 530, eio(k2)), lerp(780, 1080, eio(k2)) - math.sin(math.pi * k2) * 160)
    txt(L, p["title"], W / 2, 1300, fit(p["title"], "K", 130, 980), "K", WH, ease((u - 0.2) / 0.4))
    if p.get("caption"): caption(L, p["caption"], u, 1410, 52, "S", WH, 0.8)

def pn_save(L, u, T, p):
    """person + piggy bank, coins drop in; big words above"""
    k = ease(u / 0.4); sc, a = pop(k)
    put(L, bust(330), 290, 1110, sc, a); put(L, piggy(520), 700, 1080, sc, a)
    for j in range(3):
        kc = clamp((u - 0.5 - j * 0.6) / 0.6)
        if 0 < kc < 1: put(L, coin(55, "€"), 690, lerp(780, 960, kc * kc), 1.0, 1.0 - max(0, kc - 0.85) * 6, blur=(0, kc * 40))
    big_words(L, p["words"], u, 520, sizes=p.get("sizes", [130] * len(p["words"])))

def pn_grid(L, u, T, p):
    """60 squares (months / years / items) + magnifier finding a padlock ; title, caption, pill, note"""
    d = ImageDraw.Draw(L); x0, y0, s, g = 100, 470, 70, 18; n = p.get("cells", 60)
    for i in range(n):
        r, q = divmod(i, 10); kk = ease((u - i * 0.012) / 0.3)
        if kk <= 0: continue
        x, y = x0 + q * (s + g), y0 + r * (s + g); e = s * (1 - kk) / 2
        d.rounded_rectangle([x + e, y + e, x + s - e, y + s - e], 10, fill=(230, 230, 232, int(255 * kk)))
    km = eio((u - 0.6) / 2.2); mx = lerp(200, 640, km); my = lerp(560, 700, km) - math.sin(km * math.pi) * 120
    put(L, magnifier(130, padlock(120)), mx + 70, my + 70, 1.0, ease((u - 0.4) / 0.3))
    txt(L, p["title"], W / 2, 1110, fit(p["title"], "K", 200, 980), "K", WH, ease((u - 0.2) / 0.4))
    if p.get("caption"): caption(L, p["caption"], u, 1230, 50, "S", WH, 0.4)
    if p.get("pill"): label_pill(L, p["pill"], W / 2, 1350, ease((u - 1.0) / 0.4), fit(p["pill"], "K", 56, 860))
    if p.get("note"): caption(L, p["note"], u, 1460, 46, "M", GR, 2.6)

def pn_trap(L, u, T, p):
    """red warning + title ; cause (clock, 2 lines) -> consequence (padlock, line + red line)"""
    k = ease(u / 0.3); sh = math.sin(u * 60) * 14 * max(0, 1 - u / 0.5)
    put(L, warning(300, RED), W / 2 + sh, 520, 0.6 + 0.4 * back(k), clamp(k * 2))
    txt(L, p.get("title", "PIÈGE"), W / 2 + sh, 820, 200, "K", RED, k)
    kc = ease((u - 0.6) / 0.4); put(L, clock(120, u * 7), 290, 1090, kc, kc)
    for i, c in enumerate(p["cause"]): caption(L, c, u, 1250 + i * 55, 44, "S", WH, 0.8 + i * 0.1)
    txt(L, "→", W / 2, 1090, 120, "K", WH, ease((u - 1.6) / 0.3))
    kl = clamp((u - 2.0) / 0.5)
    if kl > 0: put(L, padlock(200, close=ease(clamp((u - 2.4) / 0.25))), 790, 1080, 1.0, ease(kl))
    e = p["effect"]
    txt(L, e[0], 790, 1260, fit(e[0], "XB", 40, 480), "XB", WH, ease((u - 2.3) / 0.3))
    if len(e) > 1: txt(L, e[1], 790, 1315, fit(e[1], "XB", 40, 480), "XB", RED, ease((u - 2.6) / 0.3))

def pn_counter(L, u, T, p):
    """big count-up number ; optional rising chart behind and accent coin above"""
    if p.get("chart"): chart_line(L, u)
    if p.get("accent"): k = ease(u / 0.4); put(L, coin(80, p["accent"]), W / 2, 560, back(k), clamp(k * 2))
    counter(L, p["value"], p.get("dec", 0), p.get("unit", ""), u - 0.2, 820, p.get("size", 190))
    if p.get("caption"): caption(L, p["caption"], u, 980, 52, "S", WH, 0.5)
    if p.get("note"): caption(L, p["note"], u, 1050, 44, "M", GR, 0.9)

def pn_flow(L, u, T, p):
    """intro words, then (step 1) a rate that drops old->new on top, piggy ; (step 2) arrow in + rate ; (step 3) arrow out + rate + pill"""
    s1, s2, s3 = (AT(r) - p["_t0"] for r in p["steps"])
    if 1 - ease((u - s1 + 0.2) / 0.35) > 0.01: big_words(L, p["words"], u, 860, sizes=p.get("sizes"))
    u1 = u - s1
    if u1 > 0:
        k1 = ease(u1 / 0.35); top = p["top"]; old = top.get("old")
        st = old if (old and u1 < 0.7) else top["new"]; kk = ease((u1 - 0.7) / 0.25) if (old and u1 >= 0.7) else 1
        txt(L, st, W / 2, 470, fit(st, "K", 200, 980), "K", WH if st == top["new"] else GR, k1, sc=(0.8 + 0.2 * kk) if st == top["new"] else 1.0)
        if old and 0.3 < u1 < 0.7: ImageDraw.Draw(L).line([(W / 2 - 230, 470), (W / 2 + 230, 470)], fill=RED + (255,), width=16)
        txt(L, top["label"], W / 2, 610, fit(top["label"], "XB", 54, 980), "XB", WH, k1)
        put(L, piggy(440), W / 2, 1060, 0.7 + 0.3 * back(ease((u1 - 0.2) / 0.4)), ease((u1 - 0.2) / 0.3))
    u2 = u - s2
    if u2 > 0 and p.get("inp"):
        k = ease(u2 / 0.4); put(L, arrow_spr(220), 300, 940, 1.0, k, rot=-30, blur=((1 - k) * 60, 0))
        txt(L, p["inp"][0], 220, 730, 96, "K", WH, k); txt(L, p["inp"][1], 220, 810, 38, "XB", GR, k)
    u3 = u - s3
    if u3 > 0 and p.get("out"):
        k = ease(u3 / 0.4); put(L, arrow_spr(220), 830, 1290, 1.0, k, rot=-30, blur=((1 - k) * 60, 0))
        txt(L, p["out"][0], 820, 1420, 96, "K", WH, k); txt(L, p["out"][1], 820, 1500, 38, "XB", GR, k)
        if p.get("pill"): label_pill(L, p["pill"], W / 2, 1610, ease((u3 - 1.2) / 0.4), fit(p["pill"], "K", 40, 900))

def pn_compare(L, u, T, p):
    """intro words ; (step 1) start coin + 2 pills ; (step 2) left pan ; (step 3) right pan, beam tips to the heavier side"""
    s1, s2, s3 = (AT(r) - p["_t0"] for r in p["steps"])
    if 1 - ease((u - s1 + 0.2) / 0.35) > 0.01: big_words(L, p["words"], u, 860, sizes=p.get("sizes"))
    u1 = u - s1
    if u1 > 0:
        k = ease(u1 / 0.4); up = ease((u1 - (s2 - s1) + 0.3) / 0.6)
        put(L, coin(150, p["coin"]), W / 2, lerp(700, 380, up), back(k) * (1 - 0.4 * up), clamp(k * 2))
        pl = p.get("pills", [])
        if len(pl) > 0: label_pill(L, pl[0], 270, lerp(990, 560, up), ease((u1 - 1.0) / 0.4), fit(pl[0], "K", 36, 380))
        if len(pl) > 1: label_pill(L, pl[1], 790, lerp(990, 560, up), ease((u1 - 2.4) / 0.4), fit(pl[1], "K", 36, 380))
    u2 = u - s2
    if u2 > 0:
        kl = ease(u2 / 0.6); u3 = u - s3; kr = ease(u3 / 0.6) if u3 > 0 else 0
        heavy = 1 if p.get("heavier", "right") == "right" else -1
        tilt = -heavy * 0.5 * kl * (1 - kr) + heavy * 0.9 * kr + (math.sin(u3 * 8) * 0.12 * max(0, 1 - u3 / 1.2) if u3 > 0 else 0)
        put(L, balance(tilt, (p["left"][0], kl), (p["right"][0], kr) if kr > 0 else None), W / 2, 1150, 0.9, ease(u2 / 0.3))
        txt(L, p["left"][1], W / 2 - 300, 1600, 40, "XB", GR, kl); txt(L, p["right"][1], W / 2 + 300, 1600, 40, "XB", WH, kr)
        if u3 > 0 and p.get("caption"): caption(L, p["caption"], u3, 1720, 44, "S", WH, 1.4)

def pn_recap(L, u, T, p):
    """'À RETENIR' + 2 lines [icon, line1, line2] ; at cta: logo + Abonne-toi"""
    s1 = AT(p["cta"]) - p["_t0"]; kout = ease((u - s1 + 0.3) / 0.4)
    if kout < 1:
        a = 1 - kout; big_words(L, [p.get("title", "À RETENIR")], u, 520, sizes=[150])
        for i, (ic, l1, l2) in enumerate(p["lines"][:2]):
            k = ease((u - 0.6 - i * 1.8) / 0.4); y = 900 + i * 340; sc, aa = pop(k)
            put(L, icon_spr(ic, 300, u), 300, y, sc, aa * a)
            txt(L, l1, 750, y - 45, fit(l1, "K", 90, 560), "K", WH, k * a); txt(L, l2, 750, y + 40, fit(l2, "K", 70, 560), "K", WH, k * a)
    u1 = u - s1
    if u1 > 0:
        k = ease(u1 / 0.5); lg = logo_spr(260)
        if lg is not None: put(L, lg, W / 2, 760, 0.7 + 0.3 * back(k), clamp(k * 2))
        txt(L, "Abonne-toi", W / 2, 1010, 110, "K", WH, ease((u1 - 0.3) / 0.4))
        txt(L, "INFO PATRIMOINE", W / 2, 1130, 70, "K", WH, ease((u1 - 0.5) / 0.4), track=6)
        caption(L, "une notion de patrimoine par jour", u1, 1240, 46, "M", GR, 0.8)
        caption(L, "info pédagogique, pas un conseil", u1, 1300, 34, "M", (90, 90, 96), 1.0)

PN = {"hook": pn_hook, "words": pn_words, "icon": pn_icon, "duo": pn_duo, "save": pn_save, "grid": pn_grid, "trap": pn_trap,
      "counter": pn_counter, "flow": pn_flow, "compare": pn_compare, "recap": pn_recap}
TR = 0.32   # whip duration

def load(spec, timing, voice_dur):
    global TIMING, DUR, SPEC, PANELS
    TIMING = [tuple(x) for x in timing]; DUR = voice_dur + 0.6; SPEC = spec
    PANELS = []
    for p in spec["panels"]:
        t0 = 0.0 if p["type"] == "hook" else AT(p["at"]); q = dict(p); q["_t0"] = t0; PANELS.append(q)
    PANELS.sort(key=lambda q: q["_t0"])

def scene_of(T): return max(i for i in range(len(TIMING)) if T >= TIMING[i][0])

def frame(T):
    j = max(i for i, p in enumerate(PANELS) if T >= p["_t0"] - 1e-6)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); P_ = PANELS[j]; u = T - P_["_t0"]
    if j > 0 and u < TR:
        e = eio(u / TR); sp = W / TR / FPS; Q = PANELS[j - 1]
        A = Image.new("RGBA", (W, H), (0, 0, 0, 0)); PN[Q["type"]](A, T - Q["_t0"], T, Q)
        B = Image.new("RGBA", (W, H), (0, 0, 0, 0)); PN[P_["type"]](B, u, T, P_)
        blur = sp * 1.5 * math.sin(math.pi * e) + 1
        _paste_clip(L, mblur(A, blur) if blur > 3 else A, int(-W * e), 0); _paste_clip(L, mblur(B, blur) if blur > 3 else B, int(W * (1 - e)), 0)
    else:
        PN[P_["type"]](L, u, T, P_)
    sc = scene_of(T); scn = SPEC["scenes"][sc]
    if scn["type"] == "step":
        st = TIMING[sc][0]; en = st + TIMING[sc][1]; a = min(ease((T - st - 0.2) / 0.3), ease((en - T - 0.1) / 0.2))
        if a > 0.01:
            s = f"{scn['num']} · {scn['kicker']}"; f = F("XB", 40); tw = f.getlength(s); d = ImageDraw.Draw(L)
            d.rounded_rectangle([W / 2 - tw / 2 - 34, 150, W / 2 + tw / 2 + 34, 236], 43, outline=WH + (int(255 * a),), width=4)
            d.text((W / 2, 193), s, font=f, fill=WH + (int(255 * a),), anchor="mm")
            nmax = max(x.get("num", 0) for x in SPEC["scenes"])
            for n in range(1, nmax + 1):
                x = W / 2 + (n - (nmax + 1) / 2) * 36; r = 9 if n == scn["num"] else 6
                d.ellipse([x - r, 270 - r, x + r, 270 + r], fill=(WH if n <= scn["num"] else (70, 70, 76)) + (int(255 * a),))
    bg = background().astype(np.float32)
    la = np.asarray(L).astype(np.float32); al = la[..., 3:4] / 255.0
    out = bg * (1 - al) + la[..., :3] * al
    out = out + cv2.resize(GRAIN[int(T * FPS) % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    out[0:6, :int(W * T / DUR)] = (245, 245, 245)
    if T > DUR - 0.5: out *= clamp((DUR - T) / 0.5)
    return np.clip(out, 0, 255).astype(np.uint8)

def voice_duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout)

if __name__ == "__main__":
    # python3 picto.py stills <nom> <timing.json | x> <voice.mp3 | durée_s> t1 t2 ...
    sys.path.insert(0, os.getcwd()); import picto_specs
    name, tj, vo = sys.argv[2:5]; spec = picto_specs.PICTO[name]
    dur = voice_duration(vo) if os.path.exists(vo) else float(vo)
    timing = json.load(open(tj)) if tj.endswith(".json") else picto_specs.est_timing(name)
    load(spec, timing, dur)
    ts = [float(x) for x in sys.argv[5:]]
    ims = [Image.fromarray(frame(t)).resize((270, 480)) for t in ts]
    per = 8; rows = (len(ims) + per - 1) // per
    c = Image.new("RGB", (270 * min(per, len(ims)), 480 * rows))
    for i, im in enumerate(ims): c.paste(im, ((i % per) * 270, (i // per) * 480))
    c.save("stills.png"); print("stills.png")
