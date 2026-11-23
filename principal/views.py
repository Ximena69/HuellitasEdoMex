
import re
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from PIL import Image, UnidentifiedImageError

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from django.forms import modelform_factory

from .models import (
    Mascota,
    SolicitudAdopcion,
    Especie,
    Fotografia,
    Usuario,
    Ubicacion,
    CampaniaBienestar,
    ReporteMascota,
)


# =========================
# FUNCIONES AUXILIARES
# =========================

def url_segura(request, destino):
    if destino and url_has_allowed_host_and_scheme(
        url=destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return destino
    return None


def redireccion_por_rol(usuario):
    if usuario.role == 'ADMIN_SISTEMA':
        return redirect('panel_admin')
    if usuario.role == 'RESPONSABLE':
        return redirect('panel_responsable')
    if usuario.role == 'INTERESADO':
        return redirect('panel_interesado')
    return redirect('inicio')


def calcular_edad(fecha_nacimiento):
    diferencia = relativedelta(timezone.localdate(), fecha_nacimiento)

    if diferencia.years:
        return f"{diferencia.years} año(s)"

    if diferencia.months:
        return f"{diferencia.months} mes(es)"

    return "Menos de un mes"


def validar_fotografia(archivo):
    if not archivo:
        raise ValidationError("Debes seleccionar una fotografía.")

    if archivo.size > 5 * 1024 * 1024:
        raise ValidationError("La fotografía no debe superar los 5 MB.")

    try:
        imagen = Image.open(archivo)

        if imagen.format not in ('JPEG', 'PNG', 'WEBP'):
            raise ValidationError("Solo se permiten imágenes JPG, PNG o WEBP.")

        if imagen.width * imagen.height > 25_000_000:
            raise ValidationError("La resolución de la fotografía es demasiado grande.")

        imagen.verify()
        archivo.seek(0)

    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValidationError("El archivo seleccionado no es una imagen válida.")


# =========================
# PÁGINAS GENERALES
# =========================

def inicio(request):
    mascotas = Mascota.objects.filter(
        estado_publicacion='Disponible'
    ).prefetch_related('fotos').order_by('-fecha_publicacion')

    if request.user.is_authenticated and request.user.ubicacion_id:
        mascotas_cercanas = mascotas.filter(
            ubicacion=request.user.ubicacion
        )
        if mascotas_cercanas.exists():
            mascotas = mascotas_cercanas

    ubicaciones = Ubicacion.objects.all().order_by('municipio')

    return render(request, 'inicio.html', {
        'mascotas': mascotas,
        'ubicaciones': ubicaciones
    })


def adoptar(request):
    mascotas = Mascota.objects.filter(
        estado_publicacion='Disponible'
    ).prefetch_related('fotos').order_by('-fecha_publicacion')

    query_nombre = request.GET.get('nombre', '').strip()
    query_especie = request.GET.get('especie', '').strip()
    query_ubicacion = request.GET.get('ubicacion', '').strip()

    if query_nombre:
        mascotas = mascotas.filter(nombre__icontains=query_nombre)

    if query_especie in ('perro', 'gato'):
        mascotas = mascotas.filter(especie__tipo_especie=query_especie)

    if query_ubicacion.isdigit():
        mascotas = mascotas.filter(ubicacion_id=int(query_ubicacion))

    ubicaciones = Ubicacion.objects.all().order_by('municipio')

    return render(request, 'adoptar.html', {
        'mascotas': mascotas,
        'ubicaciones': ubicaciones
    })


def detalle(request):
    id_mascota = request.GET.get('id')

    if not request.user.is_authenticated:
        destino = request.get_full_path()
        return redirect(f"/login/?next={destino}")

    mascota = get_object_or_404(Mascota, id_mascota=id_mascota)

    return render(request, 'detalle.html', {
        'mascota': mascota
    })


def solicitud(request):
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para enviar una solicitud.")
        return redirect('login')

    if request.user.role != 'INTERESADO':
        messages.error(request, "Solo los usuarios interesados pueden solicitar una adopción.")
        return redirect('inicio')

    id_mascota = request.GET.get('mascota_id')
    mascota = get_object_or_404(Mascota, id_mascota=id_mascota)

    if mascota.responsable_id == request.user.id:
        messages.error(request, "No puedes solicitar tu propia publicación.")
        return redirect('adoptar')

    if mascota.estado_publicacion != 'Disponible':
        messages.error(request, "Esta mascota ya no está disponible.")
        return redirect('adoptar')

    if request.method == 'POST':
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()
        vivienda = request.POST.get('vivienda', '').strip()
        patio = request.POST.get('patio', '').strip()
        otras_mascotas = request.POST.get('otras_mascotas', '').strip()
        experiencia = request.POST.get('experiencia', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()

        try:
            if not correo:
                raise ValidationError("El correo es obligatorio.")
            if len(correo) > 254:
                raise ValidationError("El correo es demasiado largo.")

            validate_email(correo)

            if telefono and (
                not telefono.isdigit() or len(telefono) > 15
            ):
                raise ValidationError("El teléfono debe contener máximo 15 dígitos.")

            if vivienda not in ('Casa propia', 'Casa rentada', 'Departamento'):
                raise ValidationError("Selecciona un tipo de vivienda válido.")

            if patio not in ('Sí', 'Si', 'No'):
                raise ValidationError("Indica si cuentas con patio.")

            if otras_mascotas not in ('Sí', 'Si', 'No'):
                raise ValidationError("Indica si tienes otras mascotas.")

            if not experiencia:
                raise ValidationError("Describe tu experiencia con mascotas.")

            if len(experiencia) > 2000:
                raise ValidationError("La experiencia no debe superar los 2000 caracteres.")

            if len(mensaje) < 20:
                raise ValidationError("El mensaje debe tener al menos 20 caracteres.")

            if len(mensaje) > 2000:
                raise ValidationError("El mensaje no debe superar los 2000 caracteres.")

            palabras_restringidas = [
                'tonto', 'bobo', 'estupido', 'maltrato', 'perro feo', 'asco'
            ]

            for palabra in palabras_restringidas:
                if re.search(r'\b' + re.escape(palabra) + r'\b', mensaje.lower()):
                    raise ValidationError("Tu mensaje contiene términos inapropiados.")

            with transaction.atomic():
                mascota_bloqueada = Mascota.objects.select_for_update().get(
                    id_mascota=mascota.id_mascota
                )

                if mascota_bloqueada.estado_publicacion != 'Disponible':
                    raise ValidationError("Esta mascota ya no está disponible.")

                existe = SolicitudAdopcion.objects.filter(
                    mascota=mascota_bloqueada,
                    interesado=request.user,
                    estado_solicitud='Pendiente'
                ).exists()

                if existe:
                    raise ValidationError("Ya tienes una solicitud pendiente para esta mascota.")

                SolicitudAdopcion.objects.create(
                    mascota=mascota_bloqueada,
                    interesado=request.user,
                    telefono=telefono or None,
                    correo=correo,
                    vivienda=vivienda,
                    patio=patio,
                    otras_mascotas=otras_mascotas,
                    experiencia=experiencia,
                    mensaje=mensaje,
                    estado_solicitud='Pendiente'
                )

            messages.success(request, f"Tu solicitud para adoptar a {mascota.nombre} fue enviada.")
            return redirect('panel_interesado')

        except ValidationError as error:
            messages.error(request, error.messages[0])

    return render(request, 'solicitud.html', {'mascota': mascota})


def sobre(request):
    return render(request, 'sobre.html')


def terminos(request):
    return render(request, 'terminos.html')


def privacidad(request):
    return render(request, 'privacidad.html')



# =========================
# CAMPAÑAS DE BIENESTAR ANIMAL
# =========================

def campanias(request):
    campanias_lista = CampaniaBienestar.objects.filter(
        estado='Publicada'
    ).select_related('ubicacion').order_by('fecha_inicio')

    # Obtener los filtros seleccionados
    municipio = request.GET.get('municipio', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    # Filtrar por municipio
    if municipio.isdigit():
        campanias_lista = campanias_lista.filter(
            ubicacion_id=int(municipio)
        )

    # Filtrar por tipo de campaña
    tipos_validos = [
        opcion[0] for opcion in CampaniaBienestar.TIPOS_CHOICES
    ]

    if tipo in tipos_validos:
        campanias_lista = campanias_lista.filter(tipo=tipo)

    ubicaciones = Ubicacion.objects.all().order_by('municipio')

    return render(request, 'campanias.html', {
        'campanias': campanias_lista,
        'ubicaciones': ubicaciones,
        'municipio_seleccionado': municipio,
        'tipo_seleccionado': tipo,
        'tipos': CampaniaBienestar.TIPOS_CHOICES,
    })


def detalle_campania(request, id):
    campania = get_object_or_404(
        CampaniaBienestar.objects.select_related('ubicacion'),
        id=id,
        estado='Publicada'
    )

    return render(request, 'detalle_campania.html', {
        'campania': campania
    })
    


# =========================
# ADMINISTRACIÓN DE CAMPAÑAS
# =========================

CampaniaBienestarForm = modelform_factory(
    CampaniaBienestar,
    fields=[
        'titulo',
        'tipo',
        'descripcion',
        'ubicacion',
        'direccion',
        'fecha_inicio',
        'fecha_fin',
        'hora_inicio',
        'hora_fin',
        'costo',
        'requisitos',
        'contacto',
        'imagen',
        'estado',
    ]
)


ReporteMascotaForm = modelform_factory(
    ReporteMascota,
    fields=[
        'tipo',
        'nombre_mascota',
        'especie',
        'raza',
        'descripcion',
        'ubicacion',
        'direccion',
        'fecha_reporte',
        'telefono',
        'correo',
        'imagen',
    ]
)

# El teléfono y el correo serán obligatorios.
ReporteMascotaForm.base_fields['telefono'].required = True
ReporteMascotaForm.base_fields['correo'].required = True

# Configuración del campo teléfono.
ReporteMascotaForm.base_fields['telefono'].widget.attrs.update({
    'type': 'tel',
    'inputmode': 'numeric',
    'maxlength': '10',
    'pattern': '[0-9]{10}',
    'placeholder': 'Ej. 7221234567',
})


@login_required
def gestionar_campania(request, id=None):

    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "No tienes permiso para gestionar campañas.")
        return redirect('inicio')

    if id:
        campania = get_object_or_404(CampaniaBienestar, id=id)
    else:
        campania = None

    if request.method == 'POST':
        form = CampaniaBienestarForm(
            request.POST,
            request.FILES,
            instance=campania
        )

        if form.is_valid():
            nueva_campania = form.save(commit=False)

            if nueva_campania.creada_por is None:
                nueva_campania.creada_por = request.user

            nueva_campania.save()

            messages.success(request, "La campaña se guardó correctamente.")
            return redirect('panel_admin')

    else:
        form = CampaniaBienestarForm(instance=campania)

    return render(request, 'gestionar_campania.html', {
        'form': form,
        'campania': campania,
    })


@login_required
def eliminar_campania(request, id):

    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "No tienes permiso para eliminar campañas.")
        return redirect('inicio')

    if request.method != 'POST':
        return redirect('panel_admin')

    campania = get_object_or_404(CampaniaBienestar, id=id)
    campania.delete()

    messages.success(request, "La campaña se eliminó correctamente.")
    return redirect('panel_admin')



# =========================
# REPORTAR MASCOTA PERDIDA O ENCONTRADA
# =========================

@login_required
def reportar_mascota(request):

    if request.user.role not in ('INTERESADO', 'RESPONSABLE'):
        messages.error(
            request,
            "Solo los usuarios interesados y responsables pueden registrar reportes."
        )
        return redirect('inicio')

    if request.method == 'POST':
        form = ReporteMascotaForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            reporte = form.save(commit=False)

            reporte.reportado_por = request.user
            reporte.estado = 'Pendiente'
            reporte.revisado_por = None

            reporte.save()

            messages.success(
                request,
                "Tu reporte se registró correctamente y está pendiente de revisión."
            )

            return redirect('inicio')

    else:
        form = ReporteMascotaForm()

    return render(request, 'reportar_mascota.html', {
        'form': form
    })


@login_required
def mis_reportes(request):

    reportes = ReporteMascota.objects.filter(
        reportado_por=request.user
    ).select_related(
        'ubicacion'
    ).order_by('-fecha_creacion')

    return render(request, 'mis_reportes.html', {
        'reportes': reportes
    })



def reportes_mascotas(request):

    reportes = ReporteMascota.objects.filter(
        estado='Aprobado'
    ).select_related(
        'ubicacion'
    ).order_by('-fecha_creacion')

    tipo = request.GET.get('tipo', '')
    municipio = request.GET.get('municipio', '')

    if tipo in ('Perdida', 'Encontrada'):
        reportes = reportes.filter(tipo=tipo)

    if municipio.isdigit():
        reportes = reportes.filter(
            ubicacion__id_ubicacion=int(municipio)
        )

    ubicaciones = Ubicacion.objects.all().order_by('municipio')

    return render(request, 'reportes_mascotas.html', {
        'reportes': reportes,
        'ubicaciones': ubicaciones,
        'tipo_seleccionado': tipo,
        'municipio_seleccionado': municipio,
    })


# =========================
# REGISTRO
# =========================

def registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirmacion = request.POST.get('confirm_password', '')
        role = request.POST.get('role', '')
        siguiente = url_segura(request, request.POST.get('next', ''))
        acepta_terminos = request.POST.get('acepta_terminos')

        try:
            if not all([nombre, apellido, username, email, password, role]):
                raise ValidationError("Todos los campos son obligatorios.")

            if role not in ('INTERESADO', 'RESPONSABLE'):
                raise ValidationError("El tipo de cuenta seleccionado no es válido.")

            if len(username) > 150:
                raise ValidationError("El nombre de usuario es demasiado largo.")

            validate_email(email)

            if Usuario.objects.filter(username__iexact=username).exists():
                raise ValidationError("El nombre de usuario ya existe.")

            if Usuario.objects.filter(email__iexact=email).exists():
                raise ValidationError("Este correo ya está registrado.")

            if password != confirmacion:
                raise ValidationError("Las contraseñas no coinciden.")
            
            if acepta_terminos != '1':
                raise ValidationError("Debes aceptar los términos y condiciones para registrarte.")

            usuario_temporal = Usuario(
                username=username,
                email=email,
                first_name=nombre,
                last_name=apellido
            )
            validate_password(password, user=usuario_temporal)

            nuevo_usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
                role=role,
                is_active=True
            )

            auth_login(request, nuevo_usuario)
            messages.success(request, f"¡Bienvenido a Huellitas EdoMex, {nombre}!")

            if siguiente:
                return redirect(siguiente)

            return redireccion_por_rol(nuevo_usuario)

        except ValidationError as error:
            messages.error(request, error.messages[0])

    return render(request, 'registro.html')


