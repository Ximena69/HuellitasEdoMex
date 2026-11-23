from django.db import models

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


# 1. ENTIDAD UBICACIÓN

class Ubicacion(models.Model):

    id_ubicacion = models.AutoField(primary_key=True)

    municipio = models.CharField(max_length=100, verbose_name="Municipio")



    def __str__(self):

        return self.municipio



    class Meta:

        verbose_name_plural = "Ubicaciones"





# 2. MODELO DE USUARIO PERSONALIZADO

class Usuario(AbstractUser):

    ROLES_CHOICES = [

        ('ADMIN_SISTEMA', 'Administrador del Sistema'),

        ('RESPONSABLE', 'Responsable (Publicador)'),

        ('INTERESADO', 'Interesado (Adoptante)'),

    ]

    

    first_name = models.CharField(max_length=150, verbose_name="Nombre")

    last_name = models.CharField(max_length=150, verbose_name="Apellido")

    role = models.CharField(max_length=20, choices=ROLES_CHOICES, default='INTERESADO', verbose_name="Rol en el Sistema")

    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    ultima_publicacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Última publicación"
    )

    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ubicación")



    def __str__(self):

        return f"{self.username} ({self.get_role_display()})"





# 3. ENTIDAD ESPECIE

class Especie(models.Model):

    id_especie = models.AutoField(primary_key=True)

    tipo_especie = models.CharField(max_length=20, choices=[('perro', 'Perro'), ('gato', 'Gato')], verbose_name="Tipo de Especie")



    def __str__(self):

        return self.tipo_especie





# 4. ENTIDAD MASCOTA (Con Moderación Previa)

class Mascota(models.Model):

    SEXO_CHOICES = [

        ('Macho', 'Macho'),

        ('Hembra', 'Hembra'),

    ]

    ESTADO_CHOICES = [

        ('Pendiente', 'Pendiente de Aprobación'),

        ('Disponible', 'Disponible'),
        
        ('Rechazada', 'Rechazada'),

        ('Adoptada', 'Adoptada'),
        
        ('Cancelada', 'Cancelada por el responsable'),

    ]

    

    id_mascota = models.AutoField(primary_key=True)

    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Mascota")

    especie = models.ForeignKey(Especie, on_delete=models.CASCADE, verbose_name="Especie")

    responsable = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name="Responsable")
    
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Municipio")
    

    esterilizado = models.BooleanField(default=False, verbose_name="¿Esterilizado?")

    vacunado = models.BooleanField(default=False, verbose_name="¿Vacunado?")

    

    fecha_nacimiento_aproximada = models.DateField(null=True, blank=True, verbose_name="Fecha Nacimiento Aproximada")

    edad_aproximada = models.CharField(max_length=50, verbose_name="Edad Aproximada")

    

    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES, verbose_name="Sexo")

    fecha_publicacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Publicación")

    # Atributo unificado: por defecto al registrarse nace oculta como 'Pendiente'

    estado_publicacion = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente', verbose_name="Estado de Publicación")

    # Dentro de tu clase Mascota añade:

    detalles = models.TextField(blank=True, null=True)
    
    TAMANO_CHOICES = [
        ('Pequeño', 'Pequeño'),
        ('Mediano', 'Mediano'),
        ('Grande', 'Grande'),
    ]

    ACTIVIDAD_CHOICES = [
        ('Bajo', 'Bajo'),
        ('Moderado', 'Moderado'),
        ('Alto', 'Alto'),
    ]

    tamano = models.CharField(
        max_length=10,
        choices=TAMANO_CHOICES,
        null=True,
        blank=True,
        verbose_name="Tamaño de la mascota"
    )

    nivel_actividad = models.CharField(
        max_length=10,
        choices=ACTIVIDAD_CHOICES,
        null=True,
        blank=True,
        verbose_name="Nivel de actividad"
    )

    convive_ninos = models.BooleanField(
        default=False,
        verbose_name="¿Puede convivir con niños?"
    )

    convive_mascotas = models.BooleanField(
        default=False,
        verbose_name="¿Puede convivir con otras mascotas?"
    )



    def __str__(self):

        return f"{self.nombre} ({self.especie.tipo_especie})"





# 5. ENTIDAD FOTOGRAFIA

class Fotografia(models.Model):

    id_fotografia = models.AutoField(primary_key=True)

    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name="fotos", verbose_name="Mascota")

    url_imagen = models.ImageField(upload_to='mascotas/', verbose_name="Imagen de la Mascota")





# 6. ENTIDAD SOLICITUD DE ADOPCION

