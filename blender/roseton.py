# Rosetón de escayola para la portada.
# Modela la pieza por procedimiento, hornea su oclusión ambiental en los vértices,
# la exporta a GLB y renderiza con Cycles los pósteres que se ven mientras carga
# el 3D (o si el navegador no lo admite).
#
# Uso: python blender/roseton.py SALIDA   (con el módulo bpy de Blender 5.x instalado)
import math
import sys
from pathlib import Path

import bpy  # bpy primero: carga bmesh y mathutils
import bmesh
from mathutils import Vector

SALIDA = Path(sys.argv[-1] if len(sys.argv) > 1 else "build-3d")
SALIDA.mkdir(parents=True, exist_ok=True)
TAU = math.tau

# ---------------------------------------------------------------------------
# Utilidades de geometría
# ---------------------------------------------------------------------------

def superficie(bm, f, nu, nv, cerrar_v=False):
    """Malla de cuadriláteros a partir de f(u, v) -> (x, y, z), u y v en [0, 1]."""
    filas = []
    cols = nv if cerrar_v else nv + 1
    for i in range(nu + 1):
        u = i / nu
        filas.append([bm.verts.new(f(u, j / nv)) for j in range(cols)])
    for i in range(nu):
        for j in range(nv if cerrar_v else nv):
            j2 = (j + 1) % cols
            if not cerrar_v and j == nv:
                continue
            a, b, c, d = filas[i][j], filas[i + 1][j], filas[i + 1][j2], filas[i][j2]
            try:
                bm.faces.new((a, b, c, d))
            except ValueError:
                pass


def torno(bm, perfil, segmentos):
    """Gira un perfil [(r, z), ...] alrededor del eje Z."""
    n = len(perfil) - 1

    def f(u, v):
        r, z = perfil[round(u * n)]
        a = v * TAU
        return (r * math.cos(a), r * math.sin(a), z)

    superficie(bm, f, n, segmentos, cerrar_v=True)


def suave(t):
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------
# Pieza
# ---------------------------------------------------------------------------

bm = bmesh.new()

# Base torneada: canto, gola, filete, media caña y lecho de las hojas
perfil = [(1.0, 0.0), (1.0, 0.025)]
for k in range(1, 25):                         # gola (curva en S)
    t = k / 24
    perfil.append((1.0 - 0.09 * t, 0.025 + 0.065 * suave(t) + 0.012 * math.sin(t * math.pi)))
perfil += [(0.885, 0.092), (0.865, 0.092)]
for k in range(1, 17):                         # media caña hacia el lecho
    t = k / 16
    perfil.append((0.865 - 0.07 * t, 0.092 - 0.03 * math.sin(t * math.pi / 2)))
perfil += [(0.70, 0.062), (0.55, 0.06), (0.40, 0.06), (0.24, 0.06), (0.0, 0.06)]
torno(bm, perfil, 384)

# Sarta de perlas
N_PERLAS, R_PERLAS, r_perla = 56, 0.835, 0.021
for k in range(N_PERLAS):
    a = k / N_PERLAS * TAU
    c = Vector((R_PERLAS * math.cos(a), R_PERLAS * math.sin(a), 0.088))
    def perla(u, v, c=c):
        th, ph = v * TAU, (u - 0.5) * math.pi
        return (c.x + r_perla * math.cos(ph) * math.cos(th),
                c.y + r_perla * math.cos(ph) * math.sin(th),
                c.z + r_perla * 0.8 * math.sin(ph))
    superficie(bm, perla, 12, 20, cerrar_v=True)

def hoja(angulo, r0, r1, ancho, alto, lobulos, rizo):
    """Hoja de acanto: lóbulos dentados, nervio central, venas que bajan a cada
    lóbulo, borde ondulado y punta que se levanta."""
    base = 0.06
    ca, sa = math.cos(angulo), math.sin(angulo)

    def f(u, v):
        s = v * 2 - 1                                       # -1 .. 1 a lo ancho
        a = abs(s)
        lob = math.sin(u * math.pi * lobulos) ** 2
        w = ancho * math.sin(math.pi * u ** 0.75) ** 0.9
        w *= 1 + 0.2 * lob + 0.05 * abs(math.sin(u * math.pi * lobulos * 4)) * lob  # lóbulos y dientes
        r = r0 + (r1 - r0) * u
        y = s * w
        z = base + alto * (1 - s * s) ** 0.7 * math.sin(math.pi * min(1, u * 1.05)) ** 0.6
        z += 0.013 * math.exp(-(s / 0.11) ** 2) * (1 - 0.7 * u)               # nervio
        z -= 0.006 * math.exp(-((a - 0.18) / 0.06) ** 2) * math.sin(math.pi * u)  # canal junto al nervio
        vena = max(0.0, math.cos(TAU * (u * lobulos - a * 0.6))) ** 8
        z -= 0.006 * vena * a * (1 - a) * 4 * math.sin(math.pi * u)           # venas hacia cada lóbulo
        z += 0.012 * s * s * math.sin(u * math.pi * lobulos * 2)              # borde ondulado
        z += rizo * u ** 3 * (1 - s * s)                                      # la punta se levanta
        z = base + (z - base) * (1 - s ** 10)                                 # el borde apoya en el lecho
        return (r * ca - y * sa, r * sa + y * ca, z)

    superficie(bm, f, 140, 56)


for k in range(8):
    a = k / 8 * TAU
    hoja(a, 0.20, 0.79, 0.15, 0.085, 6, 0.045)
    hoja(a + TAU / 16, 0.22, 0.6, 0.08, 0.05, 4, 0.015)

