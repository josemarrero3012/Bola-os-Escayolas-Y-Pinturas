// Portada en 3D: «Arquitectura suspendida», la composición de escayola que José Manuel
// modeló en Blender (arco, paneles, medio rosetón, cornisas y panel terracota).
// Al bajar, las siete piezas se abren por capas siguiendo los estados de su
// transforms.json (hero → scrollStart → scrollMid) y después se dispersan en abanico
// hacia los bordes de la pantalla, creciendo y desvaneciéndose mientras sube «Qué
// hacemos». La cámara es la misma ortográfica de tres cuartos del render y la luz, el
// mismo estudio de blender/portada-luz.py, así que al entrar el 3D encaja encima del
// póster sin salto.
import {
  Box3,
  Color,
  DirectionalLight,
  DoubleSide,
  Group,
  HemisphereLight,
  Mesh,
  MeshBasicMaterial,
  NeutralToneMapping,
  OrthographicCamera,
  PlaneGeometry,
  PMREMGenerator,
  Quaternion,
  Scene,
  SRGBColorSpace,
  Vector3,
  VSMShadowMap,
  WebGLRenderer,
} from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
import coreografia from "./portada-estados.json";

// Cámaras del .blend, ya en ejes glTF: (x, y, z) Blender → (x, z, −y)
const TRES_CUARTOS = { posicion: new Vector3(4.227, 3.255, 10), mira: new Vector3(-0.372, -0.281, -0.885), arriba: new Vector3(-0.109, 0.96, -0.259) };
const FRENTE = { posicion: new Vector3(0.227, 1.155, 12), mira: new Vector3(-0.017, -0.091, -0.996), arriba: new Vector3(-0.002, 0.996, -0.091) };
const ALTO_ENCUADRE = 4.65;     // ortho_scale de la cámara: metros que caben en el alto del render
const PROPORCION_POSTER = 1600 / 1800;
const GIRO_HACIA_FRENTE = 0.25; // cuánto se acerca la vista al frente mientras se abre
const EMPUJE = 0.14;            // la cámara avanza un poco mientras las piezas salen
const CRECER = 0.45;            // cada pieza crece hasta un 45 % camino del borde
const ESCALONADO = 0.12;        // las piezas de delante salen antes que las del fondo
const LLEGADA = 0.8;            // en ese punto de la salida la última pieza cruza el borde
const GIRO_ABANICO = 0.35;      // el abanico gira ~20°: el arco sale hacia la izquierda y no cruza el titular que sube
const DESATURAR_ESCAYOLA = 0.6;
const DESATURAR_BARRO = 0.15;
const ACLARAR_BARRO = 1.45;

// Estudio de blender/portada-luz.py en ejes glTF: posición, tamaño (ancho × alto), color
// y vatios de cada luz de área. Aquí son paneles que brillan en el entorno y dan los
// reflejos en la veladura; la clave, el relleno y el recorte, además, iluminan como
// luces direccionales (la clave con sus sombras suaves).
const LUCES = {
  clave: { posicion: [-3.473, 6.055, 4.2], tam: [2.0, 3.2], color: [1, 0.92, 0.82], vatios: 1900 },
  relleno: { posicion: [4.027, 2.555, 3.0], tam: [3.1, 3.1], color: [0.84, 0.9, 1], vatios: 40 },
  recorte: { posicion: [2.527, 5.055, -3.0], tam: [2.66, 2.66], color: [1, 0.96, 0.9], vatios: 650 },
  tiraDelante: { posicion: [-6.0, 2.4, 5.5], tam: [0.12, 5.0], color: [1, 0.97, 0.93], vatios: 250 },
  tiraCenital: { posicion: [0.4, 7.5, 1.5], tam: [6.0, 0.12], color: [1, 0.97, 0.92], vatios: 120 },
  contraluzIzquierda: { posicion: [-4.6, 1.8, -3.6], tam: [0.15, 4.5], color: [0.84, 0.9, 1], vatios: 1300 },
  contraluzDerecha: { posicion: [5.2, 2.4, -2.2], tam: [0.15, 4.5], color: [1, 0.88, 0.74], vatios: 1300 },
};
const RADIANCIA = 0.05;         // brillo de los paneles por vatio y metro cuadrado
const SALA = 0.2;               // penumbra del estudio, el mundo de Blender

