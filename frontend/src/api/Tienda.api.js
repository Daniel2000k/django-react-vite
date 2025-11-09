import axios from 'axios';
//podemos crear una instancia para evitar escribir la misma direccion
axios,create({
    baseURL: 'http://localhost'
})


export const getAllTasks = () => { // cuando se ejecute la funcion digo que ejecute axios
    return axios.get('http://127.0.0.1:8000/api/Productos/') 
//peticion del backend de donde pedimos  informacion

}


export const createTask = (task) =>{
    return axios.post('http://127.0.0.1:8000/api/Productos/') 
}