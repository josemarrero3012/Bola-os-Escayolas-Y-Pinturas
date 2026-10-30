// Visor 3D de «Cómo trabajamos»: enseña la maqueta del paso activo sobre un fondo de
// estudio, en vista axonométrica como la cámara de Blender del autor, con su animación
// en bucle y un ligero vaivén que sigue al puntero. Cada pieza se carga la primera vez
// que hace falta; un paso sin pieza deja ver su número en relieve.
import {
  AnimationMixer,
  Box3,
  Color,
  DirectionalLight,
  Group,
  HemisphereLight,
  Mesh,
  NeutralToneMapping,
  OrthographicCamera,
  PlaneGeometry,
  PMREMGenerator,
  Scene,
  ShadowMaterial,
  SRGBColorSpace,
  Vector3,
  VSMShadowMap,
  WebGLRenderer,
} from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

const TAMANO = 2;          // cada pieza se escala para que su lado mayor mida esto
// Dirección de la cámara de las maquetas (la de Blender, pasada a ejes glTF)
const VISTA = new Vector3(5.8, 6.8, 8).normalize();

export async function iniciar({ lienzo, escenario, modelos, alCambiar }) {
  // Fondo transparente: el degradado de estudio lo pone la hoja de estilos
  const renderer = new WebGLRenderer({ canvas: lienzo, antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = NeutralToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = VSMShadowMap;

  const escena = new Scene();
  const pmrem = new PMREMGenerator(renderer);
  escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  escena.environmentIntensity = 0.45;
  pmrem.dispose();

  const cielo = new HemisphereLight(new Color("#ffffff"), new Color("#d9d6cf"), 0.7);
  escena.add(cielo);

  // Las tres luces del estudio de las maquetas: principal, relleno y contraluz
  const sol = new DirectionalLight(new Color("#fff6ea"), 2.2);
  sol.position.set(1, 7, 4);
  sol.castShadow = true;
  sol.shadow.mapSize.set(2048, 2048);
  sol.shadow.camera.left = sol.shadow.camera.bottom = -2.5;
  sol.shadow.camera.right = sol.shadow.camera.top = 2.5;
  sol.shadow.camera.near = 1;
  sol.shadow.camera.far = 14;
  sol.shadow.radius = 10;
  sol.shadow.blurSamples = 16;
  sol.shadow.bias = -0.0004;
  sol.shadow.normalBias = 0.02;
  escena.add(sol);
  const relleno = new DirectionalLight(new Color("#f4f6f8"), 0.55);
  relleno.position.set(-4, 4, 1);
  const contraluz = new DirectionalLight(new Color("#ffffff"), 0.8);
  contraluz.position.set(3, 6, -4);
  escena.add(relleno, contraluz);

  // Suelo invisible que solo recoge la sombra
  const suelo = new Mesh(new PlaneGeometry(12, 12), new ShadowMaterial({ opacity: 0.16 }));
  suelo.rotation.x = -Math.PI / 2;
  suelo.receiveShadow = true;
  escena.add(suelo);

  const camara = new OrthographicCamera(-1, 1, 1, -1, 0.1, 50);
  const mira = new Vector3(0, 0.5, 0);
  let radio = 1.2;

  const plato = new Group();      // gira con el tiempo
  escena.add(plato);

  const cargador = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const cache = new Map();
  const cargar = (url) => {
    if (!cache.has(url)) {
      cache.set(url, cargador.loadAsync(url).then(({ scene: pieza, animations }) => {
        pieza.traverse((o) => {
          if (o.isMesh) {
            o.castShadow = true;
            o.receiveShadow = true;
          }
        });
        // Centrada, apoyada en el suelo y a un tamaño común
        const caja = new Box3().setFromObject(pieza);
        const tam = caja.getSize(new Vector3());
        const escala = TAMANO / Math.max(tam.x, tam.y, tam.z);
        pieza.scale.setScalar(escala);
        const centro = caja.getCenter(new Vector3()).multiplyScalar(escala);
        pieza.position.set(-centro.x, -caja.min.y * escala, -centro.z);
        const soporte = new Group();
        soporte.add(pieza);
        soporte.userData.alto = tam.y * escala;
        soporte.userData.radio = tam.multiplyScalar(escala / 2).length();
        // La animación de la maqueta, en bucle
        if (animations.length) {
          const mezclador = new AnimationMixer(pieza);
          animations.forEach((clip) => mezclador.clipAction(clip).play());
          soporte.userData.mezclador = mezclador;
        }
        return soporte;
      }));
    }
    return cache.get(url);
  };

  // Puntero: inclina un poco la pieza
  const puntero = { x: 0, y: 0 };
  const inclinacion = { x: 0, y: 0 };
  const fino = window.matchMedia("(pointer: fine)");
  escenario.addEventListener("pointermove", (e) => {
    if (!fino.matches) return;
    const r = escenario.getBoundingClientRect();
    puntero.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    puntero.y = ((e.clientY - r.top) / r.height) * 2 - 1;
  });
  escenario.addEventListener("pointerleave", () => { puntero.x = puntero.y = 0; });

  let aspecto = 1;
  const encuadrar = () => {
    // La maqueta entra entera, con aire alrededor
    const medio = radio * (aspecto < 1 ? 1.02 / aspecto : 1.02);
    camara.left = -medio * aspecto;
    camara.right = medio * aspecto;
    camara.top = medio;
    camara.bottom = -medio;
    camara.updateProjectionMatrix();
  };
  const medir = () => {
    const ancho = lienzo.clientWidth;
    const alto = lienzo.clientHeight;
    renderer.setSize(ancho, alto, false);
    aspecto = ancho / alto;
    encuadrar();
  };
  new ResizeObserver(medir).observe(lienzo);
  medir();

  let visible = true;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(escenario);

  // Entrada de cada pieza: sube un poco y se asienta
  let actual = null;
  let entrada = 1;
  let pedido = 0;

  const mostrar = async (n) => {
    const turno = ++pedido;
    const url = modelos[n];
    if (!url) {
      alCambiar?.(false);
      return;
    }
    let soporte;
    try {
      soporte = await cargar(url);
    } catch {
      alCambiar?.(false);
      return;
    }
    if (turno !== pedido) return;      // mientras cargaba, el usuario ya pasó a otro paso
    if (actual !== soporte) {
      if (actual) plato.remove(actual);
      plato.add(soporte);
      actual = soporte;
      entrada = 0;
      // Encuadre según el tamaño de la pieza
      mira.y = soporte.userData.alto * 0.42;
      radio = soporte.userData.radio;
      encuadrar();
    }
    alCambiar?.(true);
  };

  let antes = performance.now();
  const dibujar = (ahora) => {
    requestAnimationFrame(dibujar);
    const dt = Math.min(0.05, (ahora - antes) / 1000);
    antes = ahora;
    if (!visible || !actual) return;

    entrada = Math.min(1, entrada + dt / 1.1);
    const e = 1 - Math.pow(1 - entrada, 4);
    actual.position.y = (1 - e) * -0.25;
    actual.scale.setScalar(0.92 + 0.08 * e);

    actual.userData.mezclador?.update(dt);

    // Vaivén lento y el puntero, que gira la maqueta un poco hacia donde miras
    inclinacion.x += (puntero.y * 0.1 - inclinacion.x) * 0.05;
    inclinacion.y += (puntero.x * 0.32 - inclinacion.y) * 0.05;
    plato.rotation.y = Math.sin(ahora / 1000 * 0.35) * 0.1 + inclinacion.y;

    camara.position.copy(VISTA).multiplyScalar(12).add(mira);
    camara.position.y += inclinacion.x * 4;
    camara.lookAt(mira);

    renderer.render(escena, camara);
  };
  requestAnimationFrame(dibujar);

  return { mostrar };
}
