from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.jwt_handler import get_current_user
from app.db.session import get_db

def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def get_current_admin_user(current_user = Depends(get_current_active_user)):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return current_user




