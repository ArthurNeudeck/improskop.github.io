"""Baut die Mikroskop-Szene fuer improskop.ch und speichert blender/mikroskop.blend.

Aufruf (aus dem Projektordner):
  /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python blender/build_mikroskop.py

ACHTUNG: Ueberschreibt mikroskop.blend. Wer das Modell von Hand in Blender
bearbeitet hat, rendert danach nur noch mit render_web.py und fuehrt dieses
Skript nicht mehr aus.
"""
import bpy, math
from pathlib import Path
from mathutils import Vector

HIER = Path(__file__).resolve().parent
PROJEKT = HIER.parent


def srgb(hexwert):
    """Hex-Farbe (sRGB) -> lineare RGBA-Werte fuer Blender."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (*(lin(int(hexwert[i:i + 2], 16)) for i in (0, 2, 4)), 1.0)


# Markenfarben (identisch mit den CSS-Tokens der Website)
HAEMATOXYLIN = "3B2A63"
LICHT = "EAB25B"
BUEHNE_HINTERGRUND = "1C1430"  # = --nacht im CSS, Hintergrund der Outro-Sektion

# --- Leere Szene -------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Improskop"
scene.unit_settings.system = "METRIC"


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c


C_MIKRO = collection("Mikroskop")
C_OKULAR = collection("Okular", C_MIKRO)
C_BUEHNE = collection("Bühne")
C_KAMERAS = collection("Kameras")


def link(obj, coll):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


# --- Materialien ---------------------------------------------------------------
def material(name, farbe=None, metallic=0.0, rauheit=0.4, coat=0.0, transmission=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    if farbe:
        p.inputs["Base Color"].default_value = srgb(farbe)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rauheit
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Transmission Weight"].default_value = transmission
    p.inputs["IOR"].default_value = ior
    return m


M_LACK = material("Lack_Haematoxylin", HAEMATOXYLIN, rauheit=0.32, coat=0.7)
M_CHROM = material("Chrom", "E6E9EE", metallic=1.0, rauheit=0.12)
M_MESSING = material("Messing_Licht", LICHT, metallic=1.0, rauheit=0.28)
M_GLAS = material("Linsenglas", "F4FBF8", rauheit=0.0, transmission=1.0, ior=1.5)
M_DUNKEL = material("Schwarz_Matt", "141018", rauheit=0.6)

M_LAMPE = bpy.data.materials.new("Lampe")
M_LAMPE.use_nodes = True
nt = M_LAMPE.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = srgb("FFE2A8")
em.inputs["Strength"].default_value = 6.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], out.inputs[0])

# Praeparat: cremeweiss mit beigen Verfaerbungen, wie der Hintergrund der Website
M_PRAEP = bpy.data.materials.new("Praeparat")
M_PRAEP.use_nodes = True
nt = M_PRAEP.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.35
rauschen = nt.nodes.new("ShaderNodeTexNoise")
rauschen.inputs["Scale"].default_value = 180.0
rauschen.inputs["Detail"].default_value = 6.0
rampe = nt.nodes.new("ShaderNodeValToRGB")
rampe.color_ramp.elements[0].position = 0.42
rampe.color_ramp.elements[0].color = srgb("F4EEE1")
rampe.color_ramp.elements[1].position = 0.7
rampe.color_ramp.elements[1].color = srgb("D8C39C")
nt.links.new(rauschen.outputs["Fac"], rampe.inputs["Fac"])
nt.links.new(rampe.outputs["Color"], bsdf.inputs["Base Color"])

# Durchblick: hier wird die Linse transparent, darunter liegt im Browser die echte Website
M_DURCHBLICK = bpy.data.materials.new("Linse_Durchblick")
M_DURCHBLICK.use_nodes = True
nt = M_DURCHBLICK.node_tree
nt.nodes.clear()
ho = nt.nodes.new("ShaderNodeHoldout")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(ho.outputs[0], out.inputs[0])


# --- Geometrie-Helfer --------------------------------------------------------------
def fertig(obj, name, mat, coll=C_MIKRO, bevel=0.0, glatt=True):
    obj.name = name
    obj.data.name = name
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    if bevel:
        b = obj.modifiers.new("Kante", "BEVEL")
        b.width = bevel
        b.segments = 4
        b.limit_method = "ANGLE"
    if glatt and obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
        if bevel:
            obj.modifiers.new("Glatt", "WEIGHTED_NORMAL")
    return link(obj, coll)


def zylinder(name, mat, radius, tiefe, ort, rot=(0, 0, 0), coll=C_MIKRO, bevel=0.0015, ecken=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=ecken, radius=radius, depth=tiefe, location=ort, rotation=rot)
    return fertig(bpy.context.object, name, mat, coll, bevel)


def kegel(name, mat, r1, r2, tiefe, ort, rot=(0, 0, 0), coll=C_MIKRO):
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r1, radius2=r2, depth=tiefe, location=ort, rotation=rot)
    return fertig(bpy.context.object, name, mat, coll, 0.001)


def quader(name, mat, groesse, ort, bevel=0.004, coll=C_MIKRO):
    bpy.ops.mesh.primitive_cube_add(size=1, location=ort)
    o = bpy.context.object
    o.scale = groesse
    bpy.ops.object.transform_apply(scale=True)
    return fertig(o, name, mat, coll, bevel)


def ring(name, mat, r_gross, r_klein, ort, rot=(0, 0, 0), coll=C_MIKRO):
    bpy.ops.mesh.primitive_torus_add(major_radius=r_gross, minor_radius=r_klein, major_segments=96,
                                     minor_segments=24, location=ort, rotation=rot)
    return fertig(bpy.context.object, name, mat, coll)


# --- Mikroskop ---------------------------------------------------------------------
# Masse in Metern. Vorne = -Y (dort sitzt man), Arm hinten (+Y).
quader("Fuss", M_LACK, (0.17, 0.21, 0.028), (0, 0.0, 0.014), bevel=0.012)
quader("Fuss_Platte", M_CHROM, (0.13, 0.17, 0.004), (0, 0.0, 0.030), bevel=0.0015)

# Arm: Kurve (in Blender direkt mit den Punkten verformbar)
kurve = bpy.data.curves.new("Arm", "CURVE")
kurve.dimensions = "3D"
kurve.bevel_mode = "ROUND"
kurve.bevel_depth = 0.021
kurve.bevel_resolution = 6
kurve.resolution_u = 24
kurve.use_fill_caps = True
sp = kurve.splines.new("BEZIER")
punkte = [(0, 0.072, 0.03), (0, 0.082, 0.16), (0, 0.035, 0.265)]
sp.bezier_points.add(len(punkte) - 1)
for bp, p in zip(sp.bezier_points, punkte):
    bp.co = p
    bp.handle_left_type = bp.handle_right_type = "AUTO"
arm = bpy.data.objects.new("Arm", kurve)
arm.data.materials.append(M_LACK)
C_MIKRO.objects.link(arm)
arm.scale.x = 1.15  # leicht oval

# Kopf, Revolver, Objektive
quader("Kopf", M_LACK, (0.05, 0.075, 0.035), (0, 0.005, 0.262), bevel=0.012)
zylinder("Revolver", M_CHROM, 0.028, 0.012, (0, -0.012, 0.238), ecken=96)
for i, (w, laenge, r) in enumerate([(0, 0.046, 0.0085), (2.1, 0.036, 0.0095), (4.2, 0.028, 0.011)]):
    dx, dy = math.sin(w) * 0.014, -math.cos(w) * 0.014
    oy = -0.012 + dy
    zylinder(f"Objektiv_{i + 1}", M_CHROM, r, laenge, (dx, oy, 0.232 - laenge / 2))
    ring(f"Objektiv_{i + 1}_Ring", M_MESSING, r + 0.0004, 0.0012, (dx, oy, 0.232 - laenge * 0.35))

# Tubus schraeg nach vorne (30 Grad)
NEIGUNG = math.radians(30)
ACHSE = Vector((0, -math.sin(NEIGUNG), math.cos(NEIGUNG)))
TUBUS_FUSS = Vector((0, -0.006, 0.272))
TUBUS_LAENGE = 0.13
mitte = TUBUS_FUSS + ACHSE * (TUBUS_LAENGE / 2)
zylinder("Tubus", M_LACK, 0.0215, TUBUS_LAENGE, mitte, rot=(NEIGUNG, 0, 0))
ring("Tubus_Ring", M_CHROM, 0.0218, 0.0016, TUBUS_FUSS + ACHSE * (TUBUS_LAENGE - 0.004), rot=(NEIGUNG, 0, 0))

# Okular (eigene Collection, wird fuer den Okular-Rand der Website separat gerendert)
OKULAR_FUSS = TUBUS_FUSS + ACHSE * TUBUS_LAENGE
OKULAR_LAENGE = 0.042
OKULAR_OBEN = OKULAR_FUSS + ACHSE * OKULAR_LAENGE
LINSE_R = 0.0135
# offene Roehre (ohne Deckel), damit man hineinsehen kann
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.0168, depth=OKULAR_LAENGE, end_fill_type="NOTHING",
                                    location=OKULAR_FUSS + ACHSE * (OKULAR_LAENGE / 2), rotation=(NEIGUNG, 0, 0))
huelse = fertig(bpy.context.object, "Okular_Huelse", M_CHROM, C_OKULAR)
dicke = huelse.modifiers.new("Wand", "SOLIDIFY")
dicke.thickness = 0.0016
huelse.modifiers.move(len(huelse.modifiers) - 1, 0)
ring("Okular_Rand", M_CHROM, 0.0152, 0.0024, OKULAR_OBEN, rot=(NEIGUNG, 0, 0), coll=C_OKULAR)
zylinder("Okular_Linse", M_GLAS, LINSE_R, 0.0012, OKULAR_OBEN - ACHSE * 0.0012, rot=(NEIGUNG, 0, 0),
         coll=C_OKULAR, bevel=0.0004, ecken=96)
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=LINSE_R, fill_type="NGON",
                                  location=OKULAR_OBEN - ACHSE * 0.004, rotation=(NEIGUNG, 0, 0))
fertig(bpy.context.object, "Okular_Durchblick", M_DURCHBLICK, C_OKULAR)

# Objekttisch mit Klemmen und Praeparat
quader("Objekttisch", M_LACK, (0.11, 0.1, 0.008), (0, -0.012, 0.142), bevel=0.003)
zylinder("Tisch_Blende", M_DUNKEL, 0.009, 0.0085, (0, -0.012, 0.142), bevel=0.0005)
for s in (-1, 1):
    quader(f"Klemme_{'links' if s < 0 else 'rechts'}", M_CHROM, (0.007, 0.04, 0.0018),
           (s * 0.03, -0.022, 0.1475), bevel=0.0008)
quader("Objekttraeger", M_GLAS, (0.075, 0.026, 0.0012), (0, -0.016, 0.1468), bevel=0.0003)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.016, 0.1476))
pr = bpy.context.object
pr.scale = (0.02, 0.018, 1)
bpy.ops.object.transform_apply(scale=True)
fertig(pr, "Praeparat", M_PRAEP)
quader("Tisch_Stuetze", M_LACK, (0.03, 0.03, 0.06), (0, 0.055, 0.11), bevel=0.006)

# Lampe unter dem Tisch
zylinder("Lampe_Gehaeuse", M_CHROM, 0.017, 0.022, (0, -0.012, 0.043), ecken=96)
zylinder("Lampe", M_LAMPE, 0.012, 0.003, (0, -0.012, 0.0545), bevel=0)

# Fokusrad (zwei Raeder, dreht sich in der Animation)
fokus = bpy.data.objects.new("Fokusrad", None)
fokus.empty_display_type = "ARROWS"
fokus.empty_display_size = 0.03
fokus.location = (0, 0.072, 0.115)
C_MIKRO.objects.link(fokus)
for s, name in ((-1, "links"), (1, "rechts")):
    for teil, r, d, x, mat in (("gross", 0.024, 0.011, 0.034, M_MESSING), ("klein", 0.014, 0.01, 0.046, M_CHROM)):
        o = zylinder(f"Fokusrad_{name}_{teil}", mat, r, d, (s * x, 0.072, 0.115), rot=(0, math.radians(90), 0),
                     ecken=48)
        o.parent = fokus
        o.matrix_parent_inverse = fokus.matrix_world.inverted()
zylinder("Fokus_Achse", M_CHROM, 0.006, 0.1, (0, 0.072, 0.115), rot=(0, math.radians(90), 0))

# Schriftzug auf dem Fuss (Text bleibt editierbar)
bpy.ops.object.text_add(location=(0, -0.1052, 0.016), rotation=(math.radians(90), 0, 0))
txt = bpy.context.object
txt.data.body = "IMPROSKOP"
txt.data.align_x = "CENTER"
txt.data.align_y = "CENTER"
txt.data.size = 0.014
txt.data.extrude = 0.0006
txt.data.space_character = 1.15
fertig(txt, "Schriftzug", M_MESSING, glatt=False)

# --- Buehne & Licht --------------------------------------------------------------
world = bpy.data.worlds.new("Buehne_Hintergrund")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = srgb(BUEHNE_HINTERGRUND)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.world = world

# Boden: im Dunkeln exakt Hintergrundfarbe, im Scheinwerfer heller
boden_m = bpy.data.materials.new("Buehnenboden")
boden_m.use_nodes = True
nt = boden_m.node_tree
nt.nodes.clear()
diff = nt.nodes.new("ShaderNodeBsdfPrincipled")
diff.inputs["Base Color"].default_value = srgb("2E2546")
diff.inputs["Roughness"].default_value = 0.5
hinten = nt.nodes.new("ShaderNodeEmission")  # = Hintergrund, macht den Rand unsichtbar
hinten.inputs["Color"].default_value = srgb(BUEHNE_HINTERGRUND)
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1 / 0.75, 1 / 0.75, 1)  # Radius des sichtbaren Bodens: 75 cm
grad = nt.nodes.new("ShaderNodeTexGradient")
grad.gradient_type = "SPHERICAL"
rampe = nt.nodes.new("ShaderNodeValToRGB")
rampe.color_ramp.interpolation = "EASE"
rampe.color_ramp.elements[0].position = 0.0
rampe.color_ramp.elements[1].position = 0.75
mix = nt.nodes.new("ShaderNodeMixShader")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
nt.links.new(mp.outputs[0], grad.inputs["Vector"])
nt.links.new(grad.outputs["Fac"], rampe.inputs["Fac"])
nt.links.new(rampe.outputs["Color"], mix.inputs["Fac"])
nt.links.new(hinten.outputs[0], mix.inputs[1])
nt.links.new(diff.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
boden = fertig(bpy.context.object, "Buehnenboden", boden_m, C_BUEHNE, glatt=False)

# Hintergrund-Kugel: nur fuer die Kamera sichtbar. So bleibt der Himmel beim transparenten
# Rendern deckend, und nur die Linse (Holdout) wird durchsichtig.
kugel_m = bpy.data.materials.new("Hintergrund_Kugel")
kugel_m.use_nodes = True
nt = kugel_m.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = srgb(BUEHNE_HINTERGRUND)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], out.inputs[0])
bpy.ops.mesh.primitive_uv_sphere_add(radius=18, segments=48, ring_count=24)
kugel = fertig(bpy.context.object, "Hintergrund_Kugel", kugel_m, C_BUEHNE, glatt=False)
for strahl in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
    setattr(kugel, strahl, False)

licht = bpy.data.lights.new("Scheinwerfer", "SPOT")
licht.energy = 170
licht.spot_size = math.radians(24)
licht.spot_blend = 0.6
licht.shadow_soft_size = 0.12
licht.color = srgb("FFF1DC")[:3]
o = bpy.data.objects.new("Scheinwerfer", licht)
o.location = (-0.75, -1.0, 1.65)
C_BUEHNE.objects.link(o)
ziel_licht = bpy.data.objects.new("Scheinwerfer_Ziel", None)
ziel_licht.location = (0, 0, 0.15)
C_BUEHNE.objects.link(ziel_licht)
c = o.constraints.new("TRACK_TO")
c.target = ziel_licht
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"

gegen = bpy.data.lights.new("Gegenlicht", "AREA")
gegen.energy = 45
gegen.size = 0.6
gegen.color = srgb(LICHT)[:3]
o = bpy.data.objects.new("Gegenlicht", gegen)
o.location = (0.55, 0.75, 0.55)
C_BUEHNE.objects.link(o)
c = o.constraints.new("TRACK_TO")
c.target = ziel_licht
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"

# --- Kameras -------------------------------------------------------------------
MITTE = Vector((0, -0.01, 0.2))
ENDE_START, ENDE = 1, 96
scene.frame_start, scene.frame_end = ENDE_START, ENDE
scene.render.fps = 24


def kamera(name, linse=50.0):
    cam = bpy.data.cameras.new(name)
    cam.lens = linse
    cam.clip_start = 0.002
    o = bpy.data.objects.new(name, cam)
    C_KAMERAS.objects.link(o)
    return o


def rueckfahrt(name, start_abstand, ende_ort, ende_linse, shift):
    """Kamera faehrt von 'im Okular' zur Ansicht des ganzen Mikroskops."""
    cam = kamera(name)
    ziel = bpy.data.objects.new(f"{name}_Ziel", None)
    ziel.empty_display_size = 0.02
    C_KAMERAS.objects.link(ziel)
    c = cam.constraints.new("TRACK_TO")
    c.target = ziel
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    schluessel = [
        # Bild, Kamera-Ort, Ziel-Ort, Brennweite, Shift
        (ENDE_START, OKULAR_OBEN + ACHSE * start_abstand, OKULAR_OBEN, 50.0, (0, 0)),
        (34, OKULAR_OBEN + ACHSE * 0.42 + Vector((-0.06, -0.05, 0)), OKULAR_OBEN.lerp(MITTE, 0.5), 45.0,
         (shift[0] * 0.3, shift[1] * 0.3)),
        (ENDE, Vector(ende_ort), MITTE, ende_linse, shift),
    ]
    for bild, ort, zielort, linse, (sx, sy) in schluessel:
        scene.frame_set(bild)
        cam.location = ort
        ziel.location = zielort
        cam.data.lens = linse
        cam.data.shift_x, cam.data.shift_y = sx, sy
        cam.keyframe_insert("location", frame=bild)
        ziel.keyframe_insert("location", frame=bild)
        cam.data.keyframe_insert("lens", frame=bild)
        cam.data.keyframe_insert("shift_x", frame=bild)
        cam.data.keyframe_insert("shift_y", frame=bild)
    return cam


# Laptop (Querformat): Mikroskop am Ende rechts, Platz fuer Footer links
CAM_QUER = rueckfahrt("CAM_Rueckfahrt_Quer", 0.12, (-0.5, -0.78, 0.52), 35.0, (-0.2, 0.0))
# Handy (Hochformat): Mikroskop am Ende oben, Footer darunter
CAM_HOCH = rueckfahrt("CAM_Rueckfahrt_Hoch", 0.10, (-0.48, -0.8, 0.55), 42.0, (0.0, -0.1))

# Okular-Rand fuer den Einstieg der Website: orthografisch von oben in die Linse
cam = kamera("CAM_Okular")
cam.data.type = "ORTHO"
OKULAR_SICHT = 0.06  # sichtbare Breite in Metern
cam.data.ortho_scale = OKULAR_SICHT
cam.location = OKULAR_OBEN + ACHSE * 0.2
cam.rotation_euler = ACHSE.to_track_quat("Z", "Y").to_euler()  # schaut entlang der Tubus-Achse

# Fokusrad dreht sich am Ende eine Umdrehung
scene.frame_set(60)
fokus.rotation_euler.x = 0
fokus.keyframe_insert("rotation_euler", index=0, frame=60)
fokus.rotation_euler.x = math.tau
fokus.keyframe_insert("rotation_euler", index=0, frame=ENDE)

scene.camera = CAM_QUER
scene.frame_set(ENDE_START)

# --- Render-Grundeinstellungen ------------------------------------------------
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900

# --- Notiz in der Datei ------------------------------------------------------------
notiz = bpy.data.texts.new("LIESMICH")
notiz.write(f"""IMPROSKOP – Mikroskop fuer die Website
==========================================

