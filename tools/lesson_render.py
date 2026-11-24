#!/usr/bin/env python3
"""Online İSG eğitimi ders videosu v2 (16:9, 1920x1080, premium şablon).
Sahne türleri: cover (tam ekran fotoğraf + başlık), split (fotoğraf + adım adım açılan maddeler), stats (büyük sayı kartları),
cards (fotoğraflı kartlar, sırayla), roles (yuvarlak fotoğraflı roller), check (özet onay listesi), quote (vurgu cümlesi).
Her sahne 'steps' listesine bölünür: her adımın kendi seslendirmesi vardır, görsel öğe konuşmayla birlikte belirir.
Fotoğraflar yavaş yakınlaşır (Ken Burns); sahne geçişlerinde yumuşak kararma. Marka: alt şerit + logo, giriş/kapanış jeneriği.
Ses: Google Chirp 3 HD (markup + [pause] ile doğal duraklama), kısaltmalar kelime gibi okunur (job 'say' ile genişletilebilir).
Kullanım: python3 tools/lesson_render.py lessons/x.json  → out/lessons/<code>.mp4 (+ .json süre bilgisi)"""
import base64, json, os, re, subprocess, sys, tempfile, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tts_google as T

W, H, FPS = 1920, 1080, 24
NAVY, NAVY2, ORANGE, IVORY, INK, MUTED, WHITE = (8, 41, 90), (14, 58, 118), (242, 140, 15), (250, 249, 246), (22, 30, 46), (98, 108, 126), (255, 255, 255)
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(ROOT, ".fonts"))
DV = "/usr/share/fonts/truetype/dejavu/"
# Kısaltmalar kelime gibi, tek parça (kullanıcı 24.11: "NACE, DASK, TBMM, İSG kelime gibi okunsun")
SAY = {"İSG": "İsge", "ISG": "İsge", "OSGB": "Osgebe", "NACE": "Nase", "DASK": "Dask", "TBMM": "Tebeme", "KKD": "Kakade", "SGK": "Esgeka", "ÇSGB": "Çesgebe",
       "KOSGEB": "Kosgeb", "İSG-KÂTİP": "İsge Kâtip", "TS": "Tese", "CE": "Se", "AB": "Abe", "GBF": "Gebef"}

def font(kind, size):
    try:
        if kind in ("head", "display"):
            f = ImageFont.truetype(os.path.join(FONT_DIR, "SchibstedGrotesk.ttf"), size)
            try: f.set_variation_by_axes([800 if kind == "display" else 700])
            except Exception: pass
            return f
        return ImageFont.truetype(os.path.join(FONT_DIR, {"body": "Lato-Regular.ttf", "bold": "Lato-Bold.ttf", "light": "Lato-Light.ttf"}.get(kind, "Lato-Regular.ttf")), size)
    except Exception:
        return ImageFont.truetype(DV + ("DejaVuSans.ttf" if kind in ("body", "light") else "DejaVuSans-Bold.ttf"), size)

def wrap(d, text, f, maxw):
    out, line = [], ""
    for w in str(text).split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: line = t
        else:
            if line: out.append(line)
            line = w
    if line: out.append(line)
    return out

def fetch(url, tmp, name):
    p = os.path.join(tmp, name)
    if not os.path.exists(p):
        u = re.sub(r"([?&])w=\d+", r"\1w=2400", url) if "unsplash.com" in url else url
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            open(p, "wb").write(urllib.request.urlopen(req, timeout=60).read())
        except Exception as e:
            if not os.environ.get("LESSON_PREVIEW"): raise
            ph = Image.new("RGB", (1600, 1000), (120, 132, 150)); dd = ImageDraw.Draw(ph)
            for i in range(0, 1600, 80): dd.line([(i, 0), (i - 400, 1000)], fill=(135, 147, 165), width=30)
            ph.save(p, "JPEG")
    return p

def cover_crop(im, w, h):
    r = max(w / im.width, h / im.height); im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

