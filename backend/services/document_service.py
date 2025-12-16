"""
Сервис для работы с документами и генерации PDF
"""
import logging
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from algorithms.streebog.streebog import streebog_512
from backend.models import Document, User, UserRole

logger = logging.getLogger(__name__)


class DocumentService:
    """Сервис для работы с документами"""

    @staticmethod
    def create_document(
        user_id: int,
        original_text: str,
        encrypted_text: str,
        algorithm: str,
        db: Session
    ) -> Document:
        """
        Создание документа

        Args:
            user_id: ID пользователя
            original_text: Оригинальный текст
            encrypted_text: Зашифрованный текст
            algorithm: Алгоритм шифрования
            db: Database session

        Returns:
            Document: Созданный документ
        """
        doc = Document(
            user_id=user_id,
            original_text=original_text,
            encrypted_text=encrypted_text,
            algorithm=algorithm
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info(f"Document {doc.id} created by user {user_id}")

        return doc

    @staticmethod
    def generate_pdf(doc: Document, user: User) -> bytes:
        """
        Генерация PDF документа с цифровой подписью

        Args:
            doc: Документ
            user: Пользователь

        Returns:
            bytes: PDF содержимое
        """
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

        # Разбиение текста на строки
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

        for line in text_lines[:30]:
            c.drawString(50, y, line)
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 50

        # Зашифрованный текст (если есть)
        if doc.encrypted_text:
            y -= 30
            if y < 100:
                c.showPage()
                y = height - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Encrypted Text:")
            y -= 20
            c.setFont("Helvetica", 10)
            encrypted_lines = [
                doc.encrypted_text[i:i + 80]
                for i in range(0, len(doc.encrypted_text), 80)
            ]
            for line in encrypted_lines[:20]:
                c.drawString(50, y, line)
                y -= 15
                if y < 100:
                    c.showPage()
                    y = height - 50

        # Цифровая подпись (используя Streebog-512)
        y -= 30
        if y < 100:
            c.showPage()
            y = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Digital Signature (GOST Streebog-512):")
        y -= 20
        c.setFont("Helvetica", 10)

        # Создаем подпись
        signature_data = f"{doc.id}{doc.original_text}{doc.created_at}".encode('utf-8')
        doc_hash = streebog_512(signature_data).hex()

        # Выводим хеш по частям
        hash_lines = [doc_hash[i:i + 64] for i in range(0, len(doc_hash), 64)]
        for hash_line in hash_lines:
            c.drawString(50, y, hash_line)
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 50

        y -= 10
        c.drawString(50, y, f"Signed by: {user.username}")
        y -= 15
        c.drawString(50, y, f"Date: {doc.created_at}")

        c.save()
        buffer.seek(0)

        logger.info(f"PDF generated for document {doc.id}")

        return buffer.read()

    @staticmethod
    def get_document(document_id: int, db: Session) -> Document:
        """
        Получение документа по ID

        Args:
            document_id: ID документа
            db: Database session

        Returns:
            Document: Документ

        Raises:
            ValueError: Если документ не найден
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError("Document not found")
        return doc

    @staticmethod
    def check_access(doc: Document, user: User) -> None:
        """
        Проверка прав доступа к документу

        Args:
            doc: Документ
            user: Пользователь

        Raises:
            ValueError: Если нет прав доступа
        """
        if doc.user_id != user.id and user.role != UserRole.ADMIN:
            raise ValueError("Not enough permissions")

    @staticmethod
    def list_documents(user: User, db: Session) -> list[Document]:
        """
        Получение списка документов пользователя

        Args:
            user: Пользователь
            db: Database session

        Returns:
            list: Список документов
        """
        if user.role == UserRole.ADMIN:
            documents = db.query(Document).all()
        else:
            documents = db.query(Document).filter(Document.user_id == user.id).all()

        return documents

    @staticmethod
    def delete_document(document_id: int, user: User, db: Session) -> None:
        """
        Удаление документа

        Args:
            document_id: ID документа
            user: Пользователь
            db: Database session

        Raises:
            ValueError: Если документ не найден или нет прав
        """
        doc = DocumentService.get_document(document_id, db)
        DocumentService.check_access(doc, user)

        db.delete(doc)
        db.commit()

        logger.info(f"Document {document_id} deleted by user {user.username}")
