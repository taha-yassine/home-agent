from pydantic import BaseModel, Field, ConfigDict


class BackendBase(BaseModel):
    name: str | None = Field(None, description="Name of the backend")
    url: str = Field(..., description="URL of the backend")
    api_key: str | None = Field(None, description="API key for the backend")
    type: str = Field(
        ..., description="Type of the backend (e.g., vLLM, llama.cpp)"
    )


class BackendCreate(BackendBase):
    pass


class BackendUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    api_key: str | None = None
    type: str | None = None


class Backend(BackendBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


