# Prototipo Web - Escayolas y Pinturas Bolaños

Propuesta de web para **Escayolas y Pinturas Bolaños**, empresa de escayola, pladur, pintura y reformas en Las Palmas de Gran Canaria, desarrollada para Aterna Studio.

**[Ver el prototipo publicado](https://josemarrero3012.github.io/Bola-os-Escayolas-Y-Pinturas/)**

> Versión de presentación. Los textos, las opiniones y los datos de contacto deben confirmarse con el negocio antes de pasar a producción. El formulario no envía nada por sí mismo: prepara el mensaje y lo abre en WhatsApp o en el correo.

## Concepto

La página es una habitación: empieza en el techo y termina en el rodapié. Cada animación sale del oficio:

- **Portada:** un rosetón de escayola modelado en Blender, en gris perla sobre un techo blanco, con hojas de acanto detalladas y oclusión ambiental horneada en Cycles. En escritorio se pinta en 3D en tiempo real: una luz rasante sigue al puntero y descubre el relieve, y al bajar la cámara se acerca y la pieza gira. Mientras carga, en móvil o sin WebGL se ve su render de Cycles. El titular se extiende como la pasta bajo la llana y los iconos de los oficios se trazan como con lápiz de obra.
- **Servicios:** lista desplegable; en escritorio, un visor cambia de foto con una pasada de llana.
- **Obra reciente:** las fotos aparecen enlucidas y se rascan al entrar en pantalla.
- **Cómo trabajamos:** va justo después de los servicios. Los pasos bajan en vertical por una línea que se marca en rojo según avanzas. En escritorio, un visor fijo enseña la maqueta 3D animada del paso activo, y los pasos sin maqueta muestran su número en relieve. En móvil, cada paso lleva el render de su maqueta.

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

## El rosetón en Blender

`blender/roseton.py` modela la pieza por procedimiento (base torneada, sarta de perlas, hojas de acanto y florón gallonado), la exporta a GLB y renderiza con Cycles los pósteres de escritorio y móvil. Necesita el módulo `bpy` de Blender 5.x (`pip install bpy` con Python 3.13):

```bash
python blender/roseton.py build-3d
npx @gltf-transform/cli meshopt build-3d/roseton.glb assets/3d/roseton.glb
```

Los pósteres (`build-3d/roseton-*.png`) se pasan a WebP en `assets/img/`. El modelo publicado pesa unos 1,6 MB (600 KB comprimido) y solo se carga en escritorio.

## Las maquetas de «Cómo trabajamos»

Cada paso puede tener una maqueta hecha en Blender (un `.blend` y su `.glb` con la animación en un solo clip). `blender/paso.py` pasa sus materiales de marca a la paleta actual («Azul Bolaños» a verde, «Tinta de plano» a rojo) y renderiza con Cycles el póster con fondo transparente:

```bash
python blender/paso.py MAQUETA.blend MAQUETA.glb build-paso [--fotograma 96]
npx @gltf-transform/cli meshopt build-paso/paso.glb assets/3d/paso-N.glb
```

La maqueta del paso 02 (presupuesto por partidas, calculadora, sello y calendario con el plazo de obra) se genera entera con `blender/paso-2-presupuesto.py`, sobre la misma base, estudio y cámara que la del paso 01:

```bash
python blender/paso-2-presupuesto.py build-maqueta-2
python blender/paso.py build-maqueta-2/02-presupuesto-por-escrito.blend build-maqueta-2/02-presupuesto-por-escrito.glb build-paso --fotograma 131
```

El póster (`build-paso/paso.png`) se pasa a WebP de 1000 × 1000 en `assets/img/paso-N.webp`. Para activar el paso N en `index.html`, se añade `data-modelo="assets/3d/paso-N.glb"` a su `<li>` y su `<figure class="paso-figura">`. En el visor, su `<span data-cifra-paso="N">` se cambia por `<img class="visor-paso-poster" data-poster-paso="N" …>`, como en el paso 1.

## Organización

```text
.github/         Publicación en GitHub Pages, verificación y plantilla de pull requests
assets/3d/       Rosetón en GLB (comprimido con meshopt)
assets/css/      Estilos
assets/fonts/    Archivo (fuente variable, servida desde el propio sitio)
assets/img/      Imágenes optimizadas que se publican
assets/js/       Comportamiento del navegador
blender/         Rosetón y maquetas de «Cómo trabajamos», con sus renders
images/          Fotos originales del negocio; no se publican
scripts/         Compilación y verificación
src/             Portada en 3D (three.js); se empaqueta al compilar
dist/            Web compilada; fuera de Git
```

`assets/img/estuco.webp` es una textura generada (pasadas de llana sombreadas con luz rasante), no una fotografía.

## Publicación

Cada push a `main` publica la web con GitHub Actions (`.github/workflows/deploy.yml`). Las pull requests se verifican con `.github/workflows/ci.yml`. La primera vez hay que elegir en **Settings → Pages → Build and deployment → Source** la opción «GitHub Actions».
