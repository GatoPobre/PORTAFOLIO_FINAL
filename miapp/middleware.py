from django.utils.functional import SimpleLazyObject


class ProfileAndGroupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Guardamos una referencia al objeto perezoso original de Django.
        original_lazy_user = request.user

        def get_optimized_user():
            """
            Esta función se ejecutará la primera vez que se acceda a request.user.
            Usa el objeto perezoso original para obtener el usuario real sin causar recursión.
            """
            # 2. Resolvemos el usuario real (User o AnonymousUser) usando el mecanismo de Django.
            user = original_lazy_user

            # 3. Si el usuario está autenticado, devolvemos la versión optimizada.
            if user.is_authenticated:
                return user.__class__.objects.select_related('perfil').prefetch_related('groups').get(pk=user.pk)
            return user

        # 4. Reemplazamos request.user con nuestro nuevo objeto perezoso optimizado.
        request.user = SimpleLazyObject(get_optimized_user)
        response = self.get_response(request)
        return response
