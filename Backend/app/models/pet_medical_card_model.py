from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class PetMedicalCard(Base):
    __tablename__ = "pet_medical_cards"

    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, unique=True)

    blood_type = Column(String(20), nullable=True)
    allergies = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    pet = relationship("Pet", back_populates="medical_card")
