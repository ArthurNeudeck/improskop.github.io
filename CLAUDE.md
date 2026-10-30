# CLAUDE.md – improskop.ch

Website des Improtheater-Vereins **Improskop** (Riehen/Basel). Statische Seite auf GitHub Pages, ohne Build-Schritt.
Ansprechperson und Entwickler: Mika. Mit Mika auf **Deutsch** kommunizieren.

## Arbeitsordner und Veröffentlichung
- **Hauptordner (Git, mit GitHub verbunden):** `/Users/mikaneudeck/IdeaProjects/improskop.github.io`
  Remote: `https://github.com/ArthurNeudeck/improskop.github.io.git`, Branch `main`.
  GitHub Pages veröffentlicht den Ordner `docs/` auf www.improskop.ch (`docs/CNAME` nie löschen).
- **Mika committet und pusht selbst in IntelliJ.** Claude committet oder pusht dort nicht, ausser Mika verlangt es ausdrücklich.
  Neue Dateien und Ordner mit `git add` vormerken, sonst landen sie in IntelliJ unter „Unversioned Files“ und fehlen online.
  Das ist schon einmal passiert und hat die Live-Seite kaputt gemacht.
- Alter Arbeitsordner aus dem Redesign: `~/Documents/Dokumente – MacBook Pro von Mika/Projekte/Website/improskop.github.io-main`
  (eigene lokale Git-Historie, nicht mit GitHub verbunden). Achtung: Vor dem „–“ steht ein **geschütztes Leerzeichen (U+00A0)**.
  Read/Write/Edit-Tools scheitern daran, also Bash benutzen. Neue Arbeit im Hauptordner machen.
- Sicherung des Stands vor dem Redesign: `…/Projekte/Website/improskop.github.io-main_backup_2026-10-29/`.
- Nach dem Push 2–5 Minuten warten, dann im privaten Tab prüfen.

## Harte Regeln
1. **Sichtbarer Text bleibt wörtlich gleich**, inklusive Tippfehlern, ausser Mika gibt eine Änderung frei.
   Prüfen mit `python3 tools/textcheck.py check` (Referenz: `tools/text-baseline.json` = Stand vor dem Redesign).
   Erwartete, gewollte Abweichungen:
   - `☰` fehlt (ist jetzt ein gezeichnetes Icon).
   - Impressum und Datenschutz haben zusätzlich Navigation und Footer.
   - Die Show-Zelle und die Show-Leiste wiederholen den Show-Text; sie sind mit `data-textcheck="ignore"` markiert.

   Nach freigegebenen Textänderungen: `python3 tools/textcheck.py snapshot`.
2. **Nach jeder Änderung an CSS oder JS die Versionsnummer erhöhen**: `style.css?v=…`, `script.js?v=…`, `zellen.js?v=…`
   in allen HTML-Dateien (aktuell `v=20261031`). Sonst mischt der Browser neue HTML mit alten Skripten, und die
   Seite wird nicht mehr scrollbar.
3. **Leistung:** Nie `border-radius`, `width`/`height`, `box-shadow` oder `filter` animieren. Bewegung nur über `transform`/`opacity`.
   Das Animieren der Zellform war der Grund, warum die Seite auf Handys mit 11 statt 60 Bildern/s lief.
   Auf Handys keine Live-Unschärfe (`backdrop-filter`) über bewegten Inhalten.
4. Grössere Umbauten erst als kurzer Plan mit Mika abstimmen.

## Aufbau
```
docs/                 ← wird veröffentlicht
  index.html          Startseite („Der Objektträger“)
  Funsec.html, shop.html, impressum.html, datenschutz.html, fun/impro-resources.html (nirgends verlinkt, unfertig)
  style.css           ein Stylesheet für alle Seiten
  script.js           alle Seiten: Navigation/Burger, Countdown, Cookie-Banner, Glanzlicht, Rückblick-Pfeile
  zellen.js           nur Startseite: Kamera, Zeitachse, Blender-Bildfolge, Sparmodus
  media/              optimierte WebP-Bilder, Logos, Favicons, og-vorschau.jpg
  media/outro/        Blender-Bildfolge: quer/ (1600×900), hoch/ (900×1600), *-leicht/ (60 %, jedes 2. Bild),
                      linse-quer.json / linse-hoch.json (Lage der Linse in jedem Bild)
  fonts/              Gloock + Hanken Grotesk, selbst gehostet
originale/            Original-Fotos (nicht veröffentlicht)
blender/              mikroskop.blend, build_mikroskop.py, render_web.py
tools/                optimize_images.py (Bildpipeline), textcheck.py
```

