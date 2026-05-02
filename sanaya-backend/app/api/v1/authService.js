import axios from 'axios';

// 10.0.2.2 es la forma en que el emulador de Android se comunica con tu PC local
const API_URL = 'http://10.0.2.2:8000';

export const loginUser = async (email, password) => {
    try {
        const response = await axios.post(`${API_URL}/login`, { 
            email: email.toLowerCase(), // Normalizamos el correo
            password: password 
        });
        return response.data;
    } catch (error) {
        // Capturamos el mensaje de error exacto de FastAPI (ej. "Credenciales incorrectas")
        throw error.response?.data?.detail || "Error al conectar con el servidor de SanaYa";
    }
};