import hashlib
from urllib.parse import urlencode

def get_gravatar(email, size=200):
    """Return Gravatar URL from an email."""
    if not email:
        return None  # evita error si el email es None

    # Normaliza el email
    normalized_email = email.strip().lower()

    # Genera el hash MD5 del correo
    email_hash = hashlib.md5(normalized_email.encode('utf-8')).hexdigest()

    # Construye la URL completa
    params = urlencode({'d': 'retro', 's': str(size)})
    gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?{params}"

    return gravatar_url
