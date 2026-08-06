
import re
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Mascota, SolicitudAdopcion, Especie, Fotografia, Usuario, Ubicacion
from django.core.validators import validate_email
from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError

# =========================
# PÁGINAS GENERALES (FRONTEND)
# =========================

def inicio(request):
    mascotas_cercanas = Mascota.objects.filter(
        estado_publicacion='Disponible'
    ).prefetch_related('fotos').order_by('-fecha_publicacion')
    
    if request.user.is_authenticated and request.user.ubicacion:
        mascotas_usuario = Mascota.objects.filter(
            estado_publicacion='Disponible',
            ubicacion=request.user.ubicacion
        ).order_by('-fecha_publicacion')
        
        if mascotas_usuario.exists():
            mascotas_cercanas = mascotas_usuario

    ubicaciones = Ubicacion.objects.all().order_by('municipio')
    
    return render(request, 'inicio.html', {
        'mascotas': mascotas_cercanas,
        'ubicaciones': ubicaciones
    })

def adoptar(request):
    mascotas = Mascota.objects.filter(
        estado_publicacion='Disponible'
    ).prefetch_related('fotos').order_by('-fecha_publicacion')

    query_nombre = request.GET.get('nombre')
    query_especie = request.GET.get('especie')
    query_ubicacion = request.GET.get('ubicacion')

    if query_nombre:
        mascotas = mascotas.filter(nombre__icontains=query_nombre)
        
    if query_especie:
        mascotas = mascotas.filter(especie__tipo_especie=query_especie)
        
    if query_ubicacion:
        mascotas = mascotas.filter(ubicacion_id=query_ubicacion)

    ubicaciones = Ubicacion.objects.all().order_by('municipio')

    return render(request, 'adoptar.html', {
        'mascotas': mascotas,
        'ubicaciones': ubicaciones
    })

def detalle(request):
    id_mascota = request.GET.get('id')
    mascota_obj = get_object_or_404(Mascota, id_mascota=id_mascota)
    return render(request, 'detalle.html', {'mascota': mascota_obj})

def solicitud(request):
    if not request.user.is_authenticated or request.user.role not in ['RESPONSABLE', 'INTERESADO']:
        messages.error(request, "Debes estar registrado para enviar una solicitud de adopción.")
        return redirect('login')

    id_mascota = request.GET.get('mascota_id')
    mascota_obj = get_object_or_404(Mascota, id_mascota=id_mascota)

    if mascota_obj.responsable == request.user:
        messages.error(request, "No puedes enviar una solicitud de adopción para una mascota que tú mismo publicaste.")
        return redirect('detalle')

    if request.method == 'POST':
        telefono = request.POST.get('telefono')
        correo = request.POST.get('correo')
        vivienda = request.POST.get('vivienda')
        patio = request.POST.get('patio')
        otras_mascotas = request.POST.get('otras_mascotas')
        experiencia = request.POST.get('experiencia')
        mensaje = request.POST.get('mensaje','').strip()

        if not mensaje or len(mensaje) < 20:
            messages.error(request, "Por favor, escribe un mensaje más detallado (mínimo 20 caracteres) explicando por qué deseas adoptarlo.")
            return render(request, "solicitud.html", {'mascota': mascota_obj})

        palabras_restringidas = ['tonto', 'bobo', 'estupido', 'maltrato', 'perro feo', 'asco']
        mensaje_minusculas = mensaje.lower()

        for palabra in palabras_restringidas:
            if re.search(
                r'\b' + re.escape(palabra) + r'\b',
                mensaje_minusculas
            ):
                messages.error(request, "Tu mensaje contiene términos inapropiados u ofensivos. Por favor, redáctalo con respeto..")
                return render(request, "solicitud.html", {'mascota': mascota_obj})

        nueva_solicitud = SolicitudAdopcion.objects.create(
            mascota=mascota_obj,
            interesado=request.user,
            telefono=telefono,
            correo=correo,
            vivienda=vivienda,
            patio=patio,
            otras_mascotas=otras_mascotas,
            experiencia=experiencia,
            mensaje=mensaje,
            estado_solicitud='Pendiente'
        )
        nueva_solicitud.save()

        messages.success(request, f"¡Tu postulación para adoptar a {mascota_obj.nombre} fue enviada con éxito!")
        return redirect('panel_interesado')

    return render(request, "solicitud.html", {'mascota': mascota_obj})

def sobre(request):
    return render(request, "sobre.html")

def terminos(request):
    return render(request, "terminos.html")

def privacidad(request):
    return render(request, "privacidad.html")

# =========================
# REGISTRO DE USUARIOS
# =========================

def registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if not all([nombre, apellido, username, email, password, role]):
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, "registro.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "El correo electrónico ingresado no tiene un formato válido.")
            return render(request, "registro.html")

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
            return render(request, "registro.html")

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Este correo electrónico ya está registrado.")
            return render(request, "registro.html")

        # CORRECCIÓN: Se agrega is_active=True para que puedan loguearse al instante
        nuevo_usuario = Usuario.objects.create_user(
            username=username, email=email, password=password,
            first_name=nombre, last_name=apellido, role=role,
            is_active=True
        )
        nuevo_usuario.save()

        messages.success(request, f"¡Cuenta creada con éxito para {username}!")
        return redirect('login')

    return render(request, "registro.html")

