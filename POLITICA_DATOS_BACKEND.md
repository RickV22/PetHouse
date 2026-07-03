# Guía de Implementación Backend - Política de Datos

## 📋 Resumen

Este documento describe los cambios necesarios en el backend para soportar la Política de Tratamiento de Datos Personales.

## 🔧 Cambios Necesarios

### 1. Modelo de Usuario (Backend/app/models/user_model.py)

Agregar el campo `accepted_policy` al modelo:

```python
from sqlalchemy import Boolean

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), default=2)
    accepted_policy = Column(Boolean, default=False)  # ← AGREGAR ESTA LÍNEA
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2. Schema de Usuario (Backend/app/schemas/user_schema.py)

Actualizar los schemas:

```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    password: str
    role_id: int = 2
    accepted_policy: bool = False  # ← AGREGAR ESTE CAMPO

class UserUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    accepted_policy: Optional[bool] = None  # ← AGREGAR ESTE CAMPO

class UserResponse(BaseModel):
    id: int
    name: str
    last_name: str
    email: str
    role_id: int
    accepted_policy: bool  # ← AGREGAR ESTE CAMPO
    created_at: datetime

    class Config:
        from_attributes = True
```

### 3. Controlador de Usuario (Backend/app/controllers/user_controller.py)

Asegurar que el endpoint de actualización maneje `accepted_policy`:

```python
async def update_user(id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actualizar campos incluido accepted_policy
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
```

### 4. Servicio Google Sign-In (Backend/app/controllers/user_controller.py)

Asegurar que el endpoint de Google retorna `accepted_policy`:

```python
async def google_login(credentials: GoogleLoginRequest, db: Session = Depends(get_db)):
    # ... código existente para verificar credenciales ...

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Crear nuevo usuario con accepted_policy = False
        user = User(
            name=name,
            last_name=last_name or "",
            email=email,
            password=hash_password("google_" + id_token),
            role_id=2,
            accepted_policy=False  # ← Primera vez que inicia sesión
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Retornar respuesta incluida accepted_policy
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "last_name": user.last_name,
            "email": user.email,
            "role_id": user.role_id,
            "accepted_policy": user.accepted_policy  # ← IMPORTANTE
        },
        "access_token": generate_token(user.id, user.role_id),
        "token_type": "bearer"
    }
```

### 5. Migración de Base de Datos

Si usas Alembic para migraciones:

```bash
alembic revision --autogenerate -m "Add accepted_policy field to users table"
alembic upgrade head
```

O ejecutar SQL manualmente:

```sql
ALTER TABLE users ADD COLUMN accepted_policy BOOLEAN DEFAULT FALSE;
```

## 📌 Puntos Importantes

1. **Compatibilidad**: Usuarios existentes tendrán `accepted_policy = False` por defecto
2. **Google Sign-In**: Nuevos usuarios que se registren con Google tendrán `accepted_policy = False` inicialmente
3. **Validación**: El campo es opcional en actualizaciones, obligatorio solo en creación
4. **Lógica de Negocio**: El frontend muestra modal al primer login si `accepted_policy = False`

## ✅ Checklist de Validación

- [ ] Campo `accepted_policy` agregado al modelo User
- [ ] Schemas actualizados con el nuevo campo
- [ ] Endpoint de registro acepta `accepted_policy`
- [ ] Endpoint de actualización puede modificar `accepted_policy`
- [ ] Endpoint de Google Sign-In retorna `accepted_policy`
- [ ] Base de datos migrada/actualizada
- [ ] Tests unitarios actualizados
- [ ] Documentación de API actualizada (si aplica)

## 🧪 Pruebas Recomendadas

1. **Registro manual**:
   - Crear usuario con `accepted_policy: true`
   - Verificar que se guarde correctamente

2. **Google Sign-In**:
   - Primera vez: Usuario nuevo retorna `accepted_policy: false`
   - Segunda vez: Usuario existente retorna `accepted_policy: true` (después de aceptar en modal)

3. **Actualización de política**:
   - `PUT /users/{id}` con `{"accepted_policy": true}`
   - Verificar que se actualice correctamente

## 📞 Soporte

Si encuentras problemas durante la implementación, verifica:

- Los tipos de datos coincidan con lo especificado
- Las respuestas de la API incluyan el campo `accepted_policy`
- El frontend recibe correctamente el campo en las respuestas
