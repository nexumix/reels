#!/usr/bin/env python3
"""Ücretsiz seslendirme: Google Cloud Text-to-Speech (aylık 1M karakter Chirp 3 HD ücretsiz).
GitHub Actions'ta GOOGLE_TTS_KEY secret'ı ile çalışır. Job alanı:
 "tts": {"lang": "tr-TR" | "en-US", "gender": "MALE"|"FEMALE", "voice": "<opsiyonel tam ad>",
         "rate": 1.0, "lines": ["sahne 1 konuşma", "sahne 2", ...]}   (lines sayısı = sahne sayısı)
Sahne süreleri seslendirmeye göre otomatik uzatılır; karışık ses loudnorm I=-14 ile normalize edilir."""
import base64, json, os, re, subprocess, urllib.request, urllib.error

# TELAFFUZ (kullanıcı 23.11: "kısaltmaları yanlış okuyorlar, tek parça okumalı: NACE, DASK gibi")
# Kelime gibi okunan kısaltmalar TEK PARÇA yazılır (büyük harf TTS'te harf harf okunuyor).
# Harf harf okunması gereken yerleşik kısaltmalar Türkçe harf adlarıyla yazılır.
# Job'da "tts": {"say": {"XYZ": "okunuş"}} ile ek/özel okunuş verilebilir.
SAY = {
    "tr-TR": {"NACE": "Nase", "DASK": "Dask", "KOSGEB": "Kosgeb", "TÜİK": "Tüik", "TÜFE": "Tüfe", "ÜFE": "Üfe",
              "KOBİ": "Kobi", "KOBİ'ler": "Kobiler", "ISO": "İso", "İSO": "İso", "HIT": "Hit", "EnPI": "Enpi",
              "İSG-KÂTİP": "i se ge kâtip", "İSGGM": "i se ge ge me", "ÇSGB": "çe se ge be", "İSG": "i se ge", "OSGB": "o se ge be", "SGK": "se ge ka",
              "KVKK": "ka ve ka ka", "SPK": "se pe ka", "AB": "a be", "CE": "se e", "TL": "te le"},
    "en-US": {"NACE": "Nace", "DASK": "Dask", "KOSGEB": "Kosgeb", "TÜİK": "Tooik", "İSG": "OHS"},
}
_L = "A-Za-zÇĞİÖŞÜçğıöşü"

def say(text, lang, extra=None):
    m = dict(SAY.get(lang, {})); m.update(extra or {})
    for k in sorted(m, key=len, reverse=True):
        text = re.sub(rf"(?<![{_L}]){re.escape(k)}(?![{_L}])", m[k], text)
    return text

API = "https://texttospeech.googleapis.com/v1"
PREF = ["Chirp3-HD", "Neural2", "Wavenet", "Standard"]

def _req(url, body=None, tries=8):
    data = json.dumps(body).encode() if body is not None else None
    for k in range(tries):
        r = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=60) as resp: return json.load(resp)
        except urllib.error.HTTPError as e:   # 429/5xx: paralel işlerde kota; bekleyip tekrar dene
            if e.code not in (429, 500, 502, 503) or k == tries - 1: raise
            import time, random; time.sleep(min(60, 4 * 2 ** k) + random.random() * 3)

def pick_voice(key, lang, gender, wanted=None):
    vs = _req(f"{API}/voices?languageCode={lang}&key={key}").get("voices", [])
    names = [v["name"] for v in vs]
    if wanted and wanted in names: return wanted
    for p in PREF:
        c = sorted(v["name"] for v in vs if p in v["name"] and (not gender or v.get("ssmlGender") == gender))
        if c: return c[0]
    return names[0] if names else None

def _dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def build_voice(job, tmp):
    t = job.get("tts"); key = os.environ.get("GOOGLE_TTS_KEY")
    if not t or not key: return None
    lang = t.get("lang", "tr-TR"); voice = pick_voice(key, lang, t.get("gender"), t.get("voice"))
    if not voice: return None
    print("TTS voice:", voice)
    rate = float(t.get("rate", 1.0)); lens = []
    for i, line in enumerate(t["lines"]):
        line = say(line, lang, t.get("say")); print("TTS line:", line)
        body = {"input": {"text": line}, "voice": {"languageCode": lang, "name": voice},
                "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 44100, "speakingRate": rate}}
        if "Chirp3" in voice: body["audioConfig"].pop("speakingRate")  # Chirp 3 HD hız ayarını desteklemeyebilir
        a = _req(f"{API}/text:synthesize?key={key}", body)
        raw = os.path.join(tmp, f"tts{i}.wav"); open(raw, "wb").write(base64.b64decode(a["audioContent"]))
        out = os.path.join(tmp, f"tts{i}t.wav")
        af = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
        if "Chirp3" in voice and rate != 1.0: af += f",atempo={rate}"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", af, "-ar", "44100", "-ac", "1", out], check=True)
        lens.append(_dur(out))
    tr = float(job.get("transition", 1.0)); sc = job["scenes"]
    for i, l in enumerate(lens):
        if i < len(sc): sc[i]["dur"] = round(max(float(sc[i].get("dur", 3.4)), l + 1.25 + (0.6 if i == len(sc) - 1 else 0)), 2)
    starts, s = [], 0.0
    for x in sc: starts.append(s); s += float(x["dur"]) - tr
    ins, fc = [], []
    for i in range(len(lens)):
        ins += ["-i", os.path.join(tmp, f"tts{i}t.wav")]; fc.append(f"[{i}]adelay={int((starts[i] + 0.4) * 1000)}[a{i}]")
    fc.append("".join(f"[a{i}]" for i in range(len(lens))) + f"amix=inputs={len(lens)}:normalize=0[m]")
    mix = os.path.join(tmp, "tts_mix.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + ins + ["-filter_complex", ";".join(fc), "-map", "[m]", mix], check=True)
    norm = os.path.join(tmp, "tts_norm.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mix, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", norm], check=True)
    # ikinci geçiş: seyrek konuşmada loudnorm hedefi tutturamayabiliyor → ölç, farkı gain ile düzelt
    m = subprocess.run(["ffmpeg", "-i", norm, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    try:
        v = float(json.loads(m[m.rindex("{"):m.rindex("}") + 1])["input_i"])
        if not -15 < v < -13:
            fixed = os.path.join(tmp, "tts_norm2.wav")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", norm, "-af", f"volume={-14 - v}dB,alimiter=limit=0.85", fixed], check=True); norm = fixed
    except Exception as e: print("loudness check skipped:", e)
    print("TTS durs:", [x["dur"] for x in sc])
    return norm