# =========================
# PUBLICAR MASCOTA
# =========================

def publicar(request):
    if not request.user.is_authenticated or request.user.role not in ['RESPONSABLE', 'INTERESADO']:
        messages.error(request, "Debes iniciar sesión para poder publicar una mascota.")
        return redirect('inicio')

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo_especie = request.POST.get('especie')
        sexo = request.POST.get('sexo')

        fecha_nacimiento_aproximada = request.POST.get('fecha_nacimiento_aproximada')

        # Calcular automáticamente la edad
        fecha = date.fromisoformat(fecha_nacimiento_aproximada)
        hoy = date.today()

        diferencia = relativedelta(hoy, fecha)

        if diferencia.years > 0:
            if diferencia.years == 1:
                edad_aproximada = "1 año"
            else:
                edad_aproximada = f"{diferencia.years} años"
        else:
            if diferencia.months == 1:
                edad_aproximada = "1 mes"
            else:
                edad_aproximada = f"{diferencia.months} meses"

        vacunado = request.POST.get('vacunado') == 'True'
        esterilizado = request.POST.get('esterilizado') == 'True'
        detalles = request.POST.get('detalles', '').strip()
        foto_archivo = request.FILES.get('fotografia')

        especie_obj, _ = Especie.objects.get_or_create(tipo_especie=tipo_especie)

        id_ubicacion = request.POST.get('ubicacion')
        ubicacion_obj = Ubicacion.objects.get(id_ubicacion=id_ubicacion)

        nueva_mascota = Mascota.objects.create(
            nombre=nombre,
            especie=especie_obj,
            responsable=request.user,
            ubicacion=ubicacion_obj,
            sexo=sexo,
            edad_aproximada=edad_aproximada,
            fecha_nacimiento_aproximada=fecha_nacimiento_aproximada,
            vacunado=vacunado,
            esterilizado=esterilizado,
            detalles=detalles,
            estado_publicacion='Pendiente'
        )

        request.user.ultima_publicacion = nueva_mascota.fecha_publicacion
        request.user.save()

        if foto_archivo:
            Fotografia.objects.create(
                mascota=nueva_mascota,
                url_imagen=foto_archivo
            )

        messages.success(
            request,
            f"¡La mascota '{nombre}' ha sido registrada con éxito y está pendiente de moderación!"
        )
        return redirect('panel_responsable')

    ubicaciones = Ubicacion.objects.all().order_by('municipio')

    return render(request, "publicar.html", {
        'municipios': ubicaciones
    })
# =========================
# LOGIN Y LOGOUT POR ROL
# =========================

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            usuario_obj = Usuario.objects.get(email=email)
            username = usuario_obj.username
        except Usuario.DoesNotExist:
            username = None

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            if user.role == 'ADMIN_SISTEMA':
                return redirect('panel_admin')
            elif user.role == 'RESPONSABLE':
                return redirect('panel_responsable')
            elif user.role == 'INTERESADO':
                return redirect('panel_interesado')
            else:
                return redirect('inicio')
        else:
            messages.error(request, "Credenciales incorrectas o correo no registrado. Inténtalo de nuevo.")

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('inicio')

# =========================
# PANELES DE CONTROL
# =========================

@login_required
def panel_responsable(request):
    if request.user.role != 'RESPONSABLE':
        return redirect('inicio')

    mascotas = Mascota.objects.filter(responsable=request.user)

    solicitudes = SolicitudAdopcion.objects.filter(
        mascota__responsable=request.user
    )

    historial_adopciones = SolicitudAdopcion.objects.filter(
        mascota__responsable=request.user,
        estado_solicitud='Aceptada'
    ).order_by('-fecha_solicitud')

    return render(request, 'panel_responsable.html', {
        'mascotas': mascotas,
        'solicitudes': solicitudes,
        'historial_adopciones': historial_adopciones
    })

@login_required
def panel_interesado(request):
    if request.user.role != 'INTERESADO':
        return redirect('inicio')
    
    solicitudes = SolicitudAdopcion.objects.filter(interesado=request.user)
    mis_mascotas = Mascota.objects.filter(responsable=request.user).order_by('-fecha_publicacion')
    
    return render(request, 'panel_interesado.html', {
        'solicitudes': solicitudes,
        'mis_mascotas': mis_mascotas
    })

