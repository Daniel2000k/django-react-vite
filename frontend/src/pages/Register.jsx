export function Register() {
  return (
    <div className="container">
      <h2>Crear cuenta</h2>
      <form>
        <input type="text" placeholder="Nombre de usuario" />
        <input type="email" placeholder="Correo electrónico" />
        <input type="password" placeholder="Contraseña" />
        <button type="submit">Registrarse</button>
      </form>
    </div>
  );
}
