from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from tienda.models import Producto


class StaticViewSitemap(Sitemap):
    """Sitemap para las páginas estáticas principales del sitio."""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # Nombres de las URLs definidas en tu urls.py
        return ['miapp:inicio', 'miapp:contacto', 'tienda:tienda']

    def location(self, item):
        return reverse(item)


class ProductoSitemap(Sitemap):
    """Sitemap dinámico para los productos disponibles en la tienda."""
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        # Solo indexamos en Google los productos que tengan stock
        return Producto.objects.filter(stock__gt=0)

    def lastmod(self, obj):
        return obj.fecha_creacion

    def location(self, obj):
        return reverse('tienda:producto_detalle', args=[obj.id])
