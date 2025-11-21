from pydantic import BaseModel, Field, ConfigDict


class ModelConfigBase(BaseModel):
    role: str = Field(..., description="Role name (e.g., 'main', 'document_qa')")
    backend_id: int = Field(..., description="ID of the backend to use")
    model: str = Field(..., description="Model name to use for this role")


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    backend_id: int | None = None
    model: str | None = None


class ModelConfig(ModelConfigBase):
    model_config = ConfigDict(from_attributes=True)


class ModelConfigMap(BaseModel):
    """Map of role names to model configurations."""
    main: ModelConfig | None = Field(default=None)
    document_qa: ModelConfig | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)

