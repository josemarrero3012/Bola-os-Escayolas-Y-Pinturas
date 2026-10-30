"""Piezas comunes de las maquetas de «Cómo trabajamos».

Cada paso tiene su propio escenario, pero todas comparten lo que las hace de la misma
familia: los materiales (con los nombres de la maqueta del paso 01, ya en la paleta de
la web), los cantos suaves, el estudio de tres luces, la cámara axonométrica y un bucle
de seis segundos (144 fotogramas a 24 fps) exportado como un solo clip.
"""
import json
import math
import struct
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

FOTOGRAMAS = 144
NADA = .0001
# Dirección de la cámara del paso 01; la web mira desde la misma
DIRECCION_CAMARA = Vector((5.8, -8, 6.8)).normalized()

modelo = None
estudio = None
_grupo_animacion = "Maqueta · 6 s"


def iniciar(nombre):
    """Escena vacía con la colección de la maqueta y la del estudio."""
    global modelo, estudio, _grupo_animacion
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.frame_start = 0
    s.frame_end = FOTOGRAMAS
    s.render.fps = 24
    modelo = bpy.data.collections.new(nombre)
    s.collection.children.link(modelo)
    estudio = bpy.data.collections.new("Estudio de render")
    s.collection.children.link(estudio)
    _grupo_animacion = nombre.split("·")[-1].strip().capitalize() + " · 6 s"
    return s


# --- Materiales ------------------------------------------------------------------

def mat(nombre, color, rugosidad=.6, metal=0):
    if nombre in bpy.data.materials:
        return bpy.data.materials[nombre]
    def lin(v):
        return v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4
    rgb = tuple(lin(int(color[i:i + 2], 16) / 255) for i in (0, 2, 4))
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    m.diffuse_color = (*rgb, 1)
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rugosidad
    p.inputs["Metallic"].default_value = metal
    return m


class Paleta:
    """Los materiales del paso 01 en los colores de la web (paso.py los deja igual)."""
    def __init__(self):
        self.blanco = mat("Escayola · blanco mineral", "EEECE5", .78)
        self.marfil = mat("Acabado satinado", "FAF7EC", .45)
        self.piedra = mat("Piedra caliza", "D5CBBB", .82)
        self.suelo = mat("Caliza clara", "E6DFD0", .8)
        self.verde = mat("Azul Bolaños", "0E3B2A", .46)
        self.goma = mat("Goma azul oscura", "072B1F", .84)
        self.tinta = mat("Tinta de plano", "D10A22", .8)
        self.ocre = mat("Cinta · ocre suave", "E5C77D", .42, .25)
        self.acero = mat("Acero cepillado", "B6BBC3", .3, .72)
        self.papel = mat("Papel cálido", "FFFCF2", .85)
        self.pantalla = mat("Pantalla LCD", "DAE4CD", .32)
        self.grafito = mat("Grafito", "34363D", .8)


# --- Primitivas con cantos suaves -------------------------------------------------

def enlazar(o, col=None):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    (col or modelo).objects.link(o)
    return o


def _bisel(o, ancho, segmentos=4):
    b = o.modifiers.new("Bordes suaves", "BEVEL")
    b.width = ancho
    b.segments = segmentos
    n = o.modifiers.new("Normales", "WEIGHTED_NORMAL")
    n.keep_sharp = True


def grupo(nombre, loc=(0, 0, 0), padre=None, rot=(0, 0, 0), escala=(1, 1, 1)):
    o = bpy.data.objects.new(nombre, None)
    modelo.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.scale = escala
    o.parent = padre
    return o


def malla(nombre, vertices, caras, ma, padre=None, loc=(0, 0, 0), rot=(0, 0, 0), bisel=0):
    m = bpy.data.meshes.new(nombre)
    m.from_pydata(vertices, [], caras)
    bm = bmesh.new()
    bm.from_mesh(m)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)    # caras siempre hacia fuera
    bm.to_mesh(m)
    bm.free()
    m.update()
    o = bpy.data.objects.new(nombre, m)
    modelo.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.parent = padre
    o.data.materials.append(ma)
    if bisel:
        _bisel(o, bisel)
    return o


def caja(nombre, loc, dims, ma, padre=None, bisel=.012, rot=(0, 0, 0)):
    x, y, z = [v / 2 for v in dims]
    vs = [(-x, -y, -z), (-x, -y, z), (-x, y, -z), (-x, y, z), (x, -y, -z), (x, -y, z), (x, y, -z), (x, y, z)]
    fs = [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]
    return malla(nombre, vs, fs, ma, padre, loc, rot, bisel)


def prisma(nombre, perfil, largo, ma, padre=None, loc=(0, 0, 0), rot=(0, 0, 0), bisel=0):
    """Extruye en X un perfil cerrado (y, z) dado en sentido antihorario."""
    n = len(perfil)
    vs = [(-largo / 2, y, z) for y, z in perfil] + [(largo / 2, y, z) for y, z in perfil]
    caras = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    caras += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return malla(nombre, vs, caras, ma, padre, loc, rot, bisel)


