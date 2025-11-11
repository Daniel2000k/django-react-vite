import { useForm } from "react-hook-form";
import { createTask,deleteTask } from "../api/Tienda.api";// añade tareas a la pagina(post)
import {useNavigate,useParams} from 'react-router-dom' //redirecciona de la pagina de los registro a donde quedan registrados
//use params extrae los parametros que tengo en la url
export function Pageform() {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm();

    const navigate = useNavigate();
    const params= useParams()
    console.log(params) //ver params en consola




    const onSubmit = handleSubmit(async (data) => {
        
        console.log("Datos enviados:", data);
        await createTask(data);// apenas terminde de crear la tarea navegar a 
        navigate("/tasks");// me redirecciona a esta direccion
    });
    //debo eliminar descripcion y acomodarlo en los models
    return (
    <div>
      <form onSubmit={onSubmit}>
        <input
          type="number"
          placeholder="Código"
          {...register("codigo", { required: true })}
        />
        {errors.codigo && <span>El código es obligatorio</span>}

        <input
          type="text"
          placeholder="Nombre"
          {...register("nombre", { required: true })}
        />
        {errors.nombre && <span>El nombre es obligatorio</span>}                                
        <textarea
          rows="3"
          placeholder="Descripción"
          {...register("descripcion")}
        ></textarea>

        <input
          type="number"
          step="0.001"
          placeholder="Precio de compra"
          {...register("precio_compra", { required: true })}
        />
        {errors.precio_compra && <span>El precio de compra es obligatorio</span>}

        <input
          type="number"
          step="0.001"
          placeholder="Precio de venta"
          {...register("precio_venta", { required: true })}
        />
        {errors.precio_venta && <span>El precio de venta es obligatorio</span>}

        <input
          type="number"
          placeholder="Stock"
          {...register("stock", { required: true })}
        />
        {errors.stock && <span>El stock es obligatorio</span>}

        <button>Guardar</button>
      </form>


        {params.id && <button onClick={async() =>{
            const accepted= window.confirm('¿Estas seguro?')
            if (accepted) {
                await deleteTask(params.id);
                navigate("/tasks");

            }
        }}>Borrar</button>} 
    
    </div>
  );
}
//si params.id existe mostrar el boton borrar