import {useEffect, useState} from 'react'  //importo funcion para guardar elemntos
import {getAllTasks} from '../api/Tienda.api'
import {TaskCard} from './TaskCard'

export function List() {

    const [tasks,setTasks] = useState([]);// los corchetes indican que inicia como arreglo vacio


useEffect(() => {    //apenas arracnque la pagina quiero que muestre

//console.log('pagina loaded') nos sirve para mostrar en la consola de la web
    async function loadTasks(){
        const res = await getAllTasks ();// recivo la respuesta del backend
        setTasks(res.data); //me permite guardar la tarea solicitada
    }
    loadTasks();
},[]);
    
    
    //List ya tiene la posibilidad de revisar todas las tareas
    
return (
  <div>
    {tasks.map(task => (
      <TaskCard key= {task.id}task={task}/>
    ))}
  </div>
);
}
