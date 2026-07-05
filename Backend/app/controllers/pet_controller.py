from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, or_
from fastapi import HTTPException, UploadFile
from datetime import datetime
import base64

from app.models.pet_model import Pet
from app.models.adoption_model import Adoption
from app.models.adoption_status_model import AdoptionStatus
from app.models.user_model import User
from app.schemas.pet_schema import PetCreate, PetUpdate
from app.core.email import send_pet_approval_email, send_pet_rejection_email, send_sede_instructions_email
from app.controllers.audit_log_controller import log_action


# =========================
# CREATE
# =========================

def _upload_file_to_data_uri(file: UploadFile):
    contents = file.file.read()
    mime = file.content_type or "application/octet-stream"
    encoded = base64.b64encode(contents).decode("utf-8")
    return f"data:{mime};base64,{encoded}", contents


def create_pet(db: Session, pet: PetCreate, user_id: int, image: UploadFile = None):
    # Obtener el usuario para verificar su rol
    user = db.query(User).filter(User.id == user_id).first()
    
    # Si es admin (role_id == 1), se publica directamente como AVAILABLE
    # De lo contrario, queda como PENDING_APPROVAL
    initial_status = "AVAILABLE" if user and user.role_id == 1 else "PENDING_APPROVAL"

    image_url = None
    image_data = None
    if image:
        image_url, image_data = _upload_file_to_data_uri(image)

    new_pet = Pet(
        publisher_id=user_id,
        name=pet.name,
        species=pet.species,
        race=pet.race,
        birth_date=pet.birth_date,
        gender=pet.gender,
        description=pet.description,
        image_url=image_url,
        image_data=image_data,
        status=initial_status,
        modalidad=pet.modalidad or "sede",
        telefono_contacto=pet.telefono_contacto,
    )

    db.add(new_pet)
    db.commit()
    db.refresh(new_pet)
    
    # Inicializar campos virtuales para el schema
    new_pet.adopter_name = None
    new_pet.adopter_id = None
    new_pet.publisher_name = f"{user.name} {user.last_name or ''}" if user else "Sistema"

    try:
        log_action(
            db=db,
            user_id=user_id,
            action="create",
            resource="pet",
            resource_id=new_pet.id,
            changes={
                "name": new_pet.name,
                "species": new_pet.species,
                "race": new_pet.race,
                "status": new_pet.status
            },
            status="success"
        )
    except Exception as e:
        print(f"Audit logging error: {e}")

    return new_pet


# =========================
# GET ALL
# =========================

def get_pets(db: Session, status: str = None):
    # Usar joinedload para evitar N+1 y errores de lazy load
    query = db.query(Pet).options(joinedload(Pet.publisher)).filter(Pet.deleted_at == None)
    
    if status and status.upper() == "AVAILABLE":
        rejected_status_filter = func.upper(func.coalesce(AdoptionStatus.name, '')).in_(
            ['REJECTED', 'RECHAZADO', 'RECHAZADA']
        )

        approved_adoption_exists = (
            db.query(Adoption.id)
            .join(AdoptionStatus, AdoptionStatus.id == Adoption.status_id)
            .filter(
                Adoption.pet_id == Pet.id,
                Adoption.deleted_at == None,
                or_(
                    Adoption.status_id == 2,
                    func.upper(func.coalesce(AdoptionStatus.name, ''))
                    .in_(['APPROVED', 'APROBADO', 'APROBADA']),
                    and_(AdoptionStatus.is_final == True, ~rejected_status_filter),
                ),
            )
            .exists()
        )
        query = query.filter(Pet.status == "AVAILABLE").filter(~approved_adoption_exists)
    elif status:
        query = query.filter(Pet.status == status)

    pets = query.all()

    for pet in pets:
        # Adopter name - buscar la adopción activa más reciente
        adoption = db.query(Adoption).options(joinedload(Adoption.adoptante)).filter(
            Adoption.pet_id == pet.id,
            Adoption.deleted_at == None
        ).order_by(Adoption.fecha_solicitud.desc()).first()
        
        if adoption and adoption.adoptante:
            pet.adopter_name = f"{adoption.adoptante.name} {adoption.adoptante.last_name}"
            pet.adopter_id = adoption.adoptante.id
        else:
            pet.adopter_name = None
            pet.adopter_id = None
            
        # Publisher name
        if pet.publisher:
            pet.publisher_name = f"{pet.publisher.name} {pet.publisher.last_name or ''}"
        else:
            pet.publisher_name = "Anónimo"
    
    return pets


