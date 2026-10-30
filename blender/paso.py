# Prepara la pieza de un paso de «Cómo trabajamos» para la web.
# 1. Pasa los materiales de marca de la pieza a la paleta actual (verde y rojo
#    Bolaños) en el GLB, sin tocar la geometría ni la animación.
# 2. Abre el .blend, aplica los mismos colores y renderiza con Cycles el póster
#    con fondo transparente (se ve en móvil y mientras carga el 3D).
#
# Uso: python blender/paso.py PIEZA.blend PIEZA.glb SALIDA [--fotograma 96] [--rapido]
# Después: gltf-transform meshopt SALIDA/paso.glb assets/3d/paso-N.glb
import json
import struct
import sys
from pathlib import Path

import bpy

argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
BLEND, GLB, SALIDA = (Path(a) for a in argumentos[-3:])
SALIDA.mkdir(parents=True, exist_ok=True)
fotograma = int(sys.argv[sys.argv.index("--fotograma") + 1]) if "--fotograma" in sys.argv else 96
rapido = "--rapido" in sys.argv


def lineal(hexa):
    """#RRGGBB en sRGB a color lineal, como lo guardan glTF y Blender."""
    c = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


# Material de la pieza -> color de la paleta (los demás se quedan como están)
PALETA = {
    "Azul Bolaños": lineal("#0E3B2A"),      # verde Bolaños
    "Goma azul oscura": lineal("#072B1F"),  # verde más hondo
    "Tinta de plano": lineal("#D10A22"),    # cotas y trazos en el rojo de la marca
}

# 1. GLB: los colores viven en el bloque JSON
datos = GLB.read_bytes()
largo_json = struct.unpack("<I", datos[12:16])[0]
gltf = json.loads(datos[20:20 + largo_json])
binario = datos[20 + largo_json:]
for material in gltf.get("materials", []):
    color = PALETA.get(material.get("name"))
    if color:
        pbr = material.setdefault("pbrMetallicRoughness", {})
        alfa = pbr.get("baseColorFactor", [1, 1, 1, 1])[3]
        pbr["baseColorFactor"] = [round(x, 5) for x in color] + [alfa]
        print("Recoloreado:", material["name"])
texto = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf8")
texto += b" " * (-len(texto) % 4)
cuerpo = struct.pack("<II", len(texto), 0x4E4F534A) + texto + binario
(SALIDA / "paso.glb").write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + len(cuerpo)) + cuerpo)

# 2. Póster con Cycles desde el .blend del autor
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
for material in bpy.data.materials:
    color = PALETA.get(material.name)
    if color and material.node_tree:
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1)

# El fondo de estudio del autor pasa a recoger solo sombras: el fondo lo pone la web
for objeto in bpy.data.objects:
    if any(r.material and r.material.name == "Fondo marfil" for r in getattr(objeto, "material_slots", [])):
        objeto.is_shadow_catcher = True

escena = bpy.context.scene
escena.frame_set(fotograma)
escena.render.film_transparent = True
escena.render.engine = "CYCLES"
escena.cycles.device = "CPU"
escena.cycles.samples = 16 if rapido else 128
escena.cycles.use_denoising = True
escena.render.resolution_x = escena.render.resolution_y = 1100
escena.render.resolution_percentage = 40 if rapido else 100
escena.render.image_settings.file_format = "PNG"
escena.render.image_settings.color_mode = "RGBA"
escena.render.filepath = str(SALIDA / "paso.png")
bpy.ops.render.render(write_still=True)
