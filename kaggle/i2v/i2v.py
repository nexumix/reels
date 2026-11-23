# Kaggle GPU: fotoğraftan yapay zeka video klip (image-to-video) — LTX-Video, v2 (daha güçlü hareket)
import subprocess, sys, json, os, urllib.request, time, traceback, gc
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.33", "transformers<5", "accelerate", "sentencepiece", "imageio[ffmpeg]"], check=True)
import torch
from diffusers import LTXImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
from PIL import Image
QUEUE = "https://raw.githubusercontent.com/nexumix/reels/main/clips/queue.json"
OUT = "/kaggle/working"
jobs = json.load(urllib.request.urlopen(QUEUE, timeout=60))
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none", "| jobs:", len(jobs), flush=True)
NEG = "worst quality, static, frozen, still image, inconsistent motion, blurry, jittery, distorted, deformed, morphing, text, watermark"
pipes = {}
def get_pipe(name):
    if name in pipes: return pipes[name]
    for k in list(pipes):
        try: pipes[k].remove_all_hooks()
        except Exception: pass
        del pipes[k]
    gc.collect(); torch.cuda.empty_cache()
    from transformers import T5EncoderModel
    te = T5EncoderModel.from_pretrained(name, subfolder="text_encoder", torch_dtype=torch.float16, low_cpu_mem_usage=True)
    gc.collect()
    p = LTXImageToVideoPipeline.from_pretrained(name, text_encoder=te, torch_dtype=torch.float16, low_cpu_mem_usage=True)
    p.enable_model_cpu_offload()
    try: p.vae.enable_tiling()
    except Exception: pass
    pipes[name] = p; return p
def fit(img, W, H):
    r = W / H
    if img.width / img.height > r:
        nw = int(img.height * r); x = (img.width - nw) // 2; img = img.crop((x, 0, x + nw, img.height))
    else:
        nh = int(img.width / r); y = (img.height - nh) // 2; img = img.crop((0, y, img.width, y + nh))
    return img.resize((W, H), Image.LANCZOS)
log = []
for j in jobs:
    t0 = time.time(); model = j.get("model", "Lightricks/LTX-Video")
    try:
        pipe = None; gc.collect()
        pipe = get_pipe(model)
        W, H = j.get("width", 544), j.get("height", 960)
        img = fit(load_image(j["image_url"]).convert("RGB"), W, H)
        kw = dict(image=img, prompt=j["prompt"], negative_prompt=NEG, width=W, height=H,
                  num_frames=j.get("frames", 121), num_inference_steps=j.get("steps", 40),
                  guidance_scale=j.get("guidance", 3.5),
                  generator=torch.Generator("cpu").manual_seed(j.get("seed", 7)))
        for extra in ("decode_timestep", "decode_noise_scale"):
            if extra in j: kw[extra] = j[extra]
        frames = pipe(**kw).frames[0]
        export_to_video(frames, os.path.join(OUT, j["id"] + ".mp4"), fps=24)
        log.append({"id": j["id"], "model": model, "ok": True, "sec": round(time.time() - t0)})
    except Exception as e:
        traceback.print_exc(); log.append({"id": j["id"], "model": model, "ok": False, "err": str(e)[:300]})
    print(log[-1], flush=True)
    json.dump(log, open(os.path.join(OUT, "log.json"), "w"), indent=1)
    gc.collect(); torch.cuda.empty_cache()
json.dump(log, open(os.path.join(OUT, "log.json"), "w"), indent=1)
