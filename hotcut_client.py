"""HTTP-клиент HOTCUT API для нод ComfyUI.

Две ручки публичного API:
  POST /api/v1/images          — постановка задачи (GPT Image 2 t2i / i2i)
  GET  /api/v1/images/:task_id — статус и результат
  POST /api/v1/uploads         — загрузка картинки для image-to-image (отдаёт url)

Авторизация: Authorization: Bearer hc_live_...
"""

import io
import time

import requests

DEFAULT_BASE_URL = "https://hotcut.ru"


class HotcutError(Exception):
    """Понятная ошибка для отображения в ComfyUI."""


class HotcutClient:
    def __init__(self, api_key, base_url=DEFAULT_BASE_URL, timeout=60.0):
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or DEFAULT_BASE_URL).strip().rstrip("/")
        self.timeout = timeout
        if not self.api_key:
            raise HotcutError(
                "API-ключ пуст. Укажите hc_live_... в ноде «HOTCUT API» "
                "или переменную окружения HOTCUT_API_KEY."
            )

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def _submit(self, body):
        """POST /api/v1/images. Возвращает (task_id, cost_flames|None)."""
        resp = requests.post(
            f"{self.base_url}/api/v1/images",
            json=body,
            headers={**self._headers(), "Content-Type": "application/json"},
            timeout=self.timeout,
        )
        data = self._json(resp)
        if resp.status_code not in (200, 202):
            raise HotcutError(self._msg(data, resp))
        task_id = data.get("task_id")
        if not task_id:
            raise HotcutError("Сервис не вернул task_id.")
        return task_id, data.get("cost_flames")

    def submit_image(
        self,
        prompt,
        resolution="1K",
        aspect_ratio="auto",
        mode="text-to-image",
        input_urls=None,
        nsfw_checker=None,
    ):
        """GPT Image 2. Возвращает (task_id, cost_flames|None)."""
        body = {
            "model": "gpt-image-2",
            "mode": mode,
            "prompt": prompt,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
        }
        if input_urls:
            body["input_urls"] = input_urls
        # GPT Image 2 модерируется провайдером всегда — тумблера нет, не шлём.
        if nsfw_checker is not None:
            body["nsfw_checker"] = bool(nsfw_checker)
        return self._submit(body)

    def remove_background(self, input_urls):
        """Удаление фона. Возвращает (task_id, cost_flames|None)."""
        return self._submit({"model": "remove-background", "input_urls": input_urls})

    def balance(self):
        """Доступный остаток огней (GET /api/v1/me)."""
        resp = requests.get(
            f"{self.base_url}/api/v1/me",
            headers=self._headers(),
            timeout=self.timeout,
        )
        data = self._json(resp)
        if resp.status_code != 200:
            raise HotcutError(self._msg(data, resp))
        return int(data.get("flames", 0) or 0)

    def poll_image(self, task_id, max_wait=300.0, interval=2.0):
        """Ждёт результат, возвращает список URL. Бросает HotcutError на fail/timeout."""
        deadline = time.time() + max_wait
        while time.time() < deadline:
            resp = requests.get(
                f"{self.base_url}/api/v1/images/{task_id}",
                headers=self._headers(),
                timeout=self.timeout,
            )
            data = self._json(resp)
            if resp.status_code != 200:
                raise HotcutError(self._msg(data, resp))
            state = data.get("state")
            if state == "success":
                urls = data.get("result_urls") or []
                if not urls:
                    raise HotcutError("Пустой результат генерации.")
                return urls
            if state == "fail":
                raise HotcutError(data.get("error") or "Генерация не удалась.")
            time.sleep(interval)
        raise HotcutError("Истекло время ожидания генерации.")

    def upload_image(self, png_bytes, filename="input.png"):
        """Загружает картинку, возвращает временный URL для input_urls."""
        files = {"file": (filename, io.BytesIO(png_bytes), "image/png")}
        resp = requests.post(
            f"{self.base_url}/api/v1/uploads",
            files=files,
            headers=self._headers(),
            timeout=max(self.timeout, 120),
        )
        data = self._json(resp)
        if resp.status_code not in (200, 201):
            raise HotcutError(self._msg(data, resp))
        url = data.get("url")
        if not url:
            raise HotcutError("Загрузка не вернула url.")
        return url

    def download(self, url):
        resp = requests.get(url, timeout=max(self.timeout, 120))
        if resp.status_code != 200:
            raise HotcutError(f"Не удалось скачать результат: HTTP {resp.status_code}")
        return resp.content

    @staticmethod
    def _json(resp):
        try:
            return resp.json()
        except Exception:
            return {}

    @staticmethod
    def _msg(data, resp):
        if isinstance(data, dict):
            if data.get("message"):
                return str(data["message"])
            if data.get("error"):
                return str(data["error"])
        return f"HTTP {resp.status_code}"