# =========================
# PUBLICAR MASCOTA
# =========================

@login_required
def publicar(request):
    if request.user.role != 'RESPONSABLE':
        messages.error(request, "Solo los responsables pueden publicar mascotas.")
        return redirect('inicio')

    ubicaciones = Ubicacion.objects.all().order_by('municipio')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        tipo_especie = request.POST.get('especie', '')
        sexo = request.POST.get('sexo', '')
        fecha_texto = request.POST.get('fecha_nacimiento_aproximada', '')
        id_ubicacion = request.POST.get('ubicacion', '')
        vacunado_texto = request.POST.get('vacunado', '')
        esterilizado_texto = request.POST.get('esterilizado', '')
        detalles = request.POST.get('detalles', '').strip()
        fotografia = request.FILES.get('fotografia')
        tamano = request.POST.get('tamano', '')
        nivel_actividad = request.POST.get('nivel_actividad', '')
        convive_ninos_texto = request.POST.get('convive_ninos', '')
        convive_mascotas_texto = request.POST.get('convive_mascotas', '')
        acepta_informacion = request.POST.get('acepta_informacion')
        acepta_terminos = request.POST.get('acepta_terminos')
        try:
            if len(detalles) > 2000:
                raise ValidationError("La descripción no debe superar los 2000 caracteres.")
            if not nombre or len(nombre) > 100:
                raise ValidationError("El nombre de la mascota es obligatorio y no debe superar 100 caracteres.")
            
            if acepta_informacion != '1':
                raise ValidationError("Debes confirmar que la información proporcionada es correcta.")

            if acepta_terminos != '1':
                raise ValidationError("Debes aceptar los términos y condiciones para publicar.")

            if tipo_especie not in ('perro', 'gato'):
                raise ValidationError("Selecciona una especie válida.")
            
            if tamano not in ('Pequeño', 'Mediano', 'Grande'):
                raise ValidationError("Selecciona un tamaño válido.")

            if nivel_actividad not in ('Bajo', 'Moderado', 'Alto'):
                raise ValidationError("Selecciona un nivel de actividad válido.")

            if convive_ninos_texto not in ('True', 'False'):
                raise ValidationError("Selecciona si la mascota puede convivir con niños.")

            if convive_mascotas_texto not in ('True', 'False'):
                raise ValidationError("Selecciona si la mascota puede convivir con otras mascotas.")

            if sexo not in ('Macho', 'Hembra'):
                raise ValidationError("Selecciona el sexo de la mascota.")

            try:
                fecha_nacimiento = date.fromisoformat(fecha_texto)
            except (ValueError, TypeError):
                raise ValidationError("La fecha de nacimiento no es válida.")

            if fecha_nacimiento > timezone.localdate():
                raise ValidationError("La fecha de nacimiento no puede ser futura.")

            if vacunado_texto not in ('True', 'False'):
                raise ValidationError("Selecciona si la mascota está vacunada.")

            if esterilizado_texto not in ('True', 'False'):
                raise ValidationError("Selecciona si la mascota está esterilizada.")

            try:
                ubicacion = Ubicacion.objects.get(
                    id_ubicacion=id_ubicacion
                )
            except (Ubicacion.DoesNotExist, ValueError, TypeError):
                raise ValidationError("Selecciona una ubicación válida.")

            try:
                especie = Especie.objects.get(
                    tipo_especie=tipo_especie
                )
            except Especie.DoesNotExist:
                raise ValidationError("La especie seleccionada no existe.")

            validar_fotografia(fotografia)

            edad = calcular_edad(fecha_nacimiento)

            with transaction.atomic():
                mascota = Mascota.objects.create(
                    nombre=nombre,
                    especie=especie,
                    responsable=request.user,
                    ubicacion=ubicacion,
                    sexo=sexo,
                    edad_aproximada=edad,
                    fecha_nacimiento_aproximada=fecha_nacimiento,
                    vacunado=(vacunado_texto == 'True'),
                    esterilizado=(esterilizado_texto == 'True'),
                    detalles=detalles,
                    tamano=tamano,
                    nivel_actividad=nivel_actividad,
                    convive_ninos=(convive_ninos_texto == 'True'),
                    convive_mascotas=(convive_mascotas_texto == 'True'),
                    estado_publicacion='Pendiente'
                )

                Fotografia.objects.create(
                    mascota=mascota,
                    url_imagen=fotografia
                )

                request.user.ultima_publicacion = mascota.fecha_publicacion
                request.user.save(update_fields=['ultima_publicacion'])

            messages.success(
                request,
                f"La mascota '{nombre}' fue registrada y está pendiente de moderación."
            )
            return redirect('panel_responsable')

        except ValidationError as error:
            messages.error(request, error.messages[0])
    return render(request, 'publicar.html', {
        'municipios': ubicaciones
    })


