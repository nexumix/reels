#!/usr/bin/env python3
"""Online İSG eğitimi ders videosu (16:9, 1920x1080): slayt + Google TTS seslendirme.
Kullanım: python3 tools/lesson_render.py lessons/az8_g1.json   (GOOGLE_TTS_KEY gerekli; yoksa sessiz önizleme)
Job:
{ "code": "az8_g1", "course": "Temel İSG Eğitimi – Az Tehlikeli", "section": "1. Bölüm · Genel konular",
  "title": "Çalışma mevzuatı ile ilgili bilgiler", "voice": {"lang": "tr-TR", "voice": "tr-TR-Chirp3-HD-Achird", "gender": "MALE"},
  "min_sec": 1350,
  "slides": [ {"title": "...", "bullets": ["...", "..."], "say": "seslendirme metni", "note": "kaynak (ops.)"} ] }
Çıktı: out/lessons/<code>.mp4 ve out/lessons/<code>.json (süre, slayt süreleri)."""
import json, os, re, subprocess, sys, tempfile, textwrap, base64
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tts_google as T  # say(), pick_voice(), _req(), _dur()

W, H = 1920, 1080
NAVY, ORANGE, INK, MUTED, BG = (11, 61, 126), (242, 140, 15), (24, 32, 48), (100, 112, 130), (247, 249, 252)
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(ROOT, ".fonts"))
DV = "/usr/share/fonts/truetype/dejavu/"

def font(kind, size):
    try:
        if kind == "head":
            f = ImageFont.truetype(os.path.join(FONT_DIR, "SchibstedGrotesk.ttf"), size)
            try: f.set_variation_by_axes([760])
            except Exception: pass
            return f
        return ImageFont.truetype(os.path.join(FONT_DIR, {"body": "Lato-Regular.ttf", "bold": "Lato-Bold.ttf"}[kind]), size)
    except Exception:
        return ImageFont.truetype(DV + ("DejaVuSans-Bold.ttf" if kind != "body" else "DejaVuSans.ttf"), size)

def wrap(d, text, f, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: line = t
        else:
            if line: out.append(line)
            line = w
    if line: out.append(line)
    return out

def logo(path, maxw, maxh):
    im = Image.open(path).convert("RGBA"); im.thumbnail((maxw, maxh), Image.LANCZOS); return im

def slide_png(job, sl, i, n, path):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 120], fill=NAVY); d.rectangle([0, 120, W, 128], fill=ORANGE)
    lg = os.path.join(ROOT, "tools", "logos", "osgb.png")
    if os.path.exists(lg):
        L = logo(lg, 220, 92); pad = Image.new("RGBA", (L.width + 24, L.height + 16), (255, 255, 255, 255)); pad.alpha_composite(L, (12, 8)); im.paste(pad, (60, 14), pad)
    d.text((340, 30), job.get("course", ""), font=font("bold", 30), fill=(255, 255, 255))
    d.text((340, 72), job.get("section", "") + "  ·  " + job.get("title", ""), font=font("body", 26), fill=(210, 222, 240))
    y = 190
    for ln in wrap(d, sl.get("title", ""), font("head", 64), W - 240)[:2]:
        d.text((120, y), ln, font=font("head", 64), fill=NAVY); y += 80
    d.rectangle([120, y + 6, 220, y + 12], fill=ORANGE); y += 50
    fb = font("body", 42)
    for b in sl.get("bullets", [])[:6]:
        lines = wrap(d, b, fb, W - 340)[:3]
        d.ellipse([128, y + 16, 146, y + 34], fill=ORANGE)
        for ln in lines: d.text((180, y), ln, font=fb, fill=INK); y += 56
        y += 18
        if y > H - 170: break
    if sl.get("note"): d.text((120, H - 120), sl["note"], font=font("body", 24), fill=MUTED)
    d.rectangle([0, H - 64, W, H], fill=(234, 239, 246))
    d.text((60, H - 48), "Tepe OSGB · İş Güvenliğinin Tepe Noktası", font=font("body", 24), fill=MUTED)
    t = f"{i + 1} / {n}"; d.text((W - 60 - d.textlength(t, font=font("bold", 26)), H - 50), t, font=font("bold", 26), fill=NAVY)
    im.save(path)

def chunks(text, limit=4200):
    """Google TTS istek sınırı (5000 bayt) için cümle bazlı bölme."""
    parts, cur = [], ""
    for s in re.split(r"(?<=[.!?…])\s+", text.strip()):
        if len((cur + " " + s).encode()) > limit and cur: parts.append(cur); cur = s
        else: cur = (cur + " " + s).strip()
    if cur: parts.append(cur)
    return parts

def tts(job, text, tmp, idx):
    key = os.environ.get("GOOGLE_TTS_KEY"); v = job.get("voice", {}); lang = v.get("lang", "tr-TR")
    out = os.path.join(tmp, f"s{idx}.wav")
    if not key:  # önizleme: konuşma süresini kelime sayısından tahmin et (dakikada ~140 kelime), sessiz ses
        dur = max(3.0, len(text.split()) / 140 * 60)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{dur:.2f}", out], check=True); return out
    voice = T.pick_voice(key, lang, v.get("gender"), v.get("voice"))
    segs = []
    for k, part in enumerate(chunks(T.say(text, lang, job.get("say")))):
        body = {"input": {"text": part}, "voice": {"languageCode": lang, "name": voice}, "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 44100}}
        a = T._req(f"{T.API}/text:synthesize?key={key}", body)
        p = os.path.join(tmp, f"s{idx}_{k}.wav"); open(p, "wb").write(base64.b64decode(a["audioContent"])); segs.append(p)
    lst = os.path.join(tmp, f"s{idx}.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in segs))
    raw = os.path.join(tmp, f"s{idx}_raw.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "1", out], check=True)
    return out

def main(path):
    job = json.load(open(path, encoding="utf-8")); code = job["code"]
    os.makedirs(os.path.join(ROOT, "out", "lessons"), exist_ok=True)
    tmp = tempfile.mkdtemp(); n = len(job["slides"]); segs, durs = [], []
    for i, sl in enumerate(job["slides"]):
        png = os.path.join(tmp, f"p{i}.png"); slide_png(job, sl, i, n, png)
        wav = tts(job, sl["say"], tmp, i); d = T._dur(wav) + 1.2; durs.append(round(d, 2))
        mp4 = os.path.join(tmp, f"v{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "5", "-i", png, "-i", wav, "-af", "adelay=500|500,apad", "-t", f"{d:.2f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "5", "-c:a", "aac", "-b:a", "96k", "-ar", "44100", "-ac", "1", mp4], check=True)
        segs.append(mp4); print(f"slayt {i + 1}/{n}: {d:.1f} sn", flush=True)
    lst = os.path.join(tmp, "all.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in segs))
    out = os.path.join(ROOT, "out", "lessons", f"{code}.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
    total = round(sum(durs), 1)
    json.dump({"code": code, "duration_sec": total, "slides": durs, "min_sec": job.get("min_sec")}, open(out[:-4] + ".json", "w"), ensure_ascii=False)
    print(f"OK {out} {total} sn ({total / 60:.1f} dk)" + (f" — UYARI: hedef {job['min_sec']} sn altında" if job.get("min_sec") and total < job["min_sec"] else ""))

if __name__ == "__main__":
    for p in sys.argv[1:]: main(p)
