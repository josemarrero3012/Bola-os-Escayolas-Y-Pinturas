"""Bolaños — 02 Presupuesto por escrito.

Maqueta del segundo paso de «Cómo trabajamos», con la misma base, estudio de luces y
cámara que la del paso 01 y un bucle de seis segundos (144 fotogramas a 24 fps):
el presupuesto se escribe partida a partida mientras la calculadora suma, aparece el
total, el calendario de la pared marca el plazo de obra y el sello lo valida.

Uso: python blender/paso-2-presupuesto.py SALIDA
Deja en SALIDA el .blend editable y el .glb con un solo clip de animación. Después,
como cualquier maqueta: python blender/paso.py SALIDA/….blend SALIDA/….glb build-paso2 --fotograma 131
"""
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

SALIDA = Path(sys.argv[-1]).resolve()
SALIDA.mkdir(parents=True, exist_ok=True)
NOMBRE = "02-presupuesto-por-escrito"
CLIP = "Presupuesto_por_escrito_loop"

bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.frame_start = 0
s.frame_end = 144
s.render.fps = 24
modelo = bpy.data.collections.new("02 · PRESUPUESTO POR ESCRITO")
s.collection.children.link(modelo)
estudio = bpy.data.collections.new("Estudio de render")
s.collection.children.link(estudio)


def enlazar(o, col=modelo):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def mat(nombre, color, rugosidad=.6, metal=0):
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


# Los materiales del paso 01, ya en la paleta de la web (paso.py los deja igual)
blanco = mat("Escayola · blanco mineral", "EEECE5", .78)
marfil = mat("Acabado satinado", "FAF7EC", .45)
piedra = mat("Piedra caliza", "D5CBBB", .82)
suelo = mat("Caliza clara", "E6DFD0", .8)
verde = mat("Azul Bolaños", "0E3B2A", .46)
goma = mat("Goma azul oscura", "072B1F", .84)
tinta = mat("Tinta de plano", "D10A22", .8)
acero = mat("Acero cepillado", "B6BBC3", .3, .72)
papel = mat("Papel cálido", "FFFCF2", .85)
pantalla = mat("Pantalla LCD", "DAE4CD", .32)
grafito = mat("Grafito", "34363D", .8)


