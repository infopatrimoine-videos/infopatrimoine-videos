"""Upbeat background music, different every day: python3 music.py <dur> [seed]
Seed defaults to today's date: each day gets its own major key, tempo (108-124 bpm), happy chord progression,
groove (pop / house / funk / tropical), lead sound and a short melodic hook. Writes music.wav (stereo 44.1 kHz)."""
import numpy as np, wave, sys, datetime, os
SR = 44100
dur = float(sys.argv[1])
seed = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.environ.get("MUSIC_SEED", datetime.date.today().toordinal()))
rng = np.random.default_rng(seed)
n = int(SR * dur); t = np.arange(n) / SR

# happy progressions in a major key: (semitone offset of chord root, quality)
PROGS = [
    [(0, "M"), (7, "M"), (9, "m"), (5, "M")],     # I V vi IV
    [(0, "M"), (5, "M"), (7, "M"), (5, "M")],     # I IV V IV
    [(9, "m"), (5, "M"), (0, "M"), (7, "M")],     # vi IV I V
    [(0, "M"), (9, "m"), (5, "M"), (7, "M")],     # I vi IV V
    [(5, "M"), (7, "M"), (0, "M"), (0, "M")],     # IV V I I
    [(0, "M"), (4, "m"), (5, "M"), (7, "M")],     # I iii IV V
    [(0, "M"), (7, "M"), (5, "M"), (7, "M")],     # I V IV V
]
prog = PROGS[rng.integers(len(PROGS))]
root = 48 + int(rng.integers(0, 8))                         # C3..G3
bpm = int(rng.choice([108, 112, 115, 118, 120, 122, 124]))
beat = 60 / bpm; bar = 4 * beat
groove = str(rng.choice(["pop", "house", "funk", "tropical"]))
lead = str(rng.choice(["pluck", "marimba", "bell", "saw"]))
MAJ = [0, 2, 4, 5, 7, 9, 11]

def chord(i):
    off, q = prog[i % 4]; b = root + off
    return [b, b + (4 if q == "M" else 3), b + 7]
def hz(m): return 440 * 2 ** ((m - 69) / 12)
out = np.zeros(n)

def add(s, sig, amp):
    if s >= n: return
    e = min(n, s + len(sig)); out[s:e] += amp * sig[:e - s]

def tone(f, d, kind):
    tt = np.arange(int(d * SR)) / SR
    if kind == "pluck":   return np.exp(-tt * 7) * (np.sin(2*np.pi*f*tt) + .35*np.sin(2*np.pi*2*f*tt) + .15*np.sin(2*np.pi*3*f*tt))
    if kind == "marimba": return np.exp(-tt * 10) * (np.sin(2*np.pi*f*tt) + .4*np.sin(2*np.pi*4*f*tt) * np.exp(-tt*25))
    if kind == "bell":    return np.exp(-tt * 4.5) * (np.sin(2*np.pi*f*tt) + .5*np.sin(2*np.pi*2.76*f*tt) * np.exp(-tt*9))
    saw = sum(np.sin(2*np.pi*k*f*tt) / k for k in range(1, 7))
    return np.exp(-tt * 5) * saw * .5

# --- chords: short bright stabs on the off-beats (pop/house) or sustained pad (funk/tropical)
for b_ in range(int(dur / bar) + 1):
    ch = chord(b_); s0 = b_ * bar
    if groove in ("pop", "house"):
        for k in range(4):
            for m in ch: add(int((s0 + k * beat + beat / 2) * SR), tone(hz(m + 12), .22, "pluck"), .032)
    else:
        tt = np.arange(int(bar * SR)) / SR; env = np.minimum(1, tt / .08) * np.exp(-tt * .6)
        for m in ch: add(int(s0 * SR), env * (np.sin(2*np.pi*hz(m + 12)*tt) + .2*np.sin(2*np.pi*hz(m + 24)*tt)), .03)
    # bass: bouncy octaves on 8ths
    for k in range(8):
        f = hz(ch[0] - 12 + (12 if k % 2 else 0))
        tt = np.arange(int(beat / 2 * SR * .9)) / SR
        add(int((s0 + k * beat / 2) * SR), np.exp(-tt * 6) * np.tanh(2 * np.sin(2*np.pi*f*tt)), .06)

# --- melodic hook (2 bars, repeated, small variation every other time)
hook_deg = [int(x) for x in rng.choice([0, 2, 4, 4, 7, 9, 7, 4], size=8)]
rhythm = rng.choice([[0, 1, 1.5, 2, 3, 3.5], [0, .5, 1, 2, 2.5, 3], [0, .75, 1.5, 2, 3, 3.5], [.5, 1, 1.5, 2.5, 3, 3.5]])
for b_ in range(int(dur / bar) + 1):
    if b_ < 2: continue                                    # let the intro breathe
    ch = chord(b_)
    for j, pos in enumerate(rhythm):
        deg = hook_deg[(j + (b_ % 2) * 3) % 8]
        m = root + 24 + deg
        m = min(ch + [c + 12 for c in ch], key=lambda c: abs((c + 12) - m)) + 12 if rng.random() < .35 else m
        add(int((b_ * bar + pos * beat) * SR), tone(hz(m), .4, lead), .035)

# --- drums
def kick(s, amp=.2):
    tt = np.arange(int(.22 * SR)) / SR
    add(s, np.exp(-tt * 16) * np.sin(2*np.pi*(48 + 90*np.exp(-tt*35))*tt), amp)
def clap(s, amp=.07):
    L = int(.16 * SR); x = rng.standard_normal(L); tt = np.arange(L) / SR
    env = np.exp(-tt * 25) + .6*np.exp(-np.maximum(0, tt - .012) * 30) * (tt > .012)
    add(s, x * env, amp)
def hat(s, amp=.02, open_=False):
    L = int((.12 if open_ else .04) * SR); x = rng.standard_normal(L); x = np.diff(x, prepend=0)
    add(s, x * np.exp(-np.arange(L) / SR * (25 if open_ else 90)), amp)
def shaker(s, amp=.012):
    L = int(.06 * SR); tt = np.arange(L) / SR; add(s, rng.standard_normal(L) * np.sin(np.pi * tt / .06), amp)

nb = int(dur / beat)
for k in range(nb):
    s = int(k * beat * SR); h = int((k * beat + beat / 2) * SR); q1 = int((k * beat + beat / 4) * SR); q3 = int((k * beat + 3 * beat / 4) * SR)
    if groove == "house":
        kick(s); hat(h, .03, open_=True)
        if k % 2: clap(s)
    elif groove == "pop":
        if k % 2 == 0: kick(s)
        if k % 4 == 2 and rng.random() < .5: kick(h, .14)
        if k % 2: clap(s)
        hat(s, .015); hat(h, .02)
    elif groove == "funk":
        if k % 4 == 0: kick(s)
        if k % 4 == 1: kick(q3, .15)
        if k % 4 == 2: kick(h, .16)
        if k % 2: clap(s, .06)
        for p in (s, q1, h, q3): hat(p, .012)
    else:  # tropical
        kick(s, .17)
        if k % 2: clap(s, .05)
        for p in (s, q1, h, q3): shaker(p)

fade = np.minimum(1, np.minimum(t / .6, (dur - t) / 1.5))
out = np.tanh(out * 1.4) * fade
out /= np.abs(out).max() * 1.1
st = np.stack([out, out], 1)
with wave.open("music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print(f"music seed={seed} key={root} major bpm={bpm} groove={groove} lead={lead}")