## Design „Unter dem Objektiv / Der Objektträger“
- Konzept: Das Logo-Mikroskop. Die Website liegt als Präparat unter dem Mikroskop.
- Farben (`:root` in style.css):

  | Rolle | Werte |
  |---|---|
  | Präparat-Hintergrund | `--praeparat #F4EEE1` (cremeweiss), `--beige`, `--ocker-hauch`, `--eosin-hauch`, `--lila-hauch` |
  | Text | `--haematoxylin #3B2A63` |
  | Akzent (nur Deko/gross) | `--eosin #E7859B` |
  | Buttons | `--licht #EAB25B`, Hover `--buehne #EF8649` |
  | Bühne ausserhalb des Mikroskops | `--nacht #1C1430` (= Hintergrundfarbe der Blender-Renderings) |

- Schriften: **Gloock** (Titel), **Hanken Grotesk** (Text).
- **Liquid Glass**: Klasse `.glas` (+ `.glas--dunkel`, `.glas--licht`) für schwebende Bedienelemente (Navigation, Buttons,
  Show-Leiste, Countdown, Footer, Cookie-Banner). Die SVG-Lichtbrechung (`#linse`) gibt es nur auf starken Chromium-Geräten (`html.brechung`).
- Navigation: Glas-Kapsel, auf dem Laptop oben, auf dem Handy unten.
- Fotos sind „Organellen“ (`<figure class="organell …" data-tiefe>`) mit organischer Maske und einem eosin-farbenen Ring
  **direkt am Bildrand**. Fotos nie unscharf machen.

## Startseite: Ablauf (`docs/zellen.js`)
Alles hängt nur an der Scroll-Position (kein Einrasten, kein Scroll-Hijacking). Abschnitte der Zeitachse:
1. **hinein**: Start = Mikroskop von aussen (Blender-Bild 96). Das Show-Panel (Titel, Countdown, Untertitel, Datum, Tickets,
   Instagram) ist sofort sichtbar. Beim Scrollen läuft die Bildfolge rückwärts, und in der **durchsichtigen Linse** liegt die echte
   Website (Holdout in Blender, Abgleich über linse-*.json). Das Show-Panel dockt dabei als `.show-leiste` oben an und bleibt bis zum Ende stehen.
2. **oeffnen**: Blender-Bild 1 bleibt stehen und wird per `transform: scale` um die Linse vergrössert: Die Kamera fliegt durchs
   Okular, das Website-Loch wächst mit. Danach wird die Bühne ausgeblendet. (`okular-rand.webp` wird nicht mehr benutzt.)
3. **zelle / uebergang**: 10 Zellen (`section.zelle` in `.welt`) in dieser Reihenfolge: Show (Wiederholung), Gast & Musik,
   Newsletter + VIP, Letzte Aufführung (`#shows`), Verein (`#ueber-uns`), Schauspielende, Rückblicke (`#my-work`), Orga, Q&A, Funsection.
   Beim Verweilen fährt die Kamera die Zelle ab (normales Lesen); im Übergang zoomt sie heraus, gleitet zur nächsten Zelle und zoomt wieder hinein.
4. **abschied**: Die letzte Zelle gleitet nach oben weg, der Kreis schliesst sich, und Bild 1 schrumpft wieder auf Normalgrösse
   (bewusst ohne Übersicht aller Zellen: zu teuer).
5. **hinaus**: Die Bildfolge läuft vorwärts, das Footer-Panel erscheint neben dem Mikroskop.

Weitere Mechanik:
- **Zellen** sind Liquid-Glass-Bakterien. Die Blase (`::before`/`::after`) ragt 21 % über den Inhalt hinaus (`--blase`, in JS `BLASE`),
  damit der Text ganz in der Form liegt. Jede Zelle hat eine feste Form (`--form` je `nth-of-type`). Seitlicher Versatz: `--x`.
- Es werden nur Zellen im Kamerablick und die Deko-Bakterien direkt daneben gemalt (`data-fern` → `visibility: hidden`).
  In `hinein`/`hinaus` (`html.im-film`) ist das Atmen angehalten.
- Werte, die `zellen.js` pro Bild setzt, sind per `@property … inherits: false` nicht vererbt, und `setze()` schreibt nur Änderungen.
  Neue Werte pro Bild genauso behandeln, sonst rechnet der Browser bei jedem Bild ganze Teilbäume neu.
- Das Website-Loch folgt immer dem tatsächlich gezeichneten Blender-Bild (`zeichne()` gibt dessen Nummer zurück).
  Die Leinwand ist nie feiner als das Quellbild.
