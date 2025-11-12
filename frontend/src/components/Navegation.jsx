import { Link } from "react-router-dom";

export function Navigation() {
  return (
    <nav>
      <ul>
        <li><Link to="/tasks">Tareas</Link></li>
        <li><Link to="/tasks-create">Crear Tarea</Link></li>
        <li><Link to="/login">Login</Link></li>
        <li><Link to="/register">Register</Link></li>
      </ul>
    </nav>
  );
}
