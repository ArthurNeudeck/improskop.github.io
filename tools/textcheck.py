#!/usr/bin/env python3
"""Vergleicht den sichtbaren Text aller HTML-Seiten mit einem Referenzstand.

  python3 tools/textcheck.py snapshot   # Referenz speichern (tools/text-baseline.json)
  python3 tools/textcheck.py check      # aktuellen Stand gegen Referenz prüfen
"""
import json, sys, re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "docs"
BASE = Path(__file__).resolve().parent / "text-baseline.json"
SKIP = {"script", "style", "title", "noscript", "svg"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        # Elemente, die nur fuer Screenreader/Deko sind, ignorieren
        if dict(attrs).get("data-textcheck") == "ignore":
            self.skip += 1
            self._ign = getattr(self, "_ign", []) + [tag]

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip -= 1
        if getattr(self, "_ign", None) and self._ign[-1] == tag:
            self._ign.pop()
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def words(path):
    p = Text()
    p.feed(path.read_text(encoding="utf-8"))
    return re.sub(r"\s+", " ", " ".join(p.parts)).split()


def collect():
    return {str(f.relative_to(ROOT)): words(f) for f in sorted(ROOT.rglob("*.html"))}


if __name__ == "__main__":
    if sys.argv[1:] == ["snapshot"]:
        BASE.write_text(json.dumps(collect(), ensure_ascii=False, indent=1), encoding="utf-8")
        print("Referenz gespeichert")
    else:
        base, now, ok = json.loads(BASE.read_text(encoding="utf-8")), collect(), True
        for page, w in base.items():
            if now.get(page) != w:
                ok = False
                import difflib
                print(f"\n--- {page}")
                for line in difflib.unified_diff(w, now.get(page, []), lineterm="", n=2):
                    print(line)
        print("OK: Text unverändert" if ok else "\nABWEICHUNGEN gefunden")
        sys.exit(0 if ok else 1)
