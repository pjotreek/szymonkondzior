# GDi Merch

Statyczna strona sklepu z merchem GDi aka Simon Gaming MC. Pikselowe akcenty, bez backendu.

Podgląd lokalnie: `python3 -m http.server`, potem http://localhost:8000

## Struktura

- `data/products.json`: produkty i kategorie
- `assets/products/full/`: zdjęcia produktów w pełnej rozdzielczości (PNG, przezroczyste tło)
- `templates/`: szablon podstrony produktu oraz wspólny header i footer z koszykiem
- `index.html`: strona główna; bloki między `<!-- build:... -->` są generowane
- `produkt/<slug>/`: podstrony produktów (generowane)
- `js/products.js`: dane dla koszyka (generowane), `js/main.js`: koszyk, filtry, wybór wariantu
- `css/style.css`: cały wygląd

## Jak zmienić produkty

1. Edytuj `data/products.json` (nazwa, cena, opis, rozmiary, zdjęcia).
2. Uruchom `python3 tools/build_pages.py` (wymaga `pip install pillow`).
3. Commit i push.

Zdjęcia: PNG z przezroczystym tłem w pełnej rozdzielczości wrzucasz do `assets/products/full/`,
a w polu `images` wpisujesz ich nazwy bez `.png` (pierwsze to główne, kolejne trafiają do galerii).
Build sam robi z nich lekkie WebP 600 i 1200 px do strony.

## Assety

`tools/build_assets.py` pobiera kilka tekstur Minecraft 1.21.1 (trawa, ziemia, diament, szmaragd),
buduje czcionkę WOFF z bitmap fontu gry i odtwarza logo jako czyste 8x8.
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
