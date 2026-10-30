// Portada en 3D: «Arquitectura suspendida», la composición de escayola que José Manuel
// modeló en Blender (arco, paneles, medio rosetón, cornisas y panel terracota).
// Las siete piezas se abren por capas al bajar, siguiendo los estados de su
// transforms.json (hero → scrollStart → scrollMid → exit). La cámara es la misma
// ortográfica de tres cuartos del render, así que al entrar el 3D encaja encima del
// póster sin salto; después se centra y gira un poco hacia el frente.
import {
  Color,
  NeutralToneMapping,
  DirectionalLight,
  HemisphereLight,
  OrthographicCamera,
  VSMShadowMap,
  PMREMGenerator,
  Group,
  Scene,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import coreografia from "./portada-estados.json";

// Cámaras del .blend, ya en ejes glTF: (x, y, z) Blender → (x, z, −y)
const TRES_CUARTOS = { posicion: new Vector3(4.227, 3.255, 10), mira: new Vector3(-0.372, -0.281, -0.885), arriba: new Vector3(-0.109, 0.96, -0.259) };
const FRENTE = { posicion: new Vector3(0.227, 1.155, 12), mira: new Vector3(-0.017, -0.091, -0.996), arriba: new Vector3(-0.002, 0.996, -0.091) };
const ALTO_ENCUADRE = 4.65;     // ortho_scale de la cámara: metros que caben en el alto del render
const PROPORCION_POSTER = 1600 / 1800;
const GIRO_HACIA_FRENTE = 0.3;  // cuánto se acerca la vista al frente a mitad del recorrido
const ACERCAMIENTO = 1.12;      // zoom suave mientras la pieza se abre
const DESATURAR_ESCAYOLA = 0.6;

// Punto del eje de una cámara más cercano al origen: el centro de su encuadre
const centroDeEje = ({ posicion, mira }) => {
  const d = mira.clone().normalize();
  return posicion.clone().addScaledVector(d, -posicion.dot(d));
};

export async function iniciar({ lienzo, escenario, poster, modelo, alListo }) {
  const renderer = new WebGLRenderer({ canvas: lienzo, antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = NeutralToneMapping;   // conserva el blanco de la escayola y el naranja del panel
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = VSMShadowMap;   // sombras suaves, como bajo un softbox

  const escena = new Scene();
  const pmrem = new PMREMGenerator(renderer);
  escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  escena.environmentIntensity = 0.3;
  pmrem.dispose();

  escena.add(new HemisphereLight(new Color("#f4f7ff"), new Color("#cfcbc4"), 0.42));

  // Las tres luces de estudio del .blend, como luces direccionales
  const clave = new DirectionalLight(new Color("#fffaf3"), 3.3);
  clave.position.set(-3.473, 6.055, 4.2);
  clave.castShadow = true;
  clave.shadow.mapSize.set(2048, 2048);
  Object.assign(clave.shadow.camera, { left: -3.4, right: 3.4, top: 3.4, bottom: -3.4, near: 0.5, far: 20 });
  clave.shadow.bias = -0.0004;
  clave.shadow.normalBias = 0.02;
  clave.shadow.radius = 16;
  clave.shadow.blurSamples = 24;
  const relleno = new DirectionalLight(new Color("#eef3ff"), 0.4);
  relleno.position.set(4.027, 2.555, 3.0);
  const contra = new DirectionalLight(new Color("#fff4e4"), 0.8);
  contra.position.set(2.527, 5.055, -3.0);
  escena.add(clave, relleno, contra);

  const cargador = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const gltf = await cargador.loadAsync(modelo);
  const pieza = gltf.scene;
  const ajustados = new Set();
  pieza.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true;
    o.receiveShadow = true;
    // Blender pinta con AgX, que apaga la saturación de los claros; aquí la escayola
    // se acerca al gris para que no amarillee y quede como en el render
    const m = o.material;
    if (m.name.startsWith("Plaster") && !ajustados.has(m)) {
      ajustados.add(m);
      const gris = m.color.r * 0.2126 + m.color.g * 0.7152 + m.color.b * 0.0722;
      m.color.lerp(new Color(gris, gris, gris), DESATURAR_ESCAYOLA);
    }
  });
  // El puntero inclina el conjunto sin tocar las transformaciones de cada pieza
  const conjunto = new Group();
  conjunto.add(pieza);
  escena.add(conjunto);

  // Estados de scroll: posición, giro (Euler XYZ, radianes) y escala de cada pieza
  const estados = coreografia.estados;
  const tiempos = estados.map((e) => e.avance);
  const piezas = Object.keys(estados[0].piezas).map((nombre) => {
    const objeto = pieza.getObjectByName(nombre);
    if (!objeto) throw new Error(`Falta la pieza ${nombre} en ${modelo}`);
    const curva = (campo) => estados.map((e) => e.piezas[nombre][campo]);
    return { objeto, posicion: curva("posicion"), giro: curva("giro"), escala: curva("escala") };
  });

  // Interpolación cúbica de Hermite con tangentes de Catmull-Rom (no uniformes):
  // pasa por cada estado sin frenar en seco entre tramos
  const tangente = (valores, i, k) => {
    const a = Math.max(0, i - 1);
    const b = Math.min(valores.length - 1, i + 1);
    return (valores[b][k] - valores[a][k]) / (tiempos[b] - tiempos[a]);
  };
  const interpolar = (valores, p, salida) => {
    let i = 0;
    while (i < tiempos.length - 2 && p > tiempos[i + 1]) i++;
    const h = tiempos[i + 1] - tiempos[i];
    const t = Math.min(1, Math.max(0, (p - tiempos[i]) / h));
    const t2 = t * t;
    const t3 = t2 * t;
    for (let k = 0; k < 3; k++) {
      salida[k] =
        (2 * t3 - 3 * t2 + 1) * valores[i][k] +
        (t3 - 2 * t2 + t) * h * tangente(valores, i, k) +
        (-2 * t3 + 3 * t2) * valores[i + 1][k] +
        (t3 - t2) * h * tangente(valores, i + 1, k);
    }
    return salida;
  };
  const tmp = [0, 0, 0];
  const colocar = (p) => {
    for (const { objeto, posicion, giro, escala } of piezas) {
      objeto.position.fromArray(interpolar(posicion, p, tmp));
      objeto.rotation.set(...interpolar(giro, p, tmp), "XYZ");
      objeto.scale.fromArray(interpolar(escala, p, tmp));
    }
  };

  const camara = new OrthographicCamera(-1, 1, 1, -1, 0.1, 60);
  const ejeTresCuartos = centroDeEje(TRES_CUARTOS);
  const ejeFrente = centroDeEje(FRENTE);
  const mira = new Vector3();
  const arriba = new Vector3();
  const eje = new Vector3();

  // Estado: desplazamiento, puntero y tamaño
  let avance = 0;
  let avanceSuave = 0;
  const puntero = { x: 0, y: 0 };
  const inclinacion = { x: 0, y: 0 };
  let ancho = 0;
  let alto = 0;
  let encuadre = null;   // dónde está el póster dentro del lienzo, en píxeles
  let visible = true;
  let primerFotograma = true;

  const fino = window.matchMedia("(pointer: fine)");
  escenario.addEventListener("pointermove", (e) => {
    if (!fino.matches) return;
    puntero.x = (e.clientX / window.innerWidth) * 2 - 1;
    puntero.y = (e.clientY / window.innerHeight) * 2 - 1;
  });

  // El póster se ve con object-fit: contain alineado arriba a la derecha; su rectángulo
  // real marca la escala (px por metro) y el centro del encuadre de la cámara
  const medir = () => {
    ancho = lienzo.clientWidth;
    alto = lienzo.clientHeight;
    renderer.setSize(ancho, alto, false);
    const caja = poster.getBoundingClientRect();
    const marco = lienzo.getBoundingClientRect();
    const h = Math.min(caja.height, caja.width / PROPORCION_POSTER);
    const w = h * PROPORCION_POSTER;
    encuadre = {
      x: caja.right - w / 2 - marco.left,
      y: caja.top + h / 2 - marco.top,
      pxPorMetro: h / ALTO_ENCUADRE,
    };
  };
  new ResizeObserver(medir).observe(lienzo);
  medir();

  const alDesplazar = () => {
    const r = escenario.getBoundingClientRect();
    const recorrido = Math.max(1, r.height - window.innerHeight);
    avance = Math.min(1, Math.max(0, -r.top / recorrido));
  };
  window.addEventListener("scroll", alDesplazar, { passive: true });
  alDesplazar();

  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(escenario);

  const mezcla = (a, b, t) => a + (b - a) * t;
  const suave = (t) => t * t * (3 - 2 * t);
  // Se acerca con inercia y se detiene al llegar, para dejar de pintar
  const acercar = (a, b, k) => (Math.abs(b - a) < 0.0004 ? b : a + (b - a) * k);

  // Solo se pinta cuando algo se mueve: con la escena quieta la GPU descansa
  let ultimo = "";
  const dibujar = () => {
    requestAnimationFrame(dibujar);
    if (!visible || !encuadre) return;

    avanceSuave = acercar(avanceSuave, avance, 0.09);
    inclinacion.x = acercar(inclinacion.x, puntero.y * 0.035, 0.05);
    inclinacion.y = acercar(inclinacion.y, puntero.x * 0.07, 0.05);
    const p = avanceSuave;

    const firma = [p, inclinacion.x, inclinacion.y, ancho, alto].map((n) => n.toFixed(4)).join();
    if (firma === ultimo) return;
    ultimo = firma;

    colocar(p);
    conjunto.rotation.set(inclinacion.x, inclinacion.y, 0);

    // Hasta la mitad del recorrido la pieza va al centro, se acerca un poco y gira hacia el frente
    const t = suave(Math.min(1, p / tiempos[2]));
    const estrecho = ancho < 1100;
    const cx = mezcla(encuadre.x, ancho * (estrecho ? 0.5 : 0.56), t);
    // En la salida la pieza baja algo más y se desvanece mientras llega la sección siguiente
    const s = suave(Math.min(1, Math.max(0, (p - tiempos[2]) / (1 - tiempos[2]))));
    const cy = mezcla(encuadre.y, alto * 0.52, t) + alto * 0.08 * s;
    const desvanecer = 1 - suave(Math.min(1, Math.max(0, (p - 0.8) / 0.2)));
    lienzo.style.filter = desvanecer < 1 ? `opacity(${desvanecer.toFixed(3)})` : "";
    const k = encuadre.pxPorMetro * mezcla(1, ACERCAMIENTO, t);

    const g = t * GIRO_HACIA_FRENTE;
    mira.copy(TRES_CUARTOS.mira).lerp(FRENTE.mira, g).normalize();
    arriba.copy(TRES_CUARTOS.arriba).lerp(FRENTE.arriba, g).normalize();
    eje.copy(ejeTresCuartos).lerp(ejeFrente, g);
    camara.position.copy(eje).addScaledVector(mira, -24);
    camara.up.copy(arriba);
    camara.lookAt(eje);
    // El eje de la cámara cae en (cx, cy) del lienzo
    camara.left = -cx / k;
    camara.right = (ancho - cx) / k;
    camara.top = cy / k;
    camara.bottom = -(alto - cy) / k;
    camara.updateProjectionMatrix();

    renderer.render(escena, camara);
    if (primerFotograma) {
      primerFotograma = false;
      alListo?.();
    }
  };
  requestAnimationFrame(dibujar);
}
