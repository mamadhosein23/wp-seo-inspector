from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from backend.app.core.security import validate_target_url
from backend.app.engine.pipeline import AuditPipeline

router = APIRouter()

@router.get("/stream")
async def stream_audit(url: str = Depends(validate_target_url)):
    pipeline = AuditPipeline()

    async def event_generator():
        async for chunk in pipeline.execute_stream(url):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
