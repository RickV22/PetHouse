from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import func, or_
from app.core.email import send_adoption_approval_email, send_adoption_rejection_email

from app.models.adoption_model import Adoption
from app.models.pet_model import Pet
from app.models.adoption_status_model import AdoptionStatus


def _is_approved_status(status: AdoptionStatus | None, status_id: int | None = None) -> bool:
    if status_id == 2:
        return True
    if not status:
        return False
    normalized = (status.name or '').strip().upper()
    return normalized in {'APPROVED', 'APROBADO', 'APROBADA'}


def _is_rejected_status(status: AdoptionStatus | None) -> bool:
    if not status:
        return False
    normalized = (status.name or '').strip().upper()
    return normalized in {'REJECTED', 'RECHAZADO', 'RECHAZADA'}


def _is_effective_approval(status: AdoptionStatus | None, status_id: int | None = None) -> bool:
    if _is_approved_status(status, status_id=status_id):
        return True
    if not status:
        return False
    return bool(status.is_final) and not _is_rejected_status(status)


# helper para cargar relaciones
def _query_with_relations(db: Session):
    return db.query(Adoption).options(
        joinedload(Adoption.pet),
        joinedload(Adoption.adoptante),
        joinedload(Adoption.status)
    )


# =========================
# CREATE ADOPTION
# =========================

def create_adoption(db: Session, data, user_id: int):
    pet = db.query(Pet).filter(
        Pet.id == data.pet_id,
        Pet.deleted_at == None
    ).first()

    if not pet:
        raise HTTPException(404, "Mascota no encontrada")

    existing_approved = (
        db.query(Adoption)
        .join(AdoptionStatus, AdoptionStatus.id == Adoption.status_id)
        .filter(
            Adoption.pet_id == data.pet_id,
            Adoption.deleted_at == None,
            or_(
                Adoption.status_id == 2,
                func.upper(func.coalesce(AdoptionStatus.name, ''))
                .in_(['APPROVED', 'APROBADO', 'APROBADA']),
            ),
        )
        .first()
    )

    if existing_approved:
        raise HTTPException(400, "La mascota ya fue adoptada")

    adoption = Adoption(
        pet_id=data.pet_id,
        adoptante_id=user_id,
        status_id=1,  # PENDING
        cedula_url=data.cedula_url,
        recibo_url=data.recibo_url
    )

    db.add(adoption)
    db.add(pet)
    db.commit()
    db.refresh(adoption)

    return _query_with_relations(db).filter(Adoption.id == adoption.id).first()


# =========================
# GET ALL
# =========================

def get_adoptions(db: Session):
    return _query_with_relations(db).filter(
        Adoption.deleted_at == None
    ).all()


# =========================
# GET ONE
# =========================

def get_adoption(db: Session, adoption_id: int):
    adoption = _query_with_relations(db).filter(
        Adoption.id == adoption_id,
        Adoption.deleted_at == None
    ).first()

    if not adoption:
        raise HTTPException(404, "Adopción no encontrada")

    return adoption


# =========================
# CHANGE STATUS
# =========================

def change_adoption_status(db: Session, adoption_id: int, status_id: int):
    adoption = db.query(Adoption).filter(
        Adoption.id == adoption_id,
        Adoption.deleted_at == None
    ).first()

    if not adoption:
        raise HTTPException(404, "Adopción no encontrada")

    status = db.query(AdoptionStatus).filter(
        AdoptionStatus.id == status_id
    ).first()

    if not status:
        raise HTTPException(404, "Estado inválido")

    current_status = db.query(AdoptionStatus).filter(
        AdoptionStatus.id == adoption.status_id
    ).first()

    if current_status.is_final:
        raise HTTPException(400, "Esta adopción ya es final")

    if _is_effective_approval(status, status_id=status_id):
        existing_approved_for_pet = (
            db.query(Adoption.id)
            .join(AdoptionStatus, AdoptionStatus.id == Adoption.status_id)
            .filter(
                Adoption.pet_id == adoption.pet_id,
                Adoption.id != adoption.id,
                Adoption.deleted_at == None,
                or_(
                    Adoption.status_id == 2,
                    func.upper(func.coalesce(AdoptionStatus.name, '')).in_(
                        ['APPROVED', 'APROBADO', 'APROBADA']
                    ),
                ),
            )
            .first()
        )
        if existing_approved_for_pet:
            raise HTTPException(400, "La mascota ya tiene una adopción aprobada")

    adoption.status_id = status_id
    adoption.fecha_respuesta = datetime.utcnow()

    if _is_effective_approval(status, status_id=status_id):
        adoption.pet.status = "ADOPTED"
        # Enviar correo de aprobación
        try:
            send_adoption_approval_email(
                adoption.adoptante.email,
                adoption.adoptante.name,
                adoption.pet.name
            )
        except Exception as e:
            print(f"Error enviando correo de aprobación: {e}")

    elif _is_rejected_status(status):
        # Enviar correo de rechazo
        try:
            send_adoption_rejection_email(
                adoption.adoptante.email,
                adoption.adoptante.name,
                adoption.pet.name
            )
        except Exception as e:
            print(f"Error enviando correo de rechazo: {e}")

    db.commit()

    return _query_with_relations(db).filter(Adoption.id == adoption_id).first()


# =========================
# SOFT DELETE
# =========================

def delete_adoption(db: Session, adoption_id: int):
    adoption = db.query(Adoption).filter(
        Adoption.id == adoption_id,
        Adoption.deleted_at == None
    ).first()

    if not adoption:
        raise HTTPException(404, "Adopción no encontrada")

    adoption.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Adopción eliminada lógicamente"}