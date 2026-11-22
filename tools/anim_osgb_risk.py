#!/usr/bin/env python3
"""Kod ile çizilen animasyonlu reels (motion graphics) — OSGB 'Risk değerlendirmesi 3 adımda'.
Usage: python3 tools/anim_osgb_risk.py <out.mp4> [voice.mp3] [music]"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.environ.get("FONT_DIR", os.path.join(ROOT, ".fonts"))
NAVY, NAVY2, ORANGE, WHITE, INK = (8, 41, 90), (18, 70, 140), (242, 140, 15), (255, 255, 255), (8, 41, 90)
GREEN, YELLOW, RED = (46, 170, 90), (245, 196, 40), (220, 60, 50)
SCENES = [4.6, 5.8, 5.2, 4.4, 5.0]
STARTS = [sum(SCENES[:i]) for i in range(len(SCENES))]
TOTAL = sum(SCENES)

def F(kind, size):
    try:
        if kind == "head":
            f = ImageFont.truetype(os.path.join(FD, "SchibstedGrotesk.ttf"), size)
            try: f.set_variation_by_axes([800])
            except Exception: pass
            return f
        return ImageFont.truetype(os.path.join(FD, {"bold": "Lato-Black.ttf", "semi": "Lato-Bold.ttf"}.get(kind, "Lato-Regular.ttf")), size)
    except Exception:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/" + ("DejaVuSans-Bold.ttf" if kind != "body" else "DejaVuSans.ttf"), size)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def back_out(x, s=1.7): x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def mix(c1, c2, t): return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

BG = Image.new("RGB", (W, H))
for y in range(H):
    ImageDraw.Draw(BG).line([(0, y), (W, y)], fill=mix(NAVY2, NAVY, y / H))
LOGO = None
try:
    lg = Image.open(os.path.join(ROOT, "tools/logos/osgb.png")).convert("RGB").resize((240, 160), Image.LANCZOS)
    LOGO = Image.new("RGBA", (240, 160)); LOGO.paste(lg)
    m = Image.new("L", (240, 160), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 239, 159], 24, fill=255); LOGO.putalpha(m)
except Exception:
    pass

def text_reveal(img, text, cx, y, font, color, t0, t, maxw=920, per=0.12, align="center", line=1.08):
    d = ImageDraw.Draw(img)
    words = text.split(); lines, cur = [], []
    for w in words:
        if d.textlength(" ".join(cur + [w]), font=font) <= maxw or not cur: cur.append(w)
        else: lines.append(cur); cur = [w]
    lines.append(cur)
    k = 0; lh = int(font.size * line)
    for li, ln in enumerate(lines):
        full = " ".join(ln); lw = d.textlength(full, font=font)
        x = cx - lw / 2 if align == "center" else cx
        for w in ln:
            p = ease_out((t - t0 - k * per) / 0.35); k += 1
            if p > 0:
                layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
                ld.text((x, y + li * lh + (1 - p) * 40), w, font=font, fill=color + (int(255 * p),))
                img.alpha_composite(layer)
            x += d.textlength(w + " ", font=font)
    return y + len(lines) * lh

def pill(img, text, cx, cy, font, bg, fg, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0: return
    d = ImageDraw.Draw(img); tw = d.textlength(text, font=font); w, h = (tw + 64) * scale, (font.size + 36) * scale
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], h / 2, fill=bg + (int(255 * alpha),))
    if scale > 0.6:
        f2 = font if scale >= 0.99 else F("bold", max(10, int(font.size * scale)))
        tw2 = ld.textlength(text, font=f2); ld.text((cx - tw2 / 2, cy - f2.size * 0.62), text, font=f2, fill=fg + (int(255 * alpha),))
    img.alpha_composite(layer)

def step_badge(img, n, lt):
    s = back_out(lt / 0.5); r = 90 * s
    if r < 2: return
    d = ImageDraw.Draw(img); cx, cy = 540, 560
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=mix(NAVY, ORANGE, 0.25))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ORANGE)
    if s > 0.6:
        f = F("head", int(110 * s)); tw = d.textlength(str(n), font=f); d.text((cx - tw / 2, cy - f.size * 0.6), str(n), font=f, fill=WHITE)

def card(img, cx, cy, s, draw_icon, label):
    if s <= 0.01: return
    w, h = 270 * s, 300 * s
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([cx - w / 2 + 6, cy - h / 2 + 10, cx + w / 2 + 6, cy + h / 2 + 10], 30 * s, fill=(0, 0, 0, 70))
    ld.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 30 * s, fill=WHITE + (255,))
    img.alpha_composite(layer); d = ImageDraw.Draw(img)
    draw_icon(d, cx, cy - 40 * s, s)
    if s > 0.7:
        f = F("semi", int(30 * s)); tw = d.textlength(label, font=f); d.text((cx - tw / 2, cy + 75 * s), label, font=f, fill=INK)

def icon_bolt(d, cx, cy, s):
    p = [(10, -70), (-35, 10), (0, 10), (-15, 70), (40, -15), (5, -15), (25, -70)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in p], fill=ORANGE)
def icon_drop(d, cx, cy, s):
    d.ellipse([cx - 42 * s, cy - 10 * s, cx + 42 * s, cy + 70 * s], fill=(40, 140, 220))
    d.polygon([(cx - 38 * s, cy + 18 * s), (cx, cy - 70 * s), (cx + 38 * s, cy + 18 * s)], fill=(40, 140, 220))
def icon_gear(d, cx, cy, s, ang=0):
    for k in range(8):
        a = ang + k * math.pi / 4; x, y = cx + math.cos(a) * 58 * s, cy + math.sin(a) * 58 * s
        d.ellipse([x - 16 * s, y - 16 * s, x + 16 * s, y + 16 * s], fill=(90, 100, 120))
    d.ellipse([cx - 55 * s, cy - 55 * s, cx + 55 * s, cy + 55 * s], fill=(90, 100, 120))
    d.ellipse([cx - 22 * s, cy - 22 * s, cx + 22 * s, cy + 22 * s], fill=WHITE)

def warning(d, cx, cy, s, rot):
    if s < 0.03: return
    pts = []
    for k in range(3):
        a = rot - math.pi / 2 + k * 2 * math.pi / 3; pts.append((cx + math.cos(a) * 230 * s, cy + math.sin(a) * 230 * s))
    d.polygon(pts, fill=ORANGE)
    inner = [(cx + (x - cx) * 0.8, cy + (y - cy) * 0.8 + 10 * s) for x, y in pts]
    d.polygon(inner, fill=YELLOW)
    d.rounded_rectangle([cx - 18 * s, cy - 80 * s, cx + 18 * s, cy + 40 * s], 14 * s, fill=INK)
    d.ellipse([cx - 20 * s, cy + 62 * s, cx + 20 * s, cy + 102 * s], fill=INK)

def hardhat(d, cx, cy, s):
    if s < 0.03: return
    d.pieslice([cx - 220 * s, cy - 210 * s, cx + 220 * s, cy + 230 * s], 180, 360, fill=ORANGE)
    d.rounded_rectangle([cx - 280 * s, cy + 0 * s, cx + 280 * s, cy + 50 * s], 25 * s, fill=ORANGE)
    d.rectangle([cx - 26 * s, cy - 210 * s, cx + 26 * s, cy], fill=mix(ORANGE, WHITE, 0.35))

def frame(t):
    img = BG.copy().convert("RGBA"); d = ImageDraw.Draw(img)
    # ambient: floating dots
    for k in range(26):
        x = (k * 173 + t * (12 + k % 5 * 6)) % W; y = (k * 311 - t * (20 + k % 7 * 5)) % H; r = 3 + k % 4
        d.ellipse([x - r, y - r, x + r, y + r], fill=mix(NAVY, WHITE, 0.18))
    si = max(i for i in range(len(SCENES)) if t >= STARTS[i]); lt = t - STARTS[si]
    # scene slide-in offset
    off = (1 - ease_out(lt / 0.45)) * 120 if si > 0 else 0
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); L = ImageDraw.Draw(layer)
    head = F("head", 96); body = F("body", 44); semi = F("semi", 44)
    if si == 0:
        s = back_out(lt / 0.6); warning(L, 540, 640, s, math.sin(lt * 3) * 0.06 * clamp(lt - 0.6, 0, 1))
        pill(layer, "3 ADIMDA", 540, 950, F("bold", 40), WHITE, INK, back_out((lt - 0.5) / 0.4))
        text_reveal(layer, "İşyerinde risk değerlendirmesi yaptın mı?", 540, 1060, F("head", 104), WHITE, 0.7, lt)
    elif si == 1:
        step_badge(layer, 1, lt)
        text_reveal(layer, "Tehlikeleri belirle", 540, 720, head, WHITE, 0.3, lt)
        for k, (ic, lb) in enumerate([(icon_bolt, "Kablolar"), (icon_drop, "Kaygan zemin"), (lambda dd, x, y, sc: icon_gear(dd, x, y, sc, lt * 1.5), "Makineler")]):
            card(layer, 210 + k * 330, 1260, back_out((lt - 1.0 - k * 0.45) / 0.45), ic, lb)
        # magnifier sweep
        mp = clamp((lt - 2.6) / 2.4)
        if mp > 0:
            mx = 150 + mp * 780; my = 1190 + math.sin(mp * math.pi * 2) * 30
            L.ellipse([mx - 85, my - 85, mx + 85, my + 85], outline=WHITE, width=16)
            L.line([(mx + 60, my + 60), (mx + 150, my + 150)], fill=WHITE, width=28)
    elif si == 2:
        step_badge(layer, 2, lt)
        text_reveal(layer, "Riskleri puanla", 540, 720, head, WHITE, 0.3, lt)
        cols = [[GREEN, YELLOW, RED], [GREEN, YELLOW, RED], [GREEN, GREEN, YELLOW]]
        g0x, g0y, cs = 300, 940, 170
        for r in range(3):
            for c in range(3):
                idx = r * 3 + (c if r % 2 == 0 else 2 - c)
                p = back_out((lt - 1.0 - idx * 0.22) / 0.35)
                x0, y0 = g0x + c * (cs + 14), g0y + r * (cs + 14)
                L.rounded_rectangle([x0, y0, x0 + cs, y0 + cs], 22, fill=mix(NAVY, WHITE, 0.12))
                if p > 0:
                    m = cs * (1 - p) / 2
                    L.rounded_rectangle([x0 + m, y0 + m, x0 + cs - m, y0 + cs - m], 22, fill=cols[2 - r][c])
        f = F("semi", 36); L.text((g0x, g0y + 3 * (cs + 14) + 10), "Olasılık →", font=f, fill=WHITE)
        lay2 = Image.new("RGBA", (320, 60), (0, 0, 0, 0)); ImageDraw.Draw(lay2).text((0, 0), "Şiddet →", font=f, fill=WHITE)
        lay2 = lay2.rotate(90, expand=True); layer.alpha_composite(lay2, (g0x - 80, g0y + 3 * (cs + 14) - 330))
    elif si == 3:
        step_badge(layer, 3, lt)
        text_reveal(layer, "Önlem al, kayda geçir", 540, 720, head, WHITE, 0.3, lt)
        p = back_out((lt - 0.8) / 0.5)
        if p > 0.01:
            bx, by, bw, bh = 540 - 300 * p, 1010, 600 * p, 640 * p
            L.rounded_rectangle([bx, by, bx + bw, by + bh], 36, fill=WHITE)
            L.rounded_rectangle([540 - 110 * p, by - 34, 540 + 110 * p, by + 40], 20, fill=ORANGE)
            for k, lbl in enumerate(["Eğitim", "Ekipman", "Kayıt"]):
                yy = by + 130 + k * 160
                if p > 0.9:
                    L.text((bx + 190, yy - 26), lbl, font=F("semi", 52), fill=INK)
                    L.rounded_rectangle([bx + 60, yy - 40, bx + 140, yy + 40], 16, outline=mix(INK, WHITE, 0.5), width=6)
                    cp = clamp((lt - 1.6 - k * 0.6) / 0.35)
                    if cp > 0:
                        a, b, c = (bx + 72, yy), (bx + 96, yy + 26), (bx + 150, yy - 40)
                        if cp < 0.5:
                            q = cp / 0.5; L.line([a, (a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q)], fill=GREEN, width=16)
                        else:
                            q = (cp - 0.5) / 0.5; L.line([a, b], fill=GREEN, width=16); L.line([b, (b[0] + (c[0] - b[0]) * q, b[1] + (c[1] - b[1]) * q)], fill=GREEN, width=16)
    else:
        bounce = abs(math.sin(lt * 4)) * 30 * math.exp(-lt * 1.2)
        hardhat(L, 540, 680 - bounce, back_out(lt / 0.6))
        text_reveal(layer, "Tepe OSGB uzmanları sizin için yapsın.", 540, 840, F("head", 88), WHITE, 0.5, lt)
        ps = back_out((lt - 1.4) / 0.4) * (1 + 0.03 * math.sin(lt * 6) * clamp(lt - 1.8))
        pill(layer, "Hemen ara  0216 434 83 73", 540, 1260, F("bold", 54), ORANGE, INK, ps)
        a = ease_out((lt - 2.0) / 0.4)
        if a > 0:
            for k, (tx, col) in enumerate([("WhatsApp  0532 138 51 54", WHITE), ("info@tepeosgb.com  ·  0850 305 40 19", ORANGE)]):
                f = F("semi", 46 if k == 0 else 38); tw = L.textlength(tx, font=f)
                L.text((540 - tw / 2, 1370 + k * 80 + (1 - a) * 30), tx, font=f, fill=col + (int(255 * a),))
    img.alpha_composite(layer, (0, int(off)))
    # chrome: logo + progress
    if LOGO: img.alpha_composite(LOGO, (64, 96))
    d = ImageDraw.Draw(img)
    for k in range(3):
        x0 = 300 + k * 170; on = (si - 1) >= k or (si == 4)
        d.rounded_rectangle([x0, 1780, x0 + 150, 1792], 6, fill=ORANGE if on else mix(NAVY, WHITE, 0.25))
    f = F("semi", 36); tw = d.textlength("@tepeosgb", font=f); d.text((540 - tw / 2, 1820), "@tepeosgb", font=f, fill=ORANGE)
    return img.convert("RGB")

def main():
    out = sys.argv[1]; voice = sys.argv[2] if len(sys.argv) > 2 else None; music = sys.argv[3] if len(sys.argv) > 3 else None
    silent = out + ".v.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(TOTAL * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent]; fc = []; maps = []
    if voice: cmd += ["-i", voice]
    if music: cmd += ["-stream_loop", "-1", "-i", music]
    if voice and music:
        fc = [f"[1:a]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{TOTAL}[vo]", "[vo]asplit=2[vk][vm]",
              f"[2:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:{TOTAL},volume=0.15,afade=t=out:st={TOTAL-1.5}:d=1.5[mu]",
              "[mu][vk]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[du]", "[du][vm]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]"]
        maps = ["-map", "[a]"]
    cmd += (["-filter_complex", ";".join(fc)] if fc else []) + ["-map", "0:v"] + maps + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL), "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True); os.remove(silent); print(out, TOTAL)

if __name__ == "__main__":
    main()
