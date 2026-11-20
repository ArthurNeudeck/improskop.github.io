"""Erzeugt optimierte WebP-Bilder fuer die Website aus den Originalen in originale/ (ausserhalb von docs/, wird nicht veröffentlicht).

Aufruf (aus dem Projektordner):
  /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python tools/optimize_images.py

Blender dient hier nur als Bildwerkzeug (kann WebP schreiben, bringt numpy mit).
Neue Bilder: unten in BILDER eintragen und Skript erneut ausfuehren.
"""
import bpy, numpy as np
from pathlib import Path

ROOT = Path(bpy.path.abspath("//")) if bpy.data.filepath else Path.cwd()
SRC = ROOT / "originale"
OUT = ROOT / "docs" / "media"
OUT.mkdir(parents=True, exist_ok=True)

# Quelle -> (Name, Breiten)
BILDER = {
    # Shows (je Show ein Ordner: JJJJ-MM-name)
    "shows/2025-10-zu-besuch/Showposter_25_1.png": ("shows/2025-10-zu-besuch/plakat", [480, 960]),
    "shows/2026-01-neujahr/hanna & Max.png": ("shows/2026-01-neujahr/plakat", [800, 1600, 1920]),
    # Bescherung: erzeugt mit cwebp -q 82 -sharp_yuv (Schrift bleibt schaerfer als mit Blender)
    "shows/2026-12-bescherung/hum-2026-xmas-eventfrog.png": ("shows/2026-12-bescherung/quer", [800, 1568]),
    "shows/2026-12-bescherung/hum-2026-xmas-online.png": ("shows/2026-12-bescherung/quadrat", [540, 1080]),
    # Verein
    "verein/DRAUSSEN_HM_Lachen.png": ("verein/hanna-max-lachen", [640, 908]),
    "verein/HuM_Txt2.JPG": ("verein/arthur-lea", [640, 1280]),
    "verein/HuM_LeaCut.JPG": ("verein/arthur-lea-breit", [960, 1600, 2400]),
    # Rueckblick
    "rueckblick/Lang1.jpg": ("rueckblick/verbeugung", [640, 1280, 2000]),
    "rueckblick/Lang2.jpg": ("rueckblick/boden", [640, 1280, 2000]),
    "rueckblick/Hoch0.jpg": ("rueckblick/flasche", [480, 960, 1440]),
    "rueckblick/Hoch1.jpg": ("rueckblick/staunen", [480, 960, 1440]),
    "rueckblick/Hoch2.jpg": ("rueckblick/umarmung", [480, 960, 1440]),
    "rueckblick/Hoch3.jpg": ("rueckblick/applaus", [480, 960, 1440]),
    # Funsection
    "spiele/Talking_people.jpg": ("spiele/gespraech", [640, 1280]),
    "spiele/ChatGPT Image 23. Okt. 2025, 21_30_58.png": ("spiele/abc", [640, 1280]),
    "spiele/Unsichtbare_Objekte.JPG": ("spiele/objekt", [640, 1280]),
    # Shop
    "shop/Sternentod_Shirt_prof.jpg": ("shop/shirt", [640, 1179]),
    "shop/Sternentod_motiv_prof.jpg": ("shop/motiv", [640, 1179]),
}

scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
fmt = scene.render.image_settings
fmt.file_format = "WEBP"


def save(img, path, quality=76, alpha=False):
    fmt.quality = quality
    fmt.color_mode = "RGBA" if alpha else "RGB"
    img.save_render(str(path), scene=scene)


def exif_drehung(pfad):
    """Liest die EXIF-Ausrichtung eines JPEGs (1 = normal, 3/6/8 = gedreht)."""
    import struct
    with open(pfad, "rb") as f:
        if f.read(2) != b"\xff\xd8":
            return 1
        while True:
            marker = f.read(2)
            if len(marker) < 2 or marker[0] != 0xFF:
                return 1
            laenge = struct.unpack(">H", f.read(2))[0]
            daten = f.read(laenge - 2)
            if marker[1] == 0xE1 and daten[:6] == b"Exif\0\0":
                tiff = daten[6:]
                e = "<" if tiff[:2] == b"II" else ">"
                start = struct.unpack(e + "I", tiff[4:8])[0]
                for i in range(struct.unpack(e + "H", tiff[start:start + 2])[0]):
                    eintrag = tiff[start + 2 + i * 12:start + 14 + i * 12]
                    if struct.unpack(e + "H", eintrag[:2])[0] == 0x0112:
                        return struct.unpack(e + "H", eintrag[8:10])[0]
                return 1
            if marker[1] == 0xDA:
                return 1


