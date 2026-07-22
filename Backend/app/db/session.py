from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_NEON_URL = (
    "postgresql://neondb_owner:npg_ReiUD27Fftnw"
    "@ep-damp-block-ai81i5p8-pooler.c-4.us-east-1.aws.neon.tech"
    ":5432/neondb?sslmode=require&channel_binding=require"
)

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
        DATABASE_URL = DEFAULT_NEON_URL

print("DATABASE_URL:", DATABASE_URL)

# ===========================
# Engine
# ===========================

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,

        # Verifica que la conexión siga viva
        pool_pre_ping=True,

        # Recicla conexiones cada 30 minutos
        pool_recycle=1800,

        # Pool de conexiones
        pool_size=5,
        max_overflow=10,

        # Espera máxima antes de lanzar timeout
        pool_timeout=30,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()