# =========================
# GET ONE
# =========================

def get_pet(db: Session, pet_id: int):

    pet = db.query(Pet).options(joinedload(Pet.publisher)).filter(
        Pet.id == pet_id,
        Pet.deleted_at == None
    ).first()

    if not pet:
        raise HTTPException(404, "Mascota no encontrada")

    # Adopter name
    adoption = db.query(Adoption).options(joinedload(Adoption.adoptante)).filter(
        Adoption.pet_id == pet.id,
        Adoption.deleted_at == None
    ).order_by(Adoption.fecha_solicitud.desc()).first()
    
    if adoption and adoption.adoptante:
        pet.adopter_name = f"{adoption.adoptante.name} {adoption.adoptante.last_name}"
        pet.adopter_id = adoption.adoptante.id
    else:
        pet.adopter_name = None
        pet.adopter_id = None

    # Publisher name
    if pet.publisher:
        pet.publisher_name = f"{pet.publisher.name} {pet.publisher.last_name or ''}"
    else:
        pet.publisher_name = "Anónimo"

    return pet


# =========================
# UPDATE
# =========================

def update_pet(db: Session, pet_id: int, data: PetUpdate):

    pet = db.query(Pet).filter(
        Pet.id == pet_id,
        Pet.deleted_at == None
    ).first()

    if not pet:
        raise HTTPException(404, "Mascota no encontrada")

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(pet, key, value)

    # Si la mascota vuelve a estar disponible, desvincularla del adoptante anterior
    if "status" in update_data and update_data["status"] == "AVAILABLE":
        db.query(Adoption).filter(
            Adoption.pet_id == pet.id,
            Adoption.deleted_at == None
        ).update({"deleted_at": datetime.utcnow()}, synchronize_session=False)

        # Notificar al publicador que su mascota fue aprobada
        try:
            publisher = pet.publisher
            if publisher:
                send_pet_approval_email(publisher.email, publisher.name, pet.name)
        except Exception as e:
            print(f"Error enviando correo de aprobación de mascota: {e}")

    elif "status" in update_data and update_data["status"] == "REJECTED":
        # Notificar al publicador que su publicación fue rechazada
        try:
            publisher = pet.publisher
            if publisher:
                send_pet_rejection_email(publisher.email, publisher.name, pet.name)
        except Exception as e:
            print(f"Error enviando correo de rechazo de mascota: {e}")

    db.commit()
    db.refresh(pet)

    try:
        log_action(
            db=db,
            user_id=None,
            action="update",
            resource="pet",
            resource_id=pet.id,
            changes=update_data,
            status="success"
        )
    except Exception as e:
        print(f"Audit logging error: {e}")

    return pet


# =========================
# SOFT DELETE
# =========================

def delete_pet(db: Session, pet_id: int):

    pet = db.query(Pet).filter(
        Pet.id == pet_id,
        Pet.deleted_at == None
    ).first()

    if not pet:
        raise HTTPException(404, "Mascota no encontrada")

    pet.deleted_at = datetime.utcnow()
    db.commit()

    try:
        log_action(
            db=db,
            user_id=None,
            action="delete",
            resource="pet",
            resource_id=pet.id,
            details=f"Mascota {pet.name} eliminada",
            status="success"
        )
    except Exception as e:
        print(f"Audit logging error: {e}")

    return {"message": "Mascota eliminada lógicamente"}