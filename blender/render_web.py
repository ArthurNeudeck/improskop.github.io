"""Rendert die Bilder fuer die Website aus mikroskop.blend.

  Blender --background blender/mikroskop.blend --python blender/render_web.py            # alles
  Blender --background blender/mikroskop.blend --python blender/render_web.py -- --test  # nur Testbilder
  Blender --background blender/mikroskop.blend --python blender/render_web.py -- --nur quer  # nur ein Format (quer/hoch/okular)
  Blender --background blender/mikroskop.blend --python blender/render_web.py -- --nur leicht # nur Sparversion neu erzeugen

Ergebnis:
  docs/media/okular-rand.webp          Okular-Rand mit transparenter Mitte (Seiteneinstieg)
  docs/media/outro/quer/0001-0096.webp Rueckfahrt fuer Laptop (1600x900)
  docs/media/outro/hoch/0001-0096.webp Rueckfahrt fuer Handy (900x1600)
  docs/media/outro/*-leicht/           Sparversion fuer schwache Geraete: jedes 2. Bild, 60 % Groesse
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HIER = Path(bpy.data.filepath).parent
MEDIA = HIER.parent / "docs" / "media"
TEST = "--test" in sys.argv
NUR = sys.argv[sys.argv.index("--nur") + 1] if "--nur" in sys.argv else None
scene = bpy.context.scene


def gpu_an():
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for typ in ("METAL", "OPTIX", "CUDA", "HIP"):
            try:
                prefs.compute_device_type = typ
                break
            except TypeError:
                continue
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = "GPU"
        print("Rendergeraet:", prefs.compute_device_type)
    except Exception as e:  # CPU geht auch, nur langsamer
        print("GPU nicht verfuegbar:", e)


def webp(qualitaet, alpha):
    f = scene.render.image_settings
    f.file_format = "WEBP"
    f.quality = qualitaet
    f.color_mode = "RGBA" if alpha else "RGB"


def okular_rand(ziel):
    """Nur das Okular, Bild in der Linse ausgeblendet, Hintergrund transparent."""
    sichtbar = set(bpy.data.collections["Okular"].all_objects)
    gemerkt = {o: o.hide_render for o in scene.objects}
    for o in scene.objects:
        if o.type in {"MESH", "CURVE", "FONT"}:
            o.hide_render = o not in sichtbar or o.name == "Okular_Durchblick"
    scene.render.film_transparent = True
    scene.cycles.film_transparent_glass = True
    scene.camera = bpy.data.objects["CAM_Okular"]
    scene.render.resolution_x = scene.render.resolution_y = 1200 if TEST else 2400
    webp(85, alpha=True)
    scene.render.filepath = str(ziel)
    bpy.ops.render.render(write_still=True)
    # kleinere Variante fuers Handy
    klein = bpy.data.images.load(str(ziel))
    klein.scale(klein.size[0] // 2, klein.size[1] // 2)
    klein.save_render(str(ziel).replace(".webp", "-klein.webp"), scene=scene)
    for o, h in gemerkt.items():
        o.hide_render = h
    scene.render.film_transparent = False


def linse_im_bild(cam):
    """Lage des Linsen-Durchblicks im aktuellen Bild: Mittelpunkt und Radien (0..1, y von oben)."""
    rand = bpy.data.objects["Okular_Rand"]
    r = 0.0128  # innerer Rand des Okular-Rings (Meter)
    mw = rand.matrix_world
    punkte = []
    for i in range(64):
        w = i / 64 * math.tau
        welt = mw @ Vector((math.cos(w) * r, math.sin(w) * r, 0))
        p = world_to_camera_view(scene, cam, welt)
        punkte.append((p.x, 1 - p.y))
    xs, ys = [p[0] for p in punkte], [p[1] for p in punkte]
    return {"x": round((min(xs) + max(xs)) / 2, 5), "y": round((min(ys) + max(ys)) / 2, 5),
            "rx": round((max(xs) - min(xs)) / 2, 5), "ry": round((max(ys) - min(ys)) / 2, 5)}


def rueckfahrt(kamera, breite, hoehe, ordner, bilder):
    """Bildfolge mit durchsichtiger Linse (Holdout) und deckendem Rest (Hintergrund-Kugel)."""
    cam = bpy.data.objects[kamera]
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = breite, hoehe
    scene.render.film_transparent = True
    scene.cycles.film_transparent_glass = True
    webp(74, alpha=True)
    ordner.mkdir(parents=True, exist_ok=True)
    linsen = []
    for b in bilder:
        scene.frame_set(b)
        linsen.append(linse_im_bild(cam))
        scene.render.filepath = str(ordner / f"{b:04d}.webp")
        bpy.ops.render.render(write_still=True)
        print("Bild", kamera, b)
    scene.render.film_transparent = False
    (ordner.parent / f"linse-{ordner.name}.json").write_text(json.dumps(linsen))


def leichte_folge(ordner, bilder):
    """Sparversion fuer schwache Handys: jedes zweite Bild, 60 % Groesse (gleiche Dateinamen)."""
    ziel = ordner.parent / f"{ordner.name}-leicht"
    ziel.mkdir(parents=True, exist_ok=True)
    webp(70, alpha=True)
    for b in bilder:
        if b % 2 == 0 and b != bilder[-1]:   # erstes und letztes Bild immer behalten
            continue
        img = bpy.data.images.load(str(ordner / f"{b:04d}.webp"))
        img.scale(round(img.size[0] * 0.6), round(img.size[1] * 0.6))
        img.save_render(str(ziel / f"{b:04d}.webp"), scene=scene)
        bpy.data.images.remove(img)
    print("Sparversion", ziel.name)


gpu_an()
scene.render.resolution_percentage = 100
if TEST:
    scene.cycles.samples = 32
    test = HIER / "test"
    okular_rand(test / "okular-rand.webp")
    rueckfahrt("CAM_Rueckfahrt_Quer", 1600, 900, test / "quer", [1, 20, 34, 60, 96])
    rueckfahrt("CAM_Rueckfahrt_Hoch", 900, 1600, test / "hoch", [1, 96])
else:
    alle = range(scene.frame_start, scene.frame_end + 1)
    if NUR in (None, "okular"):
        okular_rand(MEDIA / "okular-rand.webp")
    if NUR in (None, "quer"):
        rueckfahrt("CAM_Rueckfahrt_Quer", 1600, 900, MEDIA / "outro" / "quer", alle)
    if NUR in (None, "hoch"):
        rueckfahrt("CAM_Rueckfahrt_Hoch", 900, 1600, MEDIA / "outro" / "hoch", alle)
    if NUR in (None, "quer", "hoch", "leicht"):
        for name in ("quer", "hoch"):
            if NUR in (None, "leicht", name):
                leichte_folge(MEDIA / "outro" / name, alle)
print("RENDER FERTIG")