# =========================
# LOGIN Y LOGOUT
# =========================

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        usuarios = Usuario.objects.filter(email__iexact=email)

        if usuarios.count() != 1:
            messages.error(request, "Credenciales incorrectas o correo no registrado.")
            return render(request, 'login.html')

        usuario = usuarios.first()
        user = authenticate(
            request,
            username=usuario.username,
            password=password
        )

        if user is not None:
            auth_login(request, user)

            siguiente = url_segura(
                request,
                request.GET.get('next') or request.POST.get('next')
            )

            if siguiente:
                return redirect(siguiente)

            return redireccion_por_rol(user)

        messages.error(request, "Credenciales incorrectas o correo no registrado.")

    return render(request, 'login.html')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('inicio')


# =========================
# PANELES
# =========================

@login_required
def panel_responsable(request):
    if request.user.role != 'RESPONSABLE':
        return redirect('inicio')

    mascotas = Mascota.objects.filter(responsable=request.user)
    solicitudes = SolicitudAdopcion.objects.filter(
        mascota__responsable=request.user
    ).select_related('mascota', 'interesado')

    historial = SolicitudAdopcion.objects.filter(
        mascota__responsable=request.user,
        estado_solicitud='Aceptada'
    ).order_by('-fecha_solicitud')

    return render(request, 'panel_responsable.html', {
        'mascotas': mascotas,
        'solicitudes': solicitudes,
        'historial_adopciones': historial
    })


