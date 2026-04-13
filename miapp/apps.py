from django.apps import AppConfig


class TuAplicacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'miapp'  # Este es el nombre de tu app

    def ready(self):
        # Importamos las señales cuando la aplicación se inicia
        import miapp.signals
