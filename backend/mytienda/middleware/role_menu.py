from django.shortcuts import redirect

class RoleMenuMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.menu_items = []

        if request.user.is_authenticated:
            if request.user.rol == "ADMIN":
                request.menu_items = [
                    ("Home", "/"),
                    ("Usuarios", "/usuarios/"),
                    ("Inventario", "/inventario/productos/"),
                    ("Ventas", "/ventas/"),
                    ("Compras", "/compras/"),
                    ("Proveedores", "/inventario/proveedores/"),
                    ("Devoluciones", "/devoluciones/"),
                    ("Reportes", "/reportes/"),
                ]
            elif request.user.rol == "CAJERO":
                # Cajero: menú minimalista — acceso a ventas y a sus ventas (mis ventas)
                request.menu_items = [
                    ("Venta", "/ventas/crear/"),
                    ("Mis Ventas", "/ventas/mis-ventas/"),
                ]
            else:
                # Otros roles por defecto: menú reducido similar al administrador pero sin usuarios
                request.menu_items = [
                    ("Home", "/"),
                    ("Inventario", "/inventario/productos/"),
                    ("Ventas", "/ventas/"),
                    ("Compras", "/compras/"),
                    ("Proveedores", "/inventario/proveedores/"),
                    ("Devoluciones", "/devoluciones/"),
                ]

        return self.get_response(request)
