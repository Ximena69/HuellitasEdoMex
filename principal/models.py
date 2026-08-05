from django.db import models

from django.contrib.auth.models import AbstractUser



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