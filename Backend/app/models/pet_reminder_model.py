from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base

# ===========================
# Pet Reminder Model    
# que hace? = Representa un recordatorio para una mascota   
class PetReminder(Base):
    __tablename__ = "pet_reminders"

    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)

    type = Column(String(30), nullable=False)
    fecha = Column(DateTime, nullable=False)
    proxima_fecha = Column(DateTime, nullable=True)
    status = Column(String(20), default="pendiente")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    pet = relationship("Pet", back_populates="reminders")
