// Póster de la portada pintado con el mismo visor 3D de la web (src/portada-3d.js), en
// reposo y con fondo transparente. Sirve cuando no está a mano el .blend para el render
// de Cycles (blender/portada-luz.py): el póster y el 3D salen idénticos.
// Necesita Playwright con Chromium y la web construida en dist/ (npm run build).
// Uso: node scripts/poster-3d.cjs SALIDA.png [ancho alto]
const { chromium } = require("playwright");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const [salida, ancho = "1600", alto = "1800"] = process.argv.slice(2);
const raiz = path.resolve("dist");
const tipos = { ".js": "text/javascript", ".glb": "model/gltf-binary", ".html": "text/html" };
const pagina = `<!DOCTYPE html><html><body style="margin:0;background:transparent">
<canvas id="l" style="position:absolute;inset:0;width:100%;height:100%"></canvas>
<div id="p" style="position:absolute;inset:0"></div>
<script type="module">
import { iniciar } from "./assets/js/portada-3d.js";
iniciar({ lienzo: l, escenario: document.body, poster: p, modelo: "assets/3d/arquitectura.glb",
  progreso: { valor: 0 }, alListo: () => (window.listo = true) });
</script></body></html>`;

const servidor = http.createServer((pet, res) => {
  const ruta = decodeURIComponent(new URL(pet.url, "http://x").pathname);
  if (ruta === "/") return res.end(pagina);
  const archivo = path.join(raiz, ruta);
  if (!archivo.startsWith(raiz) || !fs.existsSync(archivo)) return res.writeHead(404).end();
  res.writeHead(200, { "content-type": tipos[path.extname(archivo)] || "application/octet-stream" });
  fs.createReadStream(archivo).pipe(res);
});

servidor.listen(0, async () => {
  const navegador = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const p = await navegador.newPage({ viewport: { width: +ancho, height: +alto } });
  await p.goto(`http://localhost:${servidor.address().port}/`);
  await p.waitForFunction(() => window.listo, null, { timeout: 180000 });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: salida, omitBackground: true, timeout: 180000 });
  await navegador.close();
  servidor.close();
  console.log("Póster en", salida);
});
