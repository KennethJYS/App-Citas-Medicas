from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import logging

# Importaciones de tu base de datos y seguridad
from app.database.database import get_db_connection
from passlib.context import CryptContext

# --- CONFIGURACIÓN ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SanaYa API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Seguridad (Bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- MODELOS ---
class RegisterRequest(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    rol: str 
    especialidad: Optional[str] = None
    licencia: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

# --- ENDPOINTS ---

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: RegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Hashear la contraseña
        hashed_password = pwd_context.hash(user.password)

        # 2. Insertar Usuario
        query_usuario = """
            INSERT INTO Usuarios (Nombre, Apellido, Email, Password_Hash, Rol, Fecha_Registro)
            OUTPUT INSERTED.ID_Usuario
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_usuario, (
            user.nombre, user.apellido, user.email, 
            hashed_password, user.rol, datetime.now()
        ))
        new_user_id = cursor.fetchone()[0]

        # 3. Insertar en tabla de Rol
        if user.rol.lower() == 'medico':
            cursor.execute("INSERT INTO Medicos (ID_Medico, Especialidad, Licencia_Medica) VALUES (?, ?, ?)", 
                           (new_user_id, user.especialidad, user.licencia))
        else:
            cursor.execute("INSERT INTO Pacientes (ID_Paciente) VALUES (?)", (new_user_id,))

        conn.commit()
        return {"message": "Usuario creado correctamente", "id": new_user_id}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error al registrar usuario")
    finally:
        conn.close()

@app.post("/login")
async def login(data: LoginRequest):
    logger.info(f"Intento de login para: {data.email}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscamos el usuario por el campo Email
        cursor.execute("SELECT ID_Usuario, Nombre, Password_Hash, Rol FROM Usuarios WHERE Email = ?", (data.email,))
        user = cursor.fetchone()

        # Si no existe el usuario
        if not user:
            logger.warning("Usuario no encontrado en la DB")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        # user[2] es el Password_Hash almacenado en SQL Server
        if not pwd_context.verify(data.password, user[2]):
            logger.warning("La contraseña no coincide con el Hash")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        return {
            "message": "Login exitoso",
            "user": {
                "id": user[0],
                "nombre": user[1],
                "rol": user[3]
            }
        }
    except Exception as e:
        logger.error(f"Error interno: {e}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()