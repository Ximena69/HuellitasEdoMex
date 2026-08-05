document.addEventListener("DOMContentLoaded", () => {

    const buscador =
    document.querySelector("#buscadorMascotas");

    if (buscador) {

        buscador.addEventListener("input", () => {

            const texto =
            buscador.value.toLowerCase();

            const tarjetas =
            document.querySelectorAll(".mascota-card");

            tarjetas.forEach(card => {

                const nombre =
                card.querySelector(".card-title")
                .textContent
                .toLowerCase();

                if (nombre.includes(texto)) {

                    card.style.display = "block";

                } else {

                    card.style.display = "none";

                }

            });

        });

    }

});
const formRegistro =
document.querySelector("#formRegistro");

if (formRegistro) {

    formRegistro.addEventListener("submit", (e) => {

        const pass =
        document.querySelector("#password").value;

        const confirm =
        document.querySelector("#confirmPassword").value;

        if (pass !== confirm) {

            e.preventDefault();

            alert("Las contraseñas no coinciden");

        }

    });

}
const formPublicar =
document.querySelector("#formPublicar");

if (formPublicar) {

    formPublicar.addEventListener("submit", (e) => {

        const respuesta = confirm(
            "¿Deseas publicar esta mascota?"
        );

        if (!respuesta) {

            e.preventDefault();

        }

    });

}
const formSolicitud =
document.querySelector("#formSolicitud");

if (formSolicitud) {

    formSolicitud.addEventListener("submit", (e) => {

        const respuesta = confirm(
            "¿Deseas enviar la solicitud?"
        );

        if (!respuesta) {

            e.preventDefault();

        }

    });

}
const telefonos =
document.querySelectorAll('input[type="tel"]');

telefonos.forEach(campo => {

    campo.addEventListener("input", () => {

        campo.value =
        campo.value.replace(/\D/g, "");

    });

});