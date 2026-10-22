#!/usr/bin/env python3
"""Pobiera tekstury Minecrafta (1.21.1) i buduje z nich assety strony.

- assets/textures/...      oryginalne tekstury bloków, itemów i GUI
- assets/items/*.png       itemy skórzane przefarbowane na kolory GDi (placeholdery produktów)
- assets/ui/*.png          9-slice panelu (z inventory.png)
- assets/fonts/minecraft.woff  czcionka zbudowana z bitmap font/ascii.png + accented.png
- assets/img/logo.png      logo GDi odtworzone 1:1 jako 8x8 (twarz skina)

Wymaga: pip install pillow fonttools
Uruchom z katalogu repo: python3 tools/build_assets.py
"""
import io
import json
import os
import urllib.request

from PIL import Image
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

VERSION = "1.21.1"
BASE = f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/{VERSION}/assets/minecraft/"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets")

TEXTURES = [
    "block/grass_block_side", "block/grass_block_top", "block/dirt", "block/stone",
    "block/cobblestone", "block/oak_planks", "block/oak_log", "block/bedrock",
    "block/deepslate", "block/diamond_ore", "block/emerald_ore", "block/gold_block",
    "block/crafting_table_front", "block/bookshelf", "block/obsidian",
    "gui/sprites/widget/button", "gui/sprites/widget/button_highlighted",
    "gui/sprites/widget/button_disabled", "gui/sprites/container/slot",
    "gui/sprites/hud/hotbar", "gui/sprites/hud/hotbar_selection",
    "gui/sprites/hud/experience_bar_background", "gui/sprites/hud/experience_bar_progress",
    "gui/sprites/hud/heart/full", "gui/sprites/toast/advancement",
    "item/emerald", "item/diamond", "item/paper", "item/painting", "item/name_tag",
    "item/totem_of_undying", "item/bundle", "item/music_disc_cat", "item/book",
]

# Kolory z logo GDi
GREEN, CYAN, BLUE, SKY = (0x60, 0xDC, 0x46), (0x46, 0xDC, 0xD3), (0x2D, 0x7C, 0xDB), (0x5F, 0xB5, 0xE4)
LEATHER = {
    "hoodie_green": ("chestplate", GREEN),
    "tshirt_cyan": ("chestplate", CYAN),
    "cap_blue": ("helmet", BLUE),
    "pants_sky": ("leggings", SKY),
    "shoes_green": ("boots", GREEN),
}
GRASS_TINT = (0x91, 0xBD, 0x59)  # plains


def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return r.read()


def fetch_png(path):
    return Image.open(io.BytesIO(fetch(path))).convert("RGBA")


