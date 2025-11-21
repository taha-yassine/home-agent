from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import ModelConfig as ModelConfigModel
from ..models import ModelConfig, ModelConfigCreate, ModelConfigUpdate, ModelConfigMap


class ModelConfigService:
    @staticmethod
    async def get_model_config(
        db: AsyncSession, role: str
    ) -> ModelConfig | None:
        """Get model configuration for a specific role."""
        result = await db.execute(
            select(ModelConfigModel).where(ModelConfigModel.role == role)
        )
        config = result.scalar_one_or_none()
        if config:
            return ModelConfig.model_validate(config)
        return None

    @staticmethod
    async def get_all_model_configs(db: AsyncSession) -> ModelConfigMap:
        """Get all model configurations as a map."""
        result = await db.execute(select(ModelConfigModel))
        configs = result.scalars().all()
        
        config_map = {}
        for config in configs:
            validated = ModelConfig.model_validate(config)
            if config.role == "main":
                config_map["main"] = validated
            elif config.role == "document_qa":
                config_map["document_qa"] = validated
        
        return ModelConfigMap(**config_map)

    @staticmethod
    async def create_or_update_model_config(
        db: AsyncSession, role: str, config_data: ModelConfigCreate | ModelConfigUpdate
    ) -> ModelConfig:
        """Create or update model configuration for a role."""
        result = await db.execute(
            select(ModelConfigModel).where(ModelConfigModel.role == role)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            update_data = config_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(existing, key, value)
            await db.commit()
            await db.refresh(existing)
            return ModelConfig.model_validate(existing)
        else:
            # Create new
            if isinstance(config_data, ModelConfigCreate):
                db_config = ModelConfigModel(
                    role=role,
                    backend_id=config_data.backend_id,
                    model=config_data.model,
                )
            else:
                # ModelConfigUpdate - need backend_id and model
                if config_data.backend_id is None or config_data.model is None:
                    raise ValueError("backend_id and model are required for new configs")
                db_config = ModelConfigModel(
                    role=role,
                    backend_id=config_data.backend_id,
                    model=config_data.model,
                )
            db.add(db_config)
            await db.commit()
            await db.refresh(db_config)
            return ModelConfig.model_validate(db_config)

    @staticmethod
    async def delete_model_config(db: AsyncSession, role: str) -> None:
        """Delete model configuration for a role."""
        result = await db.execute(
            select(ModelConfigModel).where(ModelConfigModel.role == role)
        )
        config = result.scalar_one_or_none()
        if config:
            await db.delete(config)
            await db.commit()

