"""
FastAPI Backend для CyberSecurity Web Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import sys
import os

# Добавляем путь к algorithms
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.routers import auth, crypto, users, documents
from backend.database import engine, Base

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CyberSecurity API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Роутеры
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["crypto"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


@app.get("/")
async def root():
    return {"message": "CyberSecurity API"}


@app.get("/health")
async def health():
    return {"status": "ok"}

