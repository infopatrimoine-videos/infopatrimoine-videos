"""python3 build_picto.py <nom> <voice.mp3> <out.mp4>
À lancer depuis le dossier qui contient picto.py, picto_specs.py, music.py, mixer.py, logo.b64.
Le kit moteur (motion.py, motion_tmpl.py, build.py) doit être dans /home/claude/motion.
Si timing_<nom>.json existe, il est réutilisé ; sinon il est calculé par transcription (build.align)."""
import sys, os, json, subprocess
sys.path.insert(0, "/home/claude/motion"); sys.path.insert(0, os.getcwd())
from multiprocessing import Pool
import picto, picto_specs, build
name, voice, out = sys.argv[1:4]
SPEC = picto_specs.PICTO[name]
tj = f"timing_{name}.json"
if os.path.exists(tj): timing = [tuple(x) for x in json.load(open(tj))]
elif any(s.get("num") for s in SPEC["scenes"] if s["type"] == "step"):
    timing, _ = build.align(SPEC["scenes"], voice); json.dump(timing, open(tj, "w"))
else:                                    # narrative video: align every sentence by transcription
    import align_story; timing = align_story.align(SPEC["scenes"], voice); json.dump(timing, open(tj, "w"))
VD = picto.voice_duration(voice); DUR = VD + 0.6
timing[-1] = (timing[-1][0], DUR - timing[-1][0], timing[-1][2])
picto.load(SPEC, timing, VD)
N = int(DUR * 30); K = 4
def job(k):
    a, b = k * N // K, (k + 1) * N // K; tmp = f"part{k}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                          "-c:v", "libx264", "-b:v", "9M", "-maxrate", "12M", "-bufsize", "18M", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp],
                         stdin=subprocess.PIPE)
    for i in range(a, b): p.stdin.write(picto.frame(i / 30).tobytes())
    p.stdin.close(); assert p.wait() == 0; os.rename(tmp, f"part{k}.mp4")
if __name__ == "__main__":
    print("timing", [(round(a, 2), round(b, 2)) for a, b, _ in timing])
    with Pool(os.cpu_count() or 2) as pl: pl.map(job, range(K))
    open("list.txt", "w").write("".join(f"file 'part{k}.mp4'\n" for k in range(K)))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "video.mp4"], check=True)
    import mixer; mixer.mix_audio(voice, DUR, "mix.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "video.mp4", "-i", "mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    for t in [2, DUR * 0.25, DUR * 0.5, DUR * 0.75, DUR - 3]:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", out, "-frames:v", "1", "-vf", "scale=360:640", f"check_{int(t)}.png"])
    print("OK", out, DUR)
