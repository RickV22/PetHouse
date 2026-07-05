#!/usr/bin/env python3
"""Reconcilia adopciones aprobadas duplicadas por mascota.

Reglas:
- Mantiene solo una adopcion aprobada activa por mascota (la mas reciente).
- Las aprobadas adicionales se marcan como deleted_at (soft delete).
- Si una mascota tiene adopcion aprobada activa, su estado se fuerza a ADOPTED.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.adoption_model import Adoption
from app.models.adoption_status_model import AdoptionStatus
from app.models.pet_model import Pet


APPROVED_NAMES = {"APPROVED", "APROBADO", "APROBADA"}
REJECTED_NAMES = {"REJECTED", "RECHAZADO", "RECHAZADA"}


def is_effective_approved(status: AdoptionStatus | None, status_id: int) -> bool:
    if status_id == 2:
        return True
    if not status:
        return False
    normalized = (status.name or "").strip().upper()
    if normalized in APPROVED_NAMES:
        return True
    if status.is_final and normalized not in REJECTED_NAMES:
        return True
    return False


def sort_key(adoption: Adoption) -> tuple:
    # Mantener la mas reciente como adopcion activa
    return (
        adoption.fecha_respuesta or adoption.fecha_solicitud or datetime.min,
        adoption.id,
    )


def reconcile() -> None:
    db = SessionLocal()
    now = datetime.utcnow()

    try:
        adoptions = (
            db.query(Adoption)
            .options(joinedload(Adoption.status), joinedload(Adoption.pet), joinedload(Adoption.adoptante))
            .filter(Adoption.deleted_at == None)
            .all()
        )

        by_pet: dict[int, list[Adoption]] = defaultdict(list)
        for adoption in adoptions:
            by_pet[adoption.pet_id].append(adoption)

        duplicates_soft_deleted = 0
        pets_forced_adopted = 0

        for pet_id, pet_adoptions in by_pet.items():
            approved = [
                a for a in pet_adoptions if is_effective_approved(a.status, a.status_id)
            ]

            if not approved:
                continue

            approved_sorted = sorted(approved, key=sort_key, reverse=True)
            keeper = approved_sorted[0]

            for duplicate in approved_sorted[1:]:
                duplicate.deleted_at = now
                duplicates_soft_deleted += 1

            pet = keeper.pet or db.query(Pet).filter(Pet.id == pet_id).first()
            if pet and (pet.status or "").upper() != "ADOPTED":
                pet.status = "ADOPTED"
                pets_forced_adopted += 1

        db.commit()

        print("Reconciliacion completada")
        print(f"- Adopciones aprobadas duplicadas desactivadas: {duplicates_soft_deleted}")
        print(f"- Mascotas sincronizadas a ADOPTED: {pets_forced_adopted}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reconcile()
