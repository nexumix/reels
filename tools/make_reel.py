"""Reels v2: illustrated scenes, readable timing, slow zoom.
config: bg (gradient top), bg2 (gradient bottom), fg, accent, card (rgba hex or null), handle, logo, logo_w, out,
slides: [{title, sub?, scene?: city|house|safety|doc|chart|key|globe, size?, dur?}]"""
import sys, json, subprocess, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def hx(c, a=255):
    c = c.lstrip('#'); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4)) + (a,)

def mix(c1, c2, t): return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def gradient(c1, c2):
    g = Image.new("RGB", (1, H))
    for y in range(H): g.putpixel((0, y), mix(hx(c1), hx(c2), y / H))
    return g.resize((W, H)).convert("RGBA")

def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def scene_city(acc, fg, rnd):
    L = layer(); d = ImageDraw.Draw(L)
    for _ in range(70):  # stars / lights
        x, y = rnd.randint(0, W), rnd.randint(80, 900); r = rnd.choice((2, 3, 4))
        d.ellipse([x-r, y-r, x+r, y+r], fill=acc[:3] + (rnd.randint(80, 200),))
    d.ellipse([760, 760, 960, 960], fill=acc[:3] + (70,))  # moon glow
    d.ellipse([800, 800, 920, 920], fill=acc[:3] + (170,))
    base = 1500; x = -20
    while x < W:  # towers
        w = rnd.randint(60, 130); h = rnd.randint(180, 620)
        d.rectangle([x, base-h, x+w, base], fill=fg[:3] + (rnd.randint(150, 220),))
        for wy in range(base-h+20, base-20, 36):
            for wx in range(x+12, x+w-14, 26):
                if rnd.random() < .45: d.rectangle([wx, wy, wx+10, wy+16], fill=acc[:3] + (190,))
        x += w + rnd.randint(4, 18)
    # Galata-like tower
    d.rectangle([480, base-760, 600, base], fill=fg[:3] + (235,))
    d.polygon([(470, base-760), (610, base-760), (540, base-930)], fill=fg[:3] + (235,))
    d.rectangle([470, base-800, 610, base-770], fill=acc[:3] + (200,))
    # bridge
    for i in range(0, W, 6):
        y = base + 60 - 120 * math.sin(math.pi * i / W)
        d.line([i, y, i, base + 110], fill=acc[:3] + (60,), width=1) if i % 30 == 0 else None
    d.line([(0, base+110), (W, base+110)], fill=acc[:3] + (220,), width=8)
    pts = [(i, base + 60 - 120 * math.sin(math.pi * i / W)) for i in range(0, W + 1, 10)]
    d.line(pts, fill=acc[:3] + (220,), width=5)
    for y in range(base + 130, H, 14):  # water shimmer
        for _ in range(6):
            x0 = rnd.randint(0, W); d.line([x0, y, x0 + rnd.randint(30, 120), y], fill=acc[:3] + (rnd.randint(30, 90),), width=3)
    return L

def scene_house(acc, fg, rnd):
    L = layer(); d = ImageDraw.Draw(L)
    cx, by = W // 2, 1560
    d.ellipse([cx-470, by-40, cx+470, by+60], fill=(0, 0, 0, 40))
    d.polygon([(cx-420, by-520), (cx, by-880), (cx+420, by-520)], fill=acc[:3] + (235,))
    d.rectangle([cx-340, by-520, cx+340, by], fill=fg[:3] + (230,))
    d.rectangle([cx+190, by-820, cx+260, by-640], fill=fg[:3] + (230,))
    for wx in (cx-270, cx+90):
        d.rectangle([wx, by-420, wx+180, by-260], fill=acc[:3] + (220,))
        d.line([wx+90, by-420, wx+90, by-260], fill=fg[:3] + (255,), width=8)
        d.line([wx, by-340, wx+180, by-340], fill=fg[:3] + (255,), width=8)
    d.rectangle([cx-80, by-240, cx+80, by], fill=acc[:3] + (255,))
    d.ellipse([cx+40, by-130, cx+60, by-110], fill=fg[:3] + (255,))
    for _ in range(25):
        x, y = rnd.randint(0, W), rnd.randint(100, 700); r = rnd.choice((3, 5))
        d.ellipse([x-r, y-r, x+r, y+r], fill=acc[:3] + (120,))
    return L

