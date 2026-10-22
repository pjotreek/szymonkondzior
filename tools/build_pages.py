#!/usr/bin/env python3
"""Generuje strony sklepu z data/products.json.

- produkt/<slug>/index.html   podstrona każdego produktu (z templates/product.html)
- index.html                  wstawia header, footer i siatkę produktów między znaczniki build:*
- js/products.js              dane produktów dla koszyka
- assets/og/*.png             obrazki do podglądu linków (Discord, X, Messenger)

Po każdej zmianie w data/products.json albo templates/ uruchom:
    python3 tools/build_pages.py
"""
import html
import json
import os
import re
import shutil

from PIL import Image

# Adres strony po publikacji, potrzebny do linków kanonicznych i og:image.
SITE_URL = "https://pjotreek.github.io/szymonkondzior/"

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TEMPLATES = os.path.join(ROOT, "templates")

esc = html.escape


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def write(text, *parts):
    path = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def fill(template, values):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)


def fill_block(page, name, content):
    pattern = re.compile(rf"(<!-- build:{name} -->\n).*?(<!-- /build:{name} -->)", re.S)
    assert pattern.search(page), f"brak znacznika build:{name}"
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), page)


def money(value):
    whole, frac = f"{value:.2f}".split(".")
    return f"{int(whole):,}".replace(",", " ") + f",{frac} zł"


def tint_of(data, color):
    c = data["colors"][color]
    return c.get("tint", c["hex"])


def image_for(product, color=None):
    color = color or (product.get("colors") or [None])[0]
    return product["image"].replace("{color}", color) if color else product["image"]


def card(p, data, root):
    tint = tint_of(data, p["colors"][0]) if p.get("colors") else "#46dcd3"
    badge = f'<span class="badge">{esc(p["badge"])}</span>' if p.get("badge") else ""
    swatches = ""
    if p.get("colors"):
        dots = "".join(f'<li style="--c:{data["colors"][c]["hex"]}" title="{esc(data["colors"][c]["name"])}"></li>'
                       for c in p["colors"])
        swatches = f'<ul class="dots" aria-label="Dostępne kolory">{dots}</ul>'
    return f"""<a class="card" href="{root}produkt/{p['slug']}/" data-category="{p['category']}">
  <div class="media" style="--tint:{tint}">{badge}<img src="{root}assets/items/{image_for(p)}.png" alt="" width="16" height="16" loading="lazy"></div>
  <div class="card-body">
    <h3>{esc(p['name'])}</h3>
    <div class="card-meta"><p class="price">{money(p['price'])}</p>{swatches}</div>
  </div>
</a>
"""


def color_field(p, data):
    if not p.get("colors"):
        return ""
    first = data["colors"][p["colors"][0]]["name"]
    opts = "".join(
        f'<label class="swatch"><input type="radio" name="color" value="{c}" data-name="{esc(data["colors"][c]["name"])}" '
        f'data-tint="{tint_of(data, c)}" data-img="{image_for(p, c)}"{" checked" if i == 0 else ""}>'
        f'<span style="--c:{data["colors"][c]["hex"]}"></span><span class="sr-only">{esc(data["colors"][c]["name"])}</span></label>'
        for i, c in enumerate(p["colors"]))
    return f"""<fieldset class="field">
          <legend>Kolor: <b data-color-name>{esc(first)}</b></legend>
          <div class="swatches">{opts}</div>
        </fieldset>"""


def size_field(p):
    sizes = p.get("sizes")
    if not sizes:
        return ""
    single = len(sizes) == 1
    opts = "".join(f'<label class="size"><input type="radio" name="size" value="{esc(s)}"{" checked" if single else ""}>'
                   f'<span>{esc(s)}</span></label>' for s in sizes)
    return f"""<fieldset class="field" data-size-field>
          <legend>Rozmiar</legend>
          <div class="sizes">{opts}</div>
        </fieldset>"""


def thumbs(p, data, root):
    if not p.get("colors") or len(p["colors"]) < 2:
        return ""
    items = "".join(
        f'<button type="button" class="thumb media{" is-active" if i == 0 else ""}" style="--tint:{tint_of(data, c)}" '
        f'data-thumb="{c}" aria-label="{esc(data["colors"][c]["name"])}"><img src="{root}assets/items/{image_for(p, c)}.png" alt="" width="16" height="16"></button>'
        for i, c in enumerate(p["colors"]))
    return f'<div class="thumbs">{items}</div>'