@login_required
def panel_interesado(request):
    if request.user.role != 'INTERESADO':
        return redirect('inicio')

    solicitudes = SolicitudAdopcion.objects.filter(
        interesado=request.user
    ).select_related('mascota')

    mis_mascotas = Mascota.objects.filter(
        responsable=request.user
    ).order_by('-fecha_publicacion')

    return render(request, 'panel_interesado.html', {
        'solicitudes': solicitudes,
        'mis_mascotas': mis_mascotas
    })



@login_required
def panel_admin(request):
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso exclusivo para administradores.")
        return redirect('inicio')

    fecha_limite = timezone.now() - timedelta(days=180)

    return render(request, 'panel_admin.html', {
        'todas_mascotas': Mascota.objects.all().order_by('-fecha_publicacion'),
        'todos_usuarios': Usuario.objects.exclude(role='ADMIN_SISTEMA'),
        'todas_solicitudes': SolicitudAdopcion.objects.all().order_by('-fecha_solicitud'),

        'todas_campanias': CampaniaBienestar.objects.all().order_by('-fecha_creacion'),

        'reportes_pendientes': ReporteMascota.objects.filter(
            estado='Pendiente'
        ).select_related(
            'ubicacion',
            'reportado_por'
        ).order_by('-fecha_creacion'),

        'todos_reportes': ReporteMascota.objects.all().select_related(
            'ubicacion',
            'reportado_por',
            'revisado_por'
        ).order_by('-fecha_creacion'),

        'usuarios_inactivos': Usuario.objects.filter(
            role='RESPONSABLE',
            ultima_publicacion__lt=fecha_limite
        ),

        'historial_adopciones': SolicitudAdopcion.objects.filter(
            estado_solicitud='Aceptada'
        ).order_by('-fecha_solicitud')
    })



