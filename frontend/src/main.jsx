import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css"; // Importa el CSS principal con Tailwind
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
