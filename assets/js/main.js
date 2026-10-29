(() => {
  const TELEFONO = "34660812651";
  const CORREO = "info@tutistar.com";

  // Cabecera: sombra al despegarse del techo
  const cabecera = document.querySelector("[data-cabecera]");
  const marcarScroll = () => cabecera.classList.toggle("is-scrolled", window.scrollY > 8);
  marcarScroll();
  window.addEventListener("scroll", marcarScroll, { passive: true });

  // Menú en móvil
  const botonMenu = document.querySelector("[data-menu]");
  const nav = document.getElementById("nav");

  const cerrarMenu = () => {
    botonMenu.setAttribute("aria-expanded", "false");
    botonMenu.textContent = "Menú";
    cabecera.classList.remove("menu-abierto");
  };

  botonMenu.addEventListener("click", () => {
    const abierto = botonMenu.getAttribute("aria-expanded") === "true";
    if (abierto) return cerrarMenu();
    botonMenu.setAttribute("aria-expanded", "true");
    botonMenu.textContent = "Cerrar";
    cabecera.classList.add("menu-abierto");
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
