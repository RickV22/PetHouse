import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.db.session import engine
from app.db.base import Base

# MODELOS (importarlos para que SQLAlchemy los registre)
from app.models import *

# ROUTES
from app.routes.user_routes import router as user_router
from app.routes.pet_routes import router as pet_router
from app.routes.adoption_routes import router as adoption_router
from app.routes.role_routes import router as role_router
from app.routes.adoption_status_routes import router as adoption_status_router
from app.routes.role_permission_routes import router as role_permission_router
from app.routes.permission_routes import router as permission_router
from app.routes.tracker_routes import router as tracker_router
from app.routes.tracker_location_routes import router as tracker_location_router
from app.routes.audit_log_routes import router as audit_log_router


app = FastAPI()


@app.on_event("startup")
def startup_event():
    for attempt in range(30):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            if attempt == 29:
                raise
            time.sleep(1)

# ==========================
# CORS
# ==========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:4173",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# STATIC FILES
# ==========================

# ==========================
# ROUTES
# ==========================

app.include_router(user_router)
app.include_router(pet_router)
app.include_router(adoption_router)
app.include_router(role_router)
app.include_router(adoption_status_router)
app.include_router(role_permission_router)
app.include_router(permission_router)
app.include_router(tracker_router)
app.include_router(tracker_location_router)
app.include_router(audit_log_router)



# ==========================
# RUN
# ==========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)