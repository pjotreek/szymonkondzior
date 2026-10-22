# GDi Merch

Statyczna strona sklepu z merchem GDi aka Simon Gaming MC, w stylu Minecrafta.

Otwórz `index.html` przez dowolny serwer statyczny, np. `python3 -m http.server`.

- `js/main.js`: lista produktów (na razie placeholdery), koszyk w hotbarze, tooltipy
- `css/style.css`: cały wygląd
- `assets/`: tekstury, czcionka i logo, generowane przez `tools/build_assets.py`

## Assety

`tools/build_assets.py` pobiera oryginalne tekstury Minecraft 1.21.1 (mirror InventivetalentDev/minecraft-assets),
przefarbowuje skórzane itemy na kolory GDi, buduje czcionkę WOFF z bitmap `font/ascii.png` i `font/accented.png`
oraz odtwarza logo jako czyste 8x8.

```
pip install pillow fonttools
python3 tools/build_assets.py
```

## Uwaga prawna

Tekstury i czcionka należą do Mojang/Microsoft. Strona sprzedająca merch to użycie komercyjne, więc przed
startem sprawdź Minecraft Usage Guidelines (https://www.minecraft.net/usage-guidelines). Stopka zawiera
wymagany disclaimer "NOT AN OFFICIAL MINECRAFT PRODUCT...". Jeśli Mojang się przyczepi, podmień pliki w
`assets/textures` i `assets/fonts` na własne pixel-arty, ścieżki zostają te same.