def scene_safety(acc, fg, rnd):
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W // 2, 1200
    d.polygon([(cx, cy-480), (cx+380, cy-330), (cx+340, cy+150), (cx, cy+430), (cx-340, cy+150), (cx-380, cy-330)], fill=fg[:3] + (40,))
    d.polygon([(cx, cy-420), (cx+320, cy-290), (cx+285, cy+120), (cx, cy+360), (cx-285, cy+120), (cx-320, cy-290)], outline=fg[:3] + (200,), width=14)
    # hard hat
    d.pieslice([cx-260, cy-260, cx+260, cy+260], 180, 360, fill=acc[:3] + (255,))
    d.rounded_rectangle([cx-320, cy-10, cx+320, cy+50], 25, fill=acc[:3] + (255,))
    d.rectangle([cx-30, cy-260, cx+30, cy-10], fill=mix(acc, (255, 255, 255), .35) + (255,))
    d.line([(cx-120, cy+170), (cx-30, cy+250), (cx+140, cy+110)], fill=fg[:3] + (255,), width=26)
    for _ in range(18):
        x, y = rnd.randint(0, W), rnd.randint(150, 650)
        d.regular_polygon((x, y, rnd.randint(8, 16)), 3, fill=acc[:3] + (90,))
    return L

def scene_doc(acc, fg, rnd):
    L = layer(); d = ImageDraw.Draw(L)
    x0, y0 = 220, 820
    d.rounded_rectangle([x0+40, y0+40, x0+680, y0+880], 30, fill=(0, 0, 0, 35))
    d.rounded_rectangle([x0, y0, x0+640, y0+840], 30, fill=(255, 255, 255, 240), outline=fg[:3] + (255,), width=8)
    d.rectangle([x0+80, y0+90, x0+560, y0+130], fill=fg[:3] + (230,))
    for i, yy in enumerate(range(y0+200, y0+600, 80)):
        d.line([(x0+90, yy+15), (x0+120, yy+40), (x0+165, yy-5)], fill=acc[:3] + (255,), width=12)
        d.rectangle([x0+200, yy+5, x0+540 - (i % 2) * 90, yy+30], fill=fg[:3] + (120,))
    sx, sy = x0+520, y0+720
    d.polygon([(sx-60, sy+40), (sx-90, sy+190), (sx-30, sy+150), (sx, sy+200), (sx+10, sy+40)], fill=acc[:3] + (255,))
    d.ellipse([sx-110, sy-110, sx+110, sy+110], fill=acc[:3] + (255,))
    d.ellipse([sx-80, sy-80, sx+80, sy+80], outline=(255, 255, 255, 255), width=8)
    d.line([(sx-40, sy), (sx-10, sy+30), (sx+45, sy-30)], fill=(255, 255, 255, 255), width=14)
    return L

def scene_chart(acc, fg, rnd):
    L = layer(); d = ImageDraw.Draw(L)
    base = 1620
    for i, h in enumerate((220, 340, 300, 480, 620, 820)):
        x = 150 + i * 135
        d.rounded_rectangle([x, base-h, x+95, base], 14, fill=(acc if i == 5 else fg)[:3] + (220,))
    pts = [(197 + i * 135, base - h - 60) for i, h in enumerate((220, 340, 300, 480, 620, 820))]
    d.line(pts, fill=acc[:3] + (255,), width=12)
    ex, ey = pts[-1]; d.polygon([(ex+10, ey-70), (ex+60, ey+20), (ex-40, ey+10)], fill=acc[:3] + (255,))
    for p in pts[:-1]: d.ellipse([p[0]-16, p[1]-16, p[0]+16, p[1]+16], fill=acc[:3] + (255,))
    return L

def scene_key(acc, fg, rnd):
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = 430, 1180
    d.ellipse([cx-200, cy-200, cx+200, cy+200], fill=acc[:3] + (255,))
    d.ellipse([cx-90, cy-90, cx+90, cy+90], fill=(0, 0, 0, 0))
    d.ellipse([cx-90, cy-90, cx+90, cy+90], fill=fg[:3] + (90,))
    d.rectangle([cx+180, cy-40, cx+620, cy+40], fill=acc[:3] + (255,))
    for tx in (cx+470, cx+560): d.rectangle([tx, cy+40, tx+50, cy+150], fill=acc[:3] + (255,))
    for _ in range(30):
        x, y = rnd.randint(0, W), rnd.randint(120, 760); r = rnd.choice((3, 6))
        d.ellipse([x-r, y-r, x+r, y+r], fill=acc[:3] + (130,))
    return L

def scene_globe(acc, fg, rnd):
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy, r = W // 2, 1200, 380
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=fg[:3] + (230,), width=12)
    for k in (.35, .7):
        d.ellipse([cx-r*k, cy-r, cx+r*k, cy+r], outline=fg[:3] + (160,), width=6)
    for t in (-.5, 0, .5):
        y = cy + r * t; w = r * math.sqrt(1 - t * t)
        d.line([(cx-w, y), (cx+w, y)], fill=fg[:3] + (160,), width=6)
    for ang in range(0, 360, 45):
        a = math.radians(ang); px, py = cx + (r+90) * math.cos(a), cy + (r+90) * math.sin(a)
        d.ellipse([px-18, py-18, px+18, py+18], fill=acc[:3] + (230,))
        d.line([(cx, cy), (px, py)], fill=acc[:3] + (70,), width=3)
    d.ellipse([cx-30, cy-30, cx+30, cy+30], fill=acc[:3] + (255,))
    return L

