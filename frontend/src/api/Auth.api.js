/**
 * Ejemplo de integración con React/Vite
 * Conexión a los endpoints de autenticación
 */

// ==================== CONFIGURACIÓN BASE ====================
const API_BASE_URL = 'http://localhost:8000/accounts/api';

// ==================== FUNCIONES DE AUTENTICACIÓN ====================

/**
 * Registrar un nuevo usuario
 */
export const registerUser = async (email, username, password) => {
    try {
        const response = await fetch(`${API_BASE_URL}/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                username,
                password
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.email || error.username || error.password || 'Error en registro');
        }

        return await response.json();
    } catch (error) {
        console.error('Error en registro:', error);
        throw error;
    }
};

/**
 * Login de usuario
 */
export const loginUser = async (email, password) => {
    try {
        const response = await fetch(`${API_BASE_URL}/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        if (!response.ok) {
            throw new Error('Credenciales inválidas');
        }

        const data = await response.json();
        
        // Guardar tokens en localStorage
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        return data;
    } catch (error) {
        console.error('Error en login:', error);
        throw error;
    }
};

/**
 * Obtener información del usuario actual
 */
export const getCurrentUser = async (token) => {
    try {
        const response = await fetch(`${API_BASE_URL}/user/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error('No autorizado');
        }

        return await response.json();
    } catch (error) {
        console.error('Error al obtener usuario:', error);
        throw error;
    }
};

/**
 * Logout (eliminar tokens locales)
 */
export const logoutUser = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
};

/**
 * Verificar si el usuario está autenticado
 */
export const isAuthenticated = () => {
    return !!localStorage.getItem('access_token');
};

/**
 * Obtener el token de acceso
 */
export const getAccessToken = () => {
    return localStorage.getItem('access_token');
};

// ==================== EJEMPLO DE USO EN REACT ====================

/*
import { registerUser, loginUser, logoutUser, isAuthenticated } from './api/auth';

// Componente de Registro
function RegisterPage() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleRegister = async (e) => {
        e.preventDefault();
        try {
            await registerUser(email, username, password);
            // Redirigir a home o login
            window.location.href = '/accounts/home/';
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <form onSubmit={handleRegister}>
            {error && <p style={{color: 'red'}}>{error}</p>}
            <input 
                type="email" 
                placeholder="Email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
            />
            <input 
                type="text" 
                placeholder="Usuario" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
            />
            <input 
                type="password" 
                placeholder="Contraseña" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            <button type="submit">Registrarse</button>
        </form>
    );
}

// Componente de Login
function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            await loginUser(email, password);
            window.location.href = '/accounts/home/';
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <form onSubmit={handleLogin}>
            {error && <p style={{color: 'red'}}>{error}</p>}
            <input 
                type="email" 
                placeholder="Email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
            />
            <input 
                type="password" 
                placeholder="Contraseña" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            <button type="submit">Iniciar Sesión</button>
        </form>
    );
}

// Componente protegido
function ProtectedRoute() {
    if (!isAuthenticated()) {
        return <Navigate to="/accounts/login/" />;
    }
    return <YourComponent />;
}
*/
