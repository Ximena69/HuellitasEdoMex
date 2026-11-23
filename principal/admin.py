
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Ubicacion,
    Usuario,
    Especie,
    Mascota,
    Fotografia,
    SolicitudAdopcion,
    CampaniaBienestar,
    ReporteMascota
)


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_staff',
        'fecha_registro'
    )

    list_filter = ('role', 'is_staff')

    fieldsets = UserAdmin.fieldsets + (
        ('Información de Rol y Ubicación', {
            'fields': ('role', 'ubicacion')
        }),
    )


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'especie',
        'responsable',
        'sexo',
        'estado_publicacion',
        'fecha_publicacion'
    )

    list_filter = ('estado_publicacion', 'especie', 'sexo')

    search_fields = ('nombre', 'responsable__username')


@admin.register(CampaniaBienestar)
class CampaniaBienestarAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'tipo',
        'ubicacion',
        'fecha_inicio',
        'estado'
    )

    list_filter = ('tipo', 'estado', 'ubicacion')

    search_fields = (
        'titulo',
        'descripcion',
        'ubicacion__municipio'
    )

    date_hierarchy = 'fecha_inicio'

    readonly_fields = ('fecha_creacion',)

    def save_model(self, request, obj, form, change):

        if not obj.creada_por_id:
            obj.creada_por = request.user

        super().save_model(request, obj, form, change)


admin.site.register(Ubicacion)
admin.site.register(Especie)
admin.site.register(Fotografia)
admin.site.register(SolicitudAdopcion)

@admin.register(ReporteMascota)
class ReporteMascotaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'tipo',
        'nombre_mascota',
        'especie',
        'ubicacion',
        'estado',
        'reportado_por',
        'fecha_creacion'
    )

    list_filter = (
        'tipo',
        'estado',
        'ubicacion'
    )

    search_fields = (
        'nombre_mascota',
        'especie',
        'raza',
        'descripcion',
        'reportado_por__username'
    )

    readonly_fields = (
        'fecha_creacion',
    )