_LOGO = {}
def logo_img(width, mono_white=False):
    k = (width, mono_white)
    if k in _LOGO: return _LOGO[k]
    src = Image.open(os.path.join(ROOT, "tools", "logos", "osgb.png")).convert("RGBA")
    px = src.load(); out = Image.new("RGBA", src.size); po = out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            d = 255 - min(r, g, b)  # beyaz zemini şeffaflaştır
            al = max(0, min(255, int((d - 12) * 3.2))) * a // 255
            if al <= 0: po[x, y] = (0, 0, 0, 0); continue
            po[x, y] = (255, 255, 255, al) if mono_white else (r, g, b, al)
    bb = out.getbbox(); out = out.crop(bb) if bb else out
    out = out.resize((width, int(out.height * width / out.width)), Image.LANCZOS); _LOGO[k] = out; return out

def rounded(im, rad):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], rad, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o

def shadow(canvas, box, rad=24, blur=28, alpha=60):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([box[0], box[1] + 10, box[2], box[3] + 10], rad, fill=(8, 20, 40, alpha))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))

def brand_bar(im, job, dark=False):
    """Alt marka şeridi: ince turuncu çizgi + logo + akademi adı + ders adı (her slaytta aynı yerde, şablonun parçası)."""
    d = ImageDraw.Draw(im); y0 = H - 78
    if not dark: d.rectangle([0, y0, W, H], fill=(243, 241, 236))
    d.rectangle([0, y0, 120, y0 + 4], fill=ORANGE)
    lg = logo_img(70, mono_white=dark); im.alpha_composite(lg, (64, y0 + (78 - lg.height) // 2))
    d.text((150, y0 + 18), "TEPE OSGB AKADEMİ", font=font("head", 22), fill=WHITE if dark else NAVY)
    d.text((150, y0 + 44), job.get("course", ""), font=font("body", 18), fill=(220, 228, 240) if dark else MUTED)
    t = job.get("section", ""); f = font("bold", 20); d.text((W - 64 - d.textlength(t, font=f), y0 + 30), t, font=f, fill=WHITE if dark else NAVY)

# ---------------- Sahne çizimleri: her biri adım sayısı kadar katman (RGBA, tam kare) döndürür ----------------
def kicker(d, x, y, text, dark=False):
    f = font("bold", 24); d.rectangle([x, y + 12, x + 46, y + 16], fill=ORANGE)
    d.text((x + 62, y), text.upper(), font=f, fill=ORANGE if not dark else (255, 196, 120))

def draw_title(d, x, y, text, maxw, size=72, color=NAVY, lines=2):
    f = font("display", size)
    for ln in wrap(d, text, f, maxw)[:lines]: d.text((x, y), ln, font=f, fill=color); y += int(size * 1.12)
    return y

def scene_cover(sc, job, tmp):
    frames = []
    for k in range(len(sc["steps"])):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = Image.new("L", (W, 1))
        for x in range(W): g.putpixel((x, 0), int(235 * max(0.0, 1 - x / (W * 0.72)) ** 1.1))
        grad = Image.new("RGBA", (W, H), NAVY + (0,)); grad.putalpha(g.resize((W, H))); im.alpha_composite(grad)
        d = ImageDraw.Draw(im)
        kicker(d, 120, 250, sc.get("kicker", job.get("section", "")), dark=True)
        y = draw_title(d, 120, 300, sc["title"], 1050, 92, WHITE, 3)
        if sc.get("subtitle"): d.text((122, y + 20), sc["subtitle"], font=font("body", 36), fill=(214, 224, 240))
        brand_bar(im, job, dark=True); frames.append(im)
    return frames

def scene_split(sc, job, tmp):
    frames = []; photo_w = 860 if sc.get("photo") else 0
    for k in range(len(sc["steps"])):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W - photo_w, H], fill=IVORY + (255,))
        if photo_w: d.rectangle([W - photo_w - 8, 0, W - photo_w, H], fill=ORANGE)
        kicker(d, 110, 120, sc.get("kicker", job.get("title", "")))
        y = draw_title(d, 110, 168, sc["title"], W - photo_w - 220, 66)
        y += 34; fb = font("body", 38)
        for i, b in enumerate(sc.get("bullets", [])[:5]):
            if i > k - (1 if sc.get("intro_step", True) else 0): break
            lines = wrap(d, b, fb, W - photo_w - 330)[:3]; bh = len(lines) * 50 + 34
            on = i == k - (1 if sc.get("intro_step", True) else 0)
            d.rounded_rectangle([110, y, W - photo_w - 110, y + bh], 18, fill=(255, 255, 255) if on else (244, 243, 239), outline=(230, 228, 222))
            d.ellipse([136, y + 22, 178, y + 64], fill=ORANGE if on else NAVY2); d.text((157, y + 43), str(i + 1), font=font("head", 24), fill=WHITE, anchor="mm")
            for j, ln in enumerate(lines): d.text((204, y + 17 + j * 50), ln, font=fb, fill=INK if on else (70, 80, 98))
            y += bh + 16
        brand_bar(im, job); frames.append(im)
    return frames

