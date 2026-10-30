# Prototipo Web - Escayolas y Reformas Bolaños

Propuesta de web para **Escayolas y Reformas Bolaños**, empresa de escayola, pladur, pintura y reformas en Las Palmas de Gran Canaria, desarrollada para Aterna Studio.

**[Ver el prototipo publicado](https://josemarrero3012.github.io/Bola-os-Escayolas-Y-Pinturas/)**

> Versión de presentación. Los textos, las opiniones y los datos de contacto deben confirmarse con el negocio antes de pasar a producción. El formulario no envía nada por sí mismo: prepara el mensaje y lo abre en WhatsApp o en el correo.

## Concepto

La página es una habitación: empieza en el techo y termina en el rodapié. Cada animación sale del oficio:

- **Portada:** «Arquitectura suspendida», siete piezas de escayola modeladas en Blender por José Manuel: arco, paneles moldurados, medio rosetón de acanto, dos cornisas y un panel terracota. En escritorio se pinta en 3D en tiempo real con la misma cámara ortográfica de tres cuartos del render, así que encaja encima de la imagen sin salto. Al bajar, las piezas se abren por capas siguiendo los estados de su `transforms.json` (`hero` → `scrollStart` → `scrollMid` → `exit`): la composición va al centro, gira un poco hacia el frente y al final sale hacia abajo a la derecha. El puntero la inclina levemente. Mientras carga, en móvil o sin WebGL se ve su render de Cycles. El titular se extiende como la pasta bajo la llana y los iconos de los oficios se trazan como con lápiz de obra.
- **Servicios:** lista desplegable; en escritorio, un visor cambia de foto con una pasada de llana.
- **Obra reciente:** las fotos aparecen enlucidas y se rascan al entrar en pantalla.
- **Cómo trabajamos:** va justo después de los servicios. Los pasos bajan en vertical por una línea que se marca en naranja según avanzas. Cada paso tiene su maqueta animada, y cada una en un escenario distinto. En escritorio, un visor fijo enseña en 3D la del paso activo; en móvil, cada paso lleva su render. Un paso sin maqueta mostraría su número en relieve.

Con «reducir movimiento» activado en el sistema, todo aparece ya terminado y la portada usa el render.

## Desarrollo local

Requiere **Node.js 22** (`.nvmrc`).

```bash
npm ci
npm run dev        # compila en dist/ y la sirve en localhost:8765
npm run check      # recursos, anclas, alt de imágenes, JSON-LD, 3D y sintaxis del JS
npm run build      # compila la web publicable en dist/ (empaqueta el 3D con three.js)
npm run check:dist # comprueba la copia de dist/
```

Abrir `index.html` sin compilar funciona, pero la portada se queda con el render: el 3D solo existe en `dist/`.

## La pieza de la portada

La pieza se modela fuera del repositorio, en la carpeta `bolanos-3d` de José Manuel (Blender 5.2, con sus scripts de construcción, validación y render). A la web llegan tres cosas:

- `assets/3d/arquitectura.glb`: su `exports/bolanos_architecture.glb` con las texturas en WebP y la geometría comprimida con meshopt (de 6,1 MB a 1,1 MB). Solo se carga en escritorio.
- `src/portada-estados.json`: los estados de `animation/transforms.json` (posición, giro Euler XYZ en radianes y escala de cada pieza, locales a `Hero_Architecture`). La web usa los tres de apertura; la salida es una dispersión en abanico hacia los bordes de la pantalla, calculada en `src/portada-3d.js`.
- `assets/img/arquitectura-escritorio.webp` y `arquitectura-movil.webp`: el render transparente de `blender/portada-luz.py`, reducido a 1200×1350 y 800×900. El script abre su `.blend`, le pone la luz de estudio de la web (softbox cálido, relleno frío muy bajo, tiras de contraluz y veladura satinada en la escayola) y renderiza con la cámara de tres cuartos.

```bash
npx @gltf-transform/cli webp bolanos_architecture.glb tmp.glb --quality 90
npx @gltf-transform/cli meshopt tmp.glb assets/3d/arquitectura.glb
python blender/portada-luz.py bolanos-3d/blender/bolanos_architecture.blend portada.png   # 1600×1800, 128 muestras
```

Si cambia la cámara `Camera_Three_Quarter` del `.blend`, hay que copiar su posición, dirección y `ortho_scale` a las constantes del principio de `src/portada-3d.js` para que el 3D siga encajando con el render. Lo mismo con las luces: `LUCES` en `src/portada-3d.js` repite las de `blender/portada-luz.py` en ejes glTF.

## Las maquetas de «Cómo trabajamos»

Cada paso puede tener una maqueta hecha en Blender (un `.blend` y su `.glb` con la animación en un solo clip). `blender/paso.py` pasa sus materiales de marca a la paleta actual («Azul Bolaños» a naranja, «Goma azul oscura» a tostado oscuro, «Tinta de plano» a naranja hondo, «Tapizado salvia» a lino) y renderiza con Cycles el póster con fondo transparente:

```bash
python blender/paso.py MAQUETA.blend MAQUETA.glb build-paso [--fotograma 96]
npx @gltf-transform/cli meshopt build-paso/paso.glb assets/3d/paso-N.glb
```

Las maquetas de los pasos 02, 03 y 04 se generan enteras con sus scripts, cada una en su propio escenario: una mesa de obra sobre caballetes (presupuesto), una plataforma redonda de parqué (obra limpia) y la vivienda en planta (entrega y repaso). Comparten con la del paso 01 materiales, estudio de luces, cámara y bucle de 6 s, a través de `blender/maqueta_comun.py`:

```bash
python blender/paso-2-presupuesto.py build-maqueta-2      # póster: --fotograma 131
python blender/paso-3-obra-limpia.py build-maqueta-3      # póster: --fotograma 112
python blender/paso-4-entrega.py build-maqueta-4          # póster: --fotograma 120
python blender/paso.py build-maqueta-2/02-presupuesto-por-escrito.blend build-maqueta-2/02-presupuesto-por-escrito.glb build-paso --fotograma 131
```

El póster (`build-paso/paso.png`) se pasa a WebP de 1000 × 1000 en `assets/img/paso-N.webp`. Para activar el paso N en `index.html`, se añade `data-modelo="assets/3d/paso-N.glb"` a su `<li>` y su `<figure class="paso-figura">`. En el visor, su `<span data-cifra-paso="N">` se cambia por `<img class="visor-paso-poster" data-poster-paso="N" …>`, como en el paso 1.

## Organización

```text
.github/         Publicación en GitHub Pages, verificación y plantilla de pull requests
assets/3d/       Pieza de la portada y maquetas en GLB (comprimidas con meshopt)
assets/css/      Estilos
assets/fonts/    Archivo (fuente variable, servida desde el propio sitio)
assets/img/      Imágenes optimizadas que se publican
assets/js/       Comportamiento del navegador
blender/         Maquetas de «Cómo trabajamos», con sus renders
images/          Fotos originales del negocio; no se publican
scripts/         Compilación y verificación
src/             Portada en 3D (three.js); se empaqueta al compilar
dist/            Web compilada; fuera de Git
```

`assets/img/estuco.webp` es una textura generada (pasadas de llana sombreadas con luz rasante), no una fotografía.

## Publicación

Cada push a `main` publica la web con GitHub Actions (`.github/workflows/deploy.yml`). Las pull requests se verifican con `.github/workflows/ci.yml`. La primera vez hay que elegir en **Settings → Pages → Build and deployment → Source** la opción «GitHub Actions».
