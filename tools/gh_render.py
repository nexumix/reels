#!/usr/bin/env python3
"""Premium reels renderer (runs in GitHub Actions; network open there).
Usage: python3 tools/gh_render.py jobs/<job>.json
Job JSON:
{
 "out": "out/2026-11-22/teperealestate_x.mp4",
 "scrim": "#010923", "transition": 0.8,
 "logo": {"src": "tools/logos/realestate.png", "x": 64, "y": 96, "w": 200, "h": 166, "radius": 24},
 "voice": "v/2026-11-22/vo_x.mp3" (repo path or URL, optional),
 "music": {"src": "https://cdn.orshot.com/...m4a", "volume": 0.15},
 "scenes": [ {"photo": "<url or repo path>", "dur": 5.0, "pan": 1,
     "elements": [ {"text": "...", "x":72, "y":1100, "w":936, "size":110, "font":"head|body|bold",
                    "color":"#FFFFFF", "align":"left", "at":0.4, "anim":"up|fade|none",
                    "pill": "#E3B33F" (optional bg), "pad": [24,12], "radius": 999, "line": 1.05} ] } ]
}"""
import json, os, subprocess, sys, tempfile, urllib.request, shutil
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(ROOT, ".fonts"))
DV = "/usr/share/fonts/truetype/dejavu/"

def font(kind, size):
    try:
        if kind == "head":
            f = ImageFont.truetype(os.path.join(FONT_DIR, "SchibstedGrotesk.ttf"), size)
            try: f.set_variation_by_axes([800])
            except Exception: pass
            return f
        name = {"body": "Lato-Regular.ttf", "bold": "Lato-Black.ttf", "semi": "Lato-Bold.ttf"}.get(kind, "Lato-Regular.ttf")
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except Exception:
        return ImageFont.truetype(DV + ("DejaVuSans-Bold.ttf" if kind in ("head", "bold", "semi") else "DejaVuSans.ttf"), size)

def hexrgb(c, a=255):
    c = c.lstrip("#"); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4)) + (a,)

def fetch(src, tmp, name):
    p = os.path.join(tmp, name)
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(p, "wb") as f: shutil.copyfileobj(r, f)
    else:
        shutil.copy(src if src.startswith("/") else os.path.join(ROOT, src), p)
    return p