# =========================
# ACCIONES DE SOLICITUD
# =========================

@login_required
@require_POST
def aceptar_solicitud(request, id):
    if request.user.role != 'RESPONSABLE':
        messages.error(request, "No tienes permiso para gestionar solicitudes.")
        return redirect('inicio')

    with transaction.atomic():
        solicitud = get_object_or_404(
            SolicitudAdopcion.objects.select_for_update().select_related('mascota'),
            id_solicitud=id,
            mascota__responsable=request.user
        )

        mascota = Mascota.objects.select_for_update().get(
            id_mascota=solicitud.mascota_id
        )

        if solicitud.estado_solicitud != 'Pendiente' or mascota.estado_publicacion != 'Disponible':
            messages.error(request, "La solicitud ya fue procesada o la mascota no está disponible.")
            return redirect('panel_responsable')

        solicitud.estado_solicitud = 'Aceptada'
        solicitud.fecha_adopcion = timezone.now()
        solicitud.save(update_fields=['estado_solicitud', 'fecha_adopcion'])

        mascota.estado_publicacion = 'Adoptada'
        mascota.save(update_fields=['estado_publicacion'])

        SolicitudAdopcion.objects.filter(
            mascota=mascota,
            estado_solicitud='Pendiente'
        ).exclude(
            id_solicitud=solicitud.id_solicitud
        ).update(estado_solicitud='Rechazada')

    messages.success(request, f"Se aceptó la solicitud para {mascota.nombre}.")
    return redirect('panel_responsable')


