"""Bolaños — 03 Obra limpia.

Maqueta del tercer paso de «Cómo trabajamos»: una plataforma redonda con suelo de
parqué, sin paredes. Bucle de seis segundos: el rollo de cartón protege el suelo, una
funda cae sobre la butaca, la escoba recoge el polvo en el recogedor y, al acabar la
jornada, todo vuelve a su sitio.

Uso: python blender/paso-3-obra-limpia.py SALIDA
Después: python blender/paso.py SALIDA/….blend SALIDA/….glb build-paso3 --fotograma 112
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maqueta_comun import *  # noqa: E402,F401,F403
import maqueta_comun as comun  # noqa: E402
from mathutils import Vector  # noqa: E402

POSTER = 112
iniciar("03 · OBRA LIMPIA")
c = Paleta()
roble = mat("Parqué de roble", "D6B994", .62)
roble_claro = mat("Parqué de roble claro", "E2CAA4", .62)
carton = mat("Cartón protector", "B8935F", .9)
plastico = mat("Plástico protector", "EEF2F2", .28)
tapizado = mat("Tapizado salvia", "93A698", .92)
polvo = mat("Polvo de yeso", "E2DED6", .95)
carrocero = mat("Cinta de carrocero", "EFE1B8", .7)

raiz = grupo("Obra_limpia")


def suavizar(o, ancho, segmentos=3):
    b = o.modifiers.new("Bordes suaves", "BEVEL")
    b.width = ancho
    b.segments = segmentos
    n = o.modifiers.new("Normales", "WEIGHTED_NORMAL")
    n.keep_sharp = True


def suavestep(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


# --- Plataforma redonda con suelo de parqué --------------------------------------
R = 1.55
F = .18            # cara superior del parqué
cilindro("Zócalo de la plataforma", (0, 0, .07), R + .07, .14, c.piedra, raiz, lados=128, bisel=.02)
cilindro("Lecho del parqué", (0, 0, .15), R, .02, c.piedra, raiz, lados=128, bisel=.004)
cortador = cilindro("Contorno del parqué", (0, 0, F - .02), R - .01, .1, c.piedra, None, lados=128, bisel=0)
cortador.modifiers.clear()
enlazar(cortador, comun.estudio)
cortador.hide_render = cortador.hide_viewport = True
azar = random.Random(3)
ANCHO_TABLA = .2
for fila, y in enumerate([-R + ANCHO_TABLA * (i + .5) for i in range(int(2 * R / ANCHO_TABLA) + 1)]):
    x = -R - azar.uniform(0, .9)
    while x < R:
        largo = azar.uniform(.9, 1.35)
        x0, x1 = x, x + largo
        x = x1
        if x1 < -R or x0 > R:
            continue
        xc, ancho = (x0 + x1) / 2, largo - .008
        dentro = all(math.hypot(px, py) < R - .02 for px in (x0, x1) for py in (y - .1, y + .1))
        cerca = math.hypot(min(max(0, x0), x1), min(max(0, y - .1), y + .1))    # punto más cercano al centro
        if cerca > R - .01:
            continue
        tabla = caja("Tabla de parqué", (xc, y, F - .015), (ancho, ANCHO_TABLA - .008, .03),
                     roble if azar.random() < .55 else roble_claro, raiz, 0)
        if not dentro:
            corte = tabla.modifiers.new("Contorno", "BOOLEAN")
            corte.operation = "INTERSECT"
            corte.object = cortador
            corte.solver = "EXACT"
        suavizar(tabla, .004, 2)
ANGULO_PLACA = math.radians(-118)
placa = grupo("Placa del paso", ((R + .07) * math.cos(ANGULO_PLACA), (R + .07) * math.sin(ANGULO_PLACA), .07), raiz,
              (0, 0, ANGULO_PLACA + math.pi / 2))
caja("Placa", (0, -.004, 0), (.34, .015, .1), c.verde, placa, .018)
texto("Número de paso", "03", (0, -.0125, .004), .085, c.marfil, placa, (math.pi / 2, 0, 0))

# --- Butaca y funda protectora ---------------------------------------------------
butaca = grupo("Butaca", (-.75, .45, F), raiz, (0, 0, math.radians(-28)))
for x in (-.34, .34):
    for y in (-.28, .28):
        cilindro("Pata de la butaca", (x, y, .06), .028, .12, c.goma, butaca, lados=16)
caja("Asiento", (0, 0, .22), (.84, .74, .2), tapizado, butaca, .06)
caja("Cojín", (0, -.04, .36), (.58, .6, .1), tapizado, butaca, .045)
caja("Respaldo", (0, .27, .47), (.84, .2, .5), tapizado, butaca, .07)
for x in (-.35, .35):
    caja("Brazo", (x, -.02, .38), (.14, .7, .28), tapizado, butaca, .055)

funda = grupo("Funda_protectora", (0, 0, 0), butaca)
caja("Funda · cuerpo", (0, -.01, .3), (.98, .9, .6), plastico, funda, .13)
caja("Funda · respaldo", (0, .27, .64), (.98, .3, .2), plastico, funda, .1)
for x in (-.3, -.05, .22):
    trazo("Pliegue de la funda", (x, -.465, .04), (x + .03, -.455, .5), .018, plastico, funda, 10)
for x in (-.5, .5):
    trazo("Pliegue lateral", (x, -.2, .04), (x, -.18, .48), .018, plastico, funda, 10)
recorrido(funda, "location", [(0, (0, 0, .9)), (38, (0, 0, .9)), (48, (0, 0, -.02)), (52, (0, 0, 0)),
                              (122, (0, 0, 0)), (132, (0, 0, .85)), (144, (0, 0, .9))])
recorrido(funda, "scale", [(0, (NADA,) * 3), (33, (NADA,) * 3), (38, (1, 1, .7)), (46, (1, 1, 1.04)),
                           (49, (1.03, 1.03, .9)), (53, (1, 1, 1)), (122, (1, 1, 1)), (128, (1, 1, .8)),
                           (133, (NADA,) * 3), (144, (NADA,) * 3)])

# --- Rollo de cartón que protege el suelo ----------------------------------------
X0, LARGO, Y_TIRA, ANCHO_TIRA, R_ROLLO = -.30, 1.35, -.68, .62, .1
tira = barra("Cartón extendido", (X0, Y_TIRA, F + .003), (LARGO, ANCHO_TIRA, .006), carton, raiz, .002)
rollo = grupo("Rollo_de_carton", (X0, Y_TIRA, F + R_ROLLO), raiz)
eje = grupo("Giro del rollo", (0, 0, 0), rollo)
cilindro("Rollo", (0, 0, 0), R_ROLLO, ANCHO_TIRA + .02, carton, eje, (math.pi / 2, 0, 0), 40)
cilindro("Alma del rollo", (0, 0, 0), .035, ANCHO_TIRA + .04, c.piedra, eje, (math.pi / 2, 0, 0), 24)
caja("Cinta del rollo", (0, 0, R_ROLLO + .002), (.05, ANCHO_TIRA + .025, .006), carrocero, eje, .002)
for y in (-.2, .2):
    caja("Cinta que sujeta el cartón", (X0 + .02, Y_TIRA + y, F + .008), (.16, .05, .004), carrocero, raiz, .0015)


def extendido(f):
    if f <= 8:
        return 0
    if f <= 40:
        return suavestep((f - 8) / 32)
    if f <= 126:
        return 1
    return 1 - suavestep((f - 126) / 14)


for f in range(0, 145, 2):
    v = extendido(f)
    clave(tira, "scale", f, (max(NADA, v), 1, 1))
    clave(rollo, "location", f, (X0 + LARGO * v, Y_TIRA, F + R_ROLLO))
    clave(eje, "rotation_euler", f, (0, LARGO * v / R_ROLLO, 0))

# --- Escoba, recogedor y polvo ---------------------------------------------------
P0 = Vector((-.80, -.34, F))              # el montón de polvo, al empezar
recogedor_en = Vector((-1.08, -.70, F))
avance = (recogedor_en - P0).normalized()
giro = math.atan2(-avance.x, avance.y) + math.pi    # el +Y local mira hacia la escoba

recogedor = grupo("Recogedor", recogedor_en, raiz, (0, 0, giro))
caja("Bandeja del recogedor", (0, .02, .008), (.42, .34, .014), c.verde, recogedor, .005)
for x in (-.205, .205):
    prisma("Costado del recogedor", [(-.15, 0), (.19, 0), (-.15, .09)], .016, c.verde, recogedor,
           (x, 0, 0), bisel=.004)
caja("Fondo del recogedor", (0, -.15, .05), (.42, .016, .1), c.verde, recogedor, .005)
caja("Mango del recogedor", (0, -.27, .085), (.07, .24, .03), c.goma, recogedor, .012)

monton = grupo("Monton_de_polvo", P0, raiz)
for x, y, r in [(0, 0, .07), (.07, .04, .05), (-.06, .035, .045), (.03, -.06, .042), (-.045, -.05, .036),
                (.1, -.03, .03), (-.1, -.015, .028), (.13, .08, .018), (-.12, .09, .016), (.05, -.12, .015),
                (-.14, -.09, .014)]:
    esfera("Polvo", (x, y, r * .55), r, polvo, monton, (1, 1, .7), 16)

escoba = grupo("Escoba", P0 - avance * .14, raiz, (0, 0, giro))    # el palo, inclinado hacia atrás
caja("Cepillo de la escoba", (0, 0, .085), (.5, .1, .065), c.verde, escoba, .02)
caja("Cerdas", (0, 0, .03), (.47, .085, .06), c.grafito, escoba, .01)
trazo("Palo de la escoba", (0, .02, .11), (0, .52, 1.12), .022, c.marfil, escoba, 16)
cilindro("Remate del palo", (0, .53, 1.14), .026, .05, c.verde, escoba, (math.radians(-26), 0, 0), 16)

# Pasadas de escoba: avanza, retrocede un poco y vuelve a empujar
pasadas = [(58, 0), (62, .14), (65, .08), (69, .24), (72, .17), (76, .33), (79, .26), (84, .44), (90, .40)]
recorrido(escoba, "location", [(0, P0 - avance * .14)] +
          [(f, P0 - avance * .14 + avance * d) for f, d in pasadas] +
          [(126, P0 - avance * .14 + avance * .40), (140, P0 - avance * .14), (144, P0 - avance * .14)])
recorrido(escoba, "rotation_euler", [(f, (math.radians(a), 0, giro)) for f, a in
                                     [(0, 0), (58, 0), (62, -6), (65, 3), (69, -6), (72, 3), (76, -6),
                                      (79, 3), (84, -6), (90, 0), (144, 0)]])
empuje = [(58, 0), (62, .02), (69, .12), (76, .21), (84, .32), (92, .36)]
recorrido(monton, "location", [(0, P0)] + [(f, P0 + avance * d) for f, d in empuje] +
          [(100, P0 + avance * .36), (128, P0), (144, P0)])
recorrido(monton, "scale", [(0, (1, 1, 1)), (88, (1, 1, 1)), (96, (NADA,) * 3), (128, (NADA,) * 3),
                            (138, (1, 1, 1)), (144, (1, 1, 1))])

# --- Botes de pintura y caja de herramientas, recogidos -------------------------
def bote(nombre, loc, padre=raiz, giro_z=0):
    g = grupo(nombre, loc, padre, (0, 0, giro_z))
    cilindro("Cuerpo del bote", (0, 0, .15), .2, .3, c.blanco, g, lados=48)
    cilindro("Etiqueta del bote", (0, 0, .14), .203, .13, c.verde, g, lados=48)
    cilindro("Tapa del bote", (0, 0, .305), .19, .02, c.acero, g, lados=48)
    aro("Reborde de la tapa", (0, 0, .3), .19, .012, c.acero, g, aplastado=.8)
    caja("Asa del bote", (0, 0, .325), (.04, .3, .012), c.acero, g, .004)
    return g


bote("Bote de pintura", (.68, .78, F), giro_z=.3)
bote("Bote de pintura", (1.06, .52, F), giro_z=-.4)
bote("Bote de pintura", (.87, .65, F + .32), giro_z=1.1)
caja_h = grupo("Caja_de_herramientas", (1.02, .02, F), raiz, (0, 0, math.radians(24)))
caja("Cuerpo de la caja", (0, 0, .13), (.58, .3, .26), c.verde, caja_h, .03)
caja("Tapa de la caja", (0, 0, .275), (.6, .32, .04), c.goma, caja_h, .015)
for x in (-.18, .18):
    caja("Cierre", (x, -.155, .24), (.06, .012, .05), c.acero, caja_h, .004)
    trazo("Soporte del asa", (x * .8, 0, .29), (x * .8, 0, .36), .012, c.acero, caja_h)
trazo("Asa de la caja", (-.15, 0, .36), (.15, 0, .36), .018, c.acero, caja_h)
aro("Cinta de carrocero", (-.36, -.3, .026), .065, .016, carrocero, caja_h, aplastado=1.6, lados=40)

# --- Escalera de tijera, con el rodillo arriba ------------------------------------
def liston(nombre, a, b, ancho, grueso, ma, padre):
    a, b = Vector(a), Vector(b)
    o = caja(nombre, (a + b) / 2, (ancho, grueso, (b - a).length), ma, padre, min(ancho, grueso) * .3)
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return o


escalera = grupo("Escalera_de_tijera", (.12, .98, F), raiz, (0, 0, math.radians(12)))
ALTO = 1.32
for x in (-1, 1):
    liston("Larguero delantero", (x * .25, -.32, 0), (x * .2, -.04, ALTO), .055, .03, c.acero, escalera)
    liston("Larguero trasero", (x * .25, .34, 0), (x * .2, .05, ALTO - .04), .045, .028, c.acero, escalera)
    for y in (-.32, .34):
        caja("Taco de goma", (x * .25, y, .012), (.07, .05, .024), c.goma, escalera, .008)
    trazo("Tirante", (x * .235, -.2, .5), (x * .235, .23, .5), .008, c.acero, escalera)
for i, z in enumerate((.32, .62, .92)):
    t = z / ALTO
    caja("Peldaño", (0, -.32 + .28 * t - .03, z), (.47 - .1 * t, .13, .028), c.verde, escalera, .01)
caja("Plataforma de la escalera", (0, 0, ALTO + .015), (.44, .2, .035), c.verde, escalera, .012)
rodillo = grupo("Rodillo", (-.02, 0, ALTO + .035), escalera, (0, 0, math.radians(-20)))
cilindro("Felpa del rodillo", (.1, 0, .05), .05, .24, c.marfil, rodillo, (0, 0, 0), 32)
rodillo.children[0].rotation_euler = (math.pi / 2, 0, 0)
trazo("Estribo del rodillo", (.1, .14, .05), (-.02, .14, .05), .008, c.acero, rodillo)
trazo("Varilla del rodillo", (-.02, .14, .05), (-.08, .0, .03), .008, c.acero, rodillo)
trazo("Mango del rodillo", (-.08, 0, .03), (-.3, -.06, .03), .024, c.verde, rodillo)

estudio_y_camara("Cámara del paso 03", POSTER)
bpy.context.scene.frame_set(POSTER)
exportar(sys.argv[-1], "03-obra-limpia", "Obra_limpia_loop", [
    (0, "Inicio del bucle"), (8, "Proteger el suelo"), (34, "Tapar la butaca"), (58, "Barrer"),
    (96, "Todo recogido"), (122, "Fin de la jornada"), (144, "Cierre del bucle")])
