"""Seslendirmeli reels: python3 narrate.py config.json frames_dir music_style seed clip1.wav clip2.wav ...
Her slayt için 1 ses dosyası (slayt sırasıyla). Slayt süresi = max(okuma süresi, ses + 1.0 sn).
Müzik sesin altında kısılır (ducking). Çıktı: config["out"] (sesli, müzikli)."""
import sys, json, subprocess, os, wave, contextlib
cfg_path, frames, style, seed = sys.argv[1:5]; clips = sys.argv[5:]
here = os.path.dirname(os.path.abspath(__file__))
def wav_len(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout
    return float(out.strip())
cfg = json.load(open(cfg_path)); assert len(clips) == len(cfg["slides"]), "slayt sayısı = ses sayısı olmalı"
fade = 0.45
for s, c in zip(cfg["slides"], clips):
    words = len((s["title"] + " " + s.get("sub", "")).split())
    s["dur"] = round(max(3.5, 2.2 + 0.36 * words, wav_len(c) + 1.0), 2)
final = cfg["out"]; silent = final.replace(".mp4", "_v.mp4"); cfg["out"] = silent
tmp = cfg_path.replace(".json", "_n.json"); json.dump(cfg, open(tmp, "w"), ensure_ascii=False)
subprocess.run(["python3", os.path.join(here, "make_reel.py"), tmp, frames], check=True)
total = sum(s["dur"] for s in cfg["slides"]) - fade * (len(clips) - 1)
music = final.replace(".mp4", "_m.wav")
subprocess.run(["python3", os.path.join(here, "make_music2.py"), music, str(total + 2), style, seed], check=True, capture_output=True)
starts, t = [], 0.0
for s in cfg["slides"]: starts.append(t + 0.35); t += s["dur"] - fade
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", music]
for c in clips: cmd += ["-i", c]
fc = []
for i, st in enumerate(starts):
    fc.append(f"[{i+2}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={int(st*1000)}|{int(st*1000)},volume=1.6[v{i}]")
fc.append("".join(f"[v{i}]" for i in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0[voice]")
fc.append("[voice]asplit=2[vk][vm]")
fc.append(f"[1:a]volume=0.55,afade=t=out:st={total-1.4:.2f}:d=1.4[mus]")
fc.append("[mus][vk]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]")
fc.append("[duck][vm]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]")
cmd += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", "-movflags", "+faststart", final]
subprocess.run(cmd, check=True)
os.remove(silent)
print(final, round(total, 1), "sn")
