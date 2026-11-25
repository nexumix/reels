#!/usr/bin/env python3
"""Ders JSON doğrulayıcı: şema, metin uzunlukları, adım sayıları, kelime hedefi. Kullanım: python3 tools/lesson_check.py lessons/az8_g1.json [...]"""
import json, re, sys
TARGET = {"g": 1350, "s": 1080, "t": 900, "o": 1350}
LIM = {"title1": 46, "title2": 64, "bullet": 92, "pbullet": 62}
def main(p):
    j = json.load(open(p, encoding="utf-8")); err = []; words = 0
    for k in ("code", "course", "section", "title", "voice", "scenes"):
        if k not in j: err.append(f"eksik alan: {k}")
    for i, sc in enumerate(j.get("scenes", [])):
        t = sc.get("type"); st = sc.get("steps", []); n = f"sahne {i + 1} ({t})"
        if not st: err.append(f"{n}: steps boş")
        words += sum(len(s.split()) for s in st)
        for s in st:
            if len(s.split()) > 75: err.append(f"{n}: çok uzun adım ({len(s.split())} kelime)")
        need_photo = t in ("cover", "split_photo", "photo", "fact")
        if t in ("cover", "photo", "fact") and not sc.get("photo"): err.append(f"{n}: photo gerekli")
        for key in ("photo",):
            if sc.get(key) and not re.match(r"^https://images\.unsplash\.com/photo-[\w-]+\?w=\d+$", sc[key]): err.append(f"{n}: photo URL biçimi")
        tl = len(sc.get("title", ""))
        if t in ("stats", "cards", "roles", "process", "dodont", "photo") and tl > LIM["title1"]: err.append(f"{n}: başlık > {LIM['title1']} ({tl})")
        if t in ("split", "check", "cover") and tl > LIM["title2"]: err.append(f"{n}: başlık > {LIM['title2']} ({tl})")
        if t == "fact" and tl > 120: err.append(f"{n}: başlık > 120")
        bl = sc.get("bullets", []); it = sc.get("items", [])
        if t == "split":
            if not 2 <= len(bl) <= 5: err.append(f"{n}: 2-5 madde")
            if len(st) < len(bl) + 1: err.append(f"{n}: steps >= madde+1 olmalı")
        if t == "check":
            if not 2 <= len(bl) <= 5: err.append(f"{n}: 2-5 madde")
            if len(st) < len(bl) + 1: err.append(f"{n}: steps >= madde+1")
        if t == "photo":
            if len(bl) > 3: err.append(f"{n}: en çok 3 madde")
            if len(st) < len(bl) + 1: err.append(f"{n}: steps >= madde+1")
            for b in bl:
                if len(b) > LIM["pbullet"]: err.append(f"{n}: madde > {LIM['pbullet']}: {b}")
        else:
            for b in bl:
                if len(b) > LIM["bullet"]: err.append(f"{n}: madde > {LIM['bullet']}: {b}")
        if t == "fact":
            if len(st) < 2: err.append(f"{n}: en az 2 adım")
            if len(sc.get("value", "")) > 10: err.append(f"{n}: value > 10")
            if len(sc.get("text", "")) > 160: err.append(f"{n}: text > 160")
        lim = {"stats": (2, 4), "cards": (3, 3), "roles": (3, 3), "process": (3, 5), "dodont": (2, 2)}.get(t)
        if lim:
            if not lim[0] <= len(it) <= lim[1]: err.append(f"{n}: öğe sayısı {lim}")
            if len(st) < len(it) + 1: err.append(f"{n}: steps >= öğe+1")
            for x in it:
                if t in ("cards", "roles", "dodont") and not re.match(r"^https://images\.unsplash\.com/photo-[\w-]+\?w=\d+$", x.get("photo", "")): err.append(f"{n}: öğe photo URL")
                if t == "stats" and len(x.get("value", "")) > 6: err.append(f"{n}: stats value > 6")
                if t == "process" and (len(x.get("title", "")) > 24 or len(x.get("text", "")) > 80): err.append(f"{n}: process öğe uzun")
                if t in ("cards", "roles", "dodont") and (len(x.get("title", "")) > 26 or len(x.get("text", "")) > 110): err.append(f"{n}: öğe başlık<=26 / metin<=110")
        if t not in ("cover", "split", "stats", "cards", "roles", "check", "photo", "fact", "process", "dodont"): err.append(f"{n}: bilinmeyen tür")
    code = j.get("code", ""); m = re.match(r"az8_([gsto])\d", code); est = words / 2.02
    tgt = TARGET[m.group(1)] if m else (1350 if re.match(r"tc_[gst]\d", code) else 0)
    print(f"{p}: {len(j.get('scenes', []))} sahne, {words} kelime, tahmini {est / 60:.1f} dk" + (f" (hedef {tgt / 60:.1f} dk, gereken kelime >= {int(tgt * 2.02 * 1.03)})" if tgt else ""))
    if tgt and est < tgt * 1.03: err.append(f"süre kısa: {int(tgt * 2.02 * 1.03) - words} kelime daha gerekli")
    photos = sum(1 for sc in j["scenes"] if sc.get("photo") or any(x.get("photo") for x in sc.get("items", [])))
    print(f"  fotoğraflı sahne: {photos}/{len(j['scenes'])}")
    for e in err: print("  HATA:", e)
    return not err
if __name__ == "__main__":
    ok = all([main(p) for p in sys.argv[1:]]); sys.exit(0 if ok else 1)