# Anillo que abraza el centro
def anillo(u, v):
    th, ph = v * TAU, u * TAU
    R, r = 0.215, 0.022
    return ((R + r * math.cos(ph)) * math.cos(th), (R + r * math.cos(ph)) * math.sin(th), 0.07 + r * math.sin(ph))
superficie(bm, anillo, 24, 192, cerrar_v=True)

# Florón central gallonado
def floron(u, v):
    th, ph = v * TAU, u * math.pi / 2
    g = 1 + 0.08 * math.cos(16 * th) * math.cos(ph) ** 0.5
    R = 0.19 * g * math.cos(ph)
    return (R * math.cos(th), R * math.sin(th), 0.07 + 0.13 * math.sin(ph))
superficie(bm, floron, 40, 256, cerrar_v=True)

def boton(u, v):
    th, ph = v * TAU, u * math.pi / 2
    return (0.045 * math.cos(ph) * math.cos(th), 0.045 * math.cos(ph) * math.sin(th), 0.195 + 0.03 * math.sin(ph))
superficie(bm, boton, 16, 64, cerrar_v=True)

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

# ---------------------------------------------------------------------------
# Escena
# ---------------------------------------------------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
malla = bpy.data.meshes.new("Roseton")
bm.to_mesh(malla)
bm.free()
for p in malla.polygons:
    p.use_smooth = True
roseton = bpy.data.objects.new("Roseton", malla)
bpy.context.scene.collection.objects.link(roseton)
print("Caras:", len(malla.polygons), "Vértices:", len(malla.vertices))

# Escayola gris clara, mate
yeso = bpy.data.materials.new("Yeso")
yeso.use_nodes = True
bsdf = yeso.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.33, 0.33, 0.325, 1)   # gris perla en lineal (≈ #9C9C9A)
bsdf.inputs["Roughness"].default_value = 0.9
malla.materials.append(yeso)

mundo = bpy.data.worlds.new("Mundo")
mundo.use_nodes = True
fondo = mundo.node_tree.nodes["Background"]
fondo.inputs["Color"].default_value = (0.9, 0.9, 0.88, 1)
fondo.inputs["Strength"].default_value = 0.6
bpy.context.scene.world = mundo

escena = bpy.context.scene
escena.render.engine = "CYCLES"
escena.cycles.device = "CPU"
rapido = "--rapido" in sys.argv

# Oclusión ambiental horneada en los vértices: la web la usa para oscurecer
# los fondos de las hojas y las juntas, como en una pieza real
roseton.select_set(True)
bpy.context.view_layer.objects.active = roseton
ao = malla.color_attributes.new("AO", "BYTE_COLOR", "POINT")
malla.color_attributes.active_color = ao
mundo.light_settings.distance = 0.12
escena.cycles.samples = 16 if rapido else 96
bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")

# Exporta solo la pieza (con su oclusión); el techo lo pone la web
bpy.ops.object.select_all(action="DESELECT")
roseton.select_set(True)
bpy.context.view_layer.objects.active = roseton
bpy.ops.export_scene.gltf(
    filepath=str(SALIDA / "roseton.glb"),
    use_selection=True,
    export_format="GLB",
    export_materials="NONE",
    export_texcoords=False,
    export_vertex_color="ACTIVE",
    export_apply=True,
)

# Techo blanco de yeso
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
techo = bpy.context.active_object
pintura = bpy.data.materials.new("TechoBlanco")
pintura.use_nodes = True
pb = pintura.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (0.9, 0.89, 0.86, 1)
pb.inputs["Roughness"].default_value = 0.85
techo.data.materials.append(pintura)

# Luz rasante: un foco lejano y estrecho desde la izquierda, casi a ras del techo,
# para que cada hoja proyecte una sombra larga sobre el blanco
bpy.ops.object.light_add(type="SPOT", location=(-5.5, 1.3, 0.75))
rasante = bpy.context.active_object
rasante.data.energy = 3400
rasante.data.spot_size = math.radians(34)
rasante.data.spot_blend = 0.7
rasante.data.shadow_soft_size = 0.2
rasante.data.color = (1.0, 0.97, 0.92)
rasante.rotation_euler = (Vector((0.3, -0.1, 0.0)) - rasante.location).to_track_quat("-Z", "Y").to_euler()

escena.cycles.samples = 24 if rapido else 160
escena.render.resolution_percentage = 40 if rapido else 100
escena.cycles.use_denoising = True
escena.view_settings.view_transform = "AgX"
escena.view_settings.look = "AgX - Base Contrast"
escena.view_settings.exposure = 0.75
escena.render.image_settings.file_format = "PNG"


def render(nombre, ancho, alto, pos, mira, lente):
    bpy.ops.object.camera_add(location=pos)
    cam = bpy.context.active_object
    cam.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lente
    escena.camera = cam
    escena.render.resolution_x = ancho
    escena.render.resolution_y = alto
    escena.render.filepath = str(SALIDA / nombre)
    bpy.ops.render.render(write_still=True)


if "--sin-render" not in sys.argv:
    # Escritorio: la pieza a la derecha, sitio para el titular a la izquierda
    render("roseton-escritorio.png", 1920, 1080, (-1.45, -1.85, 3.5), (-1.12, 0.1, 0.0), 37)
    # Móvil: la pieza abajo, asomando
    if "--solo-escritorio" not in sys.argv:
        render("roseton-movil.png", 900, 1400, (0.0, -1.0, 3.6), (0.0, 0.85, 0.0), 40)
