import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...dependencies import get_db, get_openai_client, get_hass_client
from ...models import (
    Backend,
    BackendCreate,
    BackendUpdate,
    ConversationList,
    Span,
    ConversationNeighbors,
    ConversationTracesResponse,
    Document,
    ModelConfig,
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigMap,
)
from ...services import (
    ConversationService,
    BackendService,
    TraceService,
    ToolService,
    DocumentService,
    ModelConfigService,
)
from ...settings import get_settings
from ...services.document import get_document_folder

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/conversations", response_model=ConversationList)
async def get_conversations(
    db: AsyncSession = Depends(get_db),
) -> ConversationList:
    """Get all conversations."""
    return await ConversationService.get_conversations(db)


@router.get("/traces/{trace_id}/spans", response_model=list[Span])
async def get_spans(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[Span]:
    """Get all spans for a given trace."""
    return await TraceService.get_spans_by_trace_id(db, trace_id)





@router.get("/conversations/{group_id}/traces", response_model=ConversationTracesResponse)
async def get_traces_by_group(
    group_id: str, db: AsyncSession = Depends(get_db)
) -> ConversationTracesResponse:
    """Get all traces and their spans for a given conversation group."""
    traces = await TraceService.get_traces_with_spans_by_group_id(db, group_id)
    return ConversationTracesResponse(group_id=group_id, traces=traces)


@router.get("/conversations/{group_id}/neighbors", response_model=ConversationNeighbors)
async def get_group_neighbors(
    group_id: str, db: AsyncSession = Depends(get_db)
) -> ConversationNeighbors:
    """Get the neighbors for a given conversation group."""
    return await TraceService.get_group_neighbors(db, group_id)


@router.get("/backends", response_model=list[Backend])
async def get_backends(db: AsyncSession = Depends(get_db)) -> list[Backend]:
    """Get all backends."""
    return await BackendService.get_backends(db, mask_key=True)


@router.post("/backends", response_model=Backend)
async def create_backend(
    backend_create: BackendCreate, db: AsyncSession = Depends(get_db)
) -> Backend:
    """Create a new backend."""
    return await BackendService.create_backend(db, backend_create)


@router.put("/backends/{backend_id}", response_model=Backend)
async def update_backend(
    backend_id: int,
    backend_update: BackendUpdate,
    db: AsyncSession = Depends(get_db),
) -> Backend:
    """Update a backend."""
    return await BackendService.update_backend(db, backend_id, backend_update)


@router.delete("/backends/{backend_id}", status_code=204)
async def delete_backend(
    backend_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a backend."""
    await BackendService.delete_backend(db, backend_id)


@router.get("/models")
async def get_models(
    backend_id: int | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all models from a backend. backend_id is required."""
    if not backend_id:
        raise HTTPException(status_code=400, detail="backend_id is required")
    
    backend = await BackendService.get_backend(db, backend_id, mask_key=False)
    if not backend:
        raise HTTPException(status_code=404, detail="Backend not found")

    # TODO: Use a common client for all backends initialized at startup
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{backend.url}/models")
            response.raise_for_status()
            payload = response.json()

            # For OpenRouter, only keep models supporting tool calls
            try:
                if "openrouter" in (backend.url or "").lower():
                    data = payload.get("data") if isinstance(payload, dict) else None
                    if isinstance(data, list):
                        filtered = [
                            m
                            for m in data
                            if isinstance(m, dict)
                            and isinstance(m.get("supported_parameters"), list)
                            and "tools" in m.get("supported_parameters", [])
                        ]
                        payload["data"] = filtered
            except Exception:
                # If filtering fails, fall back to unfiltered payload
                pass

            return payload
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500, detail=f"Error connecting to backend: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, detail=exc.response.text
            )

@router.get("/tools")
async def get_tools():
    """Get all tools."""
    return ToolService.get_tools()


@router.get("/model-config", response_model=ModelConfigMap)
async def get_model_config(
    db: AsyncSession = Depends(get_db),
) -> ModelConfigMap:
    """Get all model configurations."""
    return await ModelConfigService.get_all_model_configs(db)


@router.put("/model-config/{role}", response_model=ModelConfig)
async def update_model_config(
    role: str,
    config_update: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> ModelConfig:
    """Update model configuration for a role."""
    return await ModelConfigService.create_or_update_model_config(
        db, role, config_update
    )


@router.post("/model-config/{role}", response_model=ModelConfig)
async def create_model_config(
    role: str,
    config_create: ModelConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> ModelConfig:
    """Create model configuration for a role."""
    return await ModelConfigService.create_or_update_model_config(
        db, role, config_create
    )


@router.delete("/model-config/{role}", status_code=204)
async def delete_model_config(
    role: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete model configuration for a role."""
    await ModelConfigService.delete_model_config(db, role)


@router.post("/documents", response_model=Document)
async def create_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new document."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    settings = get_settings()
    return await DocumentService.ingest_document(file, db, settings)


@router.get("/documents", response_model=list[Document])
async def get_documents(db: AsyncSession = Depends(get_db)) -> list[Document]:
    """Get all documents."""
    return await DocumentService.get_documents(db)


@router.get("/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Get a document by ID."""
    document = await DocumentService.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document."""
    settings = get_settings()
    await DocumentService.delete_document(db, document_id, settings)


@router.get("/documents/{document_id}/thumbnail")
async def get_document_thumbnail(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a document's thumbnail."""
    document = await DocumentService.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    settings = get_settings()
    thumbnail_path = get_document_folder(settings, document.folder_name) / "thumbnail.png"
    
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(thumbnail_path, media_type="image/png")