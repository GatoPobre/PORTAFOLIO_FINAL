def extras_carro(request):
    """
    Context processor para inyectar la cantidad total de productos en el carrito
    en todas las plantillas del sitio, manteniendo el contador sincronizado al navegar.
    """
    carro = request.session.get('carro', {})
    # Sumamos la cantidad de cada ítem en el diccionario del carrito
    cantidad_carrito = sum(item.get('cantidad', 0) for item in carro.values())
    return {'cantidad_carrito': cantidad_carrito}
