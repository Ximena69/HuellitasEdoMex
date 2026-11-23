
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from principal.models import ReporteMascota

Usuario = get_user_model()


class PruebasPermisos(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.interesado = Usuario.objects.create_user(
            username='interesado_prueba',
            email='interesado@prueba.com',
            password='Prueba123*',
            role='INTERESADO'
        )

        cls.responsable = Usuario.objects.create_user(
            username='responsable_prueba',
            email='responsable@prueba.com',
            password='Prueba123*',
            role='RESPONSABLE'
        )

        cls.admin = Usuario.objects.create_user(
            username='admin_prueba',
            email='admin@prueba.com',
            password='Prueba123*',
            role='ADMIN_SISTEMA'
        )

    def test_usuario_sin_sesion_no_accede_a_paneles(self):
        rutas = [
            'panel_responsable',
            'panel_interesado',
            'panel_admin',
        ]

        for ruta in rutas:
            respuesta = self.client.get(reverse(ruta))
            self.assertEqual(respuesta.status_code, 302)

    def test_interesado_no_puede_publicar(self):
        self.client.force_login(self.interesado)

        respuesta = self.client.get(reverse('publicar'))

        self.assertRedirects(respuesta, reverse('inicio'))
    
    def test_responsable_no_puede_entrar_al_panel_admin(self):
        self.client.force_login(self.responsable)

        respuesta = self.client.get(reverse('panel_admin'))

        self.assertRedirects(respuesta, reverse('inicio'))

    def test_interesado_no_puede_entrar_al_panel_responsable(self):
        self.client.force_login(self.interesado)

        respuesta = self.client.get(reverse('panel_responsable'))

        self.assertRedirects(respuesta, reverse('inicio'))

    def test_registro_no_permite_rol_administrador(self):
        cantidad_anterior = Usuario.objects.count()

        respuesta = self.client.post(
            reverse('registro'),
            {
                'nombre': 'Usuario',
                'apellido': 'Prueba',
                'username': 'intento_admin',
                'email': 'intento@prueba.com',
                'password': 'Prueba123*',
                'confirm_password': 'Prueba123*',
                'role': 'ADMIN_SISTEMA',
                'acepta_terminos': '1',
            }
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), cantidad_anterior)
        self.assertFalse(
            Usuario.objects.filter(username='intento_admin').exists()
        )

    def test_acciones_protegidas_no_aceptan_get(self):
        self.client.force_login(self.admin)

        rutas = [
            ('logout', []),
            ('aprobar_mascota', [999999]),
            ('rechazar_mascota', [999999]),
            ('cambiar_estado_usuario', [999999]),
            ('eliminar_usuario_inactivo', [999999]),
            ('eliminar_publicacion', [999999]),
        ]

        for ruta, argumentos in rutas:
            respuesta = self.client.get(
                reverse(ruta, args=argumentos)
            )

            self.assertEqual(
                respuesta.status_code,
                405,
                msg=f'La ruta {ruta} está permitiendo solicitudes GET.'
            )


