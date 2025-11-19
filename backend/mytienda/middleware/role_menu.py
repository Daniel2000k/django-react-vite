from django.shortcuts import redirect

class RoleMenuMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.menu_items = []

        if request.user.is_authenticated:
            if request.user.rol == "ADMIN":
                request.menu_items = [
                    ("Home", "/home/"),
                    ("Usuarios", "/usuarios/"),
                    ("Inventario", "/inventario/"),
                    ("Ventas", "/ventas/"),
                    ("Compras", "/compras/"),
                    ("Reportes", "/reportes/"),
                ]
            else:
                request.menu_items = [
                    ("Ventas", "/ventas/"),
                    ("Mis Ventas", "/ventas/mis-ventas/"),
                ]

        return self.get_response(request)
