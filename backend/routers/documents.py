"""
Documents router - экспорт в PDF с ЭЦП
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.auth_utils import get_current_user
from backend.models import Document, User
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import hashlib

router = APIRouter()
security = HTTPBearer()


class CreateDocumentRequest(BaseModel):
    original_text: str
    encrypted_text: str = None
    algorithm: str = None


@router.post("/create")
async def create_document(
    request: CreateDocumentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Создание документа"""
    user = get_current_user(credentials.credentials, db)
    
    doc = Document(
        user_id=user.id,
        original_text=request.original_text,
        encrypted_text=request.encrypted_text,
        algorithm=request.algorithm
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {"id": doc.id, "message": "Document created"}


@router.get("/{document_id}/pdf")
async def export_to_pdf(
    document_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Экспорт документа в PDF с ЭЦП"""
    user = get_current_user(credentials.credentials, db)
    doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Создаем PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CyberSecurity Document")
    
    # Оригинальный текст
    c.setFont("Helvetica", 12)
    y = height - 100
    c.drawString(50, y, "Original Text:")
    y -= 20
    
    # Разбиваем текст на строки
    text_lines = []
    words = doc.original_text.split()
    line = ""
    for word in words:
        if len(line + word) < 80:
            line += word + " "
        else:
            text_lines.append(line)
            line = word + " "
    if line:
        text_lines.append(line)
    
    for line in text_lines[:30]:  # Ограничиваем количество строк
        c.drawString(50, y, line)
        y -= 15
        if y < 100:
            c.showPage()
            y = height - 50
    
    # Зашифрованный текст (если есть)
    if doc.encrypted_text:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Encrypted Text:")
        y -= 20
        c.setFont("Helvetica", 10)
        encrypted_lines = [doc.encrypted_text[i:i+80] for i in range(0, len(doc.encrypted_text), 80)]
        for line in encrypted_lines[:20]:
            c.drawString(50, y, line)
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 50
    
    # Электронная подпись
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Digital Signature:")
    y -= 20
    c.setFont("Helvetica", 10)
    
    # Создаем подпись (хеш документа)
    doc_hash = hashlib.sha256(f"{doc.id}{doc.original_text}{doc.created_at}".encode()).hexdigest()
    c.drawString(50, y, f"Hash: {doc_hash}")
    y -= 15
    c.drawString(50, y, f"Signed by: {user.username}")
    y -= 15
    c.drawString(50, y, f"Date: {doc.created_at}")
    
    c.save()
    buffer.seek(0)
    
    return Response(
        content=buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=document_{document_id}.pdf"}
    )

