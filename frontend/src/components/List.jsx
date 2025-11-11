//`useState` → para guardar los productos en una variable dentro del componente.  
//useEffect` → para ejecutar una acción *automáticamente* cuando el componente se carga (como “al iniciar”).


import {useEffect, useState} from 'react'  //importo funcion para guardar elemntos
import {getAllTasks} from '../api/Tienda.api'
import {TaskCard} from './TaskCard'

export function List() {

    const [tasks,setTasks] = useState([]);// los corchetes indican que inicia como arreglo vacio


useEffect(() => {    //apenas arracnque la pagina quiero que muestre

//console.log('pagina loaded') nos sirve para mostrar en la consola de la web
    async function loadTasks(){
        const res = await getAllTasks ();// recibo la respuesta del backend
        setTasks(res.data); //me permite guardar la tarea solicitada
    }
    loadTasks();
},[]);
    
    
    //El useEffect se ejecuta solo una vez (por eso [] al final).
    //Llama a la función loadTasks() que hace lo siguiente:
    //Espera la respuesta del backend (await getAllTasks()),
    //Guarda los datos recibidos en tasks usando setTasks(res.data).
    
return (
  <div>
    {tasks.map(task => (
      <TaskCard key= {task.id}task={task}/>
    ))}
  </div>
  //TaskCard` es como una “tarjeta” que muestra los datos individuales (nombre, precio, etc.).
  //getAllTasks() pide los prodctos al backend
  //map muestras los taskcards por cada producto

);
}
