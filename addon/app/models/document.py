from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class Document(BaseModel):
    id: int
    folder_name: str = Field(..., description="Unique folder name for the document")
    original_filename: str = Field(..., description="Original filename of the uploaded file")
    display_name: str | None = Field(None, description="User-friendly display name")
    mime_type: str = Field(..., description="MIME type of the document")
    created_at: datetime = Field(..., description="When the document was created")

    model_config = ConfigDict(from_attributes=True)

