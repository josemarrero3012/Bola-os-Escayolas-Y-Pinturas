// Portada en 3D: el rosetón de escayola modelado en Blender (blender/roseton.py),
// sobre un techo pintado en el verde de la casa. Una luz rasante sigue al puntero
// y deja ver el relieve; al bajar, la cámara se acerca y la pieza gira despacio.
import {
  ACESFilmicToneMapping,
  HemisphereLight,
  Color,
  Group,
  Mesh,
  MeshStandardMaterial,
  VSMShadowMap,
  PerspectiveCamera,
  PlaneGeometry,
  Scene,
  SpotLight,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";

const VERDE = new Color("#0e3a2b");
const YESO = new Color("#e9e7e1");

export async function iniciar({ lienzo, escenario, modelo, alListo }) {
  const renderer = new WebGLRenderer({ canvas: lienzo, antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = VSMShadowMap;   // sombras suaves, como bajo una lámpara de obra

  const escena = new Scene();
  escena.background = VERDE.clone().multiplyScalar(0.35);

  // Techo: plano en z = 0 mirando a la cámara
  const techo = new Mesh(
    new PlaneGeometry(14, 14),
    new MeshStandardMaterial({ color: VERDE, roughness: 0.75, metalness: 0 })
  );
  techo.receiveShadow = true;
  escena.add(techo);

  const camara = new PerspectiveCamera(29, 1, 0.1, 40);

  // Rebote de luz: la escayola en sombra queda gris, no verde
  escena.add(new HemisphereLight(new Color("#fbf7f0"), new Color("#56635b"), 0.55));

  // Luz rasante: casi a ras del techo, para que cada hoja proyecte sombra
  const luz = new SpotLight(new Color("#fff3e2"), 60, 0, 0.36, 0.7, 1.1);
  luz.castShadow = true;
  luz.shadow.mapSize.set(2048, 2048);
  luz.shadow.bias = -0.0005;
  luz.shadow.normalBias = 0.01;
  luz.shadow.radius = 9;
  luz.shadow.blurSamples = 12;
  luz.shadow.camera.near = 0.5;
  luz.shadow.camera.far = 9;
  escena.add(luz, luz.target);

  // Relleno frío desde el lado contrario
  const relleno = new SpotLight(new Color("#dde8e1"), 6, 0, 0.9, 1, 1.4);
  relleno.position.set(2.4, -1.6, 2.6);
  escena.add(relleno, relleno.target);

  const cargador = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const gltf = await cargador.loadAsync(modelo);
  const pieza = gltf.scene;
  // glTF pasa la Z de Blender a Y; la giramos para que la pieza salga del techo hacia la cámara (+Z)
  pieza.rotation.x = Math.PI / 2;
  const grupo = new Group();
  pieza.traverse((o) => {
    if (o.isMesh) {
      o.material = new MeshStandardMaterial({ color: YESO, roughness: 0.82, metalness: 0 });
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });
  grupo.add(pieza);
  escena.add(grupo);

  // Estado: puntero (luz) y desplazamiento (cámara)
  const puntero = { x: -0.7, y: 0.35 };
  const luzActual = { x: -1.6, y: 0.5 };
  let avance = 0;
  let avanceSuave = 0;
  let ancho = 0;
  let alto = 0;
  let visible = true;
  let primerFotograma = true;

  const fino = window.matchMedia("(pointer: fine)");
  escenario.addEventListener("pointermove", (e) => {
    if (!fino.matches) return;
    const r = escenario.getBoundingClientRect();
    puntero.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    puntero.y = -(((e.clientY - r.top) / r.height) * 2 - 1);
  });

  const medir = () => {
    ancho = lienzo.clientWidth;
    alto = lienzo.clientHeight;
    renderer.setSize(ancho, alto, false);
    camara.aspect = ancho / alto;
    camara.updateProjectionMatrix();
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
  // Se acerca con inercia y se detiene al llegar, para dejar de pintar
  const acercar = (a, b, k) => (Math.abs(b - a) < 0.001 ? b : a + (b - a) * k);
  const objetivo = new Vector3();

  // Solo se pinta cuando algo se mueve: con la escena quieta la GPU descansa
  let ultimo = "";
  const dibujar = () => {
    requestAnimationFrame(dibujar);
    if (!visible) return;

    avanceSuave = acercar(avanceSuave, avance, 0.08);
    const p = avanceSuave;
    const estrecho = ancho / alto < 1;

    // Cámara: de una vista oblicua con la pieza a la derecha a una vista casi frontal y cercana
    const desplazamiento = estrecho ? 0 : mezcla(-1.25, 0, p);
    camara.position.set(
      mezcla(estrecho ? 0 : -1.5, 0, p),
      mezcla(estrecho ? -1.4 : -2.0, -0.45, p),
      mezcla(estrecho ? 4.6 : 4.5, 2.6, p)
    );
    objetivo.set(desplazamiento, estrecho ? 0.55 * (1 - p) : mezcla(-0.12, 0, p), 0);
    camara.lookAt(objetivo);

    // La pieza gira despacio con el desplazamiento y respira un poco con el tiempo
    grupo.rotation.z = p * 0.9;

    // Luz: el puntero la mueve alrededor de la pieza, siempre baja
    luzActual.x = acercar(luzActual.x, puntero.x * 1.9, 0.06);
    luzActual.y = acercar(luzActual.y, puntero.y * 1.4, 0.06);
    const az = Math.atan2(luzActual.y, luzActual.x || -0.001);
    const d = 4.6;
    luz.position.set(Math.cos(az) * d, Math.sin(az) * d, 0.62 + Math.hypot(luzActual.x, luzActual.y) * 0.1);
    luz.target.position.set(0, 0, 0.05);

    const firma = [p, luzActual.x, luzActual.y, ancho, alto].map((n) => n.toFixed(4)).join();
    if (firma === ultimo) return;
    ultimo = firma;

    renderer.render(escena, camara);
    if (primerFotograma) {
      primerFotograma = false;
      alListo?.();
    }
  };
  requestAnimationFrame(dibujar);
}
