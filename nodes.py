"""Ноды HOTCUT для ComfyUI.

- HOTCUT API            — конфиг (ключ + базовый URL), отдаёт HOTCUT_CONFIG
- HOTCUT · GPT Image 2       — text-to-image  → IMAGE
- HOTCUT · GPT Image 2 Edit  — image-to-image (вход IMAGE) → IMAGE

Wedge GPT Image 2: чёткий текст/кириллица/лица — то, что локальные модели
делают плохо. Edit-нода берёт IMAGE на вход → композиция local+cloud в графе.
Оплата — огнями HOTCUT (те же, что на сайте).
"""

import io
import os

import numpy as np
import torch
from PIL import Image

from .hotcut_client import HotcutClient

RESOLUTIONS = ["1K", "2K", "4K"]
# Цена зависит ТОЛЬКО от resolution. Ограничения провайдера (нормализуются на сервере):
# 1:1 → не выше 2K; auto → только 1K.
ASPECTS = ["auto", "1:1", "5:4", "9:16", "21:9", "16:9", "4:3", "3:2", "4:5", "3:4", "2:3"]
# Верхний потолок ожидания результата (сек). Картинки готовятся за секунды —
# наружу как виджет не выносим. Защита от вечного зависания при сбое сервиса.
POLL_MAX_WAIT = 300


def _resolve_key(api_key):
    key = (api_key or "").strip()
    if not key or key == "$ENV":
        key = os.environ.get("HOTCUT_API_KEY", "").strip()
    return key


def _bytes_to_image_tensor(raw):
    """PNG/JPEG bytes → ComfyUI IMAGE-тензор [1, H, W, 3] float 0..1."""
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None,]


def _image_tensor_to_png_bytes(image):
    """ComfyUI IMAGE [B, H, W, C] float 0..1 → PNG bytes (берём первый кадр)."""
    arr = image[0].detach().cpu().numpy()
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, format="PNG")
    return buf.getvalue()


class HotcutConfig:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # "$ENV" → ключ берётся из переменной окружения HOTCUT_API_KEY
                # (чтобы не утёк в сохранённый workflow.json)
                "api_key": ("STRING", {"default": "$ENV", "multiline": False}),
                "base_url": ("STRING", {"default": "https://hotcut.ru"}),
            }
        }

    RETURN_TYPES = ("HOTCUT_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "build"
    CATEGORY = "HOTCUT"

    def build(self, api_key, base_url):
        return ({"api_key": _resolve_key(api_key), "base_url": base_url},)


class HotcutGptImage2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("HOTCUT_CONFIG",),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "resolution": (RESOLUTIONS,),
                "aspect_ratio": (ASPECTS,),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate"
    CATEGORY = "HOTCUT"

    def generate(self, config, prompt, resolution, aspect_ratio):
        client = HotcutClient(config["api_key"], config["base_url"])
        task_id, cost = client.submit_image(prompt, resolution, aspect_ratio, mode="text-to-image")
        if cost is not None:
            print(f"[HOTCUT] GPT Image 2: задача {task_id}, спишется ~{cost} огней")
        urls = client.poll_image(task_id, max_wait=POLL_MAX_WAIT)
        return (_bytes_to_image_tensor(client.download(urls[0])),)


class HotcutGptImage2Edit:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("HOTCUT_CONFIG",),
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "resolution": (RESOLUTIONS,),
                "aspect_ratio": (ASPECTS,),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate"
    CATEGORY = "HOTCUT"

    def generate(self, config, image, prompt, resolution, aspect_ratio):
        client = HotcutClient(config["api_key"], config["base_url"])
        url = client.upload_image(_image_tensor_to_png_bytes(image))
        task_id, cost = client.submit_image(
            prompt, resolution, aspect_ratio, mode="image-to-image", input_urls=[url]
        )
        if cost is not None:
            print(f"[HOTCUT] GPT Image 2 Edit: задача {task_id}, спишется ~{cost} огней")
        urls = client.poll_image(task_id, max_wait=POLL_MAX_WAIT)
        return (_bytes_to_image_tensor(client.download(urls[0])),)