def save(img, *parts):
    path = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def tint(img, rgb):
    r, g, b, a = img.split()
    r, g, b = (ch.point(lambda v, m=m: v * m // 255) for ch, m in zip((r, g, b), rgb))
    return Image.merge("RGBA", (r, g, b, a))


def build_textures():
    for name in TEXTURES:
        save(fetch_png(f"textures/{name}.png"), "textures", name + ".png")
    # grass_block_top jest szary, w grze barwi go biom
    save(tint(fetch_png("textures/block/grass_block_top.png"), GRASS_TINT), "textures", "block/grass_block_top.png")

    for out, (piece, color) in LEATHER.items():
        base = tint(fetch_png(f"textures/item/leather_{piece}.png"), color)
        base.alpha_composite(fetch_png(f"textures/item/leather_{piece}_overlay.png"))
        save(base, "items", out + ".png")

    # 9-slice panelu GUI wycięty z ekwipunku (176x166, rogi 4px)
    inv = fetch_png("textures/gui/container/inventory.png").crop((0, 0, 176, 166))
    panel = Image.new("RGBA", (12, 12))
    w, h = inv.size
    for (sx, sy), (dx, dy) in {
        (0, 0): (0, 0), (w - 4, 0): (8, 0), (0, h - 4): (0, 8), (w - 4, h - 4): (8, 8),
        (40, 0): (4, 0), (40, h - 4): (4, 8), (0, 40): (0, 4), (w - 4, 40): (8, 4), (40, 40): (4, 4),
    }.items():
        panel.paste(inv.crop((sx, sy, sx + 4, sy + 4)), (dx, dy))
    # środek panelu to jednolity kolor, czyścimy ewentualne fragmenty slotów
    for x in range(4, 8):
        for y in range(4, 8):
            panel.putpixel((x, y), inv.getpixel((5, 5)))
    save(panel, "ui", "panel.png")


def build_logo():
    """Logo z załącznika to twarz skina 8x8 w ~21px komórkach, przycięta do 160px."""
    src = Image.open(os.path.join(OUT, "img", "logo-original.jpg")).convert("RGB")
    xs = [(0, 17), (20, 38), (41, 59), (62, 80), (83, 101), (104, 122), (125, 143), (146, 159)]
    ys = [(1, 19), (22, 40), (43, 61), (64, 82), (85, 103), (106, 124), (127, 145), (148, 159)]
    out = Image.new("RGB", (8, 8))
    for j, (y0, y1) in enumerate(ys):
        for i, (x0, x1) in enumerate(xs):
            px = [src.getpixel((x, y)) for x in range(x0 + 2, x1 - 1) for y in range(y0 + 2, y1 - 1)]
            out.putpixel((i, j), tuple(sorted(p[k] for p in px)[len(px) // 2] for k in range(3)))
    save(out, "img", "logo.png")
    save(out.resize((32, 32), Image.NEAREST), "img", "favicon.png")


# --- czcionka -------------------------------------------------------------

PX = 125  # jednostki na piksel Minecrafta; UPM 1000 => 8 px MC na em


def glyph_outline(pixels):
    """Zamienia zbiór pikseli (x, y; y w dół) na kontury obrysu bez szwów."""
    edges = {}
    for x, y in pixels:
        # kierunek zgodny z ruchem wskazówek zegara w układzie y-w-górę (TrueType)
        for a, b in (((x, y), (x + 1, y)), ((x + 1, y), (x + 1, y + 1)),
                     ((x + 1, y + 1), (x, y + 1)), ((x, y + 1), (x, y))):
            if (b, a) in edges:
                del edges[(b, a)]
            else:
                edges[(a, b)] = True
    nxt = {}
    for a, b in edges:
        nxt.setdefault(a, []).append(b)
    contours = []
    while nxt:
        start = next(iter(nxt))
        loop, cur = [start], start
        while True:
            b = nxt[cur].pop()
            if not nxt[cur]:
                del nxt[cur]
            if b == start:
                break
            loop.append(b)
            cur = b
        # usuń punkty współliniowe
        pts = [p for i, p in enumerate(loop)
               if not ((loop[i - 1][0] == p[0] == loop[(i + 1) % len(loop)][0]) or
                       (loop[i - 1][1] == p[1] == loop[(i + 1) % len(loop)][1]))]
        contours.append(pts)
    return contours


def build_font():
    providers = json.loads(fetch("font/include/default.json"))["providers"]
    glyphs = {}  # char -> (advance_px, contours)
    for prov in providers:
        if prov["type"] != "bitmap":
            continue
        sheet = fetch_png("textures/" + prov["file"].split(":")[1])
        rows = prov["chars"]
        cw, ch = sheet.width // len(rows[0]), sheet.height // len(rows)
        height = prov.get("height", 8)
        scale = height / ch
        ascent = prov["ascent"]
        for r, row in enumerate(rows):
            for c, char in enumerate(row):
                if char in glyphs or char == "\0":
                    continue
                pixels = [(x, y) for y in range(ch) for x in range(cw)
                          if sheet.getpixel((c * cw + x, r * ch + y))[3] > 0]
                width = max((x for x, _ in pixels), default=-1) + 1
                if width == 0:
                    continue
                glyphs[char] = (int(0.5 + width * scale) + 1, pixels, scale, ascent)

    names = [".notdef", "space"]
    cmap = {32: "space"}
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0)); pen.lineTo((0, 7 * PX)); pen.lineTo((5 * PX, 7 * PX)); pen.lineTo((5 * PX, 0)); pen.closePath()
    tt_glyphs = {".notdef": pen.glyph(), "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (6 * PX, 0), "space": (4 * PX, 0)}
    for char, (adv, pixels, scale, ascent) in glyphs.items():
        name = f"uni{ord(char):04X}"
        pen = TTGlyphPen(None)
        for contour in glyph_outline(pixels):
            for i, (x, y) in enumerate(contour):
                pt = (round(x * scale * PX), round((ascent - y * scale) * PX))
                pen.moveTo(pt) if i == 0 else pen.lineTo(pt)
            pen.closePath()
        tt_glyphs[name] = pen.glyph()
        metrics[name] = (adv * PX, round(min(x for x, _ in pixels) * scale * PX))
        names.append(name)
        cmap[ord(char)] = name

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(tt_glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=9 * PX, descent=-2 * PX)
    fb.setupNameTable({"familyName": "Minecraft GDi", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=9 * PX, sTypoDescender=-2 * PX, usWinAscent=9 * PX, usWinDescent=2 * PX)
    fb.setupPost()
    fb.font.flavor = "woff"
    os.makedirs(os.path.join(OUT, "fonts"), exist_ok=True)
    fb.save(os.path.join(OUT, "fonts", "minecraft.woff"))
    return len(cmap)


if __name__ == "__main__":
    build_textures()
    build_logo()
    print("glifów w czcionce:", build_font())
