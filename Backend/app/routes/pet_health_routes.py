from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.controllers.pet_health_controller import (
    create_pet_reminder,
    delete_pet_reminder,
    get_pet_medical_card,
    get_pet_reminders,
    get_user_pets,
    get_user_upcoming_reminders,
    update_pet_reminder,
    upsert_pet_medical_card,
)
from app.db.session import get_db
from app.schemas.pet_health_schema import (
    PetMedicalCardResponse,
    PetMedicalCardUpsert,
    PetReminderCreate,
    PetReminderResponse,
    PetReminderUpdate,
)
from app.schemas.pet_schema import PetResponse
from app.routes.pet_routes import _format_pets_image_url

router = APIRouter(tags=["PetHealth"])


@router.get("/users/me/pets", response_model=List[PetResponse])
def read_my_pets(request: Request, current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    pets = get_user_pets(db, current_user.id)
    _format_pets_image_url(pets, request)
    return pets


@router.get("/pets/{pet_id}/medical-card", response_model=Optional[PetMedicalCardResponse])
def read_medical_card(
    pet_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return get_pet_medical_card(db, pet_id, current_user.id)


@router.put("/pets/{pet_id}/medical-card", response_model=PetMedicalCardResponse)
def upsert_medical_card(
    pet_id: int,
    data: PetMedicalCardUpsert,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return upsert_pet_medical_card(db, pet_id, data, current_user.id)


@router.get("/pets/{pet_id}/reminders", response_model=List[PetReminderResponse])
def read_pet_reminders(
    pet_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return get_pet_reminders(db, pet_id, current_user.id)


@router.get("/pet-reminders/my/upcoming", response_model=List[PetReminderResponse])
def read_upcoming_reminders(
    days: int = Query(default=7, ge=1, le=30),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return get_user_upcoming_reminders(db, current_user.id, days=days)


@router.post("/pets/{pet_id}/reminders", response_model=PetReminderResponse)
def create_reminder(
    pet_id: int,
    data: PetReminderCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return create_pet_reminder(db, pet_id, data, current_user.id)


@router.put("/pet-reminders/{reminder_id}", response_model=PetReminderResponse)
def update_reminder(
    reminder_id: int,
    data: PetReminderUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return update_pet_reminder(db, reminder_id, data, current_user.id)


@router.delete("/pet-reminders/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return delete_pet_reminder(db, reminder_id, current_user.id)
