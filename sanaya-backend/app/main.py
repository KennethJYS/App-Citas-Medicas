from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging

# Importación ajustada para ejecución como módulo: python -m uvicorn app.main:app
from app.database.database import get_db_connection
from passlib.context import CryptContext

# Configuración de Logs para ver errores reales en la terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SanaYa API - Netrunners Team")

# Configuración de Seguridad (Hashing de contraseñas)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- MODELOS DE DATOS (SCHEMAS) ---

class RegisterRequest(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    rol: str  # 'Paciente' o 'Medico'
    # Campos opcionales para Médico
    especialidad: Optional[str] = None
    licencia: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {"status": "online", "message": "Bienvenido a la API de SanaYa", "team": "Netrunners"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: RegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Verificar si el email ya existe para evitar errores 500
        cursor.execute("SELECT ID_Usuario FROM Usuarios WHERE Email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

        # 2. Hashear la contraseña (Seguridad LOPDP)
        hashed_password = pwd_context.hash(user.password)

        # 3. Insertar en tabla Usuarios y obtener el ID generado
        # Usamos OUTPUT INSERTED para SQL Server
        query_usuario = """
            INSERT INTO Usuarios (Nombre, Apellido, Email, Password_Hash, Rol, Fecha_Registro)
            OUTPUT INSERTED.ID_Usuario
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_usuario, (
            user.nombre, 
            user.apellido, 
            user.email, 
            hashed_password, 
            user.rol,
            datetime.now()
        ))
        
        new_user_id = cursor.fetchone()[0]

        # 4. Insertar en tabla específica según el Rol
        if user.rol.lower() == 'medico':
            if not user.especialidad or not user.licencia:
                conn.rollback()
                raise HTTPException(status_code=400, detail="Datos de médico incompletos (especialidad/licencia)")
            
            cursor.execute("INSERT INTO Medicos (ID_Medico, Especialidad, Licencia_Medica) VALUES (?, ?, ?)", 
                           (new_user_id, user.especialidad, user.licencia))
        else:
            cursor.execute("INSERT INTO Pacientes (ID_Paciente) VALUES (?)", (new_user_id,))

        conn.commit()
        return {"message": f"Usuario {user.rol} creado correctamente", "id": new_user_id}

    except Exception as e:
        conn.rollback()
        logger.error(f"Error en registro: {str(e)}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail="Error interno al procesar el registro en SQL Server")
    finally:
        conn.close()

@app.post("/login")
async def login(request: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar usuario por email
        cursor.execute("SELECT ID_Usuario, Nombre, Password_Hash, Rol FROM Usuarios WHERE Email = ?", (request.email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        # Verificar contraseña hasheada
        if not pwd_context.verify(request.password, user.Password_Hash):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        return {
            "message": "Login exitoso",
            "user": {
                "id": user.ID_Usuario,
                "nombre": user.Nombre,
                "rol": user.Rol
            },
            "token": "fake-jwt-token-netrunners" # Aquí se integrará JWT más adelante
        }

    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()