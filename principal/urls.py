from django.urls import path
from . import views

urlpatterns = [

    path('', views.inicio, name='inicio'),

    path('adoptar/', views.adoptar, name='adoptar'),
    path('test-compatibilidad/', views.test_compatibilidad, name='test_compatibilidad'),
    path('detalle/', views.detalle, name='detalle'),
    
    path("solicitud/", views.solicitud, name="solicitud"),
    
    path("publicar/", views.publicar, name="publicar"),
    
    path("registro/", views.registro, name="registro"),
    
    path("login/", views.login, name="login"),
    path("sobre/", views.sobre, name="sobre"),
    path('campanias/', views.campanias, name='campanias'),
    path('campania/<int:id>/', views.detalle_campania, name='detalle_campania'),

    path("panel/campanias/nueva/", views.gestionar_campania, name="crear_campania"),
    path("panel/campanias/<int:id>/editar/", views.gestionar_campania, name="editar_campania"),
    path("panel/campanias/<int:id>/eliminar/", views.eliminar_campania, name="eliminar_campania"),

    path("terminos/", views.terminos, name="terminos"),
    path("privacidad/", views.privacidad, name="privacidad"),
    path('panel/responsable/', views.panel_responsable, name='panel_responsable'),
    path("logout/", views.logout_view, name="logout"),
    path('solicitud/aceptar/<int:id>/', views.aceptar_solicitud, name='aceptar_solicitud'),
    path('solicitud/rechazar/<int:id>/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('solicitud/detalle/<int:id>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('panel/interesado/', views.panel_interesado, name='panel_interesado'),
    path('panel/admin-panel/', views.panel_admin, name='panel_admin'),
    path('panel/admin-panel/cambiar-estado-usuario/<int:id>/',views.cambiar_estado_usuario,name='cambiar_estado_usuario'),
    path('solicitud/cancelar/<int:id>/', views.cancelar_solicitud, name='cancelar_solicitud'),
    path('panel/admin-panel/aprobar/<int:id>/', views.aprobar_mascota, name='aprobar_mascota'),
    path('panel/admin-panel/rechazar/<int:id>/',views.rechazar_mascota,name='rechazar_mascota'),
    path('panel/admin-panel/eliminar-usuario/<int:id>/', views.eliminar_usuario_inactivo, name='eliminar_usuario_inactivo'),
    path("eliminar_publicacion/<int:id_mascota>/",views.eliminar_publicacion,name="eliminar_publicacion"),
    # REPORTES DE MASCOTAS PERDIDAS Y ENCONTRADAS
    path('reportes-mascotas/', views.reportes_mascotas, name='reportes_mascotas'),
    path('reportes-mascotas/nuevo/', views.reportar_mascota, name='reportar_mascota'),
    path('mis-reportes/', views.mis_reportes, name='mis_reportes'),
    path('panel/reportes-mascotas/<int:id>/aprobar/', views.aprobar_reporte_mascota, name='aprobar_reporte_mascota'),
    path('panel/reportes-mascotas/<int:id>/rechazar/', views.rechazar_reporte_mascota, name='rechazar_reporte_mascota'),

]