// Entorno para los reflejos: los paneles de luz en una sala en penumbra
const estudio = () => {
  const sala = new Scene();
  sala.background = new Color(0.62, 0.67, 0.76).multiplyScalar(SALA);
  for (const { posicion, tam, color, vatios } of Object.values(LUCES)) {
    const brillo = (vatios / (tam[0] * tam[1])) * RADIANCIA;
    const panel = new Mesh(new PlaneGeometry(...tam), new MeshBasicMaterial({ color: new Color(...color).multiplyScalar(brillo), side: DoubleSide }));
    panel.position.fromArray(posicion);
    if (tam[0] > tam[1]) panel.up.set(0, 0, -1);   // la tira cenital, de lado a lado
    panel.lookAt(0, 0.2, 0);
    sala.add(panel);
  }
  return sala;
};

const direccional = (luz, intensidad) => {
  const d = new DirectionalLight(new Color(...luz.color), intensidad);
  d.position.fromArray(luz.posicion);
  return d;
};

// Punto del eje de una cámara más cercano al origen: el centro de su encuadre
const centroDeEje = ({ posicion, mira }) => {
  const d = mira.clone().normalize();
  return posicion.clone().addScaledVector(d, -posicion.dot(d));
};

// Avance de 0 a 2 en `progreso.valor`: de 0 a 1 la pieza se abre, de 1 a 2 se dispersa.
// Lo calcula main.js, que mueve con el mismo valor el texto y la sección siguiente.
export async function iniciar({ lienzo, escenario, poster, modelo, progreso, alListo }) {
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
  const sala = estudio();
  escena.environment = pmrem.fromScene(sala, 0.01).texture;
  pmrem.dispose();
  sala.traverse((o) => {
    if (!o.isMesh) return;
    o.geometry.dispose();
    o.material.dispose();
  });

  // Sin rebote de luz entre piezas, una luz de cielo cálida y un suelo apagado hacen
  // de relleno: las caras que miran abajo quedan más oscuras, como en Cycles
  escena.add(new HemisphereLight(new Color("#fff8f0"), new Color("#8a8580"), 1.2));

  // La sombra de la clave se difumina unos 18 cm, como la de un softbox de 2 × 3,2 m a 8 m
  const clave = direccional(LUCES.clave, 3.1);
  clave.castShadow = true;
  clave.shadow.mapSize.set(1024, 1024);
  Object.assign(clave.shadow.camera, { left: -3.4, right: 3.4, top: 3.4, bottom: -3.4, near: 0.5, far: 20 });
  clave.shadow.bias = -0.0004;
  clave.shadow.normalBias = 0.02;
  clave.shadow.radius = 28;
  clave.shadow.blurSamples = 32;
  escena.add(clave, direccional(LUCES.relleno, 0.12), direccional(LUCES.recorte, 0.6));

  const cargador = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const gltf = await cargador.loadAsync(modelo);
  const pieza = gltf.scene;
  const ajustados = new Set();
  pieza.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true;
    o.receiveShadow = true;
    const m = o.material;
    if (ajustados.has(m)) return;
    ajustados.add(m);
    // La veladura satinada del render: la escayola, más brillante; el barro, menos
    if (m.isMeshPhysicalMaterial) {
      const barro = m.name.startsWith("Terracotta");
      m.specularIntensity = 0.8;
      m.clearcoat = barro ? 0.3 : 0.5;
      m.clearcoatRoughness = barro ? 0.08 : 0.06;
    }
    // Blender pinta con AgX, que apaga la saturación de los claros; aquí la escayola
    // se acerca al gris para que no amarillee y el barro se aclara un poco, como en el render
    const gris = m.color.r * 0.2126 + m.color.g * 0.7152 + m.color.b * 0.0722;
    if (m.name.startsWith("Plaster")) m.color.lerp(new Color(gris, gris, gris), DESATURAR_ESCAYOLA);
    if (m.name.startsWith("Terracotta")) m.color.lerp(new Color(gris, gris, gris), DESATURAR_BARRO).multiplyScalar(ACLARAR_BARRO);
  });
  // El puntero inclina el conjunto sin tocar las transformaciones de cada pieza
  const conjunto = new Group();
  conjunto.add(pieza);
  escena.add(conjunto);

  // Estados de apertura: posición, giro (Euler XYZ, radianes) y escala de cada pieza.
  // El último del transforms.json (exit) no se usa: la salida es la dispersión.
  const estados = coreografia.estados.slice(0, 3);
  const tiempos = estados.map((e) => e.avance);
  const abierto = tiempos.at(-1);
  escena.updateMatrixWorld(true);
  const piezas = Object.keys(estados[0].piezas).map((nombre) => {
    const objeto = pieza.getObjectByName(nombre);
    if (!objeto) throw new Error(`Falta la pieza ${nombre} en ${modelo}`);
    const curva = (campo) => estados.map((e) => e.piezas[nombre][campo]);
    // Caja de la pieza en sus propios ejes: el pivote del .blend no siempre está en medio
    const caja = new Box3();
    const aPieza = objeto.matrixWorld.clone().invert();
    objeto.traverse((o) => {
      if (!o.isMesh) return;
      o.geometry.computeBoundingBox();
      caja.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld.clone().premultiply(aPieza)));
    });
    return { objeto, posicion: curva("posicion"), giro: curva("giro"), escala: curva("escala"), caja, centro: caja.getCenter(new Vector3()) };
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
  // g = 0 es la vista del render; g = 1, la de frente
  const orientar = (g) => {
    mira.copy(TRES_CUARTOS.mira).lerp(FRENTE.mira, g).normalize();
    arriba.copy(TRES_CUARTOS.arriba).lerp(FRENTE.arriba, g).normalize();
    eje.copy(ejeTresCuartos).lerp(ejeFrente, g);
    camara.position.copy(eje).addScaledVector(mira, -24);
    camara.up.copy(arriba);
    camara.lookAt(eje);
    camara.updateMatrixWorld();
  };

  // Dispersión: cada pieza sale en línea recta desde el centro de la composición. Las
  // siete direcciones se reparten en abanico regular, en el orden en que ya están las
  // piezas en pantalla, para que lleguen a todos los bordes y no se amontonen en uno.
  // Se calcula una vez, con la pieza abierta y la cámara como queda al final de la apertura.
  colocar(abierto);
  orientar(GIRO_HACIA_FRENTE);
  escena.updateMatrixWorld(true);
  const derecha = new Vector3().setFromMatrixColumn(camara.matrixWorld, 0);
  const arribaPantalla = new Vector3().setFromMatrixColumn(camara.matrixWorld, 1);
  // Metros en el plano de la pantalla desde el eje de la cámara, con y hacia abajo
  const enPantalla = (w) => {
    w.sub(eje);
    return { x: w.dot(derecha), y: -w.dot(arribaPantalla) };
  };
  const centroTotal = enPantalla(new Box3().setFromObject(pieza).getCenter(new Vector3()));
  let bordeDerecho = -Infinity;   // hasta dónde llega a la derecha la pieza abierta, en metros
  for (const pz of piezas) {
    const mundo = pz.objeto.localToWorld(pz.centro.clone());
    pz.fondo = mundo.dot(mira);
    pz.pantalla = enPantalla(mundo);
    pz.angulo = Math.atan2(pz.pantalla.y - centroTotal.y, pz.pantalla.x - centroTotal.x);
    // Radio en pantalla: la esquina de su caja más alejada del centro
    pz.radio = 0;
    for (let i = 0; i < 8; i++) {
      const esquina = new Vector3(
        i & 1 ? pz.caja.max.x : pz.caja.min.x,
        i & 2 ? pz.caja.max.y : pz.caja.min.y,
        i & 4 ? pz.caja.max.z : pz.caja.min.z,
      );
      const e = enPantalla(pz.objeto.localToWorld(esquina));
      pz.radio = Math.max(pz.radio, Math.hypot(e.x - pz.pantalla.x, e.y - pz.pantalla.y));
      bordeDerecho = Math.max(bordeDerecho, e.x);
    }
  }
  const enAbanico = [...piezas].sort((a, b) => a.angulo - b.angulo);
  const paso = (2 * Math.PI) / enAbanico.length;
  // El abanico gira lo justo para parecerse a las direcciones naturales (media circular)
  let coseno = 0;
  let seno = 0;
  enAbanico.forEach((pz, i) => {
    coseno += Math.cos(pz.angulo - i * paso);
    seno += Math.sin(pz.angulo - i * paso);
  });
  const base = Math.atan2(seno, coseno) + GIRO_ABANICO;
  enAbanico.forEach((pz, i) => {
    const a = base + i * paso;
    pz.direccion = { x: Math.cos(a), y: Math.sin(a) };
    // Vuelca hacia fuera sobre el eje de la pantalla perpendicular a su salida, con algo de giro propio
    pz.ejeVuelco = new Vector3()
      .addScaledVector(derecha, Math.sin(a))
      .addScaledVector(arribaPantalla, Math.cos(a))
      .addScaledVector(mira, i % 2 ? 0.6 : -0.6)
      .normalize();
    pz.vuelco = 0.4 + 0.12 * (i % 3);
  });
  // Primero salen las de delante, como al abrirse
  [...piezas].sort((a, b) => a.fondo - b.fondo).forEach((pz, i, lista) => {
    pz.retraso = (i / (lista.length - 1)) * ESCALONADO;
  });

  // Estado: puntero y tamaño
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
      margen: marco.right - caja.right,
    };
  };
  new ResizeObserver(medir).observe(lienzo);
  medir();

  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(escenario);

  const limitar = (t) => Math.min(1, Math.max(0, t));
  const suave = (t) => t * t * (3 - 2 * t);
  // Se acerca con inercia y se detiene al llegar, para dejar de pintar
  const acercar = (a, b, k) => (Math.abs(b - a) < 0.0004 ? b : a + (b - a) * k);

  // Píxeles desde (x, y) hasta el borde del lienzo en la dirección d
  const hastaElBorde = (x, y, d) => {
    const enX = d.x > 1e-6 ? (ancho - x) / d.x : d.x < -1e-6 ? -x / d.x : Infinity;
    const enY = d.y > 1e-6 ? (alto - y) / d.y : d.y < -1e-6 ? -y / d.y : Infinity;
    return Math.max(0, Math.min(enX, enY));
  };

  const centro = new Vector3();
  const origen = new Vector3();
  const desplazamiento = new Vector3();
  const vuelco = new Quaternion();
  const giroPadre = new Quaternion();
  const inverso = new Quaternion();
  const dispersar = (salida, cx) => {
    escena.updateMatrixWorld();
    const k = encuadre.pxPorMetro;
    for (const pz of piezas) {
      const u = limitar((salida - pz.retraso) / (LLEGADA - ESCALONADO));
      if (u === 0) continue;
      const f = u ** 1.6;   // arranca suave y acelera hacia el borde
      const s = 1 + CRECER * f;
      // Lo que le falta a la pieza abierta para salir entera de la pantalla
      const x = cx + pz.pantalla.x * k;
      const y = encuadre.y + pz.pantalla.y * k;
      const metros = ((hastaElBorde(x, y, pz.direccion) + pz.radio * k * (1 + CRECER) + 40) / k) * f;
      desplazamiento.copy(derecha).multiplyScalar(pz.direccion.x * metros).addScaledVector(arribaPantalla, -pz.direccion.y * metros);
      vuelco.setFromAxisAngle(pz.ejeVuelco, pz.vuelco * f);
      // Crece y vuelca alrededor de su centro, no del pivote
      const { objeto } = pz;
      objeto.localToWorld(centro.copy(pz.centro));
      objeto.getWorldPosition(origen).sub(centro).applyQuaternion(vuelco).multiplyScalar(s).add(centro).add(desplazamiento);
      objeto.position.copy(objeto.parent.worldToLocal(origen));
      // El vuelco está en ejes del mundo: se pasa a los del padre
      objeto.parent.getWorldQuaternion(giroPadre);
      vuelco.premultiply(inverso.copy(giroPadre).invert()).multiply(giroPadre);
      objeto.quaternion.premultiply(vuelco);
      objeto.scale.multiplyScalar(s);
    }
  };

  // Solo se pinta cuando algo se mueve: con la escena quieta la GPU descansa
  let ultimo = "";
  const dibujar = () => {
    requestAnimationFrame(dibujar);
    if (!visible || !encuadre) return;

    inclinacion.x = acercar(inclinacion.x, puntero.y * 0.035, 0.05);
    inclinacion.y = acercar(inclinacion.y, puntero.x * 0.07, 0.05);
    const avance = progreso.valor;

    const firma = [avance, inclinacion.x, inclinacion.y, ancho, alto].map((n) => n.toFixed(4)).join();
    if (firma === ultimo) return;
    ultimo = firma;

    const apertura = limitar(avance);
    const salida = limitar(avance - 1);

    // Se abre por capas hasta el estado scrollMid, frenando al llegar; si abierta no cabe,
    // se corre a la izquierda lo justo para guardar el mismo margen que el póster
    const sobra = encuadre.x + bordeDerecho * encuadre.pxPorMetro - (ancho - encuadre.margen);
    const cx = encuadre.x - Math.max(0, sobra) * suave(apertura);
    colocar(abierto * (1 - (1 - apertura) ** 2));
    conjunto.rotation.set(inclinacion.x, inclinacion.y, 0);
    orientar(GIRO_HACIA_FRENTE * suave(apertura));
    if (salida > 0) dispersar(salida, cx);

    // Mientras se dispersa, la cámara avanza sobre el centro de la pieza y todo se desvanece
    const k = encuadre.pxPorMetro * (1 + EMPUJE * suave(salida));
    camara.left = -cx / k;
    camara.right = (ancho - cx) / k;
    camara.top = encuadre.y / k;
    camara.bottom = -(alto - encuadre.y) / k;
    camara.updateProjectionMatrix();
    const opacidad = 1 - suave(limitar((salida - 0.42) / 0.4));
    lienzo.style.filter = opacidad < 1 ? `opacity(${opacidad.toFixed(3)})` : "";

    if (opacidad > 0) renderer.render(escena, camara);
    if (primerFotograma) {
      primerFotograma = false;
      alListo?.();
    }
  };
  requestAnimationFrame(dibujar);
}
