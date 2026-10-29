(() => {
  const TELEFONO = "34660812651";
  const CORREO = "info@tutistar.com";
  const quieto = window.matchMedia("(prefers-reduced-motion: reduce)");

  // Cabecera: sombra al despegarse del techo; se esconde al bajar y vuelve al subir
  const cabecera = document.querySelector("[data-cabecera]");
  const barra = document.querySelector("[data-barra]");
  const inicio = document.querySelector("[data-inicio]");
  let ultimoScroll = window.scrollY;

  const alDesplazar = () => {
    const y = window.scrollY;
    cabecera.classList.toggle("is-scrolled", y > 8);
    if (!cabecera.classList.contains("menu-abierto")) {
      cabecera.classList.toggle("is-oculta", y > ultimoScroll && y > 320);
    }
    if (barra) barra.classList.toggle("visible", y > inicio.offsetHeight * .6);
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

  // Luz rasante: la textura de llana solo se ve donde da la luz.
  // Al cargar, la luz viaja con la terraja; después sigue al puntero con algo de inercia.
  if (inicio && !quieto.matches) {
    const pos = { x: .3, y: .42 };
    const meta = { x: .3, y: .42 };
    let animando = false;

    const pintar = () => {
      inicio.style.setProperty("--lx", `${(pos.x * 100).toFixed(2)}%`);
      inicio.style.setProperty("--ly", `${(pos.y * 100).toFixed(2)}%`);
    };

    const seguir = () => {
      pos.x += (meta.x - pos.x) * .07;
      pos.y += (meta.y - pos.y) * .07;
      pintar();
      if (Math.abs(meta.x - pos.x) > .0005 || Math.abs(meta.y - pos.y) > .0005) {
        requestAnimationFrame(seguir);
      } else {
        animando = false;
      }
    };

    const apuntar = (x, y) => {
      meta.x = x;
      meta.y = y;
      if (!animando) {
        animando = true;
        requestAnimationFrame(seguir);
      }
    };

    // Entrada: de fuera por la izquierda hasta su sitio, al ritmo de la cornisa
    const t0 = performance.now();
    const DURACION = 2100;
    const curva = (t) => 1 - Math.pow(1 - t, 3);
    let entrando = true;
    const entrar = (ahora) => {
      const t = Math.min(1, (ahora - t0 - 200) / DURACION);
      if (t > 0) {
        pos.x = meta.x = -.15 + (.3 + .15) * curva(t);
        pos.y = meta.y = .2 + (.42 - .2) * curva(t);
        pintar();
      }
      if (t < 1 && entrando) requestAnimationFrame(entrar);
      else entrando = false;
    };
    requestAnimationFrame(entrar);

    const fino = window.matchMedia("(pointer: fine)");
    inicio.addEventListener("pointermove", (e) => {
      if (!fino.matches) return;
      entrando = false;
      const r = inicio.getBoundingClientRect();
      apuntar((e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height);
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
  alVer([...document.querySelectorAll("[data-pasos]")], (el) => el.classList.add("marcados"), "0px 0px -25% 0px");

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