SCENES = dict(city=scene_city, house=scene_house, safety=scene_safety, doc=scene_doc, chart=scene_chart, key=scene_key, globe=scene_globe)

def wrap(d, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= maxw: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
    return [l for l in lines if l is not None]

def render(i, s, cfg, out, last):
    acc, fg = hx(cfg["accent"]), hx(cfg["fg"])
    img = gradient(cfg["bg"], cfg.get("bg2", cfg["bg"]))
    rnd = random.Random(hash(s["title"]) & 0xffff)
    sc = SCENES.get(s.get("scene", ""))
    if sc:
        img = Image.alpha_composite(img, sc(acc, fg, rnd))
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(B, s.get("size", 84)); small = ImageFont.truetype(R, 48)
    tl = wrap(d, s["title"], big, W - 200); sl = wrap(d, s.get("sub", ""), small, W - 220) if s.get("sub") else []
    th = len(tl) * (big.size + 22) + (len(sl) * 66 + 40 if sl else 0)
    top = 330 if (i == 0 or last) and cfg.get("logo") else 200
    cy0 = top + 40
    card = cfg.get("card", "#FFFFFFE6")
    ov = layer(); od = ImageDraw.Draw(ov)
    od.rounded_rectangle([60, cy0 - 50, W - 60, cy0 + th + 50], 40, fill=hx(card[:7], int(card[7:9], 16) if len(card) > 7 else 230))
    od.rectangle([60, cy0 - 50, 76, cy0 + th + 50], fill=acc)
    img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
    y = cy0
    tcol = cfg.get("card_fg", cfg["fg"])
    for ln in tl:
        d.text(((W - d.textlength(ln, font=big)) / 2, y), ln, font=big, fill=cfg["accent"] if i == 0 else tcol); y += big.size + 22
    if sl:
        y += 40
        for ln in sl:
            d.text(((W - d.textlength(ln, font=small)) / 2, y), ln, font=small, fill=tcol); y += 66
    if cfg.get("logo") and (i == 0 or last):
        lg = Image.open(cfg["logo"]).convert("RGBA"); lw = cfg.get("logo_w", 420)
        lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
        pad = Image.new("RGBA", (lw + 40, lg.height + 30), hx(cfg.get("logo_bg", "#FFFFFF"), 245))
        m = Image.new("L", pad.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, *pad.size], 30, fill=255)
        img.paste(pad, ((W - pad.width) // 2, 60), m); img.alpha_composite(lg, ((W - lw) // 2, 75))
    hf = ImageFont.truetype(B, 40); d = ImageDraw.Draw(img)
    d.text(((W - d.textlength(cfg["handle"], font=hf)) / 2, H - 120), cfg["handle"], font=hf, fill=cfg["accent"])
    img.convert("RGB").save(out)

def dur_of(s):
    words = len((s["title"] + " " + s.get("sub", "")).split())
    return s.get("dur", max(3.5, min(7.0, 2.2 + 0.36 * words)))

cfg = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
n = len(cfg["slides"]); fade = 0.45; files, durs = [], []
for i, s in enumerate(cfg["slides"]):
    p = f"{outdir}/s{i}.png"; render(i, s, cfg, p, i == n - 1); files.append(p); durs.append(dur_of(s))
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for p, dd in zip(files, durs): cmd += ["-loop", "1", "-t", f"{dd:.2f}", "-framerate", "30", "-i", p]
fc = []
for i, dd in enumerate(durs):
    fr = int(dd * 30)
    fc.append(f"[{i}:v]scale=1188:2112,zoompan=z='min(1+0.0009*on,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps=30,trim=duration={dd:.2f},setpts=PTS-STARTPTS[z{i}]")
prev, off = "[z0]", 0.0
for i in range(1, n):
    off += durs[i-1] - fade
    fc.append(f"{prev}[z{i}]xfade=transition=fade:duration={fade}:offset={off:.2f}[x{i}]"); prev = f"[x{i}]"
fc.append(f"{prev}format=yuv420p[out]")
cmd += ["-filter_complex", ";".join(fc), "-map", "[out]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", cfg["out"]]
subprocess.run(cmd, check=True)
print(cfg["out"], round(sum(durs) - fade * (n - 1), 1), "sn")