@login_required
@require_POST
def rechazar_solicitud(request, id):
    if request.user.role != 'RESPONSABLE':
        messages.error(request, "No tienes permiso para gestionar solicitudes.")
        return redirect('inicio')

    solicitud = get_object_or_404(
        SolicitudAdopcion,
        id_solicitud=id,
        mascota__responsable=request.user
    )

    if solicitud.estado_solicitud != 'Pendiente':
        messages.error(request, "Esta solicitud ya fue procesada.")
        return redirect('panel_responsable')

    solicitud.estado_solicitud = 'Rechazada'
    solicitud.save(update_fields=['estado_solicitud'])

    messages.warning(request, "Solicitud rechazada correctamente.")
    return redirect('panel_responsable')


@login_required
def detalle_solicitud(request, id):
    if request.user.role != 'RESPONSABLE':
        messages.error(request, "No tienes permiso para ver esta solicitud.")
        return redirect('inicio')

    solicitud = get_object_or_404(
        SolicitudAdopcion,
        id_solicitud=id,
        mascota__responsable=request.user
    )

    return render(request, 'detalle_solicitud.html', {
        'solicitud': solicitud
    })


@login_required
@require_POST
def cancelar_solicitud(request, id):
    solicitud = get_object_or_404(
        SolicitudAdopcion,
        id_solicitud=id,
        interesado=request.user
    )

    if solicitud.estado_solicitud == 'Pendiente':
        solicitud.delete()
        messages.success(request, "La solicitud fue cancelada correctamente.")
    else:
        messages.error(request, "No se puede cancelar una solicitud procesada.")

    return redirect('panel_interesado')


