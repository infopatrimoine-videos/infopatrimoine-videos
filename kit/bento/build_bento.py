"""python3 build_bento.py <name> <voice.mp3> <out.mp4>   (run from the folder holding bento.py, bento_specs.py, music.py, logo.b64;
motion kit (motion.py, motion_tmpl.py, build.py) must be in /home/claude/motion)"""
import sys, os, json, subprocess
sys.path.insert(0, "/home/claude/motion"); sys.path.insert(0, os.getcwd())
from multiprocessing import Pool
import bento, bento_specs, build
name, voice, out = sys.argv[1:4]
SPEC = bento_specs.BENTO[name]; bento.load(SPEC)
tj = f"timing_{name}.json"
if os.path.exists(tj): timing = [tuple(x) for x in json.load(open(tj))]
else:
    timing, _ = build.align(SPEC["scenes"], voice); json.dump(timing, open(tj, "w"))
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice], capture_output=True, text=True).stdout) + 0.6
timing[-1] = (timing[-1][0], DUR - timing[-1][0], timing[-1][2])
N = int(DUR * 30); K = max(2, os.cpu_count() or 2) * 2
def job(k):
    a, b = k * N // K, (k + 1) * N // K; tmp = f"part{k}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(a, b): p.stdin.write(bento.frame_at(i / 30, timing).convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0; os.rename(tmp, f"part{k}.mp4")
if __name__ == "__main__":
    print("timing", [(round(a, 2), round(b, 2)) for a, b, _ in timing])
    with Pool(os.cpu_count() or 2) as pl: pl.map(job, range(K))
    open("list.txt", "w").write("".join(f"file 'part{k}.mp4'\n" for k in range(K)))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "video.mp4"], check=True)
    import mixer; mixer.mix_audio(voice, DUR, "mix.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "video.mp4", "-i", "mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    for t in [2, DUR * 0.25, DUR * 0.5, DUR * 0.75, DUR - 1]:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", out, "-frames:v", "1", "-vf", "scale=360:640", f"check_{int(t)}.png"])
    print("OK", out, DUR)
