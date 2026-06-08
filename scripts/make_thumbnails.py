# -*- coding: utf-8 -*-
"""Генерирует брендовые превью (.jpg) для воркфлоу-шаблонов HOTCUT.
Кладёт их рядом с одноимёнными .json в example_workflows/ — ComfyUI показывает
их как миниатюры в Workflow → Browse Templates."""
import os
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "example_workflows")

W, H = 640, 360
BG = (14, 14, 16)          # #0e0e10
GRID = (26, 22, 20)
CARD = (20, 20, 20)        # #141414
CARD_BORDER = (42, 38, 36)
HEADER = (90, 36, 16)      # #5a2410 бёрнт-оранж
ACCENT = (255, 107, 53)    # #ff6b35
WHITE = (245, 245, 245)
GREY = (154, 154, 154)

A_BD = "C:/Windows/Fonts/arialbd.ttf"
A_RG = "C:/Windows/Fonts/arial.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def center(d, text, fnt, cx, y, fill):
    w = d.textlength(text, font=fnt)
    d.text((cx - w / 2, y), text, font=fnt, fill=fill)


def card(d, x, y, w, h, label, fnt):
    d.rounded_rectangle((x, y, x + w, y + h), radius=9, fill=CARD, outline=CARD_BORDER, width=1)
    d.rounded_rectangle((x, y, x + w, y + 22), radius=9, fill=HEADER)
    d.rectangle((x, y + 12, x + w, y + 22), fill=HEADER)
    d.ellipse((x + 8, y + 7, x + 16, y + 15), fill=ACCENT)
    center(d, label, fnt, x + w / 2, y + 34, WHITE)


def connector(d, x1, y, x2):
    midx = (x1 + x2) / 2
    pts = []
    for i in range(21):
        t = i / 20
        # квадратичная кривая для лёгкого изгиба
        bx = (1 - t) * x1 + t * x2
        pts.append((bx, y))
    d.line(pts, fill=ACCENT, width=2)
    d.ellipse((x1 - 3, y - 3, x1 + 3, y + 3), fill=ACCENT)
    d.ellipse((x2 - 3, y - 3, x2 + 3, y + 3), fill=ACCENT)


def render(name, nodes, title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # фон-точки как в ComfyUI
    for gy in range(0, H, 28):
        for gx in range(0, W, 28):
            d.point((gx, gy), fill=GRID)

    d.text((28, 22), "HOTCUT", font=font(A_BD, 20), fill=ACCENT)

    n = len(nodes)
    cw = 150 if n <= 3 else 118
    gap = 46 if n <= 3 else 30
    total = n * cw + (n - 1) * gap
    x = (W - total) / 2
    cy = 116
    ch = 66
    lbl_font = font(A_RG, 12 if n <= 3 else 11)
    centers = []
    for i, node in enumerate(nodes):
        cx = x + i * (cw + gap)
        card(d, cx, cy, cw, ch, node, lbl_font)
        centers.append((cx, cx + cw))
    for i in range(n - 1):
        connector(d, centers[i][1], cy + ch / 2, centers[i + 1][0])

    center(d, title, font(A_BD, 30), W / 2, 258, WHITE)
    center(d, subtitle, font(A_RG, 17), W / 2, 300, GREY)

    path = os.path.join(OUT, name + ".jpg")
    img.save(path, "JPEG", quality=90)
    print("written:", os.path.basename(path))


render("HOTCUT — GPT Image 2 (текст→картинка)",
       ["HOTCUT API", "GPT Image 2", "Save Image"],
       "GPT Image 2", "текст → картинка")

render("HOTCUT — GPT Image 2 (картинка→картинка)",
       ["Load + API", "GPT Image 2 Edit", "Save Image"],
       "GPT Image 2 Edit", "картинка → картинка")

render("HOTCUT — Удалить фон",
       ["Load + API", "Удалить фон", "Save Image"],
       "Удаление фона", "картинка → прозрачный PNG")

render("HOTCUT — Всё в одном",
       ["HOTCUT API", "GPT Image 2", "Edit / Фон", "Save"],
       "Всё в одном", "генерация · правка · фон")

print("done")
