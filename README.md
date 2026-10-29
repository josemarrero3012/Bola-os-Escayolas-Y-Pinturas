# Prototipo Web - Escayolas y Pinturas Bolaños

Propuesta de web para **Escayolas y Pinturas Bolaños**, empresa de escayola, pladur, pintura y reformas en Las Palmas de Gran Canaria, desarrollada para Aterna Studio.

**[Ver el prototipo publicado](https://josemarrero3012.github.io/Bola-os-Escayolas-Y-Pinturas/)**

> Versión de presentación. Los textos, las opiniones y los datos de contacto deben confirmarse con el negocio antes de pasar a producción. El formulario no envía nada por sí mismo: prepara el mensaje y lo abre en WhatsApp o en el correo.

## Concepto

La página es una pared. Empieza en el techo con una cornisa de escayola y termina en el suelo con un rodapié. Cada animación sale del oficio:

- **Portada:** la cornisa se corre de izquierda a derecha como con la terraja, el titular se extiende como la pasta bajo la llana y la pared de estuco solo deja ver sus pasadas bajo una luz rasante que sigue al puntero.
- **Servicios:** lista desplegable; en escritorio, un visor cambia de foto con una pasada de llana.
- **Obra reciente:** las fotos aparecen enlucidas y se rascan al entrar en pantalla.
- **Cómo trabajamos:** la línea del proceso se marca de punta a punta y los pasos se encienden en orden.

Con «reducir movimiento» activado en el sistema, todo aparece ya terminado.

## Desarrollo local

Requiere **Node.js 22** (`.nvmrc`). No hay dependencias que instalar.

```bash
npm run check      # recursos, anclas, alt de imágenes, JSON-LD y sintaxis del JS
npm run build      # copia la web publicable en dist/
npm run check:dist # comprueba la copia de dist/
npm run preview    # sirve dist/ en localhost:8765
```

## Organización

```text
.github/         Publicación en GitHub Pages, verificación y plantilla de pull requests
assets/css/      Estilos
assets/fonts/    Archivo (fuente variable, servida desde el propio sitio)
assets/img/      Imágenes optimizadas que se publican
assets/js/       Comportamiento del navegador
images/          Fotos originales del negocio; no se publican
scripts/         Compilación y verificación
dist/            Web compilada; fuera de Git
```

`assets/img/estuco.webp` es una textura generada (pasadas de llana sombreadas con luz rasante), no una fotografía.

## Publicación

Cada push a `main` publica la web con GitHub Actions (`.github/workflows/deploy.yml`). Las pull requests se verifican con `.github/workflows/ci.yml`. La primera vez hay que elegir en **Settings → Pages → Build and deployment → Source** la opción «GitHub Actions».
