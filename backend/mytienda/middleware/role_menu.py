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
                    ("Reportes", "/reportes/"),
                ]
            else:
                request.menu_items = [
                    ("Home", "/"),
                    ("Inventario", "/inventario/productos/"),
                    ("Ventas", "/ventas/"),
                    ("Compras", "/compras/"),
                    ("Proveedores", "/inventario/proveedores/"),
                ]

        return self.get_response(request)
