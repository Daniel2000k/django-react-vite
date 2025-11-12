export function Login() {
  return (
    <div className="container">
      <h2>Iniciar sesión</h2>
      <form>
        <input type="email" placeholder="Correo electrónico" />
        <input type="password" placeholder="Contraseña" />
        <button type="submit">Entrar</button>
      </form>
    </div>
  );
}
