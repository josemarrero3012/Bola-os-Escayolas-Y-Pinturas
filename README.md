# Prototipo Web - Escayolas y Pinturas Bolaños

Propuesta de web para **Escayolas y Pinturas Bolaños**, empresa de escayola, pladur, pintura y reformas en Las Palmas de Gran Canaria, desarrollada para Aterna Studio.

**[Ver el prototipo publicado](https://josemarrero3012.github.io/Bola-os-Escayolas-Y-Pinturas/)**

> Versión de presentación. Los textos, las opiniones y los datos de contacto deben confirmarse con el negocio antes de pasar a producción. El formulario no envía nada por sí mismo: prepara el mensaje y lo abre en WhatsApp o en el correo.

## Concepto

La página es una habitación: empieza en el techo y termina en el rodapié. Cada animación sale del oficio:

- **Portada:** un rosetón de escayola modelado en Blender, sobre un techo pintado en el verde de la casa. En escritorio se pinta en 3D en tiempo real: una luz rasante sigue al puntero y descubre el relieve, y al bajar la cámara se acerca y la pieza gira. Mientras carga, en móvil o sin WebGL se ve su render de Cycles. El titular se extiende como la pasta bajo la llana y los iconos de los oficios se trazan como con lápiz de obra.
- **Servicios:** lista desplegable; en escritorio, un visor cambia de foto con una pasada de llana.
- **Obra reciente:** las fotos aparecen enlucidas y se rascan al entrar en pantalla.
- **Cómo trabajamos:** la línea del proceso se marca de punta a punta y los pasos se encienden en orden.

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

Los pósteres (`build-3d/roseton-*.png`) se pasan a WebP en `assets/img/`. El modelo publicado pesa unos 190 KB (60 KB comprimido).

## Organización

```text
.github/         Publicación en GitHub Pages, verificación y plantilla de pull requests
assets/3d/       Rosetón en GLB (comprimido con meshopt)
assets/css/      Estilos
assets/fonts/    Archivo (fuente variable, servida desde el propio sitio)
assets/img/      Imágenes optimizadas que se publican
assets/js/       Comportamiento del navegador
blender/         Modelo y render del rosetón
images/          Fotos originales del negocio; no se publican
scripts/         Compilación y verificación
src/             Portada en 3D (three.js); se empaqueta al compilar
dist/            Web compilada; fuera de Git
```

`assets/img/estuco.webp` es una textura generada (pasadas de llana sombreadas con luz rasante), no una fotografía.

## Publicación

Cada push a `main` publica la web con GitHub Actions (`.github/workflows/deploy.yml`). Las pull requests se verifican con `.github/workflows/ci.yml`. La primera vez hay que elegir en **Settings → Pages → Build and deployment → Source** la opción «GitHub Actions».