def scene_stats(sc, job, tmp):
    frames = []; items = sc["items"][:4]; n = len(items); gap = 40; cw = (W - 220 - gap * (n - 1)) // n
    for k in range(len(sc["steps"])):
        im = Image.new("RGBA", (W, H), IVORY + (255,)); d = ImageDraw.Draw(im)
        kicker(d, 110, 120, sc.get("kicker", job.get("title", ""))); draw_title(d, 110, 168, sc["title"], W - 220, 64, NAVY, 1)
        for i, it in enumerate(items):
            if i > k - 1 and k > 0: break
            x = 110 + i * (cw + gap); box = (x, 360, x + cw, 820)
            shadow(im, box); d = ImageDraw.Draw(im)
            d.rounded_rectangle(box, 28, fill=WHITE); d.rounded_rectangle([x, 360, x + cw, 372], 6, fill=ORANGE if i == k - 1 else NAVY2)
            fv = font("display", 150 if len(it["value"]) <= 3 else 110); d.text((x + cw // 2, 540), it["value"], font=fv, fill=NAVY, anchor="mm")
            d.text((x + cw // 2, 650), it.get("unit", ""), font=font("head", 40), fill=ORANGE, anchor="mm")
            for j, ln in enumerate(wrap(d, it.get("label", ""), font("body", 30), cw - 60)[:2]): d.text((x + cw // 2, 712 + j * 40), ln, font=font("body", 30), fill=MUTED, anchor="mm")
        if k == 0:  # giriş adımı: tüm öğeler soluk görünür, konuşmayla sırayla vurgulanır
            veil = Image.new("RGBA", (W, 1000 - 280), IVORY + (150,)); im.alpha_composite(veil, (0, 280))
        brand_bar(im, job); frames.append(im)
    return frames

def scene_cards(sc, job, tmp):
    frames = []; items = sc["items"][:3]; n = len(items); gap = 44; cw = (W - 220 - gap * (n - 1)) // n
    photos = [cover_crop(Image.open(fetch(it["photo"], tmp, f"c_{abs(hash(it['photo']))}.jpg")).convert("RGB"), cw, 400) for it in items]
    for k in range(len(sc["steps"])):
        im = Image.new("RGBA", (W, H), IVORY + (255,)); d = ImageDraw.Draw(im)
        kicker(d, 110, 110, sc.get("kicker", job.get("title", ""))); draw_title(d, 110, 158, sc["title"], W - 220, 60, NAVY, 1)
        for i, it in enumerate(items):
            if i > k - 1 and k > 0: break
            x = 110 + i * (cw + gap); box = (x, 300, x + cw, 920); shadow(im, box); d = ImageDraw.Draw(im)
            d.rounded_rectangle(box, 26, fill=WHITE); im.alpha_composite(rounded(photos[i], 26).crop((0, 0, cw, 400)), (x, 300)); d = ImageDraw.Draw(im)
            d.rectangle([x, 690, x + cw, 700], fill=WHITE)
            tag = it.get("tag");
            if tag:
                tw = d.textlength(tag, font=font("bold", 24)) + 40; d.rounded_rectangle([x + 24, 324, x + 24 + tw, 368], 22, fill=it.get("tag_color_rgb", ORANGE)); d.text((x + 44, 332), tag, font=font("bold", 24), fill=WHITE)
            d.text((x + 34, 728), it["title"], font=font("head", 40), fill=NAVY)
            for j, ln in enumerate(wrap(d, it.get("text", ""), font("body", 28), cw - 68)[:4]): d.text((x + 34, 786 + j * 36), ln, font=font("body", 28), fill=INK)
        if k == 0:  # giriş adımı: tüm öğeler soluk görünür, konuşmayla sırayla vurgulanır
            veil = Image.new("RGBA", (W, 1000 - 280), IVORY + (150,)); im.alpha_composite(veil, (0, 280))
        brand_bar(im, job); frames.append(im)
    return frames

def scene_roles(sc, job, tmp):
    frames = []; items = sc["items"][:3]; n = len(items); cw = (W - 220) // n
    photos = []
    for it in items:
        p = cover_crop(Image.open(fetch(it["photo"], tmp, f"r_{abs(hash(it['photo']))}.jpg")).convert("RGB"), 300, 300)
        m = Image.new("L", (300, 300), 0); ImageDraw.Draw(m).ellipse([0, 0, 299, 299], fill=255); p = p.convert("RGBA"); p.putalpha(m); photos.append(p)
    for k in range(len(sc["steps"])):
        im = Image.new("RGBA", (W, H), IVORY + (255,)); d = ImageDraw.Draw(im)
        kicker(d, 110, 110, sc.get("kicker", job.get("title", ""))); draw_title(d, 110, 158, sc["title"], W - 220, 60, NAVY, 1)
        for i, it in enumerate(items):
            if i > k - 1 and k > 0: break
            cx = 110 + i * cw + cw // 2; d.ellipse([cx - 162, 300 - 12, cx + 162, 300 + 312], fill=ORANGE if i == k - 1 else NAVY2)
            im.alpha_composite(photos[i], (cx - 150, 300)); d = ImageDraw.Draw(im)
            d.text((cx, 660), it["title"], font=font("head", 44), fill=NAVY, anchor="mm")
            for j, ln in enumerate(wrap(d, it.get("text", ""), font("body", 29), cw - 80)[:4]): d.text((cx, 720 + j * 38), ln, font=font("body", 29), fill=INK, anchor="mm")
        if k == 0:  # giriş adımı: tüm öğeler soluk görünür, konuşmayla sırayla vurgulanır
            veil = Image.new("RGBA", (W, 1000 - 280), IVORY + (150,)); im.alpha_composite(veil, (0, 280))
        brand_bar(im, job); frames.append(im)
    return frames

def scene_check(sc, job, tmp):
    frames = []
    for k in range(len(sc["steps"])):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 1180, H], fill=NAVY + (242,))
        kicker(d, 110, 130, sc.get("kicker", "Özet"), dark=True); y = draw_title(d, 110, 178, sc["title"], 960, 70, WHITE, 2) + 40
        for i, b in enumerate(sc.get("bullets", [])[:5]):
            if i > k - 1: break
            d.ellipse([110, y + 4, 160, y + 54], fill=ORANGE); d.line([(123, y + 30), (133, y + 41), (149, y + 19)], fill=WHITE, width=6)
            for j, ln in enumerate(wrap(d, b, font("body", 38), 860)[:2]): d.text((190, y + 6 + j * 48), ln, font=font("body", 38), fill=WHITE)
            y += 48 * min(2, len(wrap(d, b, font("body", 38), 860))) + 34
        brand_bar(im, job, dark=True); frames.append(im)
    return frames

SCENES = {"cover": scene_cover, "split": scene_split, "stats": scene_stats, "cards": scene_cards, "roles": scene_roles, "check": scene_check}

# ---------------- Ses ----------------
def say(text, extra=None):
    m = dict(SAY); m.update(extra or {})
    for k in sorted(m, key=len, reverse=True): text = re.sub(rf"(?<![A-Za-zÇĞİÖŞÜçğıöşü]){re.escape(k)}(?![A-Za-zÇĞİÖŞÜçğıöşü])", m[k], text)
    return text

def markup(text):
    """Doğal okuma: cümle sonlarında kısa, paragraf/'…' yerlerinde uzun duraklama (Chirp 3 HD markup)."""
    t = re.sub(r"\s*\n\s*\n\s*", " [pause long] ", text.strip())
    t = re.sub(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9])", " [pause short] ", t)
    return t

_VOICE = {}
def tts(job, text, tmp, name):
    key = os.environ.get("GOOGLE_TTS_KEY"); v = job.get("voice", {}); lang = v.get("lang", "tr-TR"); out = os.path.join(tmp, name + ".wav")
    if not key:
        dur = max(2.5, len(text.split()) / 150 * 60)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{dur:.2f}", out], check=True); return out
    if lang not in _VOICE: _VOICE[lang] = T.pick_voice(key, lang, v.get("gender"), v.get("voice"))
    voice = _VOICE[lang]; txt = say(text, job.get("say")); segs = []
    parts = re.split(r"(?<=[.!?])\s+", txt); buf, chunks = "", []
    for s in parts:
        if len((buf + " " + s).encode()) > 3800 and buf: chunks.append(buf); buf = s
        else: buf = (buf + " " + s).strip()
    if buf: chunks.append(buf)
    for i, ch in enumerate(chunks):
        body = {"input": {"markup": markup(ch)}, "voice": {"languageCode": lang, "name": voice}, "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 44100}}
        try: a = T._req(f"{T.API}/text:synthesize?key={key}", body)
        except Exception as e:
            print("markup desteklenmedi, düz metin:", e); body["input"] = {"text": ch}; a = T._req(f"{T.API}/text:synthesize?key={key}", body)
        p = os.path.join(tmp, f"{name}_{i}.wav"); open(p, "wb").write(base64.b64decode(a["audioContent"])); segs.append(p)
    lst = os.path.join(tmp, name + ".lst"); open(lst, "w").write("".join(f"file '{p}'\n" for p in segs))
    raw = os.path.join(tmp, name + "_raw.wav"); subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse", "-ar", "44100", "-ac", "1", out], check=True)
    return out

def run(cmd): subprocess.run(cmd, check=True)

def render_scene(job, sc, si, tmp):
    frames = SCENES[sc["type"]](sc, job, tmp); n = len(sc["steps"])
    wavs, durs = [], []
    for k, stx in enumerate(sc["steps"]):
        w = tts(job, stx, tmp, f"a{si}_{k}"); d = T._dur(w) + (0.55 if k < n - 1 else 1.1); wavs.append(w); durs.append(d)
    total = sum(durs) + 0.5
    # katman dizisi (concat, süreli kareler); her yeni katman 0.25 sn yarı saydam ara kareyle yumuşak belirir
    lst = os.path.join(tmp, f"o{si}.txt"); lines = []; prev = None
    for k, (fr, d) in enumerate(zip(frames, durs)):
        p = os.path.join(tmp, f"f{si}_{k}.png"); fr.save(p)
        if prev is not None:
            mid = Image.blend(prev, fr, 0.5); pm = os.path.join(tmp, f"f{si}_{k}m.png"); mid.save(pm); lines += [f"file '{pm}'", "duration 0.25"]; d -= 0.25
        lines += [f"file '{p}'", f"duration {d + (0.5 if k == 0 else 0):.3f}"]; prev = fr
    lines.append(f"file '{os.path.join(tmp, f'f{si}_{len(frames) - 1}.png')}'"); open(lst, "w").write("\n".join(lines) + "\n")
    frames_n = int(total * FPS) + 2; outv = os.path.join(tmp, f"s{si}.mp4")
    if sc.get("photo"):
        ph = fetch(sc["photo"], tmp, f"p{si}.jpg"); bgw = W if sc["type"] in ("cover", "check") else 860
        bg = cover_crop(Image.open(ph).convert("RGB"), int(bgw * 1.15), int(H * 1.15)); bp = os.path.join(tmp, f"bg{si}.png"); bg.save(bp)
        x0 = 0 if bgw == W else W - bgw
        zp = f"zoompan=z='min(1+0.00035*on,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_n}:s={bgw}x{H}:fps={FPS}"
        fc = f"color=c=0x{IVORY[0]:02x}{IVORY[1]:02x}{IVORY[2]:02x}:s={W}x{H}:r={FPS}:d={total:.2f}[base];[0:v]{zp}[kb];[base][kb]overlay={x0}:0[b];[1:v]format=rgba,fps={FPS}[ov];[b][ov]overlay=0:0:shortest=1,fade=t=in:st=0:d=0.45,fade=t=out:st={total - 0.45:.2f}:d=0.45[v]"
        ins = ["-loop", "1", "-framerate", str(FPS), "-i", bp, "-f", "concat", "-safe", "0", "-i", lst]
    else:
        fc = f"color=c=0x{IVORY[0]:02x}{IVORY[1]:02x}{IVORY[2]:02x}:s={W}x{H}:r={FPS}:d={total:.2f}[b];[0:v]format=rgba,fps={FPS}[ov];[b][ov]overlay=0:0:shortest=1,fade=t=in:st=0:d=0.45,fade=t=out:st={total - 0.45:.2f}:d=0.45[v]"
        ins = ["-f", "concat", "-safe", "0", "-i", lst]
    # ses: adım sesleri arka arkaya, adım aralarında sessizlik
    alst = os.path.join(tmp, f"al{si}.txt"); al = []
    sil0 = os.path.join(tmp, f"sil{si}_0.wav"); run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.5", sil0]); al.append(f"file '{sil0}'")
    for k, (w, d) in enumerate(zip(wavs, durs)):
        al.append(f"file '{w}'"); gap = d - T._dur(w); s = os.path.join(tmp, f"sil{si}_{k + 1}.wav")
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{gap:.3f}", s]); al.append(f"file '{s}'")
    open(alst, "w").write("\n".join(al) + "\n"); aw = os.path.join(tmp, f"aud{si}.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alst, "-c", "copy", aw])
    run(["ffmpeg", "-y", "-v", "error"] + ins + ["-i", aw, "-filter_complex", fc, "-map", "[v]", "-map", f"{2 if sc.get('photo') else 1}:a", "-t", f"{total:.2f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1", outv])
    print(f"sahne {si + 1}: {sc['type']} {total:.1f} sn", flush=True)
    return outv, total

def voices(job):
    """Ses karşılaştırma dosyası: aynı paragraf farklı Chirp 3 HD seslerle (her birinin önünde adı okunur)."""
    tmp = tempfile.mkdtemp(); parts = []
    for i, v in enumerate(job["voices"]):
        j = {"voice": {"lang": "tr-TR", "voice": f"tr-TR-Chirp3-HD-{v}"}}; _VOICE.clear()
        parts.append(tts(j, f"Ses {i + 1}. " + job["text"], tmp, f"v{i}"))
        s = os.path.join(tmp, f"g{i}.wav"); run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "1.2", s]); parts.append(s)
    lst = os.path.join(tmp, "v.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    out = os.path.join(ROOT, "out", "lessons", job["code"] + ".mp3"); os.makedirs(os.path.dirname(out), exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-af", "loudnorm=I=-16", "-b:a", "128k", out]); print("OK", out)

def main(path):
    job = json.load(open(path, encoding="utf-8")); code = job["code"]; tmp = tempfile.mkdtemp()
    if job.get("voices"): return voices(job)
    os.makedirs(os.path.join(ROOT, "out", "lessons"), exist_ok=True)
    parts = [render_scene(job, sc, i, tmp) for i, sc in enumerate(job["scenes"])]
    lst = os.path.join(tmp, "all.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p, _ in parts))
    cat = os.path.join(tmp, "cat.mp4"); run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", cat])
    out = os.path.join(ROOT, "out", "lessons", f"{code}.mp4"); mus = job.get("music")
    if mus:
        mp = fetch(mus, tmp, "music.mp3")
        run(["ffmpeg", "-y", "-v", "error", "-i", cat, "-stream_loop", "-1", "-i", mp, "-filter_complex",
             "[1:a]volume=0.07,afade=t=in:d=2[m];[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[v];[v][m]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
    else:
        run(["ffmpeg", "-y", "-v", "error", "-i", cat, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
    total = round(sum(t for _, t in parts), 1)
    json.dump({"code": code, "duration_sec": total, "scenes": [round(t, 1) for _, t in parts], "min_sec": job.get("min_sec")}, open(out[:-4] + ".json", "w"), ensure_ascii=False)
    print(f"OK {out} {total} sn ({total / 60:.1f} dk)")

if __name__ == "__main__":
    for p in sys.argv[1:]: main(p)
