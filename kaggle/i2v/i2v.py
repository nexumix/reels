# Kaggle GPU: fotoğraftan kısa yapay zeka video klip (image-to-video) — LTX-Video
import subprocess, sys, json, os, urllib.request, time, traceback
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.33", "transformers", "accelerate", "sentencepiece", "imageio[ffmpeg]"], check=True)
import torch
from diffusers import LTXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
from PIL import Image
QUEUE = "https://raw.githubusercontent.com/nexumix/reels/main/clips/queue.json"
OUT = "/kaggle/working"
jobs = json.load(urllib.request.urlopen(QUEUE, timeout=60))
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none", "| jobs:", len(jobs), flush=True)
pipe = LTXImageToVideoPipeline.from_pretrained("Lightricks/LTX-Video", torch_dtype=torch.float16)
pipe.enable_model_cpu_offload()
try: pipe.vae.enable_tiling()
except Exception: pass
NEG = "worst quality, inconsistent motion, blurry, jittery, distorted, deformed, text, watermark"
log = []
for j in jobs:
    t0 = time.time()
    try:
        img = load_image(j["image_url"]).convert("RGB")
        W, H = j.get("width", 512), j.get("height", 768)
        # fotoğrafı hedef orana kırp (merkez)
        r = W / H
        if img.width / img.height > r:
            nw = int(img.height * r); x = (img.width - nw) // 2; img = img.crop((x, 0, x + nw, img.height))
        else:
            nh = int(img.width / r); y = (img.height - nh) // 2; img = img.crop((0, y, img.width, y + nh))
        img = img.resize((W, H), Image.LANCZOS)
        frames = pipe(image=img, prompt=j["prompt"], negative_prompt=NEG, width=W, height=H,
                      num_frames=j.get("frames", 97), num_inference_steps=j.get("steps", 30),
                      generator=torch.Generator("cpu").manual_seed(j.get("seed", 42))).frames[0]
        export_to_video(frames, os.path.join(OUT, j["id"] + ".mp4"), fps=24)
        log.append({"id": j["id"], "ok": True, "sec": round(time.time() - t0)})
    except Exception as e:
        traceback.print_exc(); log.append({"id": j["id"], "ok": False, "err": str(e)[:300]})
    print(log[-1], flush=True)
    torch.cuda.empty_cache()
json.dump(log, open(os.path.join(OUT, "log.json"), "w"), indent=1)
