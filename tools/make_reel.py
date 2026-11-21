import sys, json, subprocess, os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def wrap(d, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= maxw:
                cur = t
            else:
                lines.append(cur); cur = w
        lines.append(cur)
    return lines

def slide(i, s, cfg, out):
    bg, fg, ac = cfg["bg"], cfg["fg"], cfg["accent"]
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 18], fill=ac)
    d.rectangle([0, H - 18, W, H], fill=ac)
    big = ImageFont.truetype(B, s.get("size", 92))
    small = ImageFont.truetype(R, 46)
    lines = wrap(d, s["title"], big, W - 160)
    lh = big.size + 28
    sub = wrap(d, s.get("sub", ""), small, W - 180) if s.get("sub") else []
    total = len(lines) * lh + (len(sub) * 62 + 50 if sub else 0)
    y = (H - total) // 2
    for ln in lines:
        d.text(((W - d.textlength(ln, font=big)) / 2, y), ln, font=big, fill=fg if i else ac)
        y += lh
    if sub:
        y += 50
        for ln in sub:
            d.text(((W - d.textlength(ln, font=small)) / 2, y), ln, font=small, fill=fg)
            y += 62
    if cfg.get("logo") and (i == 0 or i == len(cfg["slides"]) - 1):
        lg = Image.open(cfg["logo"]).convert("RGB")
        lw = cfg.get("logo_w", 560)
        lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
        img.paste(lg, ((W - lw) // 2, 120))
    hf = ImageFont.truetype(B, 40)
    d.text(((W - d.textlength(cfg["handle"], font=hf)) / 2, H - 140), cfg["handle"], font=hf, fill=ac)
    img.save(out)

cfg = json.load(open(sys.argv[1]))
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)
dur, fade = 3.2, 0.5
files = []
for i, s in enumerate(cfg["slides"]):
    p = f"{outdir}/s{i}.png"; slide(i, s, cfg, p); files.append(p)
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for p in files:
    cmd += ["-loop", "1", "-t", str(dur), "-i", p]
fc, prev, off = [], "[0:v]", 0.0
for i in range(1, len(files)):
    off += dur - fade
    lab = f"[v{i}]"
    fc.append(f"{prev}[{i}:v]xfade=transition=slideup:duration={fade}:offset={off:.2f}{lab}")
    prev = lab
cmd += ["-filter_complex", ";".join(fc) + f";{prev}format=yuv420p[out]", "-map", "[out]",
        "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-movflags", "+faststart", cfg["out"]]
subprocess.run(cmd, check=True)
print(cfg["out"])
