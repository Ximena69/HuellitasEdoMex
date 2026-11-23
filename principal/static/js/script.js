
document.addEventListener("DOMContentLoaded", () => {

    // =====================================
    // BUSCADOR DE MASCOTAS
    // =====================================

    const buscador = document.querySelector("#buscadorMascotas");

    if (buscador) {

        buscador.addEventListener("input", () => {

            const texto = buscador.value.toLowerCase();

            const tarjetas = document.querySelectorAll(".mascota-card");

            tarjetas.forEach(card => {

                const titulo = card.querySelector(".card-title");

                if (!titulo) return;

                const nombre = titulo.textContent.toLowerCase();

                card.style.display = nombre.includes(texto) ? "" : "none";

            });

        });

    }

    // =====================================
    // VALIDAR CONTRASEÑAS EN EL REGISTRO
    // =====================================

    const formRegistro = document.querySelector("#formRegistro");

    if (formRegistro) {

        formRegistro.addEventListener("submit", (evento) => {

            const pass = document.querySelector("#password");
            const confirm = document.querySelector("#confirmPassword");

            if (pass && confirm && pass.value !== confirm.value) {

                evento.preventDefault();

                alert("Las contraseñas no coinciden.");

                confirm.focus();

            }

        });

    }

    // =====================================
    // CONFIRMAR PUBLICACIÓN
    // =====================================

    const formPublicar = document.querySelector("#formPublicar");

    if (formPublicar) {

        formPublicar.addEventListener("submit", (evento) => {

            const respuesta = confirm(
                "¿Deseas publicar esta mascota?"
            );

            if (!respuesta) {
                evento.preventDefault();
            }

        });

    }

    // =====================================
    // CONFIRMAR SOLICITUD DE ADOPCIÓN
    // =====================================

    const formSolicitud = document.querySelector("#formSolicitud");

    if (formSolicitud) {

        formSolicitud.addEventListener("submit", (evento) => {

            const respuesta = confirm(
                "¿Deseas enviar la solicitud de adopción?"
            );

            if (!respuesta) {
                evento.preventDefault();
            }

        });

    }

    // =====================================
    // VALIDAR CAMPOS TELEFÓNICOS
    // =====================================

    const telefonos = document.querySelectorAll('input[type="tel"]');

    telefonos.forEach(campo => {

        campo.addEventListener("input", () => {

            campo.value = campo.value.replace(/\D/g, "");

        });

    });

});
