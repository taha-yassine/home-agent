import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Backend as BackendModel
from ..models import Backend, BackendCreate, BackendUpdate

_LOGGER = logging.getLogger('uvicorn.error')

def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "********"
    return f"{api_key[:4]}...{api_key[-4:]}"


class BackendService:
    @staticmethod
    async def get_backends(db: AsyncSession, mask_key: bool = True) -> list[Backend]:
        """Get all backends from the database."""
        result = await db.execute(select(BackendModel))
        backends = result.scalars().all()
        validated_backends = []
        for backend in backends:
            backend_model = Backend.model_validate(backend)
            if mask_key:
                backend_model.api_key = mask_api_key(backend_model.api_key)
            validated_backends.append(backend_model)
        return validated_backends

    @staticmethod
    async def get_backend(
        db: AsyncSession, backend_id: int, mask_key: bool = True
    ) -> Backend | None:
        """Get a backend from the database."""
        result = await db.execute(select(BackendModel).where(BackendModel.id == backend_id))
        backend = result.scalar_one_or_none()
        if backend:
            backend_model = Backend.model_validate(backend)
            if mask_key:
                backend_model.api_key = mask_api_key(backend_model.api_key)
            return backend_model
        return None

    @staticmethod
    async def create_backend(
        db: AsyncSession, backend_create: BackendCreate
    ) -> Backend:
        """Create a new backend."""
        db_backend = BackendModel(**backend_create.model_dump())

        db.add(db_backend)
        await db.commit()
        await db.refresh(db_backend)
        validated_backend = Backend.model_validate(db_backend)
        validated_backend.api_key = mask_api_key(validated_backend.api_key)
        return validated_backend

    @staticmethod
    async def update_backend(
        db: AsyncSession, backend_id: int, backend_update: BackendUpdate
    ) -> Backend:
        """Update a backend."""
        update_data = backend_update.model_dump(exclude_unset=True)
        if not update_data:
            # No fields to update
            result = await db.execute(
                select(BackendModel).where(BackendModel.id == backend_id)
            )
            backend = result.scalar_one()
            return Backend.model_validate(backend)

        await db.execute(
            update(BackendModel)
            .where(BackendModel.id == backend_id)
            .values(**update_data)
        )
        await db.commit()

        result = await db.execute(
            select(BackendModel).where(BackendModel.id == backend_id)
        )
        updated_backend = result.scalar_one()

        validated_backend = Backend.model_validate(updated_backend)
        validated_backend.api_key = mask_api_key(validated_backend.api_key)
        return validated_backend

    @staticmethod
    async def delete_backend(db: AsyncSession, backend_id: int) -> None:
        """Delete a backend."""
        result = await db.execute(
            select(BackendModel).where(BackendModel.id == backend_id)
        )
        backend = result.scalar_one_or_none()
        if backend:
            await db.delete(backend)
            await db.commit()
