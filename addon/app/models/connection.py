from pydantic import BaseModel, Field, ConfigDict


class ConnectionBase(BaseModel):
    url: str = Field(..., description="URL of the backend")
    api_key: str | None = Field(None, description="API key for the backend")
    backend: str = Field(
        ..., description="Type of the backend (e.g., vLLM, llama.cpp)"
    )


class ConnectionCreate(ConnectionBase):
    pass


class ConnectionUpdate(BaseModel):
    url: str | None = None
    api_key: str | None = None
    backend: str | None = None
    model: str | None = None


class Connection(ConnectionBase):
    id: int
    model: str | None = Field(None, description="The model selected for the backend")
    is_active: bool = Field(False, description="Whether the backend is active")

    model_config = ConfigDict(from_attributes=True)