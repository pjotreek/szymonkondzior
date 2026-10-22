#!/usr/bin/env python3
"""Pobiera statystyki kanału z YouTube Data API v3 i zapisuje data/stats.json.

Wymaga zmiennej środowiskowej YT_API_KEY. Bez niej kończy się bez zmian,
żeby workflow dalej publikował stronę.
"""
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

HANDLE = "gdigsmp"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "stats.json")


def main():
    key = os.environ.get("YT_API_KEY")
    if not key:
        print("Brak YT_API_KEY, pomijam statystyki.")
        return
    query = urllib.parse.urlencode({"part": "statistics", "forHandle": HANDLE, "key": key})
    with urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/channels?{query}", timeout=30) as r:
        items = json.load(r).get("items") or []
    if not items:
        sys.exit(f"Nie znaleziono kanału @{HANDLE}")
    s = items[0]["statistics"]
    stats = {
        "subscribers": None if s.get("hiddenSubscriberCount") else int(s["subscriberCount"]),
        "videos": int(s["videoCount"]),
        "views": int(s["viewCount"]),
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")
    print(stats)


if __name__ == "__main__":
    main()