def aufrichten(img, drehung):
    """Dreht ein Bild gemaess EXIF; Blender selbst ignoriert die Ausrichtung."""
    schritte = {3: 2, 6: 1, 8: 3}.get(drehung)  # Vierteldrehungen im Uhrzeigersinn
    if not schritte:
        return img
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    # Blender speichert Zeilen von unten nach oben; rot90 mit k=-n dreht im Uhrzeigersinn
    px = np.rot90(px.reshape(h, w, 4), k=schritte)
    nh, nw = px.shape[:2]
    neu = bpy.data.images.new(img.name + "_auf", nw, nh, alpha=True)
    neu.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    neu.pack()
    bpy.data.images.remove(img)
    return neu


def scaled_copy(src_img, w):
    sw, sh = src_img.size
    h = round(sh * w / sw)
    c = src_img.copy()
    c.scale(w, h)
    return c


for rel, (name, widths) in BILDER.items():
    img = bpy.data.images.load(str(SRC / rel))
    if rel.lower().endswith((".jpg", ".jpeg")):
        img = aufrichten(img, exif_drehung(SRC / rel))
    (OUT / name).parent.mkdir(parents=True, exist_ok=True)
    for w in widths:
        w = min(w, img.size[0])
        c = scaled_copy(img, w)
        save(c, OUT / f"{name}-{w}.webp")
        bpy.data.images.remove(c)
    print("ok", name, img.size[:], widths)
    bpy.data.images.remove(img)

# Logo in Markenfarben einfaerben (Form = Alpha * Dunkelheit)
MARKE = OUT / "marke"
MARKE.mkdir(exist_ok=True)
logo_roh = bpy.data.images.load(str(SRC / "marke/Logo2_final.png"))
# Leeren Rand abschneiden (Bounding-Box der sichtbaren Form), quadratisch auffuellen
lw, lh = logo_roh.size
lp = np.empty(lw * lh * 4, dtype=np.float32)
logo_roh.pixels.foreach_get(lp)
lp = lp.reshape(lh, lw, 4)
form = lp[:, :, 3] * (1 - lp[:, :, :3].mean(axis=2)) > 0.05
ys, xs = np.where(form)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
seite = max(y1 - y0, x1 - x0) + 8
quad = np.zeros((seite, seite, 4), dtype=np.float32)
quad[:, :, :3] = 1.0
oy, ox = (seite - (y1 - y0)) // 2, (seite - (x1 - x0)) // 2
quad[oy:oy + y1 - y0, ox:ox + x1 - x0] = lp[y0:y1, x0:x1]
logo = bpy.data.images.new("logo", seite, seite, alpha=True)
logo.pixels.foreach_set(quad.ravel())
logo.pack()  # sonst verliert copy() die Pixel eines neu erzeugten Bildes
for farbe, hexwert in {"dunkel": "3B2A63", "hell": "EEF1EC"}.items():
    rgb = [int(hexwert[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    for w in (160, 512):
        c = scaled_copy(logo, w)
        px = np.empty(len(c.pixels), dtype=np.float32)
        c.pixels.foreach_get(px)
        px = px.reshape(-1, 4)
        lum = px[:, :3].mean(axis=1)
        a = px[:, 3] * (1 - lum)
        px[:, 0], px[:, 1], px[:, 2], px[:, 3] = rgb[0], rgb[1], rgb[2], a
        c.pixels.foreach_set(px.ravel())
        if not (farbe == "dunkel" and w == 512):  # logo-dunkel-512 wird nicht benutzt
            save(c, MARKE / f"logo-{farbe}-{w}.webp", quality=90, alpha=True)
        if farbe == "dunkel" and w == 512:
            # Favicon / Touch-Icon als PNG
            fmt.file_format = "PNG"
            fmt.color_mode = "RGBA"
            for s, n in ((180, "apple-touch-icon.png"), (48, "favicon-48.png")):
                ic = c.copy()
                ic.scale(s, s)
                ic.save_render(str(MARKE / n), scene=scene)
            fmt.file_format = "WEBP"
        bpy.data.images.remove(c)

# Vorschaubild fuer Links (Open Graph)
og = bpy.data.images.load(str(SRC / "rueckblick/Lang1.jpg"))  # neutrale Linkvorschau (Unterseiten)
c = scaled_copy(og, 1200)
fmt.file_format = "JPEG"
fmt.quality = 82
fmt.color_mode = "RGB"
c.save_render(str(MARKE / "og-vorschau.jpg"), scene=scene)
print("fertig")
