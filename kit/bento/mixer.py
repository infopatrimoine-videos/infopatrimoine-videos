"""Voice + music mix by loudness: python3 mixer.py <voice> <total_s> <out.wav>   (or import mix_audio)
The voice is levelled to a fixed loudness; the music sits MUSIC_DB below it while the voice speaks
and comes up a little in the pauses (smooth ducking)."""
import sys, subprocess, wave
import numpy as np
SR = 44100
MUSIC_DB = -22.0      # music level under speech, relative to the voice (RMS)
PAUSE_DB = -14.0      # music level in pauses / intro / outro

def _read(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768

def rms(x): return np.sqrt(np.mean(x ** 2) + 1e-12)

def mix_audio(voice_path, total, out, music_seed=None):
    n = int(total * SR)
    v = _read(voice_path); voice = np.zeros(n); voice[:min(n, len(v))] = v[:n]
    cmd = ["python3", "music.py", f"{total:.2f}"] + ([str(music_seed)] if music_seed is not None else [])
    subprocess.run(cmd, check=True)
    with wave.open("music.wav") as w:
        m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float).reshape(-1, 2)[:, 0] / 32768
    m = np.pad(m, (0, max(0, n - len(m))))[:n]
    # voice level: RMS over speaking parts -> 0.12 (~ -18 dBFS)
    frame = int(.05 * SR); nf = n // frame
    fr_rms = np.sqrt(np.mean(voice[:nf * frame].reshape(nf, frame) ** 2, axis=1))
    speaking = fr_rms > max(1e-4, np.percentile(fr_rms, 95) * 0.1)
    v_rms = np.sqrt(np.mean(fr_rms[speaking] ** 2)) if speaking.any() else rms(voice)
    voice *= 0.12 / max(v_rms, 1e-6)
    m *= 0.12 / max(rms(m), 1e-6)                      # music at the same RMS, then scaled by the gain curve
    # gain curve: under speech MUSIC_DB, in pauses PAUSE_DB; attack 60 ms, release 400 ms
    sp = np.repeat(speaking.astype(float), frame); sp = np.pad(sp, (0, n - len(sp)))
    g_lo, g_hi = 10 ** (MUSIC_DB / 20), 10 ** (PAUSE_DB / 20)
    target = g_hi + (g_lo - g_hi) * sp
    g = np.empty(n); cur = g_hi
    a_att, a_rel = 1 - np.exp(-1 / (0.06 * SR)), 1 - np.exp(-1 / (0.4 * SR))
    for i in range(0, n, 64):                          # block-wise smoothing (fast enough)
        tgt = target[i]; cur += (tgt - cur) * (1 - (1 - (a_att if tgt < cur else a_rel)) ** 64)
        g[i:i + 64] = cur
    mx = voice + m * g
    peak = np.abs(mx).max()
    if peak > 0.97: mx *= 0.97 / peak
    st = (np.stack([mx, mx], 1) * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())

if __name__ == "__main__":
    mix_audio(sys.argv[1], float(sys.argv[2]), sys.argv[3])
