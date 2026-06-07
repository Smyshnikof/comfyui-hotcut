"""ComfyUI HOTCUT — облачные модели изображений (GPT Image 2, удаление фона) с оплатой огнями HOTCUT."""

from .nodes import (
    HotcutConfig,
    HotcutGptImage2,
    HotcutGptImage2Edit,
    HotcutRemoveBackground,
)

NODE_CLASS_MAPPINGS = {
    "HotcutConfig": HotcutConfig,
    "HotcutGptImage2": HotcutGptImage2,
    "HotcutGptImage2Edit": HotcutGptImage2Edit,
    "HotcutRemoveBackground": HotcutRemoveBackground,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HotcutConfig": "HOTCUT API",
    "HotcutGptImage2": "HOTCUT · GPT Image 2",
    "HotcutGptImage2Edit": "HOTCUT · GPT Image 2 Edit",
    "HotcutRemoveBackground": "HOTCUT · Удалить фон",
}

# Фронтовое расширение (фирменный вид нод + кнопка баланса) — папка web/
WEB_DIRECTORY = "./web"

# Локальный роут ComfyUI для кнопки «Проверить баланс»: фронт бьёт сюда (тот же
# origin → без CORS), а мы уже server-side зовём HOTCUT. Регистрируем мягко —
# если API ComfyUI отличается, ноды всё равно загрузятся.
try:
    import asyncio
    from aiohttp import web
    from server import PromptServer  # type: ignore
    from .hotcut_client import HotcutClient, HotcutError
    from .nodes import _resolve_key

    @PromptServer.instance.routes.post("/hotcut/balance")
    async def _hotcut_balance(request):
        try:
            data = await request.json()
        except Exception:
            data = {}
        key = _resolve_key(data.get("api_key", ""))
        base = (data.get("base_url") or "https://hotcut.ru").strip()
        try:
            client = HotcutClient(key, base)
            flames = await asyncio.to_thread(client.balance)
            return web.json_response({"flames": flames})
        except HotcutError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:  # noqa: BLE001
            return web.json_response({"error": str(e)}, status=500)
except Exception as e:  # noqa: BLE001
    print(f"[HOTCUT] route /hotcut/balance не зарегистрирован: {e}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
