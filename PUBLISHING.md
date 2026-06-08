# Публикация в ComfyUI Registry

Шпаргалка (повторяет рабочую схему Preset Download Manager).

## Один раз

1. **Создать репозиторий** на GitHub: `Smyshnikof/comfyui-hotcut`, запушить код:
   ```bash
   git remote add origin https://github.com/Smyshnikof/comfyui-hotcut.git
   git push -u origin main
   ```
   > Ветка должна называться `main` (Icon-URL и workflow завязаны на `main`).

2. **Publisher + токен** на https://registry.comfy.org:
   - залогиниться, создать/подтвердить Publisher с ID `smyshnikof` (совпадает с `pyproject.toml` → `[tool.comfy] PublisherId`);
   - создать **API key** (Personal Access Token) реестра.

3. **Секрет в GitHub:** репозиторий → Settings → Secrets and variables → Actions →
   `New repository secret` → имя `REGISTRY_ACCESS_TOKEN`, значение = токен реестра.

## Каждая публикация

1. Поднять версию в `pyproject.toml` (`version = "0.1.1"` и т.д.).
2. Запушить в `main` — workflow `Publish to Comfy registry` сработает автоматически
   (триггер на изменение `pyproject.toml`), либо запустить вручную:
   GitHub → Actions → *Publish to Comfy registry* → **Run workflow**.

## Чек перед публикацией

- [ ] `pyproject.toml`: `name`, `PublisherId=smyshnikof`, `DisplayName=HOTCUT`, `Icon` (raw URL на `icon.png` в `main`), `Repository`.
- [ ] `icon.png` в корне (квадрат, ~400×400).
- [ ] `__init__.py`: `NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`, `WEB_DIRECTORY="./web"`.
- [ ] `requirements.txt` актуален.
- [ ] В коде/доках **не светится провайдер** (это моат) — проверить `grep`.
- [ ] Проверено в локальном ComfyUI: ноды грузятся, генерация и баланс работают.
