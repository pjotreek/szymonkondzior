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

## Publikacja i statystyki kanału

Workflow `.github/workflows/publish.yml` przy każdym pushu na domyślny branch (i co 6 godzin) pobiera
statystyki kanału @gdigsmp i zapisuje je w `data/stats.json`, a potem publikuje stronę na branchu `gh-pages`.

Staty idą bez klucza API, przez wewnętrzne API YouTube (InnerTube), z którego korzysta też yt-dlp i Invidious
(`tools/fetch_stats.py`). Z przeglądarki się tego nie da zrobić przez CORS, dlatego robi to Action.
Jeśli pobranie się nie uda, strona i tak się publikuje z ostatnimi zapisanymi statami
(albo z ukrytą sekcją, jeśli jeszcze ich nie było). Ręczne odświeżenie: Actions → "Publikacja i staty" → Run workflow.
