// Copia a dist/ solo lo que se publica: la página y sus recursos, y empaqueta
// el 3D de la portada (src/portada-3d.js con three.js) en assets/js/portada-3d.js.
// Con SITE_URL (la URL pública), las etiquetas para compartir pasan a usar direcciones absolutas.
import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { build } from "esbuild";

const DIST = "dist";
const sitio = (process.env.SITE_URL || "").replace(/\/+$/, "");

await rm(DIST, { recursive: true, force: true });
await mkdir(DIST, { recursive: true });
await cp("assets", `${DIST}/assets`, { recursive: true });

await build({
  entryPoints: ["src/portada-3d.js"],
  outfile: `${DIST}/assets/js/portada-3d.js`,
  bundle: true,
  format: "esm",
  minify: true,
  target: "es2022",
  legalComments: "eof",
  logLevel: "warning",
});

let html = await readFile("index.html", "utf8");
if (sitio) {
  html = html
    .replace('content="assets/img/og.jpg"', `content="${sitio}/assets/img/og.jpg"`)
    .replace('"image": "assets/img/logo.png"', `"image": "${sitio}/assets/img/logo.png",\n    "url": "${sitio}/"`)
    .replace(
      '<meta property="og:type" content="website">',
      `<link rel="canonical" href="${sitio}/">\n  <meta property="og:url" content="${sitio}/">\n  <meta property="og:type" content="website">`
    );
}
await writeFile(`${DIST}/index.html`, html);

console.log(`Web copiada en ${DIST}/${sitio ? ` para ${sitio}/` : ""}`);