def grupo(nombre, loc=(0, 0, 0), padre=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new(nombre, None)
    modelo.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.parent = padre
    return o


def caja(nombre, loc, dims, ma, padre=None, bisel=.012):
    x, y, z = [v / 2 for v in dims]
    vs = [(-x, -y, -z), (-x, -y, z), (-x, y, -z), (-x, y, z), (x, -y, -z), (x, -y, z), (x, y, -z), (x, y, z)]
    fs = [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(vs, [], fs)
    malla.update()
    o = bpy.data.objects.new(nombre, malla)
    modelo.objects.link(o)
    o.location = loc
    o.parent = padre
    o.data.materials.append(ma)
    if bisel:
        b = o.modifiers.new("Bordes suaves", "BEVEL")
        b.width = bisel
        b.segments = 4
        n = o.modifiers.new("Normales", "WEIGHTED_NORMAL")
        n.keep_sharp = True
    return o


def cilindro(nombre, loc, r, alto, ma, padre=None, rot=(0, 0, 0), lados=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=lados, radius=r, depth=alto, location=(0, 0, 0))
    o = enlazar(bpy.context.object)
    o.name = nombre
    o.location = loc
    o.rotation_euler = rot
    o.parent = padre
    o.data.materials.append(ma)
    b = o.modifiers.new("Canto suave", "BEVEL")
    b.width = min(.008, alto * .2)
    b.segments = 3
    n = o.modifiers.new("Normales", "WEIGHTED_NORMAL")
    n.keep_sharp = True
    return o


def suave(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def esfera(nombre, loc, r, ma, padre=None, escala=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=r)
    o = suave(enlazar(bpy.context.object))
    o.name = nombre
    o.location = loc
    o.scale = escala
    o.parent = padre
    o.data.materials.append(ma)
    return o


def aro(nombre, loc, r, grosor, ma, padre=None, rot=(0, 0, 0), aplastado=.35):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=grosor, major_segments=64, minor_segments=10)
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


def trazo(nombre, a, b, r, ma, padre=None):
    a, b = Vector(a), Vector(b)
    o = cilindro(nombre, (a + b) / 2, r, (b - a).length, ma, padre, lados=12)
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return o


def barra(nombre, inicio, dims, ma, padre, bisel=None):
    """Trazo que crece desde su extremo izquierdo: el grupo se escala en X."""
    g = grupo(nombre, inicio, padre)
    caja(nombre + " · trazo", (dims[0] / 2, 0, 0), dims, ma, g, bisel if bisel is not None else min(dims[1:]) * .3)
    return g


def clave(o, prop, f, valor):
    setattr(o, prop, valor)
    o.keyframe_insert(data_path=prop, frame=f, group="Presupuesto por escrito · 6 s")


NADA = .0001


def aparece(o, entra, lleno, sale, fuera):
    """Escala de nada a entero y vuelta, para que el bucle cierre sin saltos."""
    for f, v in [(0, NADA), (entra, NADA), (lleno, 1), (sale, 1), (fuera, NADA), (144, NADA)]:
        clave(o, "scale", f, (v, v, v))


def crece(o, entra, lleno, sale, fuera):
    for f, v in [(0, NADA), (entra, NADA), (lleno, 1), (sale, 1), (fuera, NADA), (144, NADA)]:
        clave(o, "scale", f, (v, 1, 1))


def visible_entre(o, *tramos):
    """Se enciende y se apaga de golpe en cada tramo [desde, hasta) (las cifras del visor)."""
    def valor(f):
        return 1 if any(a <= f < b for a, b in tramos) else NADA
    fotogramas = {0, 144}
    for a, b in tramos:
        fotogramas |= {a - 1, a, b - 1, b}
    for f in sorted(f for f in fotogramas if 0 <= f <= 144):
        clave(o, "scale", f, (valor(f),) * 3)


raiz = grupo("Presupuesto_por_escrito")
Z0 = .203          # cara superior del plano de suelo

# --- Base, paredes y placa del paso: las mismas medidas que la maqueta 01 ---------
caja("Base de la maqueta", (0, 0, .07), (3.54, 2.73, .18), piedra, raiz, .065)
caja("Plano de suelo", (0, 0, .178), (3.41, 2.60, .05), suelo, raiz, .018)
caja("Pared de fondo", (0, 1.16, 1.03), (3.40, .15, 1.67), blanco, raiz, .025)
caja("Retorno de pared", (-1.61, .63, .82), (.16, 1.06, 1.24), blanco, raiz, .025)
caja("Rodapié posterior", (0, 1.066, .26), (3.18, .035, .11), marfil, raiz, .006)
caja("Remate del canto superior", (0, 1.16, 1.88), (3.43, .17, .035), marfil, raiz, .008)
caja("Placa del paso", (-1.36, -1.37, .07), (.34, .015, .12), verde, raiz, .018)
texto("Número de paso", "02", (-1.36, -1.382, .075), .09, marfil, raiz, (math.pi / 2, 0, 0))

# --- El presupuesto: carpeta, hojas y partidas ----------------------------------
GIRO_DOC = math.radians(-8)
DOC = Vector((-.42, -.30, Z0))
doc = grupo("Documento_de_presupuesto", DOC, raiz, (0, 0, GIRO_DOC))
caja("Carpeta", (0, 0, .015), (1.08, 1.42, .03), verde, doc, .02)
hoja_baja = caja("Hoja de debajo", (.035, .03, .034), (.90, 1.26, .008), papel, doc, .004)
hoja_baja.rotation_euler.z = math.radians(3.5)
caja("Hoja del presupuesto", (0, 0, .043), (.92, 1.28, .010), papel, doc, .005)
ZH = .0495         # sobre la hoja

texto("Título del presupuesto", "PRESUPUESTO", (-.40, .55, ZH), .078, verde, doc, alinear="LEFT", negrita=True)
texto("Número del presupuesto", "N.º 0247", (.40, .555, ZH), .036, grafito, doc, alinear="RIGHT")
caja("Filete de cabecera", (0, .48, ZH), (.84, .008, .002), verde, doc, .001)
for ancho, y in [(.30, .43), (.22, .40)]:
    caja("Datos del cliente", (-.40 + ancho / 2, y, ZH), (ancho, .014, .0018), grafito, doc, .0006)

PARTIDAS = [  # ancho del concepto, ancho del importe, subtotal en la calculadora
    (.44, .12, "640"),
    (.36, .10, "1.020"),
    (.48, .13, "1.740"),
    (.30, .09, "2.050"),
    (.40, .11, "2.480"),
]
FILAS_Y = [.32, .23, .14, .05, -.04]
INICIO_PARTIDA = [10, 21, 32, 43, 54]
BORRADO = (134, 142)    # todo se recoge antes de cerrar el bucle
for i, ((concepto, importe, _), y, f) in enumerate(zip(PARTIDAS, FILAS_Y, INICIO_PARTIDA)):
    if i < len(PARTIDAS) - 1:
        caja("Separador de partida", (0, y - .045, ZH - .0004), (.84, .003, .0012), piedra, doc, .0004)
    c = barra("Concepto %d" % (i + 1), (-.40, y + .008, ZH), (concepto, .022, .0022), grafito, doc)
    crece(c, f, f + 7, *BORRADO)
    d = barra("Detalle %d" % (i + 1), (-.40, y - .02, ZH), (concepto * .55, .012, .0018), grafito, doc)
    crece(d, f + 2, f + 8, *BORRADO)
    m = barra("Importe %d" % (i + 1), (.40 - importe, y + .008, ZH), (importe, .022, .0022), grafito, doc)
    crece(m, f + 5, f + 10, *BORRADO)

linea_total = barra("Filete del total", (-.42, -.10, ZH), (.84, .006, .002), grafito, doc)
crece(linea_total, 63, 69, *BORRADO)
for nombre, cuerpo, x, tam, alinear in [("Total · rótulo", "TOTAL", -.40, .062, "LEFT"),
                                        ("Total · importe", "2.480 €", .40, .076, "RIGHT")]:
    g = grupo(nombre, (x, -.17, ZH), doc)
    texto(nombre + " · texto", cuerpo, (0, 0, 0), tam, verde, g, alinear=alinear, negrita=True)
    aparece(g, 66, 73, *BORRADO)
subrayado = barra("Subrayado del total", (.09, -.225, ZH), (.31, .012, .0024), tinta, doc)
crece(subrayado, 72, 80, *BORRADO)
plazo = grupo("Plazo anotado", (-.40, -.30, ZH), doc)
texto("Plazo · texto", "PLAZO DE EJECUCIÓN: 12 DÍAS", (0, 0, 0), .034, grafito, plazo, alinear="LEFT")
crece(plazo, 74, 82, *BORRADO)
caja("Línea de firma", (-.24, -.54, ZH), (.32, .004, .0016), grafito, doc, .0006)
texto("Firma · rótulo", "Conforme", (-.40, -.575, ZH), .026, grafito, doc, alinear="LEFT")

# Huella del sello, que aparece al estampar
SELLO_LOCAL = Vector((.21, -.47, ZH + .0004))
huella = grupo("Sello_estampado", SELLO_LOCAL, doc, (0, 0, math.radians(14)))
aro("Huella · aro exterior", (0, 0, 0), .14, .008, verde, huella)
aro("Huella · aro interior", (0, 0, 0), .113, .004, verde, huella)
trazo("Huella · visto corto", (-.055, .0, 0), (-.015, -.044, 0), .011, verde, huella)
trazo("Huella · visto largo", (-.015, -.044, 0), (.066, .052, 0), .011, verde, huella)
aparece(huella, 110, 113, *BORRADO)

# --- Bolígrafo, junto al presupuesto ------------------------------------------
boli = grupo("Boligrafo", (.40, -.46, Z0 + .03), raiz, (0, 0, math.radians(62)))
cilindro("Cuerpo del bolígrafo", (0, 0, 0), .028, .46, verde, boli, (0, math.pi / 2, 0), 24)
cilindro("Capuchón", (.25, 0, 0), .03, .07, marfil, boli, (0, math.pi / 2, 0), 24)
caja("Clip del bolígrafo", (.21, 0, .032), (.15, .014, .008), acero, boli, .003)
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.028, radius2=0, depth=.07)
o = suave(enlazar(bpy.context.object))
o.name = "Punta del bolígrafo"
o.parent = boli
o.location = (-.265, 0, 0)
o.rotation_euler = (0, -math.pi / 2, 0)
o.data.materials.append(acero)

# --- Sello y tampón: la pieza grande de la escena, como el flexómetro del paso 01 ---
TAMPON = Vector((1.02, -.74, Z0))
tampon = grupo("Tampon", TAMPON, raiz, (0, 0, math.radians(-6)))
caja("Caja del tampón", (0, 0, .035), (.74, .56, .07), marfil, tampon, .025)
caja("Almohadilla de tinta", (0, 0, .072), (.64, .46, .014), goma, tampon, .006)
REPOSO = TAMPON + Vector((0, 0, .079))

sello = grupo("Sello", REPOSO, raiz, (0, 0, math.radians(-6)))
caja("Goma del sello", (0, 0, .03), (.54, .38, .06), goma, sello, .014)
caja("Montura del sello", (0, 0, .12), (.58, .42, .12), verde, sello, .04)
cilindro("Cuello del sello", (0, 0, .30), .085, .24, marfil, sello, lados=40)
esfera("Pomo del sello", (0, 0, .52), .17, verde, sello, (1, 1, .88))
esfera("Remate del pomo", (0, 0, .665), .055, marfil, sello)

# Dónde cae: la huella, pasada a coordenadas de la maqueta
destino = DOC + Euler((0, 0, GIRO_DOC)).to_matrix() @ SELLO_LOCAL
encima = Vector((0, 0, .34))
for f, loc in [
    (0, REPOSO), (86, REPOSO), (94, REPOSO + encima),
    (104, destino + encima), (109, destino), (113, destino),
    (118, destino + encima * .9), (125, REPOSO + encima * .7), (129, REPOSO), (144, REPOSO),
]:
    clave(sello, "location", f, loc)
for f, giro in [(0, 0), (94, 0), (99, -7), (104, 0), (118, 0), (121, 6), (125, 0), (144, 0)]:
    clave(sello, "rotation_euler", f, (0, math.radians(giro), math.radians(-6)))
for f, z in [(0, 1), (109, 1), (111, .93), (113, 1), (144, 1)]:
    clave(sello, "scale", f, (1, 1, z))

# --- Calculadora de sobremesa: suma cada partida ---------------------------------
calc = grupo("Calculadora", (.84, .36, Z0), raiz, (0, 0, math.radians(16)))
caja("Cuerpo de la calculadora", (0, 0, .055), (.72, .98, .11), verde, calc, .05)
caja("Cabeza de la calculadora", (0, .33, .16), (.72, .32, .12), verde, calc, .045)
caja("Marco de la pantalla", (0, .33, .225), (.60, .24, .02), goma, calc, .008)
caja("Pantalla", (0, .33, .233), (.54, .17, .012), pantalla, calc, .004)
cifras = ["0"] + [p[2] for p in PARTIDAS]
cambios = [f + 7 for f in INICIO_PARTIDA] + [138]
for i, cifra in enumerate(cifras):
    g = grupo("Visor %s" % cifra, (.24, .325, .2395), calc)
    texto("Cifra del visor %s" % cifra, cifra, (0, 0, 0), .1, grafito, g, alinear="RIGHT", negrita=True)
    if i == 0:     # el cero, al empezar y al volver a empezar
        visible_entre(g, (0, cambios[0]), (cambios[-1], 145))
    else:
        visible_entre(g, (cambios[i - 1], cambios[i]))
ZT = .128          # altura de las teclas
teclas = {}
for fila in range(4):
    for col in range(4):
        x, y = -.24 + col * .16, .07 - fila * .13
        ma = tinta if (col, fila) == (3, 3) else goma if col == 3 else marfil
        t = grupo("Tecla %d-%d" % (fila, col), (x, y, ZT), calc)
        caja("Tecla", (0, 0, 0), (.12, .1, .036), ma, t, .016)
        teclas[(fila, col)] = t
# Signos en las teclas de operación
caja("Signo igual", (0, .013, .0185), (.048, .008, .002), marfil, teclas[(3, 3)], .001)
caja("Signo igual", (0, -.013, .0185), (.048, .008, .002), marfil, teclas[(3, 3)], .001)
caja("Signo más", (0, 0, .0185), (.048, .008, .002), marfil, teclas[(2, 3)], .001)
caja("Signo más", (0, 0, .0185), (.008, .048, .002), marfil, teclas[(2, 3)], .001)
pulsaciones = [((0, 0), 13), ((1, 2), 15), ((2, 3), 17), ((0, 1), 24), ((2, 1), 26), ((2, 3), 28),
               ((1, 0), 35), ((0, 2), 37), ((2, 3), 39), ((2, 0), 46), ((1, 1), 48), ((2, 3), 50),
               ((0, 2), 57), ((2, 2), 59), ((2, 3), 61), ((3, 3), 65)]
por_tecla = {}
for k, f in pulsaciones:
    por_tecla.setdefault(k, []).append(f)
for k, t in teclas.items():
    arriba = t.location.copy()
    clave(t, "location", 0, arriba)
    for f in por_tecla.get(k, []):
        for df, dz in [(-1, 0), (1, -.016), (3, 0)]:
            clave(t, "location", f + df, arriba + Vector((0, 0, dz)))
    clave(t, "location", 144, arriba)

# --- Calendario de obra en la pared: el plazo ------------------------------------
cal = grupo("Calendario_de_obra", (.30, 1.077, 1.12), raiz)
caja("Hoja del calendario", (0, 0, 0), (1.56, .012, 1.0), papel, cal, .006)
caja("Cabecera del calendario", (0, -.003, .415), (1.56, .014, .17), verde, cal, .006)
texto("Rótulo del calendario", "PLAZO DE OBRA", (-.64, -.0115, .415), .085, marfil, cal, (math.pi / 2, 0, 0), "LEFT",
      negrita=True)
texto("Días de plazo", "12 DÍAS", (.64, -.0115, .415), .06, marfil, cal, (math.pi / 2, 0, 0), "RIGHT", negrita=True)
for x in [-.725, .725]:
    cilindro("Chincheta", (x, -.014, .455), .024, .02, tinta, cal, (math.pi / 2, 0, 0), 20)
COL_X = [-.60 + i * .20 for i in range(7)]
FILA_Z = [.16, .005, -.15, -.305]
for x, letra in zip(COL_X, "LMXJVSD"):
    texto("Día de la semana", letra, (x, -.007, .275), .045, grafito, cal, (math.pi / 2, 0, 0))
for j, z in enumerate(FILA_Z):
    for i, x in enumerate(COL_X):
        caja("Casilla", (x, -.0065, z), (.18, .002, .135), suelo, cal, .0008)
        texto("Día %d" % (j * 7 + i + 1), str(j * 7 + i + 1), (x - .072, -.0085, z + .04), .042, grafito, cal,
              (math.pi / 2, 0, 0), "LEFT")
# Del día 3 al 14: un trazo rojo que recorre dos semanas, con su inicio y su fin
inicio = grupo("Inicio del plazo", (COL_X[2] - .07, -.014, FILA_Z[0] - .035), cal)
cilindro("Punto de inicio", (0, 0, 0), .028, .006, tinta, inicio, (math.pi / 2, 0, 0), 24)
aparece(inicio, 78, 82, *BORRADO)
semana1 = barra("Plazo · semana 1", (COL_X[2] - .085, -.0105, FILA_Z[0] - .035), (5 * .20 - .02, .005, .036),
                tinta, cal, .002)
crece(semana1, 81, 91, *BORRADO)
semana2 = barra("Plazo · semana 2", (COL_X[0] - .085, -.0105, FILA_Z[1] - .035), (7 * .20 - .02, .005, .036),
                tinta, cal, .002)
crece(semana2, 91, 101, *BORRADO)
fin = grupo("Fin del plazo", (COL_X[6], -.012, FILA_Z[1]), cal, (math.pi / 2, 0, 0))
aro("Aro del último día", (0, 0, 0), .085, .007, tinta, fin, aplastado=.5)
aparece(fin, 100, 105, *BORRADO)

# --- Archivadores en el rincón: el presupuesto queda por escrito -----------------
# El tercero se apoya en los otros dos, sobre su arista izquierda
for i, (x, ma, inclina) in enumerate([(-1.40, verde, 0), (-1.245, marfil, 0), (-.99, goma, -9)]):
    alza = .07 * math.sin(math.radians(abs(inclina)))
    a = grupo("Archivador %d" % (i + 1), (x, .76, Z0 + alza), raiz, (0, math.radians(inclina), 0))
    caja("Tapas", (0, 0, .37), (.14, .58, .74), ma, a, .02)
    caja("Etiqueta del lomo", (0, -.292, .52), (.09, .004, .2), papel, a, .002)
    caja("Rótulo de la etiqueta", (0, -.2945, .56), (.05, .002, .012), grafito, a, .0005)
    caja("Rótulo de la etiqueta", (0, -.2945, .53), (.04, .002, .012), grafito, a, .0005)
    cilindro("Agujero del lomo", (0, -.288, .2), .03, .012, goma if ma is not goma else marfil, a,
             (math.pi / 2, 0, 0), 24)

# --- Estudio, cámara y render: como la maqueta 01 --------------------------------
fondo = caja("Fondo", (0, 0, -.085), (200, 200, .10), mat("Fondo marfil", "F2F0E9", .9), None, 0)
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
d = bpy.data.cameras.new("Cámara del paso 02")
cam = bpy.data.objects.new("Cámara del paso 02", d)
estudio.objects.link(cam)
cam.location = (5.8, -8, 6.8)
cam.rotation_euler = (Vector((0, -.03, .78)) - cam.location).to_track_quat("-Z", "Y").to_euler()
d.type = "ORTHO"
d.ortho_scale = 5.3
s.camera = cam
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
for f, nombre in [(0, "Inicio del bucle"), (10, "Partidas"), (63, "Total"), (78, "Plazo"),
                  (86, "Sello"), (113, "Estampado"), (134, "Recoger"), (144, "Cierre del bucle")]:
    s.timeline_markers.new(nombre, frame=f)
s.frame_set(131)

blend = SALIDA / f"{NOMBRE}.blend"
glb = SALIDA / f"{NOMBRE}.glb"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.object.select_all(action="DESELECT")
for o in modelo.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_apply=True,
                          export_animations=True, export_animation_mode="SCENE", export_frame_range=True,
                          export_force_sampling=True, export_cameras=False, export_lights=False)

# Un solo clip con todos los movimientos, como el paso 01
datos = glb.read_bytes()
largo = struct.unpack_from("<I", datos, 12)[0]
gltf = json.loads(datos[20:20 + largo])
unido = {"name": CLIP, "samplers": [], "channels": []}
for clip in gltf.get("animations", []):
    desfase = len(unido["samplers"])
    unido["samplers"].extend(clip["samplers"])
    for canal in clip["channels"]:
        canal["sampler"] += desfase
        unido["channels"].append(canal)
gltf["animations"] = [unido]
texto_json = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode()
texto_json += b" " * (-len(texto_json) % 4)
resto = datos[20 + largo:]
glb.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(texto_json) + len(resto))
                + struct.pack("<II", len(texto_json), 0x4E4F534A) + texto_json + resto)
print(f"Maqueta lista: {blend.name}, {glb.name} ({len(unido['channels'])} canales)")
