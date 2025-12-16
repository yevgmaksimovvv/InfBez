"""
Роутер документов
Тонкий слой HTTP эндпоинтов, бизнес-логика в DocumentService
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import logging

from backend.core.database import get_db
from backend.dependencies import get_current_user
from backend.models import User
from backend.schemas import CreateDocumentRequest
from backend.services import DocumentService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create")
async def create_document(
    request: CreateDocumentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание документа"""
    try:
        doc_service = DocumentService()
        doc = doc_service.create_document(
            user_id=current_user.id,
            original_text=request.original_text,
            encrypted_text=request.encrypted_text,
            algorithm=request.algorithm,
            db=db
        )

        return {"id": doc.id, "message": "Document created"}

    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create document")


@router.get("/{document_id}/pdf")
async def export_to_pdf(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Экспорт документа в PDF с цифровой подписью"""
    try:
        doc_service = DocumentService()

        # Получение документа из базы данных
        doc = doc_service.get_document(document_id, db)

        # Проверка прав доступа пользователя к документу
        doc_service.check_access(doc, current_user)

        # Генерация документа в формате PDF
        pdf_content = doc_service.generate_pdf(doc, current_user)

        logger.info(f"PDF generated for document {document_id} by user {current_user.username}")

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=document_{document_id}.pdf"}
        )

    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 403, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export PDF")


@router.get("/")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка документов пользователя"""
    try:
        doc_service = DocumentService()
        documents = doc_service.list_documents(current_user, db)

        return {
            "documents": [
                {
                    "id": d.id,
                    "algorithm": d.algorithm,
                    "created_at": d.created_at.isoformat(),
                    "user_id": d.user_id
                }
                for d in documents
            ]
        }

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление документа"""
    try:
        doc_service = DocumentService()
        doc_service.delete_document(document_id, current_user, db)

        return {"message": "Document deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")
