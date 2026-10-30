# Prepara la pieza de un paso de «Cómo trabajamos» para la web.
# 1. Pasa los materiales de marca de la pieza a la paleta actual (naranja y
#    blanco Bolaños) en el GLB, sin tocar la geometría ni la animación.
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

argumentos = sys.argv[1:]
fotograma = 96
if "--fotograma" in argumentos:
    i = argumentos.index("--fotograma")
    fotograma = int(argumentos[i + 1])
    del argumentos[i:i + 2]
BLEND, GLB, SALIDA = (Path(a) for a in [a for a in argumentos if not a.startswith("--")][-3:])
SALIDA.mkdir(parents=True, exist_ok=True)
rapido = "--rapido" in sys.argv


def lineal(hexa):
    """#RRGGBB en sRGB a color lineal, como lo guardan glTF y Blender."""
    c = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


# Material de la pieza -> color de la paleta (los demás se quedan como están)
PALETA = {
    "Azul Bolaños": lineal("#D9561A"),      # naranja Bolaños
    "Goma azul oscura": lineal("#2E1A10"),  # tostado muy oscuro
    "Tinta de plano": lineal("#A83A0C"),    # cotas y trazos en naranja hondo
    "Tapizado salvia": lineal("#E3CFBB"),   # lino cálido, sin verdes
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

# La sombra del fondo de estudio acaba en los bordes de ese plano: se desvanece
# hacia fuera para que en la web no se vea su rectángulo
import numpy as np
imagen = bpy.data.images.load(str(SALIDA / "paso.png"))
ancho, alto = imagen.size
pixeles = np.empty(ancho * alto * 4, dtype=np.float32)
imagen.pixels.foreach_get(pixeles)
pixeles = pixeles.reshape(alto, ancho, 4)
yy, xx = np.mgrid[0:alto, 0:ancho]
distancia = np.hypot((xx - ancho / 2) / (ancho / 2), (yy - alto / 2) / (alto / 2))
desvanecer = np.clip((0.98 - distancia) / 0.3, 0, 1)
sombra = pixeles[..., 3] < 0.985          # lo opaco es la maqueta; lo translúcido, su sombra
pixeles[..., 3] = np.where(sombra, pixeles[..., 3] * desvanecer, pixeles[..., 3])
imagen.pixels.foreach_set(pixeles.ravel())
imagen.filepath_raw = str(SALIDA / "paso.png")
imagen.file_format = "PNG"
imagen.save()
