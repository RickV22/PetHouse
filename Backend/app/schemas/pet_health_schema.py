from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PetMedicalCardUpsert(BaseModel):
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    observations: Optional[str] = None


class PetMedicalCardResponse(BaseModel):
    id: int
    pet_id: int
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    observations: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class PetReminderCreate(BaseModel):
    type: str = Field(min_length=1, max_length=30)
    fecha: datetime
    proxima_fecha: Optional[datetime] = None
    status: Optional[str] = "pendiente"
    notes: Optional[str] = None


class PetReminderUpdate(BaseModel):
    type: Optional[str] = Field(default=None, min_length=1, max_length=30)
    fecha: Optional[datetime] = None
    proxima_fecha: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PetReminderResponse(BaseModel):
    id: int
    pet_id: int
    type: str
    fecha: datetime
    proxima_fecha: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
