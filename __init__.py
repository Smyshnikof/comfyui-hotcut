"""ComfyUI HOTCUT — облачные модели изображений (GPT Image 2) с оплатой огнями HOTCUT."""

from .nodes import (
    HotcutConfig,
    HotcutGptImage2,
    HotcutGptImage2Edit,
    HotcutRemoveBackground,
    HotcutBalance,
)

NODE_CLASS_MAPPINGS = {
    "HotcutConfig": HotcutConfig,
    "HotcutGptImage2": HotcutGptImage2,
    "HotcutGptImage2Edit": HotcutGptImage2Edit,
    "HotcutRemoveBackground": HotcutRemoveBackground,
    "HotcutBalance": HotcutBalance,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HotcutConfig": "HOTCUT API",
    "HotcutGptImage2": "HOTCUT · GPT Image 2",
    "HotcutGptImage2Edit": "HOTCUT · GPT Image 2 Edit",
    "HotcutRemoveBackground": "HOTCUT · Удалить фон",
    "HotcutBalance": "HOTCUT · Баланс",
}

# Фронтовое расширение (фирменный вид нод) — папка web/
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
