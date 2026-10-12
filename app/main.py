import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
# Import all models to ensure registration with Base metadata
import app.models # noqa
from app.routers import auth, students, consent, counsellors, admin, api
from app.security.authentication import get_current_user_optional
from app.database import SessionLocal

# Initialize SQLite tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Campus Mental Health Crisis Early Warning System with machine learning indicators and privacy-preserving human-in-the-loop workflows.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(consent.router)
app.include_router(counsellors.router)
app.include_router(admin.router)
app.include_router(api.router)

@app.get("/")
def root_redirect(request: Request):
    """Redirect home route to user's dashboard if logged in, otherwise to login."""
    db = SessionLocal()
    try:
        user = get_current_user_optional(request, db)
        if user:
            if user.role == "student":
                return RedirectResponse("/student/dashboard", status_code=302)
            elif user.role == "counsellor":
                return RedirectResponse("/counsellor/dashboard", status_code=302)
            elif user.role == "admin":
                return RedirectResponse("/admin/dashboard", status_code=302)
        return RedirectResponse("/login", status_code=302)
    finally:
        db.close()