def size_chart(p):
    sizes = p.get("sizes") or []
    if p["category"] != "ubrania" or len(sizes) < 2 or not sizes[0][0].isalpha():
        return ""
    rows = "".join(f"<tr><td>{esc(s)}</td><td>{50 + 3 * i}</td><td>{68 + 2 * i}</td></tr>" for i, s in enumerate(sizes))
    return f"""<details>
          <summary>Rozmiarówka</summary>
          <table class="size-table"><thead><tr><th>Rozmiar</th><th>Szerokość (cm)</th><th>Długość (cm)</th></tr></thead><tbody>{rows}</tbody></table>
          <p class="muted">Wymiary przykładowe, do podmiany.</p>
        </details>"""


def related(p, products, data, root):
    same = [q for q in products if q is not p and q["category"] == p["category"]]
    other = [q for q in products if q is not p and q["category"] != p["category"]]
    return "".join(card(q, data, root) for q in (same + other)[:4])


def og_image(img_name, tint, out_name):
    """1200x630: kafel w kolorze produktu, sprite powiększony bez rozmycia, logo w rogu."""
    tint = tuple(int(tint[i:i + 2], 16) for i in (1, 3, 5))
    bg = (13, 20, 28)
    canvas = Image.new("RGB", (1200, 630), bg)
    tile = Image.new("RGB", (560, 560), tuple(int(b + (t - b) * 0.22) for b, t in zip(bg, tint)))
    canvas.paste(tile, (600, 35))
    sprite = Image.open(os.path.join(ROOT, "assets", "items", img_name + ".png")).convert("RGBA")
    sprite = sprite.resize((384, 384), Image.NEAREST)
    canvas.paste(sprite, (688, 123), sprite)
    logo = Image.open(os.path.join(ROOT, "assets", "img", "logo.png")).resize((320, 320), Image.NEAREST)
    canvas.paste(logo, (140, 155))
    path = os.path.join(ROOT, "assets", "og", out_name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    canvas.save(path, optimize=True)


def main():
    data = json.loads(read("data", "products.json"))
    products = data["products"]
    header, footer = read("templates", "header.html"), read("templates", "footer.html")

    def chrome(page, root):
        page = fill_block(page, "header", fill(header, {"root": root}))
        return fill_block(page, "footer", fill(footer, {"root": root}))

    # podstrony produktów
    shutil.rmtree(os.path.join(ROOT, "produkt"), ignore_errors=True)
    template = read("templates", "product.html")
    root = "../../"
    for p in products:
        tint = tint_of(data, p["colors"][0]) if p.get("colors") else "#46dcd3"
        page = fill(template, {
            "root": root,
            "slug": p["slug"],
            "name": esc(p["name"]),
            "short": esc(p["short"]),
            "url": f"{SITE_URL}produkt/{p['slug']}/",
            "og_image": f"{SITE_URL}assets/og/{p['slug']}.png",
            "category_name": esc(data["categories"][p["category"]]),
            "price": money(p["price"]),
            "tint": tint,
            "image": image_for(p),
            "badge": f'<span class="badge">{esc(p["badge"])}</span>' if p.get("badge") else "",
            "thumbs": thumbs(p, data, root),
            "color_field": color_field(p, data),
            "size_field": size_field(p),
            "description": "\n          ".join(f"<p>{esc(t)}</p>" for t in p["description"]),
            "material": esc(p["material"]),
            "size_chart": size_chart(p),
            "related": related(p, products, data, root),
        })
        write(chrome(page, root), "produkt", p["slug"], "index.html")
        og_image(image_for(p), tint, p["slug"])

    # strona główna
    index = read("index.html")
    index = fill_block(index, "products", "".join(card(p, data, "") for p in products))
    index = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf"\g<1>{SITE_URL}assets/og/home.png\g<2>", index)
    write(chrome(index, "./"), "index.html")
    og_image("chestplate_green", "#60dc46", "home")

    # dane dla koszyka
    js_data = {
        "freeShipping": 200,
        "colors": data["colors"],
        "products": {p["slug"]: {"name": p["name"], "price": p["price"], "image": p["image"],
                                 "colors": p.get("colors", [])} for p in products},
    }
    write("// Wygenerowane przez tools/build_pages.py z data/products.json. Nie edytuj ręcznie.\n"
          f"window.GDI = {json.dumps(js_data, ensure_ascii=False, indent=2)};\n", "js", "products.js")
    print(f"zbudowano {len(products)} podstron")


if __name__ == "__main__":
    main()