@login_required
def panel_admin(request):
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso exclusivo para administradores.")
        return redirect('inicio')
    
    todas_mascotas = Mascota.objects.all().order_by('-fecha_publicacion')
    todos_usuarios = Usuario.objects.all().exclude(role='ADMIN_SISTEMA')
    todas_solicitudes = SolicitudAdopcion.objects.all().order_by('-fecha_solicitud')

    historial_adopciones = SolicitudAdopcion.objects.filter(
        estado_solicitud='Aceptada'
    ).order_by('-fecha_solicitud')
    
    # Fecha límite: usuarios con más de 180 días sin publicar
    fecha_limite = timezone.now() - timedelta(days=180)
    usuarios_inactivos = Usuario.objects.filter(
        role='RESPONSABLE',
        ultima_publicacion__lt=fecha_limite
    )
    return render(request, 'panel_admin.html', {
    'todas_mascotas': todas_mascotas,
    'todos_usuarios': todos_usuarios,
    'todas_solicitudes': todas_solicitudes,
    'usuarios_inactivos': usuarios_inactivos,
    'historial_adopciones': historial_adopciones
    })

# =========================
# ACCIONES DE SOLICITUD
# =========================

@login_required
def aceptar_solicitud(request, id):
    solicitud_obj = get_object_or_404(SolicitudAdopcion, id_solicitud=id)
    
    if solicitud_obj.mascota.responsable != request.user:
        messages.error(request, "No tienes permiso para gestionar esta solicitud.")
        return redirect('inicio')

    solicitud_obj.estado_solicitud = 'Aceptada'
    solicitud_obj.fecha_adopcion = timezone.now()
    solicitud_obj.save()

    mascota = solicitud_obj.mascota
    mascota.estado_publicacion = 'Adoptada'
    mascota.save()
    
    SolicitudAdopcion.objects.filter(mascota=mascota, estado_solicitud='Pendiente').update(estado_solicitud='Rechazada')

    messages.success(request, f"¡Has aceptado la solicitud de adopción para {mascota.nombre}!")
    return redirect('panel_responsable')

@login_required
def rechazar_solicitud(request, id):
    solicitud_obj = get_object_or_404(SolicitudAdopcion, id_solicitud=id)
    
    if solicitud_obj.mascota.responsable != request.user:
        messages.error(request, "No tienes permiso para gestionar esta solicitud.")
        return redirect('inicio')

    solicitud_obj.estado_solicitud = 'Rechazada'
    solicitud_obj.save()

    messages.warning(request, "Solicitud rechazada correctamente.")
    return redirect('panel_responsable')

@login_required
def detalle_solicitud(request, id):

    solicitud = get_object_or_404(
        SolicitudAdopcion,
        id_solicitud=id
    )

    # Solo el responsable de esa mascota puede verla
    if solicitud.mascota.responsable != request.user:
        messages.error(request, "No tienes permiso para ver esta solicitud.")
        return redirect('inicio')

    return render(request, 'detalle_solicitud.html', {
        'solicitud': solicitud
    })

@login_required
def cancelar_solicitud(request, id):
    solicitud_obj = get_object_or_404(SolicitudAdopcion, id_solicitud=id, interesado=request.user)
    
    if solicitud_obj.estado_solicitud == 'Pendiente':
        solicitud_obj.delete()
        messages.success(request, "La solicitud de adopción ha sido cancelada correctamente.")
    else:
        messages.error(request, "No se puede cancelar una solicitud que ya ha sido procesada.")
        
    return redirect('panel_interesado')

@login_required
def aprobar_mascota(request, id):
    
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso denegado.")
        return redirect('inicio')
        
    mascota = get_object_or_404(Mascota, id_mascota=id)
    mascota.estado_publicacion = 'Disponible'
    mascota.save()
    
    messages.success(request, f"La publicación de '{mascota.nombre}' ha sido aprobada correctamente.")
    return redirect('panel_admin')
@login_required
def rechazar_mascota(request, id):
    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso denegado.")
        return redirect('inicio')

    mascota = get_object_or_404(Mascota, id_mascota=id)

    mascota.estado_publicacion = 'Rechazada'
    mascota.save()

    messages.warning(
        request,
        f"La publicación de '{mascota.nombre}' fue rechazada."
    )

    return redirect('panel_admin')

@login_required
def eliminar_usuario_inactivo(request, id):

    if request.user.role != 'ADMIN_SISTEMA':
        messages.error(request, "Acceso denegado.")
        return redirect('inicio')

    usuario = get_object_or_404(
        Usuario,
        id=id,
        role='RESPONSABLE'
    )

    # Seguridad: solo eliminar si lleva más de 180 días sin publicar
    fecha_limite = timezone.now() - timedelta(days=180)

    if usuario.ultima_publicacion and usuario.ultima_publicacion < fecha_limite:

        nombre = f"{usuario.first_name} {usuario.last_name}"

        usuario.delete()

        messages.success(
            request,
            f"El usuario {nombre} fue eliminado por inactividad."
        )

    else:

        messages.warning(
            request,
            "Este usuario no cumple el periodo de inactividad."
        )

    return redirect('panel_admin')

@login_required
def eliminar_publicacion(request, id_mascota):

    mascota = get_object_or_404(
        Mascota,
        id_mascota=id_mascota,
        responsable=request.user
    )

    if request.method == "POST":

        # Eliminar también las fotografías
        mascota.fotos.all().delete()

        mascota.delete()

        messages.success(
            request,
            "La publicación fue cancelada correctamente."
        )

    return redirect("panel_responsable")