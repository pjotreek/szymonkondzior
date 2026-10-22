#!/usr/bin/env python3
"""Pobiera statystyki kanału bez klucza API i zapisuje data/stats.json.

Korzysta z wewnętrznego API YouTube (InnerTube), tego samego, którego używa
strona youtube.com, yt-dlp i Invidious. Nie wymaga konta ani klucza.
Z przeglądarki nie zadziała (CORS), dlatego odpala to GitHub Action.

Szukamy tekstów typu "12.3K subscribers", "87 videos", "1,234,567 views"
w całej odpowiedzi, więc drobne zmiany struktury JSON-a YouTube'a tego nie psują.
"""
import datetime
import json
import os
import re
import sys
import urllib.request

HANDLE = "gdigsmp"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "stats.json")
API = "https://www.youtube.com/youtubei/v1/"
CONTEXT = {"client": {"clientName": "WEB", "clientVersion": "2.20250101.00.00", "hl": "en", "gl": "US"}}
ABOUT_PARAMS = "EgVhYm91dPIGBAoCEgA="

PATTERNS = {
    "subscribers": re.compile(r"^([\d.,]+[KMB]?) subscribers?$"),
    "videos": re.compile(r"^([\d,]+) videos?$"),
    "views": re.compile(r"^([\d,]+) views?$"),
}


def call(endpoint, payload):
    req = urllib.request.Request(
        API + endpoint + "?prettyPrint=false",
        data=json.dumps({"context": CONTEXT, **payload}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def strings(node):
    """Wszystkie teksty z odpowiedzi: zwykłe stringi, simpleText i runs."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        if "runs" in node and isinstance(node["runs"], list):
            yield "".join(r.get("text", "") for r in node["runs"])
        for v in node.values():
            yield from strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v)


def to_number(text):
    mult = {"K": 1e3, "M": 1e6, "B": 1e9}.get(text[-1], 1)
    return int(float(text.rstrip("KMB").replace(",", "")) * mult)


def scan(data, found):
    for s in strings(data):
        s = s.strip()
        for key, rx in PATTERNS.items():
            m = rx.match(s)
            if m and key not in found:
                found[key] = to_number(m.group(1))


def main():
    resolved = call("navigation/resolve_url", {"url": f"https://www.youtube.com/@{HANDLE}"})
    channel_id = resolved["endpoint"]["browseEndpoint"]["browseId"]

    found = {}
    scan(call("browse", {"browseId": channel_id, "params": ABOUT_PARAMS}), found)
    if len(found) < 3:
        scan(call("browse", {"browseId": channel_id}), found)
    if "subscribers" not in found:
        sys.exit(f"Nie znaleziono statystyk kanału {channel_id}: {found}")

    stats = {
        "subscribers": found.get("subscribers"),
        "videos": found.get("videos"),
        "views": found.get("views"),
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")
    print(channel_id, stats)


if __name__ == "__main__":
    main()