class PruebasReportesMascotas(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.interesado = Usuario.objects.create_user(
            username='interesado_reportes',
            email='interesado_reportes@prueba.com',
            password='Prueba123*',
            role='INTERESADO'
        )

        cls.responsable = Usuario.objects.create_user(
            username='responsable_reportes',
            email='responsable_reportes@prueba.com',
            password='Prueba123*',
            role='RESPONSABLE'
        )

        cls.admin = Usuario.objects.create_user(
            username='admin_reportes',
            email='admin_reportes@prueba.com',
            password='Prueba123*',
            role='ADMIN_SISTEMA'
        )

    def crear_reporte(self, usuario, estado='Pendiente', nombre='Firulais'):
        return ReporteMascota.objects.create(
            tipo='Perdida',
            nombre_mascota=nombre,
            especie='Perro',
            raza='Labrador',
            descripcion='Perro de prueba color café.',
            direccion='Centro del municipio',
            fecha_reporte='2026-11-20',
            contacto='7221234567',
            estado=estado,
            reportado_por=usuario
        )

    def test_interesado_puede_registrar_reporte(self):
        self.client.force_login(self.interesado)

        respuesta = self.client.get(reverse('reportar_mascota'))

        self.assertEqual(respuesta.status_code, 200)

    def test_responsable_puede_registrar_reporte(self):
        self.client.force_login(self.responsable)

        respuesta = self.client.get(reverse('reportar_mascota'))

        self.assertEqual(respuesta.status_code, 200)

    def test_administrador_no_puede_registrar_reporte(self):
        self.client.force_login(self.admin)

        respuesta = self.client.get(reverse('reportar_mascota'))

        self.assertRedirects(respuesta, reverse('inicio'))

    def test_reporte_nuevo_se_guarda_como_pendiente(self):
        self.client.force_login(self.interesado)

        respuesta = self.client.post(
            reverse('reportar_mascota'),
            {
                'tipo': 'Perdida',
                'nombre_mascota': 'Luna',
                'especie': 'Perro',
                'raza': 'Criolla',
                'descripcion': 'Perrita de prueba.',
                'direccion': 'Centro',
                'fecha_reporte': '2026-11-20',
                'telefono': '7221234567',
                'correo': 'prueba@ejemplo.com',
                'estado': 'Aprobado',
                'reportado_por': self.admin.id,
                'revisado_por': self.admin.id,
            }
        )
        self.assertRedirects(respuesta, reverse('inicio'))

        reporte = ReporteMascota.objects.get(nombre_mascota='Luna')

        self.assertEqual(reporte.estado, 'Pendiente')
        self.assertEqual(reporte.reportado_por, self.interesado)
        self.assertIsNone(reporte.revisado_por)

    def test_catalogo_publico_solo_muestra_reportes_aprobados(self):
        self.crear_reporte(
            self.interesado,
            estado='Pendiente',
            nombre='PendientePrueba'
        )

        self.crear_reporte(
            self.interesado,
            estado='Rechazado',
            nombre='RechazadoPrueba'
        )

        self.crear_reporte(
            self.interesado,
            estado='Aprobado',
            nombre='AprobadoPrueba'
        )

        respuesta = self.client.get(reverse('reportes_mascotas'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'AprobadoPrueba')
        self.assertNotContains(respuesta, 'PendientePrueba')
        self.assertNotContains(respuesta, 'RechazadoPrueba')

    def test_usuario_solo_consulta_sus_reportes(self):
        self.crear_reporte(
            self.interesado,
            nombre='ReportePropio'
        )

        self.crear_reporte(
            self.responsable,
            nombre='ReporteAjeno'
        )

        self.client.force_login(self.interesado)

        respuesta = self.client.get(reverse('mis_reportes'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'ReportePropio')
        self.assertNotContains(respuesta, 'ReporteAjeno')

    def test_solo_administrador_puede_aprobar_o_rechazar(self):
        reporte = self.crear_reporte(self.interesado)

        self.client.force_login(self.responsable)

        respuesta_aprobar = self.client.post(
            reverse('aprobar_reporte_mascota', args=[reporte.id])
        )

        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, 'Pendiente')

        respuesta_rechazar = self.client.post(
            reverse('rechazar_reporte_mascota', args=[reporte.id])
        )

        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, 'Pendiente')

        self.assertRedirects(respuesta_aprobar, reverse('inicio'))
        self.assertRedirects(respuesta_rechazar, reverse('inicio'))

    def test_administrador_puede_aprobar_y_rechazar(self):
        reporte_aprobar = self.crear_reporte(
            self.interesado,
            nombre='AprobarPrueba'
        )

        reporte_rechazar = self.crear_reporte(
            self.interesado,
            nombre='RechazarPrueba'
        )

        self.client.force_login(self.admin)

        respuesta_aprobar = self.client.post(
            reverse('aprobar_reporte_mascota', args=[reporte_aprobar.id])
        )

        respuesta_rechazar = self.client.post(
            reverse('rechazar_reporte_mascota', args=[reporte_rechazar.id])
        )

        reporte_aprobar.refresh_from_db()
        reporte_rechazar.refresh_from_db()

        self.assertEqual(reporte_aprobar.estado, 'Aprobado')
        self.assertEqual(reporte_aprobar.revisado_por, self.admin)

        self.assertEqual(reporte_rechazar.estado, 'Rechazado')
        self.assertEqual(reporte_rechazar.revisado_por, self.admin)

        self.assertRedirects(respuesta_aprobar, reverse('panel_admin'))
        self.assertRedirects(respuesta_rechazar, reverse('panel_admin'))