- **Sparmodus `html.leicht`**:
  - Wann: Handys (Touch/≤900 px) immer; sonst bei wenig Speicher/Kernen, Datensparen oder gemessenem Ruckeln.
  - Was: kein Live-Glas, kein Atmen, Bildfolge aus `*-leicht/`.
  - Zum Testen: `index.html?leicht`.
- Die Blender-Bildfolge nutzt immer nur jedes 2. Bild (48 von 96) und dekodiert vorab.
- **Notbremse**: Scheitert der Aufbau, fällt die Seite auf die einfache, scrollbare Zellen-Liste zurück. Dieselbe Liste
  erscheint ohne JS und bei `prefers-reduced-motion`.
- Navigationslinks und Tab-Fokus scrollen die Kamera zur passenden Zelle.

## Inhalte pflegen
- **Nächste Show:** Das Datum steht an **drei** Stellen in `docs/index.html`: im Show-Panel, in der `.show-leiste` und in der Zelle
  `#zelle-1`. Dazu `data-ziel` am `#countdown` (nach dem Datum blendet sich der Countdown aus) und der Eventfrog-Link
  (Show-Panel, Leiste und Navigation **aller** Seiten).
- **Bilder:** Original nach `originale/`, in `tools/optimize_images.py` (Liste `BILDER`) eintragen, dann:
  `/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python tools/optimize_images.py`
  (Blender dient nur als Bildwerkzeug; ffmpeg hat hier kein WebP. Handyfotos werden per EXIF gedreht.)
- **Mikroskop:** Blender 5.1 ist installiert, Blender MCP **nicht** verbunden; gesteuert wird per Python.
  - Neu rendern: `Blender --background blender/mikroskop.blend --python blender/render_web.py`
    (Optionen `-- --test`, `-- --nur quer|hoch|okular|leicht`; ca. 6 s pro Bild auf der GPU, beide Formate ca. 25 Min.).
  - `build_mikroskop.py` baut die Szene neu und **überschreibt** `mikroskop.blend`, nach Handarbeit in Blender nicht mehr verwenden.
  - Die Notiz „LIESMICH“ in der .blend-Datei erklärt Objekte, Kameras und Materialien.

## Testen
- Lokal: `cd docs && python3 -m http.server 8765`.
- Bewährt: Chrome headless über das DevTools-Protokoll (Node ≥ 23 hat WebSocket eingebaut, keine Pakete nötig).
  - Screenshots bei 390×844 (Handy, mit Touch-Emulation) und 1440×900.
  - Scroll-Messung mit `Emulation.setCPUThrottlingRate` 4–6×.
  - Echte Eingaben mit `Input.synthesizeScrollGesture` (touch) bzw. `mouseWheel`.
  - Hilfsskripte nach `~/improskop-tmp/` legen und danach löschen.
- Lighthouse: `npx -y lighthouse@12 <url> --chrome-flags="--headless=new"`. Letzter Stand mobil: Performance 96,
  Barrierefreiheit 100, Best Practices 100, SEO 100.
- Grenze: Der Simulator bildet einen schwachen Handy-**Grafikchip** nicht ab. Am Ende muss Mika auf einem echten Handy testen.

## Offene Punkte (von Mika bzw. dem Verein zu entscheiden)
- `datenschutz.html`: Die Kontakt-E-Mail ist der Platzhalter `improgruppe@example.com`. Der Text spricht von Cookies zur Analyse
  (es gibt keine), und der Newsletter über Getform wird nicht erwähnt.
- `Funsec.html`: Das ABC-Spiel-Bild ist ein Platzhalter („Pictures are not here but they are coming“). Die Quelle beim
  „Unsichtbaren Objekt“ verlinkt auf die ABC-Spiel-Seite.
- Tippfehler, bewusst **nicht** korrigiert und erst nach Freigabe zu ändern:
  - „Limeted Edition“
  - „Kammerthater“
  - „unterstüzt“
  - „Der 16-jähriger“
  - „eine beeindruckendes Talent“
  - „dieses Mal in mit neuem Format“
  - „Zu Besuch bei Hanna & |“ (es fehlt „Max“)
  - „wie Folgt“, „Tabuu“, „beim spielen“
  - „nachfolgenen“
  - „wir eindrucksvoll“ (wie)
- Das Showdatum (31.01.2026) liegt in der Vergangenheit. Der Countdown ist deshalb ausgeblendet.
- `fun/impro-resources.html` ist unfertig („tbd“) und nicht verlinkt.
