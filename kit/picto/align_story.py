"""Sentence-level alignment for narrative videos (no "Un / Deux / Trois" markers).
The voice is cut at its pauses and transcribed (Whisper); each sentence of the spec is then placed at the
transcribed words that best match its first words, in order. Returns timing [(scene_start, duration, [sentence starts rel.])]."""
import re, unicodedata, sys
sys.path.insert(0, "/home/claude/motion")
import build

NUM = {"un": "1", "une": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7", "huit": "8",
       "neuf": "9", "dix": "10", "douze": "12", "vingt": "20", "trente": "30", "cent": "100", "mille": "1000"}
def words(s):
    s = unicodedata.normalize("NFKD", s.lower()); s = "".join(c for c in s if not unicodedata.combining(c))
    return [NUM.get(w, w) for w in re.findall(r"[a-z0-9]+", s)]

def align(scenes, voice, verbose=True):
    ch, dur = build.asr_chunks(voice)
    # flatten transcription into timed words (time spread evenly inside each chunk)
    tw = []
    for a, b, t in ch:
        ws = words(t)
        for i, w in enumerate(ws): tw.append((a + (b - a) * i / max(1, len(ws)), w))
    if verbose:
        for a, b, t in ch: print(f"  {a:6.2f} {b:6.2f} | {t}")
    sents = [(si, j, s) for si, S in enumerate(scenes) for j, s in enumerate(S["say"])]
    total_chars = sum(len(s) for _, _, s in sents)
    starts = []; pos = 0; acc = 0
    for k, (si, j, s) in enumerate(sents):
        expect = dur * acc / total_chars; acc += len(s)
        if k == 0: starts.append(0.0); continue
        target = words(s)[:5]
        best, bi = -1e9, None
        for i in range(pos, len(tw)):
            if tw[i][0] > expect + 8: break
            win = [w for _, w in tw[i:i + 7]]
            sc = sum(1.0 for x in target if x in win) + (1.5 if win and target and win[0] == target[0] else 0)
            sc -= abs(tw[i][0] - expect) * 0.08
            if sc > best: best, bi = sc, i
        if bi is None or best < 1.0:                       # no match: proportional estimate
            t0 = max(expect, starts[-1] + 0.6)
        else:
            t0 = tw[bi][0]; pos = bi + 1
        starts.append(max(t0, starts[-1] + 0.4))
        if verbose: print(f"  scène {si} phrase {j}: {starts[-1]:6.2f}  score {best:.1f}  « {s[:40]} »")
    timing = []; k = 0
    for si, S in enumerate(scenes):
        n = len(S["say"]); st = starts[k]
        nxt = starts[k + n] if k + n < len(starts) else dur
        timing.append((st, nxt - st, [x - st for x in starts[k:k + n]])); k += n
    return timing