class SolicitudAdopcion(models.Model):

    ESTADO_SOLICITUD = [

        ('Pendiente', 'Pendiente'),

        ('Aceptada', 'Aceptada'),

        ('Rechazada', 'Rechazada'),

    ]


    id_solicitud = models.AutoField(primary_key=True)


    interesado = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="mis_solicitudes",
        verbose_name="Interesado"
    )


    mascota = models.ForeignKey(
        Mascota,
        on_delete=models.CASCADE,
        verbose_name="Mascota"
    )


    # NUEVOS DATOS DEL ADOPTANTE

    telefono = models.CharField(
        max_length=15,
        verbose_name="Teléfono de contacto",
        null=True,
        blank=True
    )


    correo = models.EmailField(
        verbose_name="Correo electrónico",
        null=True,
        blank=True
    )


    # INFORMACIÓN DEL HOGAR

    vivienda = models.CharField(
        max_length=50,
        verbose_name="Tipo de vivienda",
        null=True,
        blank=True
    )

    patio = models.CharField(
        max_length=10,
        verbose_name="Cuenta con patio",
        null=True,
        blank=True
    )


    otras_mascotas = models.CharField(
        max_length=10,
        verbose_name="Tiene otras mascotas",
        null=True,
        blank=True
    )


    experiencia = models.TextField(
        verbose_name="Experiencia con mascotas",
        null=True,
        blank=True
    )


    # MOTIVO

    mensaje = models.TextField(
        verbose_name="Motivo de adopción"
    )


    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de la Solicitud"
    )
    
    fecha_adopcion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de la Adopción"
    )


    estado_solicitud = models.CharField(
        max_length=20,
        choices=ESTADO_SOLICITUD,
        default='Pendiente',
        verbose_name="Estado de Solicitud"
    )


    def __str__(self):

        return f"Solicitud de {self.interesado.username} por {self.mascota.nombre}"

    

    class Meta:

        verbose_name_plural = "Solicitudes de Adopción"



# ==========================================
# 7. CAMPAÑAS DE BIENESTAR ANIMAL
# ==========================================

class CampaniaBienestar(models.Model):

    TIPOS_CHOICES = [
        ('Esterilizacion', 'Esterilización'),
        ('Vacunacion', 'Vacunación'),
        ('Desparasitacion', 'Desparasitación'),
        ('Consulta', 'Consulta veterinaria'),
        ('Adopcion', 'Jornada de adopción'),
        ('Otro', 'Otro'),
    ]

    ESTADOS_CHOICES = [
        ('Borrador', 'Borrador'),
        ('Publicada', 'Publicada'),
        ('Cancelada', 'Cancelada'),
    ]

    titulo = models.CharField(
        max_length=150,
        verbose_name="Nombre de la campaña"
    )

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS_CHOICES,
        verbose_name="Tipo de campaña"
    )

    descripcion = models.TextField(
        verbose_name="Descripción"
    )

    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campanias",
        verbose_name="Municipio"
    )

    direccion = models.CharField(
        max_length=250,
        verbose_name="Dirección"
    )

    fecha_inicio = models.DateField(
        verbose_name="Fecha de inicio"
    )

    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de finalización"
    )

    hora_inicio = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora de inicio"
    )

    hora_fin = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora de finalización"
    )

    costo = models.CharField(
        max_length=100,
        default="Gratuita",
        verbose_name="Costo"
    )

    requisitos = models.TextField(
        blank=True,
        verbose_name="Requisitos"
    )

    contacto = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Información de contacto"
    )

    imagen = models.ImageField(
        upload_to='campanias/',
        null=True,
        blank=True,
        verbose_name="Imagen o cartel"
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS_CHOICES,
        default='Borrador',
        verbose_name="Estado"
    )

    creada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Administrador que registró la campaña"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Campaña de bienestar animal"
        verbose_name_plural = "Campañas de bienestar animal"
        ordering = ['fecha_inicio']
        

class ReporteMascota(models.Model):

    TIPOS_REPORTE = [
        ('Perdida', 'Mascota perdida'),
        ('Encontrada', 'Mascota encontrada'),
    ]

    ESTADOS_REPORTE = [
        ('Pendiente', 'Pendiente de revisión'),
        ('Aprobado', 'Aprobado'),
        ('Rechazado', 'Rechazado'),
        ('Cerrado', 'Caso cerrado'),
    ]

    tipo = models.CharField(
        max_length=15,
        choices=TIPOS_REPORTE,
        verbose_name="Tipo de reporte"
    )

    nombre_mascota = models.CharField(
        max_length=100,
        verbose_name="Nombre de la mascota",
        blank=True
    )

    ESPECIES = [
    ('Perro', 'Perro'),
    ('Gato', 'Gato'),
    ]

    especie = models.CharField(
        max_length=10,
        choices=ESPECIES,
        verbose_name="Especie"
    )

    raza = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Raza"
    )

    descripcion = models.TextField(
        verbose_name="Descripción de la mascota"
    )

    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes_mascotas",
        verbose_name="Municipio"
    )

    direccion = models.CharField(
        max_length=250,
        verbose_name="Lugar donde se perdió o encontró"
    )

    fecha_reporte = models.DateField(
        verbose_name="Fecha en que se perdió o encontró"
    )

    contacto = models.CharField(
        max_length=150,
        verbose_name="Información de contacto"
    )

    telefono = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message="El teléfono debe contener exactamente 10 números."
            )
        ],
        blank=True,
        verbose_name="Teléfono de contacto"
    )

    correo = models.EmailField(
        blank=True,
        verbose_name="Correo electrónico de contacto"
    )
    
    imagen = models.ImageField(
        upload_to='reportes_mascotas/',
        null=True,
        blank=True,
        verbose_name="Fotografía de la mascota"
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS_REPORTE,
        default='Pendiente',
        verbose_name="Estado del reporte"
    )

    reportado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reportes_mascotas",
        verbose_name="Usuario que realizó el reporte"
    )

    revisado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes_revisados",
        verbose_name="Administrador que revisó el reporte"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.especie}"

    class Meta:
        verbose_name = "Reporte de mascota"
        verbose_name_plural = "Reportes de mascotas"
        ordering = ['-fecha_creacion']

