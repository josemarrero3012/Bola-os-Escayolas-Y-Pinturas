"""Luz de estudio para la portada «Arquitectura suspendida».

Abre el .blend de José Manuel y cambia su estudio por uno de foto de producto: el
softbox cálido de arriba a la izquierda un poco más recogido, el relleno frío casi
apagado para que las sombras ganen fondo, dos tiras de contraluz que dibujan los
bordes de las molduras y la luz cenital de recorte. La escayola recibe una veladura
satinada (coat) que recoge esos reflejos. Después renderiza el póster transparente
de la web con la cámara de tres cuartos.

Uso:
  python blender/portada-luz.py RUTA/bolanos_architecture.blend SALIDA.png [ancho alto muestras]

La web usa SALIDA reducida: assets/img/arquitectura-escritorio.webp (1200×1350) y
assets/img/arquitectura-movil.webp (800×900). src/portada-3d.js repite esta misma luz
(mismas direcciones, colores y veladura) para que el 3D encaje encima del póster.
"""
import sys

import bpy
from mathutils import Vector

blend, salida, *resto = sys.argv[1:]
ancho, alto, muestras = (int(v) for v in resto) if resto else (1600, 1800, 128)

bpy.ops.wm.open_mainfile(filepath=blend)
escena = bpy.context.scene
estudio = bpy.data.collections["Presentation_Studio"]


def luz(nombre, posicion, potencia, color, tam, tam_y=None, objetivo=(0, 0, 0.2)):
    datos = bpy.data.lights.get(nombre) or bpy.data.lights.new(nombre, "AREA")
    datos.energy = potencia
    datos.color = color
    datos.shape = "RECTANGLE" if tam_y else "DISK"
    datos.size = tam
    if tam_y:
        datos.size_y = tam_y
    objeto = bpy.data.objects.get(nombre) or bpy.data.objects.new(nombre, datos)
    if objeto.name not in estudio.objects:
        estudio.objects.link(objeto)
    objeto.location = posicion
    # -Z apunta a la pieza y el lado largo de las tiras queda vertical
    objeto.rotation_euler = (Vector(objetivo) - objeto.location).to_track_quat("-Z", "Y").to_euler()
    return objeto


# Coordenadas de Blender (z arriba); la cámara mira desde delante a la derecha (+x, −y).
# Las tiras son estrechas: mucho brillo en el reflejo y poca luz difusa, para que las
# sombras no se aplanen.
luz("Key_Architectural_Softbox", (-3.473, -4.2, 6.055), 1900, (1.0, 0.92, 0.82), 2.0, 3.2)
luz("Fill_Front_Right", (4.027, -3.0, 2.555), 40, (0.84, 0.9, 1.0), 3.5)
luz("Rim_Top", (2.527, 3.0, 5.055), 650, (1.0, 0.96, 0.9), 3.0)
luz("Strip_Front_Left", (-6.0, -5.5, 2.4), 250, (1.0, 0.97, 0.93), 0.12, 5.0)
luz("Strip_Overhead", (0.4, -1.5, 7.5), 120, (1.0, 0.97, 0.92), 6.0, 0.12)
luz("Rim_Left_Strip", (-4.6, 3.6, 1.8), 1300, (0.84, 0.9, 1.0), 0.15, 4.5)
luz("Rim_Right_Strip", (5.2, 2.2, 2.4), 1300, (1.0, 0.88, 0.74), 0.15, 4.5)

fondo = escena.world.node_tree.nodes["Background"]
fondo.inputs[0].default_value = (0.62, 0.67, 0.76, 1)
fondo.inputs[1].default_value = 0.08

# Veladura satinada: reflejos nítidos de las tiras; el barro, con menos, conserva su color
for nombre, veladura, aspereza in (("Plaster_Ivory", 0.5, 0.06), ("Plaster_Warm", 0.5, 0.06), ("Terracotta_Mineral", 0.3, 0.08)):
    p = bpy.data.materials[nombre].node_tree.nodes["Principled BSDF"]
    p.inputs["Specular IOR Level"].default_value = 0.4
    p.inputs["Coat Weight"].default_value = veladura
    p.inputs["Coat Roughness"].default_value = aspereza

escena.camera = bpy.data.objects["Camera_Three_Quarter"]
escena.render.resolution_x, escena.render.resolution_y = ancho, alto
escena.render.resolution_percentage = 100
escena.render.film_transparent = True
escena.cycles.samples = muestras
escena.cycles.use_denoising = True
bpy.data.objects["Studio_Ground"].hide_render = True
escena.render.filepath = salida
bpy.ops.render.render(write_still=True)
print("PORTADA_RENDERIZADA", salida, flush=True)
