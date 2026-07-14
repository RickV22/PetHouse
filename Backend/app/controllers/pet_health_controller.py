from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.adoption_model import Adoption
from app.models.adoption_status_model import AdoptionStatus
from app.models.pet_medical_card_model import PetMedicalCard
from app.models.pet_model import Pet
from app.models.pet_reminder_model import PetReminder
from app.schemas.pet_health_schema import PetMedicalCardUpsert, PetReminderCreate, PetReminderUpdate


def _approved_adoption_filter() -> any:
    normalized_status = func.upper(func.coalesce(AdoptionStatus.name, ""))
    return or_(
        normalized_status.in_(["APPROVED", "APROBADO", "APROBADA"]),
        Adoption.status_id == 2,
    )


def _latest_approved_adoption_subquery(db: Session):
    return (
        db.query(
            Adoption.pet_id.label("pet_id"),
            func.max(Adoption.id).label("adoption_id"),
        )
        .join(AdoptionStatus, AdoptionStatus.id == Adoption.status_id)
        .filter(
            Adoption.deleted_at == None,
            _approved_adoption_filter(),
        )
        .group_by(Adoption.pet_id)
        .subquery()
    )


def _ensure_pet_health_tables(db: Session) -> None:
    bind = db.get_bind()
    Base.metadata.create_all(
        bind=bind,
        tables=[PetMedicalCard.__table__, PetReminder.__table__],
    )

    # Compatibilidad con esquemas previos: agrega columnas faltantes sin perder datos.
    db.execute(text("ALTER TABLE IF EXISTS pet_medical_cards ADD COLUMN IF NOT EXISTS blood_type VARCHAR(20)"))
    db.execute(text("ALTER TABLE IF EXISTS pet_medical_cards ADD COLUMN IF NOT EXISTS allergies TEXT"))
    db.execute(text("ALTER TABLE IF EXISTS pet_medical_cards ADD COLUMN IF NOT EXISTS conditions TEXT"))
    db.execute(text("ALTER TABLE IF EXISTS pet_medical_cards ADD COLUMN IF NOT EXISTS observations TEXT"))
    db.execute(text("ALTER TABLE IF EXISTS pet_medical_cards ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    db.execute(text("ALTER TABLE IF EXISTS pet_medical_cards ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    db.execute(text("ALTER TABLE IF EXISTS pet_medical_cards ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP"))

    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS type VARCHAR(30)"))
    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS fecha TIMESTAMP"))
    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS proxima_fecha TIMESTAMP"))
    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pendiente'"))
    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS notes TEXT"))
    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    db.execute(text("ALTER TABLE IF EXISTS pet_reminders ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP"))
    db.commit()


def _get_pet_or_404(db: Session, pet_id: int) -> Pet:
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.deleted_at == None).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return pet


def _user_can_access_pet(db: Session, pet: Pet, user_id: int) -> bool:
    if pet.publisher_id == user_id:
        return True

    latest_approved = _latest_approved_adoption_subquery(db)
    approved_adoption = (
        db.query(Adoption.id)
        .join(latest_approved, latest_approved.c.adoption_id == Adoption.id)
        .filter(
            Adoption.pet_id == pet.id,
            Adoption.adoptante_id == user_id,
            Adoption.deleted_at == None,
        )
        .first()
    )
    return approved_adoption is not None


def _assert_pet_access(db: Session, pet_id: int, user_id: int) -> Pet:
    pet = _get_pet_or_404(db, pet_id)
    if not _user_can_access_pet(db, pet, user_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta mascota")
    return pet


def get_user_pets(db: Session, user_id: int) -> list[Pet]:
    published = db.query(Pet).filter(Pet.publisher_id == user_id, Pet.deleted_at == None).all()
    latest_approved = _latest_approved_adoption_subquery(db)

    adopted = (
        db.query(Pet)
        .join(Adoption, Adoption.pet_id == Pet.id)
        .join(latest_approved, latest_approved.c.adoption_id == Adoption.id)
        .filter(
            Adoption.adoptante_id == user_id,
            Adoption.deleted_at == None,
            Pet.deleted_at == None,
        )
        .all()
    )

    pet_map: dict[int, Pet] = {pet.id: pet for pet in published}
    for pet in adopted:
        pet_map[pet.id] = pet

    return sorted(
        pet_map.values(),
        key=lambda pet: pet.created_at or datetime.min,
        reverse=True,
    )


def get_pet_medical_card(db: Session, pet_id: int, user_id: int) -> PetMedicalCard | None:
    _ensure_pet_health_tables(db)
    _assert_pet_access(db, pet_id, user_id)
    return (
        db.query(PetMedicalCard)
        .filter(PetMedicalCard.pet_id == pet_id, PetMedicalCard.deleted_at == None)
        .first()
    )


def upsert_pet_medical_card(
    db: Session,
    pet_id: int,
    data: PetMedicalCardUpsert,
    user_id: int,
) -> PetMedicalCard:
    _ensure_pet_health_tables(db)
    _assert_pet_access(db, pet_id, user_id)

    card = (
        db.query(PetMedicalCard)
        .filter(PetMedicalCard.pet_id == pet_id, PetMedicalCard.deleted_at == None)
        .first()
    )

    payload = data.dict(exclude_unset=True)

    if card:
        for key, value in payload.items():
            setattr(card, key, value)
    else:
        card = PetMedicalCard(pet_id=pet_id, **payload)
        db.add(card)

    db.commit()
    db.refresh(card)
    return card


def get_pet_reminders(db: Session, pet_id: int, user_id: int) -> list[PetReminder]:
    _ensure_pet_health_tables(db)
    _assert_pet_access(db, pet_id, user_id)
    return (
        db.query(PetReminder)
        .filter(PetReminder.pet_id == pet_id, PetReminder.deleted_at == None)
        .order_by(PetReminder.fecha.asc())
        .all()
    )


def get_user_upcoming_reminders(db: Session, user_id: int, days: int = 7) -> list[PetReminder]:
    _ensure_pet_health_tables(db)
    now = datetime.utcnow()
    user_pets = get_user_pets(db, user_id)
    user_pet_ids = [pet.id for pet in user_pets]

    if not user_pet_ids:
        return []

    upper_bound = now.timestamp() + days * 24 * 60 * 60
    max_date = datetime.utcfromtimestamp(upper_bound)

    return (
        db.query(PetReminder)
        .filter(
            PetReminder.pet_id.in_(user_pet_ids),
            PetReminder.deleted_at == None,
            PetReminder.fecha >= now,
            PetReminder.fecha <= max_date,
            func.lower(func.coalesce(PetReminder.status, "pendiente")) == "pendiente",
        )
        .order_by(PetReminder.fecha.asc())
        .all()
    )


def _send_telegram_notification(db: Session, user_id: int, pet_name: str, reminder_type: str, fecha: datetime, notes: str):
    import os
    import requests
    from app.models.user_model import User
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
        
    user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if not user or not user.telegram_chat_id:
        return
        
    fecha_str = fecha.strftime("%d/%m/%Y") if fecha else "Sin fecha"
    mensaje = (
        f"🔔 *Nuevo Recordatorio en PetHouse*\n\n"
        f"Se ha programado una tarea de salud para *{pet_name}*:\n"
        f"📌 *Tipo:* {reminder_type}\n"
        f"📅 *Fecha:* {fecha_str}\n"
        f"📝 *Notas:* {notes or 'Ninguna'}\n\n"
        f"¡Cuidemos juntos a nuestras mascotas! 🐾"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": user.telegram_chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] Error al enviar notificación de Telegram: {e}")


def create_pet_reminder(
    db: Session,
    pet_id: int,
    data: PetReminderCreate,
    user_id: int,
) -> PetReminder:
    _ensure_pet_health_tables(db)
    _assert_pet_access(db, pet_id, user_id)

    reminder = PetReminder(
        pet_id=pet_id,
        type=data.type,
        fecha=data.fecha,
        proxima_fecha=data.proxima_fecha,
        status=(data.status or "pendiente").lower(),
        notes=data.notes,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # Enviar notificación de Telegram si aplica
    try:
        _send_telegram_notification(
            db=db,
            user_id=user_id,
            pet_name=reminder.pet.name,
            reminder_type=reminder.type,
            fecha=reminder.fecha,
            notes=reminder.notes
        )
    except Exception as e:
        print(f"[WARNING] No se pudo enviar notificación de Telegram: {e}")

    return reminder


def update_pet_reminder(db: Session, reminder_id: int, data: PetReminderUpdate, user_id: int) -> PetReminder:
    _ensure_pet_health_tables(db)
    reminder = (
        db.query(PetReminder)
        .filter(PetReminder.id == reminder_id, PetReminder.deleted_at == None)
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

    _assert_pet_access(db, reminder.pet_id, user_id)

    payload = data.dict(exclude_unset=True)
    if "status" in payload and payload["status"] is not None:
        payload["status"] = payload["status"].lower()

    for key, value in payload.items():
        setattr(reminder, key, value)

    db.commit()
    db.refresh(reminder)
    return reminder


def delete_pet_reminder(db: Session, reminder_id: int, user_id: int) -> dict[str, str]:
    _ensure_pet_health_tables(db)
    reminder = (
        db.query(PetReminder)
        .filter(PetReminder.id == reminder_id, PetReminder.deleted_at == None)
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

    _assert_pet_access(db, reminder.pet_id, user_id)
    reminder.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Recordatorio eliminado"}
