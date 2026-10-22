# GDi Merch

Statyczna strona sklepu z merchem GDi aka Simon Gaming MC. Pikselowe akcenty, bez backendu.

Podgląd lokalnie: `python3 -m http.server`, potem http://localhost:8000

## Struktura

- `data/products.json`: produkty, kolory, kategorie (na razie placeholdery)
- `templates/`: szablon podstrony produktu oraz wspólny header i footer z koszykiem
- `index.html`: strona główna; bloki między `<!-- build:... -->` są generowane
- `produkt/<slug>/`: podstrony produktów (generowane)
- `js/products.js`: dane dla koszyka (generowane), `js/main.js`: koszyk, filtry, wybór wariantu
- `css/style.css`: cały wygląd

## Jak zmienić produkty

1. Edytuj `data/products.json` (nazwa, cena, opis, kolory, rozmiary, obrazek).
2. Uruchom `python3 tools/build_pages.py` (wymaga `pip install pillow`).
3. Commit i push.

Pole `image` to nazwa pliku z `assets/items/` bez `.png`; `{color}` zostanie podmienione na kolor wariantu.
Prawdziwe zdjęcia wrzuć do `assets/items/` i wpisz ich nazwy.

`SITE_URL` w `tools/build_pages.py` musi wskazywać adres opublikowanej strony (linki kanoniczne i podglądy na Discordzie).

## Assety

`tools/build_assets.py` pobiera tekstury Minecraft 1.21.1 (mirror InventivetalentDev/minecraft-assets),
barwi skórzane itemy na kolory wariantów, buduje czcionkę WOFF z bitmap fontu gry i odtwarza logo jako czyste 8x8.
Rubik (tekst) jest na licencji SIL OFL.

```
pip install pillow fonttools
python3 tools/build_assets.py
python3 tools/build_pages.py
```

## Uwaga prawna

Tekstury i pikselowa czcionka należą do Mojang/Microsoft. Sklep z merchem to użycie komercyjne, więc przed
startem sprawdź https://www.minecraft.net/usage-guidelines. Podmiana na własne grafiki to wymiana plików w
`assets/items`, `assets/textures` i `assets/fonts/minecraft.woff`, bez ruszania kodu.
