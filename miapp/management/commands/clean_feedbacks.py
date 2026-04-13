from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from modulo_feedback.models import Feedback


class Command(BaseCommand):
    help = 'Limpia automáticamente los reportes de feedback con más de 30 días de antigüedad.'

    def add_arguments(self, parser):
        # Parámetro opcional para permitir configurar los días desde la terminal
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Cantidad de días de antigüedad para eliminar los reportes (por defecto: 30).'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        # Calculamos la fecha límite restando los días a la fecha/hora actual
        fecha_limite = timezone.now() - timedelta(days=dias)

        # Buscamos los feedbacks que fueron creados antes de la fecha límite
        feedbacks_a_borrar = Feedback.objects.filter(
            fecha_creacion__lt=fecha_limite)
        cantidad = feedbacks_a_borrar.count()

        if cantidad == 0:
            self.stdout.write(self.style.WARNING(
                f'>_ [SYS] No hay reportes de feedback más antiguos que {dias} días para purgar.'))
            return

        # Recorremos y borramos uno por uno.
        # NOTA: No usamos feedbacks_a_borrar.delete() directo porque iterar y borrar
        # uno por uno asegura que se disparen las señales (signals) de Django y que
        # la librería 'django-cleanup' borre efectivamente los archivos físicos .jpeg.
        for feedback in feedbacks_a_borrar:
            feedback.delete()

        self.stdout.write(self.style.SUCCESS(
            f'>_ [SYS] PURGA COMPLETADA: Se eliminaron {cantidad} reportes antiguos y sus capturas.'))