Aufbau
- Collection "Mikroskop": alle Teile mit deutschen Namen. "Arm" ist eine Kurve:
  im Edit-Mode Punkte verschieben, um die Form zu aendern.
- Collection "Okular": Huelse, Rand, Linse und "Okular_Durchblick" (Holdout: dort wird
  das Bild transparent, im Browser liegt darunter die echte Website).
- Material "Praeparat": cremefarbene Noise-Textur auf dem Objekttraeger.
- "Hintergrund_Kugel" (Collection Buehne): nur fuer die Kamera sichtbar, haelt den Himmel
  beim transparenten Rendern deckend.
- Farben: Material "Lack_Haematoxylin" (#{HAEMATOXYLIN}), "Messing_Licht" (#{LICHT}).
  Hintergrund: World "Buehne_Hintergrund" (#{BUEHNE_HINTERGRUND}) muss zur CSS-Variable --nacht passen.
- Kameras: "CAM_Rueckfahrt_Quer" (Laptop) und "CAM_Rueckfahrt_Hoch" (Handy) fahren
  von Bild 1 (im Okular) bis Bild 96 (ganzes Mikroskop). Wohin sie schauen, steuern
  die Empties "..._Ziel". "CAM_Okular" rendert den Okular-Rand fuer den Seiteneinstieg.
- "Fokusrad" (Empty) dreht sich von Bild 60 bis 96.

Neu rendern (Terminal, im Projektordner):
  /Applications/Blender.app/Contents/MacOS/Blender --background blender/mikroskop.blend --python blender/render_web.py
  Optional nur Testbilder:  ... --python blender/render_web.py -- --test
  Nur ein Format:           ... --python blender/render_web.py -- --nur quer   (oder hoch / okular)
Die Bilder landen direkt in docs/media/outro/ (+ linse-quer.json / linse-hoch.json mit der
Lage der Linse in jedem Bild) und docs/media/okular-rand.webp.

Masse fuer die Website (nicht aendern ohne script.js anzupassen):
  Linsenradius {LINSE_R} m, CAM_Okular sichtbare Breite {OKULAR_SICHT} m
""")

bpy.ops.wm.save_as_mainfile(filepath=str(HIER / "mikroskop.blend"))
print("GESPEICHERT", HIER / "mikroskop.blend")
