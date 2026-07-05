from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True)
    publisher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    race = Column(String)
    birth_date = Column(DateTime)
    gender = Column(String)
    description = Column(String)
    image_url = Column(String)
    image_data = Column(LargeBinary)
    status = Column(String)
    modalidad = Column(String, default="sede")  # "sede" o "hogar"
    telefono_contacto = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    publisher = relationship("User", back_populates="pets")
    adoptions = relationship("Adoption", back_populates="pet")
    medical_card = relationship("PetMedicalCard", back_populates="pet", uselist=False)
    reminders = relationship("PetReminder", back_populates="pet")
