from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import hash_password
from app.core.security import verify_password
from app.auth.jwt_handler import create_access_token
from app.core.email import send_gps_email
from app.controllers.audit_log_controller import log_action
import traceback
import requests
import secrets
from app.core.security import hash_password


# =========================
# CREATE
# =========================

def create_user(db: Session, user: UserCreate):

    existing = db.query(User).filter(
        User.email == user.email,
        User.deleted_at == None
    ).first()

    if existing:
        raise HTTPException(400, "Email ya registrado")

    new_user = User(
        role_id=user.role_id,
        name=user.name,
        last_name=user.last_name,
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        log_action(
            db=db,
            user_id=None,
            action="create",
            resource="user",
            resource_id=new_user.id,
            changes=user.dict(exclude={"password"}),
            status="success"
        )
    except Exception as e:
        print(f"Audit logging error: {e}")

    return new_user


# =========================
# GET ALL
# =========================

def get_users(db: Session):

    return db.query(User).filter(
        User.deleted_at == None
    ).all()


# =========================
# GET ONE
# =========================

def get_user(db: Session, user_id: int):

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()

    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    return user

#buscar usuario por correo

def get_user_by_email(db: Session, email: str):

    user = db.query(User).filter(
        User.email == email,
        User.deleted_at == None
    ).first()

    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    return user


# =========================
# UPDATE
# =========================

def update_user(db: Session, user_id: int, data: UserUpdate):

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()

    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    update_data = data.dict(exclude_unset=True)

    # Validar email duplicado
    if "email" in update_data:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id,
            User.deleted_at == None
        ).first()

        if existing:
            raise HTTPException(400, "Email ya registrado")

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    for key, value in update_data.items():
        setattr(user, key, value)

    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    try:
        log_action(
            db=db,
            user_id=None,
            action="update",
            resource="user",
            resource_id=user.id,
            changes=update_data,
            status="success"
        )
    except Exception as e:
        print(f"Audit logging error: {e}")

    # Envío de correo real si el GPS es aprobado O si se actualiza el IMEI de un usuario ya aprobado
    is_becoming_approved = ("gps_status" in update_data and update_data["gps_status"] == "approved")
    is_updating_imei = ("gps_imei" in update_data and user.gps_status == "approved")

    if is_becoming_approved or is_updating_imei:
        print(f"--- Iniciando proceso de envío de correo a {user.email} ---")
        send_gps_email(user.email, user.name, user.gps_imei)

    return user

# login
def login_user(db: Session, email: str, password: str):
    try:
        print(f"[DEBUG] login_user called for email: {email}")

        user = db.query(User).filter(
            User.email == email,
            User.deleted_at == None
        ).first()

        if not user:
            print(f"[DEBUG] User not found for email: {email}")
            raise HTTPException(404, "Usuario no encontrado")

        if not verify_password(password, user.password):
            print(f"[DEBUG] Password verification failed for user id: {user.id}")
            raise HTTPException(400, "Contraseña incorrecta")

        # Create JWT token
        try:
            access_token = create_access_token(data={"sub": str(user.id)})
        except Exception as e:
            tb = traceback.format_exc()
            print("[ERROR] Failed creating access token:\n", tb)
            raise HTTPException(500, "Error generating access token")

        try:
            log_action(
                db=db,
                user_id=user.id,
                action="login",
                resource="user",
                resource_id=user.id,
                details="Login exitoso",
                status="success"
            )
        except Exception as e:
            print(f"Audit logging error: {e}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "role_id": user.role_id,
                "name": user.name,
                "last_name": user.last_name,
                "email": user.email,
                "is_active": user.is_active,
                "gps_status": user.gps_status,
                "gps_imei": user.gps_imei,
                "created_at": user.created_at
            }
        }
    except HTTPException:
        raise
    except Exception:
        tb = traceback.format_exc()
        print("[ERROR] Unexpected exception in login_user:\n", tb)
        raise HTTPException(500, "Internal server error during login")


def login_with_google(db: Session, id_token: str):
    """Verify Google id_token and return/create user + JWT"""
    try:
        # Verify token with Google
        resp = requests.get('https://oauth2.googleapis.com/tokeninfo', params={'id_token': id_token}, timeout=5)
        if resp.status_code != 200:
            raise HTTPException(400, 'Google token inválido')

        info = resp.json()
        email = info.get('email')
        email_verified = info.get('email_verified') in ['true', True, 'TRUE']
        name = info.get('name') or info.get('given_name') or ''
        last_name = info.get('family_name') or ''

        if not email or not email_verified:
            raise HTTPException(400, 'Email no verificado por Google')

        # Find or create user
        user = db.query(User).filter(User.email == email, User.deleted_at == None).first()
        if not user:
            # create new user with random password
            random_pw = secrets.token_urlsafe(16)
            user = User(
                role_id=2,
                name=name or email.split('@')[0],
                last_name=last_name or '',
                email=email,
                password=hash_password(random_pw)
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            try:
                log_action(db=db, user_id=None, action='create', resource='user', resource_id=user.id, details='Usuario creado via Google OAuth', status='success')
            except Exception as e:
                print(f"Audit logging error: {e}")

        # create access token
        access_token = create_access_token(data={"sub": str(user.id)})

        try:
            log_action(db=db, user_id=user.id, action='login', resource='user', resource_id=user.id, details='Login via Google', status='success')
        except Exception as e:
            print(f"Audit logging error: {e}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "role_id": user.role_id,
                "name": user.name,
                "last_name": user.last_name,
                "email": user.email,
                "is_active": user.is_active,
                "gps_status": user.gps_status,
                "gps_imei": user.gps_imei,
                "created_at": user.created_at
            }
        }
    except HTTPException:
        raise
    except Exception:
        tb = traceback.format_exc()
        print('[ERROR] Unexpected exception in login_with_google:\n', tb)
        raise HTTPException(500, 'Error interno en login con Google')

# =========================
# SOFT DELETE
# =========================

def delete_user(db: Session, user_id: int):

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()

    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    user.deleted_at = datetime.utcnow()
    user.is_active = False

    db.commit()

    try:
        log_action(
            db=db,
            user_id=None,
            action="delete",
            resource="user",
            resource_id=user.id,
            details=f"Usuario {user.email} eliminado",
            status="success"
        )
    except Exception as e:
        print(f"Audit logging error: {e}")

    return {"message": "Usuario eliminado lógicamente"}


# =========================
# RESTORE
# =========================

def restore_user(db: Session, user_id: int):

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at != None
    ).first()

    if not user:
        raise HTTPException(404, "Usuario no encontrado o no está eliminado")

    user.deleted_at = None
    user.is_active = True

    db.commit()

    try:
        log_action(
            db=db,
            user_id=None,
            action="restore",
            resource="user",
            resource_id=user.id,
            details=f"Usuario {user.email} restaurado",
            status="success"
        )
    except Exception as e:
        print(f"Audit logging error: {e}")

    return {"message": "Usuario restaurado correctamente"}