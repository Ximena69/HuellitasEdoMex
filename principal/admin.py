from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Ubicacion, Usuario, Especie, Mascota, Fotografia, SolicitudAdopcion

# 1. Personalizar la visualización de los Usuarios en el Admin
@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'fecha_registro')
    list_filter = ('role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Información de Rol y Ubicación', {'fields': ('role', 'ubicacion')}),
    )

# 2. Configurar la visualización de las Mascotas (con las correcciones de la minuta)
@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especie', 'responsable', 'sexo', 'estado_publicacion', 'fecha_publicacion')
    list_filter = ('estado_publicacion', 'especie', 'sexo')
    search_fields = ('nombre', 'responsable__username')

# 3. Registrar el resto de las tablas de control del sistema
admin.site.register(Ubicacion)
admin.site.register(Especie)
admin.site.register(Fotografia)
admin.site.register(SolicitudAdopcion)