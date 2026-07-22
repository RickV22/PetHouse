import base64
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.adoption_schema import (
    AdoptionCreate,
    AdoptionStatusUpdate,
    AdoptionResponse,
    AdoptionCreateResponse,
    AdoptionListResponse
)
from app.core.email import send_adoption_request_email
from app.auth.dependencies import get_current_active_user
from app.controllers.adoption_controller import (
    create_adoption,
    get_adoptions,
    get_adoption,
    change_adoption_status,
    delete_adoption
)

router = APIRouter(prefix="/adoptions", tags=["Adoptions"])
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


def _validate_upload_file(file: UploadFile, label: str):
    mime = (file.content_type or "").lower()
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{label}: formato no permitido. Usa PDF, JPG, PNG o WEBP"
        )

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"{label}: archivo demasiado grande (máximo 2MB)"
        )


def _upload_file_to_data_uri(file: UploadFile):
    contents = file.file.read()
    mime = file.content_type or "application/octet-stream"
    encoded = base64.b64encode(contents).decode("utf-8")
    return f"data:{mime};base64,{encoded}"
    


@router.post("", response_model=AdoptionCreateResponse)
@router.post("/", response_model=AdoptionCreateResponse)
def create(
    background_tasks: BackgroundTasks,
    pet_id: int = Form(...),
    cedula: Optional[UploadFile] = File(None),
    recibo: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if cedula:
        _validate_upload_file(cedula, "Cédula")
    if recibo:
        _validate_upload_file(recibo, "Recibo")

    cedula_url = _upload_file_to_data_uri(cedula) if cedula else None
    recibo_url = _upload_file_to_data_uri(recibo) if recibo else None

    data = AdoptionCreate(
        pet_id=pet_id,
        cedula_url=cedula_url,
        recibo_url=recibo_url
    )
    adoption = create_adoption(db, data, user_id=current_user.id)
    background_tasks.add_task(
        send_adoption_request_email,
        current_user.email,
        current_user.name,
        adoption.pet.name
    )
    return adoption


@router.get("", response_model=List[AdoptionListResponse])
@router.get("/", response_model=List[AdoptionListResponse])
def read_all(db: Session = Depends(get_db)):
    return get_adoptions(db)


@router.get("/{adoption_id}", response_model=AdoptionResponse)
def read_one(adoption_id: int, db: Session = Depends(get_db)):
    return get_adoption(db, adoption_id)


@router.put("/{adoption_id}/status", response_model=AdoptionResponse)
def change_status(adoption_id: int, data: AdoptionStatusUpdate, db: Session = Depends(get_db)):
    return change_adoption_status(db, adoption_id, data.status_id)


@router.delete("/{adoption_id}")
def delete(adoption_id: int, db: Session = Depends(get_db)):
    return delete_adoption(db, adoption_id)

