import { BrowserRouter, Routes, Route,Navigate } from "react-router-dom";
import {Page1} from "./pages/Page1";  // Importación correcta
import {Pageform} from  "./pages/Pageform";
import {Navigation} from './components/Navegation';


function App() {
  return (
    <BrowserRouter>
      <Navigation/>


      <Routes>
        <Route path="/" element={<Navigate to ="/tasks"/>} />  
        <Route path="/tasks" element={<Page1 />} /> 
        <Route path="/tasks-create" element={<Pageform />} /> 
        <Route path="/tasks/:id" element={<Pageform />} /> 
      </Routes>
    </BrowserRouter>
  );
}

export default App;
//id valor dinamico de cualquier tarea