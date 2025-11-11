import axios from 'axios';

// ✅ Creamos una instancia de axios con la URL base del backend en Render
const api = axios.create({
  baseURL: import.meta.env.MODE = 'http://127.0.0.1:8000/api/'
  //'https://django-react-vite.onrender.com/api/'
  // 👈 tu backend en Render
});

// ✅ Función para obtener todos los productos
  export const getAllTasks = () =>  api.get('Productos/');  // Axios añade automáticamente la baseURL



// ✅ Función para crear un nuevo producto (post)
  export const createTask = (task) => api.post('Productos/', task);  // enviamos los datos al backend

  export const deleteTask = (id) => api.delete(`Productos/${id}/`)


