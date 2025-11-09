export function TaskCard({task}){
    return (
      <div>
        <h2>{task.nombre}</h2>
        <p>Código: {task.codigo}</p>
        <p>{task.descripcion}</p>
        <p>Precio compra: {task.precio_compra}</p>
        <p>Precio venta: {task.precio_venta}</p>
        <p>Stock: {task.stock}</p>
        <hr/>
      </div>
    )
}