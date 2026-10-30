"""Bolaños — 04 Entrega y repaso.

Maqueta del cuarto paso de «Cómo trabajamos»: la vivienda terminada, en planta, como
una maqueta de arquitecto con los muros cortados. Bucle de seis segundos: se abre la
puerta, un marcador recorre el salón, la cocina, el baño y el dormitorio, y cada
estancia revisada recibe su visto bueno; al salir, la llave queda entregada.

Uso: python blender/paso-4-entrega.py SALIDA
Después: python blender/paso.py SALIDA/….blend SALIDA/….glb build-paso4 --fotograma 120
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maqueta_comun import *  # noqa: E402,F401,F403
import maqueta_comun as comun  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

POSTER = 120
iniciar("04 · ENTREGA Y REPASO")
c = Paleta()
roble = mat("Parqué de roble", "D6B994", .62)
roble_claro = mat("Parqué de roble claro", "E2CAA4", .62)
baldosa = mat("Baldosa porcelánica", "ECE9E3", .42)
vidrio = mat("Vidrio", "D7E3E2", .08)
tapizado = mat("Tapizado salvia", "93A698", .92)
laton = mat("Latón", "D9B66A", .3, .85)
agua = mat("Agua", "D3E3E4", .32)

raiz = grupo("Entrega_y_repaso")

# --- Losa de la maqueta ----------------------------------------------------------
caja("Losa", (0, 0, .06), (3.3, 2.7, .12), c.piedra, raiz, .03)
F = .135           # cara superior de los suelos
caja("Placa del paso", (1.3, -1.356, .06), (.34, .015, .1), c.verde, raiz, .018)
texto("Número de paso", "04", (1.3, -1.3645, .064), .085, c.marfil, raiz, (math.pi / 2, 0, 0))


def suelo_de_tablas(nombre, x0, x1, y0, y1, ma):
    ancho = .16
    y = y0
    i = 0
    while y < y1 - .01:
        alto = min(ancho, y1 - y)
        caja(nombre, ((x0 + x1) / 2, y + alto / 2, F - .0075), (x1 - x0, alto - .006, .015), ma, raiz, .003)
        y += alto
        i += 1


def suelo_de_baldosas(nombre, x0, x1, y0, y1, lado, ma):
    nx, ny = max(1, round((x1 - x0) / lado)), max(1, round((y1 - y0) / lado))
    lx, ly = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            caja(nombre, (x0 + lx * (i + .5), y0 + ly * (j + .5), F - .0075), (lx - .008, ly - .008, .015), ma,
                 raiz, .003)


# Estancias: salón (delante a la izquierda), cocina, baño y dormitorio
suelo_de_tablas("Tarima del salón", -1.5, .35, -1.1, .15, roble)
suelo_de_baldosas("Baldosa de la cocina", .35, 1.5, -1.1, .15, .19, baldosa)
suelo_de_baldosas("Baldosa del baño", .35, 1.5, .15, 1.1, .13, baldosa)
suelo_de_tablas("Tarima del dormitorio", -1.5, .35, .15, 1.1, roble_claro)

# --- Muros cortados a media altura -------------------------------------------------
ALTO_MURO, GRUESO = .34, .07


piezas_muro = []


def muro(a, b, alto=ALTO_MURO, grueso=GRUESO):
    # Cada extremo entra en el muro que cruza casi hasta su cara exterior, sin llegar a
    # ella: dos caras en el mismo plano dejarían una franja negra al fundirlas
    a, b = Vector((*a, 0)), Vector((*b, 0))
    centro, largo = (a + b) / 2, (b - a).length + GRUESO - .004
    horizontal = abs(b.x - a.x) > abs(b.y - a.y)
    dims = (largo, grueso, alto + .01) if horizontal else (grueso, largo, alto + .01)
    piezas_muro.append(((centro.x, centro.y, F - .01 + dims[2] / 2), dims))


def fundir_muros():
    """Todos los muros en una sola pieza, sin caras superpuestas en las esquinas, con la
    cara de corte pintada de verde, como en un plano."""
    sueltos = []
    for centro, dims in piezas_muro:
        o = caja("Muro suelto", centro, dims, c.blanco, None, 0)
        enlazar(o, comun.estudio)
        sueltos.append(o)
    base = sueltos.pop()
    for o in sueltos:
        union = base.modifiers.new("Unión", "BOOLEAN")
        union.operation = "UNION"
        union.object = o
        union.solver = "EXACT"
    capas = bpy.context.evaluated_depsgraph_get()
    m = bpy.data.meshes.new_from_object(base.evaluated_get(capas))
    m.transform(base.matrix_world)     # la malla sale en coordenadas del muro base
    bm = bmesh.new()
    bm.from_mesh(m)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_limit(bm, angle_limit=.01, verts=bm.verts, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(m)
    bm.free()
    for o in sueltos + [base]:
        bpy.data.objects.remove(o)
    m.materials.clear()
    m.materials.append(c.blanco)
    m.materials.append(c.verde)
    for cara in m.polygons:
        cara.material_index = 1 if cara.normal.z > .9 and cara.center.z > F + ALTO_MURO - .01 else 0
    muros = bpy.data.objects.new("Muros", m)
    comun.modelo.objects.link(muros)
    muros.parent = raiz
    for cara in m.polygons:
        cara.use_smooth = False


def ventana(a, b):
    """Antepecho bajo y vidrio en un hueco del muro exterior. El antepecho es un pelo más
    fino que el muro para que sus caras no coincidan con las de los muros vecinos."""
    muro(a, b, alto=.1, grueso=GRUESO - .006)
    a, b = Vector((*a, 0)), Vector((*b, 0))
    centro, largo = (a + b) / 2, (b - a).length
    horizontal = abs(b.x - a.x) > abs(b.y - a.y)
    dims = (largo, .014, .2) if horizontal else (.014, largo, .2)
    caja("Vidrio de la ventana", (centro.x, centro.y, F + .1 + .1), dims, vidrio, raiz, .003)


# Fachada delantera: puerta de entrada y ventana de la cocina
muro((-1.5, -1.1), (-1.235, -1.1))
muro((-.825, -1.1), (.65, -1.1))
ventana((.65, -1.1), (1.1, -1.1))
muro((1.1, -1.1), (1.5, -1.1))
muro((-1.5, 1.1), (1.5, 1.1))
muro((-1.5, -1.1), (-1.5, .35))
ventana((-1.5, .35), (-1.5, .78))
muro((-1.5, .78), (-1.5, 1.1))
muro((1.5, -1.1), (1.5, .55))
ventana((1.5, .55), (1.5, .85))
muro((1.5, .85), (1.5, 1.1))
# Tabiques interiores, con sus pasos
muro((-1.5, .15), (-.48, .15))
muro((-.08, .15), (.35, .15))
muro((.35, .15), (1.5, .15))
muro((.35, -1.1), (.35, -.78))
muro((.35, -.18), (.35, .15))
muro((.35, .15), (.35, .52))
muro((.35, .86), (.35, 1.1))
fundir_muros()

# Puerta de entrada, que se abre al llegar y se cierra al salir
bisagra = grupo("Puerta_de_entrada", (-1.2, -1.1, F), raiz)
caja("Hoja de la puerta", (.17, 0, .15), (.34, .03, .3), c.verde, bisagra, .008)
cilindro("Pomo", (.3, -.025, .15), .012, .03, c.acero, bisagra, (math.pi / 2, 0, 0), 12)
recorrido(bisagra, "rotation_euler", [(f, (0, 0, math.radians(a))) for f, a in
                                      [(0, 0), (2, 0), (10, 100), (98, 100), (108, 0), (144, 0)]])
caja("Felpudo", (-1.03, -1.24, .124), (.36, .16, .01), c.goma, raiz, .003)

# --- Muebles ---------------------------------------------------------------------
# Salón
caja("Alfombra", (-.62, -.45, F + .003), (1.0, .72, .006), c.piedra, raiz, .002)
sofa = grupo("Sofá", (-1.27, -.45, F), raiz)
caja("Asiento del sofá", (0, 0, .08), (.34, .9, .12), tapizado, sofa, .035)
caja("Respaldo del sofá", (-.13, 0, .15), (.1, .9, .24), tapizado, sofa, .04)
for y in (-.47, .47):
    caja("Brazo del sofá", (0, y, .12), (.34, .08, .18), tapizado, sofa, .03)
cilindro("Mesa de centro", (-.72, -.45, F + .06), .17, .12, c.marfil, raiz, lados=48)
cilindro("Maceta", (-1.33, -.94, F + .06), .07, .12, c.piedra, raiz, lados=24)
esfera("Planta", (-1.33, -.94, F + .2), .13, c.verde, raiz, (1, 1, 1.15), 24)
caja("Mueble de la tele", (.22, -.45, F + .07), (.12, .5, .14), c.goma, raiz, .015)
# Cocina
caja("Encimera baja", (1.3, -.47, F + .12), (.3, 1.1, .24), c.blanco, raiz, .015)
caja("Encimera", (1.3, -.47, F + .25), (.33, 1.13, .025), c.verde, raiz, .006)
caja("Fregadero", (1.3, -.25, F + .262), (.2, .26, .006), c.acero, raiz, .002)
for y in (-.62, -.78):
    for dx in (-.06, .06):
        cilindro("Fuego", (1.3 + dx, y + .04, F + .263), .04, .004, c.goma, raiz, lados=24)
caja("Isla", (.8, -.4, F + .12), (.48, .3, .24), c.blanco, raiz, .015)
caja("Encimera de la isla", (.8, -.4, F + .25), (.52, .34, .025), c.verde, raiz, .006)
# Baño
banera = grupo("Bañera", (1.02, .88, F), raiz)
caja("Bañera · cuerpo", (0, 0, .1), (.78, .34, .2), c.blanco, banera, .06)
caja("Bañera · agua", (0, 0, .195), (.66, .24, .01), agua, banera, .004)
caja("Mueble del lavabo", (1.34, .34, F + .1), (.22, .3, .2), c.goma, raiz, .015)
cilindro("Lavabo", (1.34, .34, F + .21), .09, .03, c.marfil, raiz, lados=32)
cilindro("Inodoro", (.55, .95, F + .06), .075, .12, c.blanco, raiz, lados=32)
caja("Cisterna", (.55, 1.03, F + .12), (.17, .07, .2), c.blanco, raiz, .02)
# Dormitorio
cama = grupo("Cama", (-.75, .66, F), raiz)
caja("Somier", (0, 0, .05), (.66, .8, .1), c.goma, cama, .02)
caja("Colchón", (0, 0, .13), (.62, .78, .08), c.marfil, cama, .03)
caja("Edredón", (0, -.12, .18), (.66, .54, .035), tapizado, cama, .015)
for x in (-.15, .15):
    caja("Almohada", (x, .28, .19), (.24, .13, .06), c.marfil, cama, .025)
caja("Cabecero", (0, .42, .17), (.7, .05, .34), c.verde, cama, .015)
for x in (-1.2, -.3):
    caja("Mesilla", (x, .96, F + .075), (.16, .14, .15), c.marfil, raiz, .015)

# --- El repaso: un marcador recorre las estancias y cada una recibe su visto bueno --
FUERA = Vector((-1.03, -1.24, .129))
PARADAS = [   # dónde se posa, insignia sobre la estancia y fotograma de llegada
    (Vector((-.42, -.2, F)), Vector((-.62, -.45, .82)), 14),
    (Vector((.82, -.82, F)), Vector((.92, -.47, .82)), 34),
    (Vector((.86, .45, F)), Vector((.92, .62, .82)), 54),
    (Vector((-.15, .55, F)), Vector((-.62, .62, .82)), 74),
]
REGRESO = 96
SALIDA_TODO = (130, 138)

marcador = grupo("Marcador_de_repaso", FUERA, raiz)
cono("Punta del marcador", (0, 0, .1), 0, .07, .2, c.tinta, marcador)
esfera("Cabeza del marcador", (0, 0, .23), .085, c.tinta, marcador)
esfera("Ojo del marcador", (.05, -.055, .26), .028, c.marfil, marcador, segmentos=16)

posiciones = [(0, FUERA)]
anterior, salida = FUERA, 3
for parada, _, llega in PARADAS + [(FUERA, None, REGRESO)]:
    medio = (anterior + parada) / 2 + Vector((0, 0, .55))
    posiciones += [(salida, anterior), ((salida + llega) // 2, medio), (llega, parada)]
    anterior, salida = parada, llega + 6
posiciones.append((144, FUERA))
recorrido(marcador, "location", posiciones)
escalas = [(0, (1, 1, 1))]
for _, _, llega in PARADAS + [(FUERA, None, REGRESO)]:
    escalas += [(llega, (1, 1, 1)), (llega + 2, (1.12, 1.12, .78)), (llega + 5, (1, 1, 1))]
escalas.append((144, (1, 1, 1)))
recorrido(marcador, "scale", escalas)

for i, (_, encima, llega) in enumerate(PARADAS):
    insignia = grupo("Visto bueno %d" % (i + 1), encima, raiz, mirando_a_camara())
    cilindro("Insignia", (0, 0, 0), .12, .03, c.verde, insignia, lados=48)
    aro("Bisel de la insignia", (0, 0, .016), .105, .006, c.marfil, insignia, aplastado=.4)
    visto("Visto", (.005, .01, .02), .13, c.marfil, insignia, grosor=.012)
    aparece(insignia, llega + 1, llega + 7, *SALIDA_TODO)

# --- La llave, entregada al salir -------------------------------------------------
llave = grupo("Llave_entregada", (-1.03, -1.2, .8), raiz)
cara = grupo("Llave · cara", (0, 0, 0), llave, (0, 0, math.radians(36)), (1.5, 1.5, 1.5))
aro("Ojo de la llave", (-.1, 0, 0), .065, .02, laton, cara, (math.pi / 2, 0, 0), aplastado=.5)
caja("Caña de la llave", (.11, 0, 0), (.32, .025, .036), laton, cara, .008)
for x, alto in [(.2, .05), (.235, .035), (.27, .055)]:
    caja("Diente", (x, 0, -.018 - alto / 2), (.026, .025, alto), laton, cara, .004)
aro("Anilla", (-.17, 0, -.05), .03, .006, c.acero, cara, (math.pi / 2, 0, 0), aplastado=1)
etiqueta = grupo("Etiqueta de la llave", (-.2, 0, -.13), cara, (0, math.radians(-12), 0))
caja("Etiqueta", (0, 0, 0), (.13, .012, .16), c.verde, etiqueta, .012)
cilindro("Ojal de la etiqueta", (0, -.007, .055), .014, .004, c.marfil, etiqueta, (math.pi / 2, 0, 0), 16)
aparece(llave, 104, 112, *SALIDA_TODO)
recorrido(llave, "location", [(0, (-1.03, -1.2, .62)), (104, (-1.03, -1.2, .62)), (114, (-1.03, -1.2, .82)),
                              (122, (-1.03, -1.2, .78)), (130, (-1.03, -1.2, .82)), (144, (-1.03, -1.2, .62))])
recorrido(llave, "rotation_euler", [(f, (0, 0, math.radians(a))) for f, a in
                                    [(0, -30), (104, -30), (116, 12), (126, -8), (138, 0), (144, -30)]])

estudio_y_camara("Cámara del paso 04", POSTER)
bpy.context.scene.frame_set(POSTER)
exportar(sys.argv[-1], "04-entrega-y-repaso", "Entrega_y_repaso_loop", [
    (0, "Inicio del bucle"), (3, "Entrar"), (14, "Salón"), (34, "Cocina"), (54, "Baño"),
    (74, "Dormitorio"), (96, "Salir"), (104, "Llave"), (130, "Recoger"), (144, "Cierre del bucle")])