def cilindro(nombre, loc, r, alto, ma, padre=None, rot=(0, 0, 0), lados=32, bisel=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=lados, radius=r, depth=alto, location=(0, 0, 0))
    o = enlazar(bpy.context.object)
    o.name = nombre
    o.location = loc
    o.rotation_euler = rot
    o.parent = padre
    o.data.materials.append(ma)
    _bisel(o, min(.008, alto * .2, r * .3) if bisel is None else bisel, 3)
    return o


def suave(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def esfera(nombre, loc, r, ma, padre=None, escala=(1, 1, 1), segmentos=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segmentos, ring_count=segmentos // 2, radius=r)
    o = suave(enlazar(bpy.context.object))
    o.name = nombre
    o.location = loc
    o.scale = escala
    o.parent = padre
    o.data.materials.append(ma)
    return o


def cupula(nombre, loc, r, ma, padre=None, escala=(1, 1, 1), segmentos=48):
    """Media esfera apoyada en su base (z = 0)."""
    m = bpy.data.meshes.new(nombre)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segmentos, v_segments=segmentos // 2, radius=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-5], context="VERTS")
    borde = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=borde, sides=0)
    bm.to_mesh(m)
    bm.free()
    o = bpy.data.objects.new(nombre, m)
    modelo.objects.link(o)
    suave(o)
    o.location = loc
    o.scale = escala
    o.parent = padre
    o.data.materials.append(ma)
    return o


def cono(nombre, loc, r_base, r_punta, alto, ma, padre=None, rot=(0, 0, 0), lados=32):
    bpy.ops.mesh.primitive_cone_add(vertices=lados, radius1=r_base, radius2=r_punta, depth=alto)
    o = suave(enlazar(bpy.context.object))
    o.name = nombre
    o.location = loc
    o.rotation_euler = rot
    o.parent = padre
    o.data.materials.append(ma)
    return o


def aro(nombre, loc, r, grosor, ma, padre=None, rot=(0, 0, 0), aplastado=.35, lados=64):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=grosor, major_segments=lados, minor_segments=10)
    o = suave(enlazar(bpy.context.object))
    o.name = nombre
    o.location = loc
    o.rotation_euler = rot
    o.scale = (1, 1, aplastado)
    o.parent = padre
    o.data.materials.append(ma)
    return o


def texto(nombre, cuerpo, loc, tam, ma, padre=None, rot=(0, 0, 0), alinear="CENTER", negrita=False):
    bpy.ops.object.select_all(action="DESELECT")
    curva = bpy.data.curves.new(nombre, "FONT")
    curva.body = cuerpo
    curva.size = tam
    curva.align_x = alinear
    curva.align_y = "CENTER"
    curva.extrude = .0006
    curva.resolution_u = 6
    if negrita:    # engorda el contorno de la letra: la fuente de Blender no trae negrita
        curva.offset = tam * .035
    o = bpy.data.objects.new(nombre, curva)
    modelo.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.parent = padre
    curva.materials.append(ma)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o.select_set(False)
    return o


def trazo(nombre, a, b, r, ma, padre=None, lados=12):
    a, b = Vector(a), Vector(b)
    o = cilindro(nombre, (a + b) / 2, r, (b - a).length, ma, padre, lados=lados)
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return o


def barra(nombre, inicio, dims, ma, padre, bisel=None):
    """Trazo que crece desde su extremo izquierdo: el grupo se escala en X."""
    g = grupo(nombre, inicio, padre)
    caja(nombre + " · trazo", (dims[0] / 2, 0, 0), dims, ma, g, bisel if bisel is not None else min(dims[1:]) * .3)
    return g


def visto(nombre, loc, tam, ma, padre=None, rot=(0, 0, 0), grosor=None):
    """Marca de comprobación en el plano XY del grupo."""
    g = grupo(nombre, loc, padre, rot)
    r = grosor or tam * .1
    trazo(nombre + " · corto", (-.5 * tam, .05 * tam, 0), (-.15 * tam, -.3 * tam, 0), r, ma, g)
    trazo(nombre + " · largo", (-.15 * tam, -.3 * tam, 0), (.55 * tam, .42 * tam, 0), r, ma, g)
    return g


# --- Animación en bucle ----------------------------------------------------------

def clave(o, prop, f, valor):
    setattr(o, prop, valor)
    o.keyframe_insert(data_path=prop, frame=f, group=_grupo_animacion)


def aparece(o, entra, lleno, sale, fuera, eje=None):
    """Escala de nada a entero y vuelta, para que el bucle cierre sin saltos."""
    for f, v in [(0, NADA), (entra, NADA), (lleno, 1), (sale, 1), (fuera, NADA), (FOTOGRAMAS, NADA)]:
        clave(o, "scale", f, (v, 1, 1) if eje == "x" else (v, v, v))


def crece(o, entra, lleno, sale, fuera):
    aparece(o, entra, lleno, sale, fuera, eje="x")


