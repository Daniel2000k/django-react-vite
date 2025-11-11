import {useNavigate} from 'react-router-dom'

export function TaskCard({task}){

  const navigate = useNavigate()
    return (
      <div style= {{background: "black"}}
        
        onClick={( ) => {
          navigate(`/tasks/${task.id}`)
        }}
      >
        
        <h2>{task.nombre}</h2>
        <p>Código: {task.codigo}</p>
        <p>{task.descripcion}</p>
        <p>Precio compra: {task.precio_compra}</p>
        <p>Precio venta: {task.precio_venta}</p>
        <p>Stock: {task.stock}</p>
        <hr/>
      </div>
    );
}




//useNavigate es un hook de la libreríareact-router-dom 
//Sirve para cambiar de página usando JavaScript, sin necesidad de
//  que el usuario haga clic en un enlace tradicional.