# =========================
# MODERACIÓN DE PUBLICACIONES
# =========================

@login_required
@require_POST
def aprobar_mascota(request, id):
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso denegado.")
        return redirect('inicio')

    mascota = get_object_or_404(Mascota, id_mascota=id)

    if mascota.estado_publicacion != 'Pendiente':
        messages.warning(request, "Esta publicación ya fue procesada.")
        return redirect('panel_admin')

    mascota.estado_publicacion = 'Disponible'
    mascota.save(update_fields=['estado_publicacion'])

    messages.success(request, f"La publicación de '{mascota.nombre}' fue aprobada.")
    return redirect('panel_admin')


@login_required
@require_POST
def rechazar_mascota(request, id):
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso denegado.")
        return redirect('inicio')

    mascota = get_object_or_404(Mascota, id_mascota=id)

    if mascota.estado_publicacion != 'Pendiente':
        messages.warning(request, "Esta publicación ya fue procesada.")
        return redirect('panel_admin')

    mascota.estado_publicacion = 'Rechazada'
    mascota.save(update_fields=['estado_publicacion'])

    messages.warning(request, f"La publicación de '{mascota.nombre}' fue rechazada.")
    return redirect('panel_admin')



# =========================
# MODERACIÓN DE REPORTES DE MASCOTAS
# =========================

@login_required
@require_POST
def aprobar_reporte_mascota(request, id):

    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "No tienes permiso para aprobar reportes.")
        return redirect('inicio')

    reporte = get_object_or_404(ReporteMascota, id=id)

    if reporte.estado != 'Pendiente':
        messages.warning(request, "Este reporte ya fue revisado.")
        return redirect('panel_admin')

    reporte.estado = 'Aprobado'
    reporte.revisado_por = request.user
    reporte.save(update_fields=['estado', 'revisado_por'])

    messages.success(request, "El reporte fue aprobado y ya puede mostrarse públicamente.")
    return redirect('panel_admin')


@login_required
@require_POST
def rechazar_reporte_mascota(request, id):

    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "No tienes permiso para rechazar reportes.")
        return redirect('inicio')

    reporte = get_object_or_404(ReporteMascota, id=id)

    if reporte.estado != 'Pendiente':
        messages.warning(request, "Este reporte ya fue revisado.")
        return redirect('panel_admin')

    reporte.estado = 'Rechazado'
    reporte.revisado_por = request.user
    reporte.save(update_fields=['estado', 'revisado_por'])

    messages.warning(request, "El reporte fue rechazado.")
    return redirect('panel_admin')


# =========================
# ADMINISTRACIÓN DE USUARIOS
# =========================

@login_required
@require_POST
def cambiar_estado_usuario(request, id):
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso denegado.")
        return redirect('inicio')

    usuario = get_object_or_404(
        Usuario.objects.exclude(role='ADMIN_SISTEMA'),
        id=id
    )

    if usuario == request.user:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
        return redirect('panel_admin')

    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])

    if usuario.is_active:
        messages.success(request, f"El usuario {usuario.username} fue activado.")
    else:
        messages.warning(request, f"El usuario {usuario.username} fue desactivado.")

    return redirect('panel_admin')


