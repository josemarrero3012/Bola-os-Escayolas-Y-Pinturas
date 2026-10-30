(() => {
  const TELEFONO = "34660812651";
  const CORREO = "info@tutistar.com";
  const quieto = window.matchMedia("(prefers-reduced-motion: reduce)");
  const webgl = () => {
    try {
      return !!document.createElement("canvas").getContext("webgl2");
    } catch {
      return false;
    }
  };

  // Cabecera: transparente sobre la portada, con sombra después; se esconde al bajar y vuelve al subir
  const cabecera = document.querySelector("[data-cabecera]");
  const barra = document.querySelector("[data-barra]");
  const portada = document.querySelector("[data-portada]");
  let ultimoScroll = window.scrollY;

  const alDesplazar = () => {
    const y = window.scrollY;
    cabecera.classList.toggle("is-scrolled", y > 8);
    if (!cabecera.classList.contains("menu-abierto")) {
      cabecera.classList.toggle("is-oculta", y > ultimoScroll && y > 320);
    }
    // En escritorio «Qué hacemos» sube por encima del final de la portada: la cabecera
    // deja de ser transparente cuando esa sección llega arriba
    const finPortada = portada.nextElementSibling.offsetTop - cabecera.offsetHeight;
    cabecera.classList.toggle("sobre-portada", y < finPortada);
    if (barra) barra.classList.toggle("visible", y > window.innerHeight * .6);
    ultimoScroll = y;
  };
  alDesplazar();
  window.addEventListener("scroll", alDesplazar, { passive: true });

  // Menú en móvil
  const botonMenu = document.querySelector("[data-menu]");
  const nav = document.getElementById("nav");

  const cerrarMenu = () => {
    botonMenu.setAttribute("aria-expanded", "false");
    botonMenu.setAttribute("aria-label", "Abrir menú");
    cabecera.classList.remove("menu-abierto");
    document.body.style.overflow = "";
  };

  botonMenu.addEventListener("click", () => {
    const abierto = botonMenu.getAttribute("aria-expanded") === "true";
    if (abierto) return cerrarMenu();
    botonMenu.setAttribute("aria-expanded", "true");
    botonMenu.setAttribute("aria-label", "Cerrar menú");
    cabecera.classList.add("menu-abierto");
    document.body.style.overflow = "hidden";
  });

  nav.addEventListener("click", (e) => {
    if (e.target.closest("a")) cerrarMenu();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && cabecera.classList.contains("menu-abierto")) {
      cerrarMenu();
      botonMenu.focus();
    }
  });

  // Portada en pantallas grandes: la pieza en 3D se abre por capas al bajar y después se
  // dispersa hacia los bordes mientras «Qué hacemos» sube por encima. El texto de la
  // portada, la entrada de la sección y el 3D siguen el mismo avance suavizado, para que
  // la transición vaya a la vez aunque la rueda del ratón baje a saltos.
  const grande = window.matchMedia("(min-width: 960px)").matches;
  const lienzo = portada?.querySelector("[data-lienzo]");
  if (grande && webgl() && !quieto.matches && lienzo) {
    const siguiente = portada.nextElementSibling;
    const progreso = { valor: 0 };   // de 0 a 1 se abre; de 1 a 2 se dispersa
    let objetivo = 0;
    let siguiendo = false;
    let activo = true;
    const limitar = (t) => Math.min(1, Math.max(0, t));
    const suave = (t) => t * t * (3 - 2 * t);

    const pintar = () => {
      const salida = limitar(progreso.valor - 1);
      portada.style.setProperty("--dispersion", salida.toFixed(4));
      portada.classList.toggle("sin-texto", salida > 0.25);
      siguiente.style.setProperty("--entrada", suave(limitar((salida - 0.3) / 0.6)).toFixed(4));
    };
    const seguir = () => {
      if (!activo) return;
      const resta = objetivo - progreso.valor;
      progreso.valor = Math.abs(resta) < 0.0005 ? objetivo : progreso.valor + resta * 0.12;
      pintar();
      siguiendo = progreso.valor !== objetivo;
      if (siguiendo) requestAnimationFrame(seguir);
    };
    const medir = () => {
      const alto = window.innerHeight;
      const arriba = portada.getBoundingClientRect().top;
      const entra = siguiente.getBoundingClientRect().top;
      // Se abre hasta que «Qué hacemos» asoma por abajo y se dispersa mientras sube hasta la cabecera
      const apertura = limitar(-arriba / Math.max(1, entra - arriba - alto));
      const salida = limitar((alto - entra) / Math.max(1, alto - cabecera.offsetHeight));
      objetivo = apertura + salida;
      if (!siguiendo) {
        siguiendo = true;
        requestAnimationFrame(seguir);
      }
    };

    portada.classList.add("con-3d");
    medir();
    progreso.valor = objetivo;   // al recargar a mitad de página, sin animar desde arriba
    pintar();
    window.addEventListener("scroll", medir, { passive: true });
    window.addEventListener("resize", medir);

    import("./portada-3d.js")
      .then(({ iniciar }) =>
        iniciar({
          lienzo,
          escenario: portada,
          poster: portada.querySelector(".portada-poster img"),
          modelo: "assets/3d/arquitectura.glb",
          progreso,
          alListo: () => portada.classList.add("en-3d"),
        })
      )
      .catch(() => {
        // Sin 3D se queda el render de Cycles, sin el recorrido de scroll
        activo = false;
        window.removeEventListener("scroll", medir);
        window.removeEventListener("resize", medir);
        portada.classList.remove("con-3d", "sin-texto");
        portada.style.removeProperty("--dispersion");
        siguiente.style.removeProperty("--entrada");
      });
  }

  // Servicios: un panel abierto cada vez; en escritorio el visor cambia de foto
  const servicios = [...document.querySelectorAll("[data-servicio]")];
  const fotos = new Map(
    [...document.querySelectorAll("[data-visor-foto]")].map((img) => [img.dataset.visorFoto, img])
  );
  const llana = document.querySelector(".visor-llana");

  const cambiarVisor = (id) => {
    const nueva = fotos.get(id);
    if (!nueva || nueva.classList.contains("es-activa")) return;
    fotos.forEach((img) => img.classList.remove("era-activa"));
    const vieja = [...fotos.values()].find((img) => img.classList.contains("es-activa"));
    if (vieja) {
      vieja.classList.remove("es-activa");
      vieja.classList.add("era-activa");
    }
    nueva.loading = "eager";
    nueva.classList.add("es-activa");
    if (llana) {
      llana.classList.remove("pasando");
      void llana.offsetWidth;
      llana.classList.add("pasando");
    }
  };

  const abrirServicio = (servicio) => {
    servicios.forEach((s) => {
      const abre = s === servicio;
      s.classList.toggle("abierto", abre);
      s.querySelector(".servicio-boton").setAttribute("aria-expanded", String(abre));
    });
    cambiarVisor(servicio.id);
  };

  servicios.forEach((servicio, i) => {
    if (i === 0) servicio.classList.add("abierto");
    servicio.querySelector(".servicio-boton").addEventListener("click", () => {
      if (servicio.classList.contains("abierto")) {
        servicio.classList.remove("abierto");
        servicio.querySelector(".servicio-boton").setAttribute("aria-expanded", "false");
      } else {
        abrirServicio(servicio);
      }
    });
  });

  // Los enlaces del pie a un servicio lo dejan abierto
  document.querySelectorAll("[data-abrir]").forEach((enlace) =>
    enlace.addEventListener("click", () => {
      const servicio = document.getElementById(enlace.dataset.abrir);
      if (servicio) abrirServicio(servicio);
    })
  );

  // Entradas en pantalla: fotos de obra que se rascan y línea de proceso que se marca
  const alVer = (elementos, accion, margen = "0px 0px -18% 0px") => {
    // Sin movimiento no hay nada que esperar: todo queda ya hecho
    if (quieto.matches || !("IntersectionObserver" in window)) return elementos.forEach(accion);
    const io = new IntersectionObserver((entradas) => {
      entradas.forEach((entrada) => {
        if (!entrada.isIntersecting) return;
        accion(entrada.target);
        io.unobserve(entrada.target);
      });
    }, { rootMargin: margen });
    elementos.forEach((el) => io.observe(el));
  };

  const raspables = [...document.querySelectorAll("[data-raspar]")];
  raspables.forEach((el, i) => el.style.setProperty("--retraso", `${i * 0.18}s`));
  alVer(raspables, (el) => el.classList.add("raspada"));

  // Cómo trabajamos: la línea se marca según bajas, el paso que cruza el centro
  // de la pantalla es el activo y el visor de escritorio enseña su pieza en 3D
  const proceso = document.querySelector("[data-proceso]");
  if (proceso) {
    const lista = proceso.querySelector("[data-pasos]");
    const pasos = [...lista.querySelectorAll("[data-paso]")];
    const visor = proceso.querySelector("[data-visor-paso]");
    const cuenta = proceso.querySelector("[data-visor-cuenta]");
    const tituloVisor = proceso.querySelector("[data-visor-titulo]");
    let piezas = null;
    let activo = 0;

    const activar = (n) => {
      if (n === activo) return;
      activo = n;
      pasos.forEach((paso, i) => {
        paso.classList.toggle("activo", i + 1 === n);
        paso.classList.toggle("hecho", i + 1 < n);
      });
      if (!visor) return;
      visor.dataset.activo = n;
      cuenta.textContent = String(n).padStart(2, "0");
      tituloVisor.textContent = pasos[n - 1].querySelector(".paso-titulo").textContent;
      piezas?.mostrar(n);
    };

    const seguir = () => {
      const centro = window.innerHeight / 2;
      const r = lista.getBoundingClientRect();
      lista.style.setProperty("--avance", Math.min(1, Math.max(0, (centro - r.top) / r.height)).toFixed(3));
      let n = 1;
      pasos.forEach((paso, i) => {
        if (paso.getBoundingClientRect().top < centro) n = i + 1;
      });
      activar(n);
    };
    seguir();
    window.addEventListener("scroll", seguir, { passive: true });
    window.addEventListener("resize", seguir);

    const lienzo = visor?.querySelector("[data-lienzo-paso]");
    const grande = window.matchMedia("(min-width: 960px)").matches;
    if (lienzo && grande && webgl() && !quieto.matches) {
      const modelos = Object.fromEntries(
        pasos.filter((paso) => paso.dataset.modelo).map((paso) => [paso.dataset.paso, paso.dataset.modelo])
      );
      // Se carga al acercarse a la sección, no al abrir la página
      const io = new IntersectionObserver(([entrada]) => {
        if (!entrada.isIntersecting) return;
        io.disconnect();
        import("./pasos-3d.js")
          .then(({ iniciar }) =>
            iniciar({
              lienzo,
              escenario: visor,
              modelos,
              alCambiar: (conPieza) => visor.classList.toggle("con-pieza", conPieza),
            })
          )
          .then((p) => {
            piezas = p;
            piezas.mostrar(activo);
          })
          .catch(() => visor.classList.remove("con-pieza"));
      }, { rootMargin: "600px 0px" });
      io.observe(proceso);
    }
  }

  // Formulario: prepara el mensaje y lo abre en WhatsApp o en el correo
  const formulario = document.querySelector("[data-formulario]");
  const estado = formulario.querySelector("[data-estado]");
  const campoNombre = formulario.elements.nombre;
  const campoTelefono = formulario.elements.telefono;

  const avisar = (texto, esError = false) => {
    estado.textContent = texto;
    estado.classList.toggle("es-error", esError);
  };

  [campoNombre, campoTelefono].forEach((campo) =>
    campo.addEventListener("input", () => campo.removeAttribute("aria-invalid"))
  );

  formulario.addEventListener("submit", (e) => {
    e.preventDefault();

    const nombre = campoNombre.value.trim();
    const telefono = campoTelefono.value.trim();
    const cifras = telefono.replace(/\D/g, "").length;
    const trabajo = formulario.elements.trabajo.value;
    const detalles = formulario.elements.mensaje.value.trim();

    const faltan = [];
    if (!nombre) faltan.push([campoNombre, "tu nombre"]);
    if (cifras < 9) faltan.push([campoTelefono, telefono ? "un teléfono de al menos 9 cifras" : "un teléfono"]);

    faltan.forEach(([campo]) => campo.setAttribute("aria-invalid", "true"));
    if (faltan.length) {
      avisar(`Para poder llamarte, escribe ${faltan.map(([, t]) => t).join(" y ")}.`, true);
      faltan[0][0].focus();
      return;
    }

    const mensaje =
      `Hola, soy ${nombre}. Quería pedir presupuesto: ${trabajo}.` +
      (detalles ? `\n\n${detalles}` : "") +
      `\n\nMi teléfono: ${telefono}`;

    if (e.submitter && e.submitter.value === "correo") {
      const asunto = `Presupuesto: ${trabajo}`;
      window.location.href =
        `mailto:${CORREO}?subject=${encodeURIComponent(asunto)}&body=${encodeURIComponent(mensaje)}`;
      avisar("Hemos abierto tu correo con el mensaje preparado. Solo falta enviarlo.");
    } else {
      window.open(`https://wa.me/${TELEFONO}?text=${encodeURIComponent(mensaje)}`, "_blank", "noopener");
      avisar("Hemos abierto WhatsApp con el mensaje preparado. Solo falta enviarlo.");
    }
  });

  // Año del pie
  const anio = document.querySelector("[data-anio]");
  if (anio) anio.textContent = new Date().getFullYear();
})();
