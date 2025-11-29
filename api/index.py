import sys
import os

# ruta absoluta del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# agrega backend al sys.path
BACKEND_PATH = os.path.join(BASE_DIR, "backend")
if BACKEND_PATH not in sys.path:
    sys.path.append(BACKEND_PATH)

# ahora sí importa Django
from mytienda.asgi import application as app