@login_required
@require_POST
def eliminar_usuario_inactivo(request, id):
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso denegado.")
        return redirect('inicio')

    usuario = get_object_or_404(
        Usuario,
        id=id,
        role='RESPONSABLE'
    )

    fecha_limite = timezone.now() - timedelta(days=180)

    if usuario.ultima_publicacion and usuario.ultima_publicacion < fecha_limite:
        nombre = f"{usuario.first_name} {usuario.last_name}"
        usuario.delete()
        messages.success(request, f"El usuario {nombre} fue eliminado por inactividad.")
    else:
        messages.warning(request, "Este usuario no cumple el periodo de inactividad.")

    return redirect('panel_admin')


# =========================
# ELIMINAR PUBLICACIÓN
# =========================

@login_required
@require_POST
def eliminar_publicacion(request, id_mascota):
    mascota = get_object_or_404(
        Mascota,
        id_mascota=id_mascota,
        responsable=request.user
    )

    for fotografia in mascota.fotos.all():
        if fotografia.url_imagen:
            fotografia.url_imagen.delete(save=False)

    mascota.delete()

    messages.success(request, "La publicación fue cancelada correctamente.")
    return redirect('panel_responsable')



def test_compatibilidad(request):

    if request.method == 'POST':

        especie_preferida = request.POST.get('especie')
        tamano_preferido = request.POST.get('tamano')
        tiempo_disponible = request.POST.get('actividad')
        tiene_ninos = request.POST.get('ninos')
        tiene_mascotas = request.POST.get('otras_mascotas')

        actividades = {
            'Poco tiempo': 'Bajo',
            'Tiempo moderado': 'Moderado',
            'Mucho tiempo': 'Alto',
        }

        actividad_preferida = actividades.get(tiempo_disponible)

        mascotas = Mascota.objects.filter(
            estado_publicacion='Disponible'
        ).select_related(
            'especie'
        ).prefetch_related(
            'fotos'
        )

        resultados = []

        for mascota in mascotas:

            puntos = 0
            puntos_posibles = 0
            coincidencias = []

            # ESPECIE: 25 puntos

            puntos_posibles += 25

            if (
                especie_preferida == 'Cualquiera'
                or mascota.especie.tipo_especie.lower() == especie_preferida.lower()
            ):
                puntos += 25
                coincidencias.append('Coincide con tu especie preferida')

            # TAMAÑO: 20 puntos

            if tamano_preferido == 'Cualquiera':
                puntos_posibles += 20
                puntos += 20
                coincidencias.append('Se adapta a tu preferencia de tamaño')

            elif mascota.tamano:
                puntos_posibles += 20

                if mascota.tamano == tamano_preferido:
                    puntos += 20
                    coincidencias.append('Coincide con el tamaño que prefieres')

            # ACTIVIDAD: 25 puntos

            if actividad_preferida and mascota.nivel_actividad:
                puntos_posibles += 25

                if mascota.nivel_actividad == actividad_preferida:
                    puntos += 25
                    coincidencias.append('Coincide con tu disponibilidad de tiempo')

            # CONVIVENCIA CON NIÑOS: 15 puntos

            puntos_posibles += 15

            if tiene_ninos == 'No' or mascota.convive_ninos:
                puntos += 15
                coincidencias.append('Es compatible con la convivencia indicada respecto a niños')

            # CONVIVENCIA CON OTRAS MASCOTAS: 15 puntos

            puntos_posibles += 15

            if tiene_mascotas == 'No' or mascota.convive_mascotas:
                puntos += 15
                coincidencias.append('Es compatible con la convivencia indicada respecto a otras mascotas')

            porcentaje = round((puntos / puntos_posibles) * 100)

            resultados.append({
                'mascota': mascota,
                'porcentaje': porcentaje,
                'coincidencias': coincidencias,
            })

        resultados.sort(
            key=lambda resultado: resultado['porcentaje'],
            reverse=True
        )

        return render(request, 'test_compatibilidad.html', {
            'resultados': resultados,
            'mostrar_resultados': True,
        })

    return render(request, 'test_compatibilidad.html')