def visible_entre(o, *tramos):
    """Se enciende y se apaga de golpe en cada tramo [desde, hasta)."""
    def valor(f):
        return 1 if any(a <= f < b for a, b in tramos) else NADA
    fotogramas = {0, FOTOGRAMAS}
    for a, b in tramos:
        fotogramas |= {a - 1, a, b - 1, b}
    for f in sorted(f for f in fotogramas if 0 <= f <= FOTOGRAMAS):
        clave(o, "scale", f, (valor(f),) * 3)


def recorrido(o, prop, claves):
    for f, v in claves:
        clave(o, prop, f, v)


# --- Estudio, cámara y exportación -------------------------------------------------

def mirando_a_camara():
    """Giro que pone el eje Z local de una pieza hacia la cámara (para insignias)."""
    return DIRECCION_CAMARA.to_track_quat("Z", "Y").to_euler()


def estudio_y_camara(nombre_camara, fotograma, margen=1.12):
    """Suelo de estudio, las tres luces del paso 01 y una cámara ortográfica encuadrada
    sobre la maqueta en el fotograma del póster."""
    s = bpy.context.scene
    fondo = caja("Fondo", (0, 0, -.05), (200, 200, .10), mat("Fondo marfil", "F2F0E9", .9), None, 0)
    enlazar(fondo, estudio)

    def area(nombre, loc, potencia, tam, color, objetivo):
        d = bpy.data.lights.new(nombre, "AREA")
        d.energy = potencia
        d.shape = "DISK"
        d.size = tam
        d.color = color
        o = bpy.data.objects.new(nombre, d)
        estudio.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(objetivo) - o.location).to_track_quat("-Z", "Y").to_euler()

    area("Luz principal", (1, -4, 7), 900, 5, (1, .95, .87), (0, 0, .7))
    area("Relleno", (-4, -1, 4), 550, 4, (.86, .91, 1), (0, 0, .7))
    area("Contraluz", (3, 4, 6), 750, 3, (1, .96, .9), (0, 0, .8))

    d = bpy.data.cameras.new(nombre_camara)
    cam = bpy.data.objects.new(nombre_camara, d)
    estudio.objects.link(cam)
    cam.location = DIRECCION_CAMARA * 20
    cam.rotation_euler = (-DIRECCION_CAMARA).to_track_quat("-Z", "Y").to_euler()
    d.type = "ORTHO"
    s.camera = cam

    # Encuadre: la silueta de la maqueta proyectada en los ejes de la cámara
    s.frame_set(fotograma)
    capas = bpy.context.evaluated_depsgraph_get()
    giro = cam.rotation_euler.to_matrix()
    derecha, arriba = giro @ Vector((1, 0, 0)), giro @ Vector((0, 1, 0))
    xs, ys = [], []
    for o in modelo.objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(capas)
        for esquina in ev.bound_box:
            p = ev.matrix_world @ Vector(esquina)
            xs.append(p.dot(derecha))
            ys.append(p.dot(arriba))
    ancho, alto = max(xs) - min(xs), max(ys) - min(ys)
    d.ortho_scale = max(ancho, alto) * margen
    d.shift_x = (max(xs) + min(xs)) / 2 / d.ortho_scale
    d.shift_y = (max(ys) + min(ys)) / 2 / d.ortho_scale

    if s.world is None:
        s.world = bpy.data.worlds.new("Mundo")
    s.world.use_nodes = True
    s.world.node_tree.nodes["Background"].inputs[0].default_value = (.65, .70, .8, 1)
    s.world.node_tree.nodes["Background"].inputs[1].default_value = .35
    s.render.engine = "CYCLES"
    s.cycles.samples = 32
    s.cycles.use_denoising = True
    s.render.resolution_x = s.render.resolution_y = 1100
    s.render.image_settings.file_format = "PNG"
    s.view_settings.view_transform = "AgX"


def exportar(salida, nombre, clip, marcas=()):
    """Guarda el .blend y el .glb, con todos los movimientos en un solo clip."""
    s = bpy.context.scene
    for f, texto_marca in marcas:
        s.timeline_markers.new(texto_marca, frame=f)
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    blend, glb = salida / f"{nombre}.blend", salida / f"{nombre}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="DESELECT")
    for o in modelo.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True,
                              export_animations=True, export_animation_mode="SCENE", export_frame_range=True,
                              export_force_sampling=True, export_cameras=False, export_lights=False)
    datos = glb.read_bytes()
    largo = struct.unpack_from("<I", datos, 12)[0]
    gltf = json.loads(datos[20:20 + largo])
    unido = {"name": clip, "samplers": [], "channels": []}
    for c in gltf.get("animations", []):
        desfase = len(unido["samplers"])
        unido["samplers"].extend(c["samplers"])
        for canal in c["channels"]:
            canal["sampler"] += desfase
            unido["channels"].append(canal)
    gltf["animations"] = [unido]
    cuerpo = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode()
    cuerpo += b" " * (-len(cuerpo) % 4)
    resto = datos[20 + largo:]
    glb.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(cuerpo) + len(resto))
                    + struct.pack("<II", len(cuerpo), 0x4E4F534A) + cuerpo + resto)
    print(f"Maqueta lista: {blend.name}, {glb.name} ({len(unido['channels'])} canales)")
    return blend, glb
