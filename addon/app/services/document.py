import uuid
import logging
from datetime import datetime, UTC
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pdf2image import convert_from_path
from PIL import Image

from ..db import Document as DocumentModel
from ..models import Document
from ..settings import Settings, get_settings

_LOGGER = logging.getLogger('uvicorn.error')


def get_document_folder(settings: Settings, folder_name: str) -> Path:
    """Get the Path object for a document's folder."""
    return settings.docs_path / folder_name


def generate_thumbnail(pdf_path: Path, thumbnail_path: Path) -> None:
    """Generate a thumbnail from the first page of a PDF."""
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
        if images:
            thumbnail = images[0]
            thumbnail.thumbnail((400, 533), Image.Resampling.LANCZOS)
            thumbnail.save(thumbnail_path, "PNG", optimize=True)
    except Exception as e:
        _LOGGER.error(
            f"Failed to generate thumbnail for PDF {pdf_path}: {e}",
            exc_info=True
        )


class DocumentService:
    @staticmethod
    async def ingest_document(
        file: UploadFile, db: AsyncSession, settings: Settings | None = None
    ) -> Document:
        """Ingest a document: create DB row, save PDF, and generate thumbnail."""
        if settings is None:
            settings = get_settings()
        
        # Generate folder name
        folder_name = str(uuid.uuid4())
        document_folder = get_document_folder(settings, folder_name)
        document_folder.mkdir(parents=True, exist_ok=True)

        # Save the PDF
        source_path = document_folder / "source.pdf"
        with source_path.open("wb") as f:
            content = await file.read()
            f.write(content)

        # Generate thumbnail
        thumbnail_path = document_folder / "thumbnail.png"
        generate_thumbnail(source_path, thumbnail_path)

        # Create DB record
        db_document = DocumentModel(
            folder_name=folder_name,
            original_filename=file.filename or "unknown.pdf",
            display_name=None,
            mime_type=file.content_type or "application/pdf",
            created_at=datetime.now(UTC),
        )
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)

        return Document.model_validate(db_document)

    @staticmethod
    async def get_documents(db: AsyncSession) -> list[Document]:
        """Get all documents."""
        result = await db.execute(select(DocumentModel))
        documents = result.scalars().all()
        return [Document.model_validate(doc) for doc in documents]

    @staticmethod
    async def get_document(
        db: AsyncSession, document_id: int
    ) -> Document | None:
        """Get a document by ID."""
        result = await db.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        document = result.scalar_one_or_none()
        if document:
            return Document.model_validate(document)
        return None

    @staticmethod
    async def delete_document(
        db: AsyncSession, document_id: int, settings: Settings | None = None
    ) -> None:
        """Delete a document and its folder."""
        if settings is None:
            settings = get_settings()
        
        result = await db.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        document = result.scalar_one_or_none()
        if document:
            # Delete the folder
            document_folder = get_document_folder(settings, document.folder_name)
            if document_folder.exists():
                import shutil
                shutil.rmtree(document_folder)

            # Delete DB record
            await db.delete(document)
            await db.commit()

