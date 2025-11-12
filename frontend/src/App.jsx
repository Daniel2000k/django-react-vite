import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Page1 } from "./pages/Page1";
import { Pageform } from "./pages/Pageform";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Navigation } from "./components/Navegation";
import { Toaster } from "react-hot-toast";

function App() {
  return (
    <BrowserRouter>
      <Navigation />

      <Routes>
        {/* Redirección por defecto */}
        <Route path="/" element={<Navigate to="/tasks" />} />

        {/* Rutas de tareas */}
        <Route path="/tasks" element={<Page1 />} />
        <Route path="/tasks-create" element={<Pageform />} />
        <Route path="/tasks/:id" element={<Pageform />} />

        {/* Rutas de autenticación */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Si el usuario entra a una ruta que no existe */}
        <Route path="*" element={<h2>404 - Página no encontrada</h2>} />
      </Routes>

      <Toaster />
    </BrowserRouter>
  );
}

export default App;
