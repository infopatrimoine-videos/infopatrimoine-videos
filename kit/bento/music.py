"""Background music, different every day: python3 music.py <dur> [seed]
Seed defaults to today's date, so each day gets its own key, tempo, chord progression,
arpeggio pattern, instrument colour and drum groove (lo-fi / chill / corporate-pop range,
stays soft under the voice). Writes music.wav (stereo 44.1 kHz)."""
import numpy as np, wave, sys, datetime, os
SR = 44100
dur = float(sys.argv[1])
seed = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.environ.get("MUSIC_SEED", datetime.date.today().toordinal()))
rng = np.random.default_rng(seed)
n = int(SR * dur); t = np.arange(n) / SR

PROGS = [  # scale degrees (0 = root) of triads, minor (m) or major (M) home key
    ("m", [0, 8, 3, 10]),    # i  VI  III VII   (Am F C G)
    ("m", [0, 5, 8, 7]),     # i  iv  VI  v
    ("M", [0, 7, 9, 5]),     # I  V   vi  IV
    ("M", [0, 9, 5, 7]),     # I  vi  IV  V
    ("m", [0, 3, 10, 5]),    # i  III VII iv
    ("M", [5, 0, 7, 9]),     # IV I   V   vi
    ("m", [0, 10, 8, 10]),   # i  VII VI  VII
    ("M", [0, 4, 9, 5]),     # I  iii vi  IV
]
mode, prog = PROGS[rng.integers(len(PROGS))]
root = 45 + int(rng.integers(0, 10))                      # A2..F#3
bpm = int(rng.choice([82, 86, 90, 94, 98, 104, 110]))
beat = 60 / bpm; bar = 4 * beat
SCALE = [0, 2, 3, 5, 7, 8, 10] if mode == "m" else [0, 2, 4, 5, 7, 9, 11]

def triad(deg):
    # build a diatonic-ish triad on a semitone offset from the root
    base = root + deg
    rel = deg % 12
    minor_degs = {0, 5, 7} if mode == "m" else {2, 4, 9}
    third = 3 if rel in minor_degs else 4
    if mode == "m" and rel in (3, 8, 10): third = 4
    if mode == "M" and rel in (0, 5, 7): third = 4
    return [base, base + third, base + 7]
chords = [triad(d) for d in prog]

def hz(m): return 440 * 2 ** ((m - 69) / 12)
out = np.zeros(n)

# --- instrument colours
pad_kind = rng.choice(["warm", "glass", "organ"])
pluck_kind = rng.choice(["sine", "bell", "soft_square", "marimba"])
patterns = [[0, 1, 2, 3, 2, 1, 0, 2], [0, 2, 1, 3, 0, 2, 1, 3], [0, 1, 2, 1, 3, 2, 1, 2],
            [3, 2, 1, 0, 1, 2, 3, 2], [0, 0, 2, 1, 3, 3, 2, 1], [0, 2, 3, 2, 1, 2, 3, 1]]
pat = patterns[rng.integers(len(patterns))]
arp_div = rng.choice([2, 2, 4])                            # 8ths or 16ths
groove = rng.choice(["four", "half", "boombap", "none_soft"])

def pad_tone(f, tt):
    if pad_kind == "warm":  return np.sin(2*np.pi*f*tt) + .3*np.sin(2*np.pi*2*f*tt + .5)
    if pad_kind == "glass": return np.sin(2*np.pi*f*tt) + .25*np.sin(2*np.pi*3*f*tt) + .12*np.sin(2*np.pi*4.01*f*tt)
    return np.sin(2*np.pi*f*tt) + .5*np.sin(2*np.pi*2*f*tt) + .25*np.sin(2*np.pi*4*f*tt)

def pluck(f, tt):
    if pluck_kind == "sine":  return np.exp(-tt*6) * np.sin(2*np.pi*f*tt)
    if pluck_kind == "bell":  return np.exp(-tt*4) * (np.sin(2*np.pi*f*tt) + .4*np.sin(2*np.pi*2.76*f*tt)*np.exp(-tt*8))
    if pluck_kind == "marimba": return np.exp(-tt*9) * (np.sin(2*np.pi*f*tt) + .3*np.sin(2*np.pi*4*f*tt)*np.exp(-tt*20))
    return np.exp(-tt*7) * np.tanh(3*np.sin(2*np.pi*f*tt)) * .6

# --- pad + bass
for i in range(int(dur / bar) + 1):
    ch = chords[i % 4]; s = int(i * bar * SR)
    if s >= n: break
    e = min(n, int((i + 1) * bar * SR) + int(.3 * SR)); tt = np.arange(e - s) / SR
    env = (np.minimum(1, tt / .4) * np.minimum(1, (e - s) / SR - tt)).clip(0, 1)
    for m in ch: out[s:e] += 0.045 * env * pad_tone(hz(m + 12), tt)
    out[s:e] += 0.08 * env * np.sin(2*np.pi*hz(ch[0] - 12)*tt)

# --- arpeggio
step = beat / arp_div
for k in range(int(dur / step)):
    ch = chords[int(k * step / bar) % 4]
    m = (ch + [ch[0] + 12])[pat[k % 8]] + 24
    s = int(k * step * SR); e = min(n, s + int(.6 * SR)); tt = np.arange(e - s) / SR
    out[s:e] += (0.04 if arp_div == 2 else 0.028) * pluck(hz(m), tt)

# --- drums
def kick(s, amp=0.18):
    e = min(n, s + int(.25 * SR)); tt = np.arange(e - s) / SR
    out[s:e] += amp * np.exp(-tt*18) * np.sin(2*np.pi*(50 + 80*np.exp(-tt*30))*tt)
def hat(s, amp=0.015):
    e = min(n, s + int(.05 * SR))
    if s < n: out[s:e] += amp * rng.standard_normal(e - s) * np.exp(-np.arange(e - s)/SR*80)
def snare(s, amp=0.05):
    e = min(n, s + int(.18 * SR)); tt = np.arange(e - s) / SR
    if s < n: out[s:e] += amp * (rng.standard_normal(e - s)*.7 + np.sin(2*np.pi*190*tt)) * np.exp(-tt*22)
for k in range(int(dur / beat)):
    s = int(k * beat * SR); off = int((k * beat + beat / 2) * SR)
    if groove == "four":
        kick(s, .15); hat(off)
    elif groove == "half":
        if k % 2 == 0: kick(s)
        hat(off)
    elif groove == "boombap":
        if k % 4 in (0, 2) or (k % 4 == 3 and rng.random() < .3): kick(s, .16)
        if k % 4 in (1, 3): snare(s)
        hat(off, .012)
    else:
        if k % 4 == 0: kick(s, .1)
        hat(off, .008)

fade = np.minimum(1, np.minimum(t / 1.0, (dur - t) / 2.0))
out *= fade
out /= np.abs(out).max() * 1.25
st = np.stack([out, out], 1)
with wave.open("music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print(f"music seed={seed} key={root} {mode} bpm={bpm} pad={pad_kind} pluck={pluck_kind} groove={groove} arp=1/{arp_div*4}")
