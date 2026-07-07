from fastapi import APIRouter, Depends, HTTPException
import traceback
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse, TelegramLinkRequest
from app.controllers.user_controller import (
    create_user, 
    get_users,
    get_user,
    update_user,
    delete_user,
    restore_user,
    get_user_by_email,
    login_user,
    login_with_google,
    link_telegram_chat,
    unlink_telegram_chat,
)
from app.schemas.user_schema import LoginRequest, TokenResponse
from app.schemas.user_schema import SocialLoginRequest
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/users", tags=["Users"])


# LOGIN - Must be before {user_id} to avoid conflict
@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        return login_user(db, data.email, data.password)
    except HTTPException:
        # Re-raise known HTTP exceptions (404, 400, etc.) so FastAPI handles them
        raise
    except Exception as e:
        # Log full traceback for debugging while returning a safe 500 response
        tb = traceback.format_exc()
        print("[ERROR] Exception in /users/login:\n", tb)
        raise HTTPException(status_code=500, detail="Internal server error during login")



@router.post('/google-login', response_model=TokenResponse)
def google_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    try:
        return login_with_google(db, payload.id_token)
    except HTTPException:
        raise
    except Exception:
        tb = traceback.format_exc()
        print('[ERROR] Exception in /users/google-login:\n', tb)
        raise HTTPException(status_code=500, detail='Internal server error during Google login')


# REGISTER (Public)
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Forzar que el rol sea 2 (Usuario normal) para registros públicos
    user.role_id = 2
    return create_user(db, user)


# CREATE (Admin only)
@router.post("/", response_model=UserResponse)
def create(user: UserCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin_user)):
    return create_user(db, user)


# GET ALL
@router.get("/", response_model=List[UserResponse])
def read_all(db: Session = Depends(get_db)):
    return get_users(db)


# Get by email - Must be before {user_id} to avoid conflict
@router.get("/email/{email}", response_model=UserResponse)
def read_by_email(email: str, db: Session = Depends(get_db)):
    return get_user_by_email(db, email)


# GET ONE - Must be after more specific routes
@router.get("/{user_id}", response_model=UserResponse)
def read_one(user_id: int, db: Session = Depends(get_db)):
    return get_user(db, user_id)

# UPDATE
@router.put("/{user_id}", response_model=UserResponse)
def update(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    return update_user(db, user_id, data)


# DELETE (Soft)
@router.delete("/{user_id}")
def delete(user_id: int, db: Session = Depends(get_db)):
    return delete_user(db, user_id)


# RESTORE
@router.put("/restore/{user_id}")
def restore(user_id: int, db: Session = Depends(get_db)):
    return restore_user(db, user_id)


# LINK TELEGRAM
@router.post("/link-telegram", response_model=UserResponse)
def link_telegram(payload: TelegramLinkRequest, db: Session = Depends(get_db)):
    return link_telegram_chat(db, payload.user_id, payload.telegram_chat_id)


# UNLINK TELEGRAM
@router.patch("/unlink-telegram/{user_id}", response_model=UserResponse)
def unlink_telegram(user_id: int, db: Session = Depends(get_db)):
    return unlink_telegram_chat(db, user_id)