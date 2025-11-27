from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test # Se añade user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal

# Importación de la función de chequeo de Admin
from accounts.views import es_admin 

from inventario.models import Producto, Proveedor, Inventario
from .models import Compra, DetalleCompra


# ==================== API PARA AUTOCOMPLETADO ====================

# No requiere restricción de rol, ya que asume que el usuario ya está logueado para usar el formulario de compra
def api_productos(request): 
    """API para obtener productos con búsqueda"""
    query = request.GET.get('q', '').lower()
    
    # Solo productos activos (no mostrar los eliminados/desactivados)
    productos = Producto.objects.filter(activo=True)
    
    if query:
        productos = productos.filter(nombre__icontains=query) | productos.filter(codigo__icontains=query)
    
    productos = productos[:20]  # Limitar a 20 resultados
    
    data = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'codigo': p.codigo,
            'precio_compra': str(p.precio_compra),
            'precio_venta': str(p.precio_venta),
            'stock': p.stock
        }
        for p in productos
    ]
    
    return JsonResponse(data, safe=False)


# ==================== LISTA DE COMPRAS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def compra_lista(request):
    """Mostrar todas las compras registradas"""
    compras = Compra.objects.all().order_by('-id')
    return render(request, 'compras/compra_lista.html', {'compras': compras})


# ==================== CREAR COMPRA ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def compra_crear(request):
    """Crear nueva compra con múltiples productos"""
    proveedores = Proveedor.objects.all()
    productos = Producto.objects.filter(activo=True)

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor')
        
        if not proveedor_id:
            messages.error(request, "Debes seleccionar un proveedor.")
            return redirect('compra_crear')

        items = []
        total_compra = Decimal("0")

        # Obtener listas de datos
        producto_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')
        precios = request.POST.getlist('precio_unitario[]')

        # Procesar cada producto. Soportamos líneas sin producto_id: se puede enviar
        # paralelo `producto_codigo[]` y `producto_nombre[]` para crear/reusar por código.
        producto_codigos = request.POST.getlist('producto_codigo[]')
        producto_nombres = request.POST.getlist('producto_nombre[]')

        for idx, (prod_id, cantidad_str, precio_str) in enumerate(zip(producto_ids, cantidades, precios)):
            try:
                cantidad_str = cantidad_str.strip()
                precio_str = precio_str.strip()

                if not cantidad_str or not precio_str:
                    continue

                producto = None

                # Intentar resolver por ID si viene
                if prod_id and str(prod_id).strip():
                    try:
                        producto = Producto.objects.get(id=int(prod_id))
                    except (Producto.DoesNotExist, ValueError):
                        producto = None

                # Si no se resolvió por id, intentar por código enviado en el mismo índice
                if not producto:
                    codigo = ''
                    nombre = ''
                    try:
                        codigo = producto_codigos[idx].strip()
                    except Exception:
                        codigo = ''
                    try:
                        nombre = producto_nombres[idx].strip()
                    except Exception:
                        nombre = ''

                    if codigo:
                        try:
                            producto = Producto.objects.filter(codigo=int(codigo)).first()
                        except ValueError:
                            producto = None

                        # Crear producto mínimo si no existe (esta vista es admin-only)
                        if not producto:
                            try:
                                producto = Producto.objects.create(
                                    codigo=int(codigo),
                                    nombre=(nombre or f"Producto {codigo}"),
                                    precio_compra=Decimal(precio_str),
                                    precio_venta=Decimal(precio_str),
                                    stock=0,
                                    activo=True
                                )
                            except Exception:
                                producto = None

                # Si aún no hay producto, ignorar esta línea
                if not producto:
                    continue

                cantidad = int(cantidad_str)
                precio = Decimal(precio_str)

                # Si la cantidad es cero o negativa, ignorar la línea (no es válida para crear)
                if cantidad <= 0:
                    continue

                if precio < 0:
                    messages.error(request, f"El precio debe ser válido para {producto.nombre}.")
                    return redirect('compra_crear')

                subtotal = cantidad * precio
                items.append((producto, cantidad, precio, subtotal))
                total_compra += subtotal

            except (ValueError, IndexError):
                # Ignorar si hay un error en un producto, pero podríamos ser más estrictos
                continue

        if not items:
            messages.error(request, "Debes agregar al menos un producto.")
            return redirect('compra_crear')

        # Crear compra
        compra = Compra.objects.create(
            proveedor_id=proveedor_id,
            total=total_compra
        )

        # Crear detalles y movimientos de inventario
        for producto, cantidad, precio_unitario, subtotal in items:
            # Detalle de compra
            DetalleCompra.objects.create(
                compra=compra,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )

            # Movimiento de inventario (ENTRADA)
            Inventario.objects.create(
                producto=producto,
                tipo="ENTRADA",
                cantidad=cantidad,
                numero_referencia=f"COMPRA-{compra.id}-{producto.id}"
            )
            
            # Nota: El stock del producto se actualiza mediante un signal o un método 
            # en el modelo Inventario al crearse el movimiento.

        messages.success(request, f"Compra #{compra.id} registrada correctamente. Total: ${compra.total}")
        return redirect('compra_detalle', compra_id=compra.id)

    return render(request, 'compras/compra_form.html', {
        'proveedores': proveedores,
        'productos': productos
    })


# ==================== DETALLE DE COMPRA ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def compra_detalle(request, compra_id):
    """Ver detalles de una compra específica"""
    compra = get_object_or_404(Compra, id=compra_id)
    return render(request, 'compras/compra_detalle.html', {'compra': compra})