def wrap(d, text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxw or not cur: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def element_png(el, path):
    size = int(el.get("size", 48)); f = font(el.get("font", "body"), size)
    pad = el.get("pad", [24, 12]) if el.get("pill") else [0, 0]
    maxw = int(el.get("w", 936)) - 2 * pad[0]
    tmpd = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = wrap(tmpd, el["text"], f, maxw)
    lh = int(size * el.get("line", 1.05 if el.get("font", "body") == "head" else 1.32))
    tw = max(tmpd.textlength(l, font=f) for l in lines)
    bw = int((tw if el.get("pill") else el.get("w", 936)) + 2 * pad[0]); bh = lh * len(lines) + 2 * pad[1] + int(size * 0.25)
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    if el.get("pill"):
        bg = el["pill"]; a = 255
        if len(bg) == 9: a = int(bg[7:9], 16); bg = bg[:7]
        d.rounded_rectangle([0, 0, bw - 1, bh - 1], min(el.get("radius", 999), bh // 2), fill=hexrgb(bg, a))
    col = hexrgb(el.get("color", "#FFFFFF"))
    y = pad[1]
    for l in lines:
        lw = d.textlength(l, font=f)
        al = el.get("align", "left")
        x = pad[0] if al == "left" or el.get("pill") else ((bw - lw) / 2 if al == "center" else bw - pad[0] - lw)
        if el.get("shadow", True) and not el.get("pill"):
            d.text((x + 2, y + 3), l, font=f, fill=(0, 0, 0, 110))
        d.text((x, y), l, font=f, fill=col); y += lh
    img.save(path)
    return bw, bh

def scrim_png(color, path, top=700):
    r, g, b, _ = hexrgb(color)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = img.load()
    for yy in range(H):
        if yy < top: a = 0
        else:
            t = (yy - top) / (H - top); a = int(255 * min(0.97, 0.15 + 1.6 * t) if t < 0.5 else 255 * min(0.97, 0.82 + 0.3 * (t - 0.5)))
        for xx in range(W): px[xx, yy] = (r, g, b, a)
    # top fade for logo legibility
    for yy in range(0, 320):
        a = int(110 * (1 - yy / 320))
        for xx in range(W):
            pr, pg, pb, pa = px[xx, yy]; px[xx, yy] = (r, g, b, max(pa, a))
    img.save(path)

def render_scene(sc, i, tmp, scrim):
    photo = fetch(sc["photo"], tmp, f"p{i}.jpg")
    dur = float(sc["dur"]); frames = int(dur * FPS); pan = sc.get("pan", 1 if i % 2 == 0 else -1)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", f"{dur}", "-i", photo, "-loop", "1", "-t", f"{dur}", "-i", scrim]
    els = []; last_bottom = None
    for j, el in enumerate(sc.get("elements", [])):
        p = os.path.join(tmp, f"e{i}_{j}.png"); bw, bh = element_png(el, p)
        if (el.get("y") in (None, "auto")) and last_bottom is not None:
            el = dict(el, y=last_bottom + int(el.get("gap", 28)))
        last_bottom = int(el.get("y", 1000)) + bh
        cmd += ["-loop", "1", "-t", f"{dur}", "-i", p]; els.append((el, bw, bh))
    zx = f"(iw-iw/zoom)/2+{pan}*(iw-iw/zoom)/2*on/{frames}"
    fc = [f"[0:v]scale={int(W*1.25)}:{int(H*1.25)}:force_original_aspect_ratio=increase,crop={int(W*1.25)}:{int(H*1.25)},"
          f"zoompan=z='1+0.09*on/{frames}':x='{zx}':y='(ih-ih/zoom)/2':d={frames}:s={W}x{H}:fps={FPS},setsar=1,format=rgba[bg]",
          "[bg][1:v]overlay=0:0[s0]"]
    prev = "s0"
    for j, (el, bw, bh) in enumerate(els):
        at = float(el.get("at", 0.3)); anim = el.get("anim", "up")
        fade = f",fade=t=in:st={at}:d=0.45:alpha=1" if anim != "none" else ""
        fc.append(f"[{j+2}:v]format=rgba{fade}[f{j}]")
        x = int(el.get("x", 72)); y = int(el.get("y", 1000))
        yexpr = f"{y}+50*max(0\\,1-(t-{at})/0.45)" if anim == "up" else f"{y}"
        fc.append(f"[{prev}][f{j}]overlay=x={x}:y='{yexpr}':eval=frame[s{j+1}]"); prev = f"s{j+1}"
    fc.append(f"[{prev}]format=yuv420p[out]")
    out = os.path.join(tmp, f"scene{i}.mp4")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[out]", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-t", f"{dur}", out]
    subprocess.run(cmd, check=True)
    return out, dur

def main(job_path):
    job = json.load(open(job_path)); tmp = tempfile.mkdtemp()
    scrim = os.path.join(tmp, "scrim.png"); scrim_png(job.get("scrim", "#010923"), scrim, job.get("scrim_top", 700))
    parts = [render_scene(sc, i, tmp, scrim) for i, sc in enumerate(job["scenes"])]
    tr = float(job.get("transition", 0.8))
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p, _ in parts: cmd += ["-i", p]
    fc, prev, off = [], "[0:v]", 0.0
    for k in range(1, len(parts)):
        off += parts[k-1][1] - tr
        fc.append(f"{prev}[{k}:v]xfade=transition={job.get('xfade', 'slideup')}:duration={tr}:offset={off:.3f}[x{k}]"); prev = f"[x{k}]"
    total = sum(d for _, d in parts) - tr * (len(parts) - 1)
    lg = job.get("logo"); idx = len(parts)
    if lg:
        lp = fetch(lg["src"], tmp, "logo.png"); im = Image.open(lp).convert("RGBA").resize((lg["w"], lg["h"]), Image.LANCZOS)
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.size[0]-1, im.size[1]-1], lg.get("radius", 24), fill=255)
        im.putalpha(m); im.save(os.path.join(tmp, "logo_r.png"))
        cmd += ["-loop", "1", "-t", f"{total}", "-i", os.path.join(tmp, "logo_r.png")]
        fc.append(f"{prev}[{idx}:v]overlay={lg['x']}:{lg['y']}[vl]"); prev = "[vl]"; idx += 1
    fc.append(f"{prev}format=yuv420p[v]")
    amap = []
    if job.get("voice"):
        vp = fetch(job["voice"], tmp, "voice" + os.path.splitext(job["voice"].split("?")[0])[1])
        cmd += ["-i", vp]; vi = idx; idx += 1
        fc.append(f"[{vi}:a]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{total:.2f},volume=1.0[vo]")
    if job.get("music"):
        mp = fetch(job["music"]["src"], tmp, "music" + os.path.splitext(job["music"]["src"].split("?")[0])[1])
        cmd += ["-stream_loop", "-1", "-i", mp]; mi = idx; idx += 1
        mv = job["music"].get("volume", 0.15)
        fc.append(f"[{mi}:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:{total:.2f},volume={mv},afade=t=in:d=0.3,afade=t=out:st={total-1.5:.2f}:d=1.5[mu]")
    if job.get("voice") and job.get("music"):
        fc.append("[vo]asplit=2[vk][vm]")
        fc.append("[mu][vk]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[duck]")
        fc.append("[duck][vm]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]"); amap = ["-map", "[a]"]
    elif job.get("voice"): amap = ["-map", "[vo]"]
    elif job.get("music"): amap = ["-map", "[mu]"]
    out = job["out"] if job["out"].startswith("/") else os.path.join(ROOT, job["out"]); os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]"] + amap + ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(out, round(total, 2), "s")

if __name__ == "__main__":
    for jp in sys.argv[1:]: main(jp)
