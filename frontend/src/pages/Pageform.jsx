import {useForm} from 'react-hook-form' 
//podemos utilizar estas dos bilbiotecas para añadir mas validaciones
//yup, zod 

export function Pageform() {
    const {register, handleSubmit,  formState: {
        errors
    } } = useForm(); 

    const onSubmit = handleSubmit(data => {
        console.log(data)
    })
    return (
        <div>
            <form onSubmit={onSubmit}>
                <input 
                type="text"
                placeholder="title"
                {...register("title",{ required :true})}
                />
                {errors.title && <span> este campo es requerido</span>}
                <textarea rows="3" 
                placeholder="Description">
                </textarea>
                {errors.title && <span> este campo es requerido</span>}
                <button>Save</button>
            </form>
        </div> 
    );
}
