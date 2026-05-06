import axios from 'axios';

// 10.0.2.2 es para el emulador. Si usas dispositivo físico, usa tu IP local (ej. 192.168.1.x)
const API_URL = 'http://10.0.2.2:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authService = {
  login: async (email, password) => {
    try {
      // Enviamos un objeto JSON { email, password }
      const response = await api.post('/login', { email, password });
      return response.data; 
    } catch (error) {
      // Extraemos el mensaje de error de FastAPI o usamos uno genérico
      const errorMsg = error.response?.data?.detail || 'Error de conexión';
      console.error('Login Error:', errorMsg);
      throw errorMsg; 
    }
  },

  register: async (userData) => {
    try {
      const response = await api.post('/register', userData);
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Error en el registro';
      throw errorMsg;
    }
  },
};

export default authService;