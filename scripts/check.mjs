// Comprueba la página antes de publicar: recursos que existen, anclas que apuntan
// a algo, imágenes con texto alternativo, piezas del 3D, datos estructurados válidos y JavaScript sin errores de sintaxis.
// Uso: node scripts/check.mjs [carpeta]   (por defecto, la raíz del proyecto)
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const raiz = process.argv[2] || ".";
const errores = [];
const html = readFileSync(join(raiz, "index.html"), "utf8");

// Recursos locales en src, href, srcset y url() de los estilos
const rutas = new Set();
for (const [, valor] of html.matchAll(/\s(?:src|href)="([^"#]+)"/g)) rutas.add(valor);
for (const [, valor] of html.matchAll(/\ssrcset="([^"]+)"/g)) {
  valor.split(",").forEach((parte) => rutas.add(parte.trim().split(/\s+/)[0]));
}
for (const ruta of rutas) {
  if (/^(https?:|mailto:|tel:|data:)/.test(ruta)) continue;
  if (!existsSync(join(raiz, decodeURI(ruta)))) errores.push(`Falta el recurso ${ruta}`);
}

const css = readFileSync(join(raiz, "assets/css/styles.css"), "utf8");
for (const [, ruta] of css.matchAll(/url\("(\.\.\/[^"]+)"\)/g)) {
  if (!existsSync(join(raiz, "assets/css", ruta))) errores.push(`Falta el recurso ${ruta} (styles.css)`);
}

// 3D: modelos y, en la web compilada, los módulos empaquetados
const tresD = ["assets/3d/roseton.glb"];
for (const visor of ["portada-3d.js", "pasos-3d.js"]) tresD.push(raiz === "." ? `src/${visor}` : `assets/js/${visor}`);
// Piezas de «Cómo trabajamos» declaradas en la página
for (const [, modelo] of html.matchAll(/\sdata-modelo="([^"]+)"/g)) tresD.push(modelo);
for (const ruta of tresD) {
  if (!existsSync(join(raiz, ruta))) errores.push(`Falta ${ruta}`);
}

// Anclas internas
const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map(([, id]) => id));
for (const [, ancla] of html.matchAll(/\shref="#([^"]+)"/g)) {
  if (!ids.has(ancla)) errores.push(`El enlace #${ancla} no apunta a ningún elemento`);
}
for (const [, controla] of html.matchAll(/\saria-controls="([^"]+)"/g)) {
  if (!ids.has(controla)) errores.push(`aria-controls="${controla}" no apunta a ningún elemento`);
}

// Imágenes con alt (vacío solo si son decorativas)
for (const [etiqueta] of html.matchAll(/<img\b[^>]*>/g)) {
  if (!/\salt="/.test(etiqueta)) errores.push(`Imagen sin alt: ${etiqueta.slice(0, 80)}…`);
}

// Datos estructurados
for (const [, json] of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)) {
  try { JSON.parse(json); } catch (e) { errores.push(`JSON-LD no válido: ${e.message}`); }
}

// Sintaxis del JavaScript
try {
  execFileSync(process.execPath, ["--check", join(raiz, "assets/js/main.js")], { stdio: "pipe" });
} catch (e) {
  errores.push(`main.js: ${e.stderr.toString().trim()}`);
}

if (errores.length) {
  console.error(errores.map((e) => `✗ ${e}`).join("\n"));
  process.exit(1);
}
console.log(`✓ ${raiz === "." ? "Proyecto" : raiz} sin errores (${rutas.size} recursos, ${ids.size} anclas)`);
