"""Bolaños — 02 Presupuesto por escrito.

Maqueta del segundo paso de «Cómo trabajamos»: una mesa de obra sobre caballetes, sin
paredes, con el presupuesto, la calculadora, el sello y un calendario de sobremesa.
Bucle de seis segundos: el presupuesto se escribe partida a partida mientras la
calculadora suma, aparece el total, el calendario marca el plazo y el sello lo valida.

Uso: python blender/paso-2-presupuesto.py SALIDA
Deja en SALIDA el .blend editable y el .glb con un solo clip de animación. Después,
como cualquier maqueta: python blender/paso.py SALIDA/….blend SALIDA/….glb build-paso2 --fotograma 131
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maqueta_comun import *  # noqa: E402,F401,F403
from mathutils import Euler, Vector  # noqa: E402

POSTER = 131
iniciar("02 · PRESUPUESTO POR ESCRITO")
c = Paleta()
madera = mat("Madera contrachapada", "E4D3B4", .7)
canto = mat("Canto de contrachapado", "CDB48C", .75)

raiz = grupo("Presupuesto_por_escrito")

# --- Mesa de obra: tablero sobre dos caballetes ----------------------------------
T = .89            # cara superior del tablero
for x in (-1.05, 1.05):
    cab = grupo("Caballete", (x, 0, 0), raiz)
    caja("Travesaño del caballete", (0, 0, .80), (.12, 1.62, .06), c.verde, cab, .02)
    for y in (-.64, .64):
        for lado in (-1, 1):
            trazo("Pata del caballete", (lado * .03, y, .78), (lado * .30, y * 1.04, .02), .028, c.verde, cab)
            cilindro("Contera", (lado * .30, y * 1.04, .015), .036, .03, c.goma, cab, lados=16)
    for lado in (-1, 1):
        trazo("Riostra", (lado * .19, -.66, .28), (lado * .19, .66, .28), .02, c.verde, cab)
    cilindro("Bisagra", (0, -.64, .79), .04, .14, c.acero, cab, (0, math.pi / 2, 0), 16)
    cilindro("Bisagra", (0, .64, .79), .04, .14, c.acero, cab, (0, math.pi / 2, 0), 16)
caja("Tablero", (0, 0, T - .03), (3.1, 2.0, .06), madera, raiz, .012)
caja("Canto del tablero", (0, 0, T - .03), (3.08, 1.98, .045), canto, raiz, .004)
caja("Placa del paso", (-1.22, -1.006, T - .07), (.34, .015, .12), c.verde, raiz, .018)
texto("Número de paso", "02", (-1.22, -1.0145, T - .065), .09, c.marfil, raiz, (math.pi / 2, 0, 0))

# --- El presupuesto: carpeta, hojas y partidas ----------------------------------
GIRO_DOC = math.radians(-10)
DOC = Vector((-.72, -.18, T))
doc = grupo("Documento_de_presupuesto", DOC, raiz, (0, 0, GIRO_DOC))
caja("Carpeta", (0, 0, .015), (1.08, 1.42, .03), c.verde, doc, .02)
hoja_baja = caja("Hoja de debajo", (.035, .03, .034), (.90, 1.26, .008), c.papel, doc, .004)
hoja_baja.rotation_euler.z = math.radians(3.5)
caja("Hoja del presupuesto", (0, 0, .043), (.92, 1.28, .010), c.papel, doc, .005)
ZH = .0495         # sobre la hoja

texto("Título del presupuesto", "PRESUPUESTO", (-.40, .55, ZH), .078, c.verde, doc, alinear="LEFT", negrita=True)
texto("Número del presupuesto", "N.º 0247", (.40, .555, ZH), .036, c.grafito, doc, alinear="RIGHT")
caja("Filete de cabecera", (0, .48, ZH), (.84, .008, .002), c.verde, doc, .001)
for ancho, y in [(.30, .43), (.22, .40)]:
    caja("Datos del cliente", (-.40 + ancho / 2, y, ZH), (ancho, .014, .0018), c.grafito, doc, .0006)

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
        caja("Separador de partida", (0, y - .045, ZH - .0004), (.84, .003, .0012), c.piedra, doc, .0004)
    crece(barra("Concepto %d" % (i + 1), (-.40, y + .008, ZH), (concepto, .022, .0022), c.grafito, doc),
          f, f + 7, *BORRADO)
    crece(barra("Detalle %d" % (i + 1), (-.40, y - .02, ZH), (concepto * .55, .012, .0018), c.grafito, doc),
          f + 2, f + 8, *BORRADO)
    crece(barra("Importe %d" % (i + 1), (.40 - importe, y + .008, ZH), (importe, .022, .0022), c.grafito, doc),
          f + 5, f + 10, *BORRADO)

crece(barra("Filete del total", (-.42, -.10, ZH), (.84, .006, .002), c.grafito, doc), 63, 69, *BORRADO)
for nombre, cuerpo, x, tam, alinear in [("Total · rótulo", "TOTAL", -.40, .062, "LEFT"),
                                        ("Total · importe", "2.480 €", .40, .076, "RIGHT")]:
    g = grupo(nombre, (x, -.17, ZH), doc)
    texto(nombre + " · texto", cuerpo, (0, 0, 0), tam, c.verde, g, alinear=alinear, negrita=True)
    aparece(g, 66, 73, *BORRADO)
crece(barra("Subrayado del total", (.09, -.225, ZH), (.31, .012, .0024), c.tinta, doc), 72, 80, *BORRADO)
plazo = grupo("Plazo anotado", (-.40, -.30, ZH), doc)
texto("Plazo · texto", "PLAZO DE EJECUCIÓN: 12 DÍAS", (0, 0, 0), .034, c.grafito, plazo, alinear="LEFT")
crece(plazo, 74, 82, *BORRADO)
caja("Línea de firma", (-.24, -.54, ZH), (.32, .004, .0016), c.grafito, doc, .0006)
texto("Firma · rótulo", "Conforme", (-.40, -.575, ZH), .026, c.grafito, doc, alinear="LEFT")

# Huella del sello, que aparece al estampar
SELLO_LOCAL = Vector((.21, -.47, ZH + .0004))
huella = grupo("Sello_estampado", SELLO_LOCAL, doc, (0, 0, math.radians(14)))
aro("Huella · aro exterior", (0, 0, 0), .14, .008, c.verde, huella)
aro("Huella · aro interior", (0, 0, 0), .113, .004, c.verde, huella)
visto("Huella · visto", (0, 0, 0), .15, c.verde, huella, grosor=.011)
aparece(huella, 110, 113, *BORRADO)

# --- Bolígrafo ------------------------------------------------------------------
boli = grupo("Boligrafo", (.20, -.66, T + .03), raiz, (0, 0, math.radians(58)))
cilindro("Cuerpo del bolígrafo", (0, 0, 0), .028, .46, c.verde, boli, (0, math.pi / 2, 0), 24)
cilindro("Capuchón", (.25, 0, 0), .03, .07, c.marfil, boli, (0, math.pi / 2, 0), 24)
caja("Clip del bolígrafo", (.21, 0, .032), (.15, .014, .008), c.acero, boli, .003)
cono("Punta del bolígrafo", (-.265, 0, 0), .028, 0, .07, c.acero, boli, (0, -math.pi / 2, 0), 24)

# --- Sello y tampón -------------------------------------------------------------
TAMPON = Vector((1.12, -.50, T))
tampon = grupo("Tampon", TAMPON, raiz, (0, 0, math.radians(-6)))
caja("Caja del tampón", (0, 0, .035), (.74, .56, .07), c.marfil, tampon, .025)
caja("Almohadilla de tinta", (0, 0, .072), (.64, .46, .014), c.goma, tampon, .006)
REPOSO = TAMPON + Vector((0, 0, .079))

sello = grupo("Sello", REPOSO, raiz, (0, 0, math.radians(-6)))
caja("Goma del sello", (0, 0, .03), (.54, .38, .06), c.goma, sello, .014)
caja("Montura del sello", (0, 0, .12), (.58, .42, .12), c.verde, sello, .04)
cilindro("Cuello del sello", (0, 0, .30), .085, .24, c.marfil, sello, lados=40)
esfera("Pomo del sello", (0, 0, .52), .17, c.verde, sello, (1, 1, .88))
esfera("Remate del pomo", (0, 0, .665), .055, c.marfil, sello)

destino = DOC + Euler((0, 0, GIRO_DOC)).to_matrix() @ SELLO_LOCAL
encima = Vector((0, 0, .34))
recorrido(sello, "location", [
    (0, REPOSO), (86, REPOSO), (94, REPOSO + encima),
    (104, destino + encima), (109, destino), (113, destino),
    (118, destino + encima * .9), (125, REPOSO + encima * .7), (129, REPOSO), (144, REPOSO),
])
recorrido(sello, "rotation_euler", [(f, (0, math.radians(g), math.radians(-6))) for f, g in
                                    [(0, 0), (94, 0), (99, -7), (104, 0), (118, 0), (121, 6), (125, 0), (144, 0)]])
recorrido(sello, "scale", [(f, (1, 1, z)) for f, z in [(0, 1), (109, 1), (111, .93), (113, 1), (144, 1)]])

# --- Calculadora de sobremesa: suma cada partida ---------------------------------
calc = grupo("Calculadora", (.62, .30, T), raiz, (0, 0, math.radians(16)), (.85, .85, .85))
caja("Cuerpo de la calculadora", (0, 0, .055), (.72, .98, .11), c.verde, calc, .05)
caja("Cabeza de la calculadora", (0, .33, .16), (.72, .32, .12), c.verde, calc, .045)
caja("Marco de la pantalla", (0, .33, .225), (.60, .24, .02), c.goma, calc, .008)
caja("Pantalla", (0, .33, .233), (.54, .17, .012), c.pantalla, calc, .004)
cifras = ["0"] + [p[2] for p in PARTIDAS]
cambios = [f + 7 for f in INICIO_PARTIDA] + [138]
for i, cifra in enumerate(cifras):
    g = grupo("Visor %s" % cifra, (.24, .325, .2395), calc)
    texto("Cifra del visor %s" % cifra, cifra, (0, 0, 0), .1, c.grafito, g, alinear="RIGHT", negrita=True)
    if i == 0:     # el cero, al empezar y al volver a empezar
        visible_entre(g, (0, cambios[0]), (cambios[-1], 145))
    else:
        visible_entre(g, (cambios[i - 1], cambios[i]))
teclas = {}
for fila in range(4):
    for col in range(4):
        ma = c.tinta if (col, fila) == (3, 3) else c.goma if col == 3 else c.marfil
        t = grupo("Tecla %d-%d" % (fila, col), (-.24 + col * .16, .07 - fila * .13, .128), calc)
        caja("Tecla", (0, 0, 0), (.12, .1, .036), ma, t, .016)
        teclas[(fila, col)] = t
caja("Signo igual", (0, .013, .0185), (.048, .008, .002), c.marfil, teclas[(3, 3)], .001)
caja("Signo igual", (0, -.013, .0185), (.048, .008, .002), c.marfil, teclas[(3, 3)], .001)
caja("Signo más", (0, 0, .0185), (.048, .008, .002), c.marfil, teclas[(2, 3)], .001)
caja("Signo más", (0, 0, .0185), (.008, .048, .002), c.marfil, teclas[(2, 3)], .001)
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

# --- Calendario de sobremesa: el plazo de obra -----------------------------------
INCLINA = math.atan2(.15, .62)
atril = grupo("Calendario_de_sobremesa", (-.12, .76, T), raiz, (0, 0, math.radians(4)))
prisma("Atril del calendario", [(-.15, 0), (.15, 0), (0, .62)], .98, c.verde, atril, bisel=.01)
hoja = grupo("Hoja del calendario", (0, -.075 - .006 * math.cos(INCLINA), .31 + .006 * math.sin(INCLINA)), atril,
             (-INCLINA, 0, 0), (.58, .58, .58))
caja("Papel del calendario", (0, 0, 0), (1.56, .012, 1.0), c.papel, hoja, .006)
caja("Cabecera del calendario", (0, -.003, .415), (1.56, .014, .17), c.verde, hoja, .006)
texto("Rótulo del calendario", "PLAZO DE OBRA", (-.70, -.0115, .415), .085, c.marfil, hoja, (math.pi / 2, 0, 0),
      "LEFT", negrita=True)
texto("Días de plazo", "12 DÍAS", (.70, -.0115, .415), .06, c.marfil, hoja, (math.pi / 2, 0, 0), "RIGHT",
      negrita=True)
COL_X = [-.60 + i * .20 for i in range(7)]
FILA_Z = [.16, .005, -.15, -.305]
for x, letra in zip(COL_X, "LMXJVSD"):
    texto("Día de la semana", letra, (x, -.007, .275), .045, c.grafito, hoja, (math.pi / 2, 0, 0))
for j, z in enumerate(FILA_Z):
    for i, x in enumerate(COL_X):
        caja("Casilla", (x, -.0065, z), (.18, .002, .135), c.suelo, hoja, .0008)
        texto("Día %d" % (j * 7 + i + 1), str(j * 7 + i + 1), (x - .072, -.0085, z + .04), .042, c.grafito, hoja,
              (math.pi / 2, 0, 0), "LEFT")
# Del día 3 al 14: un trazo rojo que recorre dos semanas, con su inicio y su fin
inicio = grupo("Inicio del plazo", (COL_X[2] - .07, -.014, FILA_Z[0] - .035), hoja)
cilindro("Punto de inicio", (0, 0, 0), .028, .006, c.tinta, inicio, (math.pi / 2, 0, 0), 24)
aparece(inicio, 78, 82, *BORRADO)
crece(barra("Plazo · semana 1", (COL_X[2] - .085, -.0105, FILA_Z[0] - .035), (5 * .20 - .02, .005, .036),
            c.tinta, hoja, .002), 81, 91, *BORRADO)
crece(barra("Plazo · semana 2", (COL_X[0] - .085, -.0105, FILA_Z[1] - .035), (7 * .20 - .02, .005, .036),
            c.tinta, hoja, .002), 91, 101, *BORRADO)
fin = grupo("Fin del plazo", (COL_X[6], -.012, FILA_Z[1]), hoja, (math.pi / 2, 0, 0))
aro("Aro del último día", (0, 0, 0), .085, .007, c.tinta, fin, aplastado=.5)
aparece(fin, 100, 105, *BORRADO)
for lado in (-1, 1):
    aro("Espiral", (lado * .36, -.01, .62), .025, .006, c.acero, atril, (0, math.pi / 2, 0), 1, 20)

# --- Casco de obra --------------------------------------------------------------
casco = grupo("Casco_de_obra", (1.18, .70, T), raiz, (0, 0, math.radians(-30)))
cilindro("Ala del casco", (0, -.03, .0125), .29, .025, c.marfil, casco, lados=48)
cupula("Copa del casco", (0, 0, .02), .23, c.marfil, casco, (1, 1.1, 1.18))
caja("Cresta del casco", (0, 0, .26), (.07, .36, .055), c.marfil, casco, .025)
cilindro("Banda del casco", (0, 0, .065), .232, .05, c.verde, casco, lados=48)

# --- Planos enrollados, al fondo --------------------------------------------------
for i, (x, y, r, largo, giro) in enumerate([(-.86, .79, .075, .86, 8), (-1.06, .93, .055, .55, -3)]):
    rollo = grupo("Plano enrollado %d" % (i + 1), (x, y, T + r), raiz, (0, 0, math.radians(giro)))
    cilindro("Rollo de papel", (0, 0, 0), r, largo, c.papel, rollo, (0, math.pi / 2, 0), 32)
    cilindro("Goma del rollo", (largo * .22, 0, 0), r + .004, .03, c.verde, rollo, (0, math.pi / 2, 0), 32)

estudio_y_camara("Cámara del paso 02", POSTER)
bpy.context.scene.frame_set(POSTER)
exportar(sys.argv[-1], "02-presupuesto-por-escrito", "Presupuesto_por_escrito_loop", [
    (0, "Inicio del bucle"), (10, "Partidas"), (63, "Total"), (78, "Plazo"),
    (86, "Sello"), (113, "Estampado"), (134, "Recoger"), (144, "Cierre del bucle")])
