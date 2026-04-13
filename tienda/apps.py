from django.apps import AppConfig


class TiendaConfig(AppConfig):
    name = 'tienda'

    def ready(self):
        # Importar y registrar las señales de la aplicación
        import tienda.signals
