from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_HOST = os.getenv("DATABASE_HOST")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    DATABASE_NAME = os.getenv("DATABASE_NAME")

    if DATABASE_HOST:
        DATABASE_URL = (
            f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
            f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
            "?sslmode=require&channel_binding=require"
        )
    else:
        # Usar SQLite para desarrollo local
        DATABASE_URL = "sqlite:///./pet_house.db"

print("DATABASE_URL:", DATABASE_URL) 

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
