"""Q&A 接口"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database import get_db
from src.models.user import User
from src.schemas.qa import QARequest, QAResponse
from src.services.qa_service import ask_question
from src.api.deps import get_current_user

router = APIRouter(prefix="/qa", tags=["问答"])


@router.post("/ask", response_model=QAResponse)
async def api_ask(
    req: QARequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await ask_question(
        question=req.question,
        kb_ids=req.kb_ids or [],
        model_name=req.model,
        conversation_id=req.conversation_id,
        user_id=user.id,
        db=db,
        stream=False,
    )
    return result


@router.post("/ask/stream")
async def api_ask_stream(
    req: QARequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await ask_question(
        question=req.question,
        kb_ids=req.kb_ids or [],
        model_name=req.model,
        conversation_id=req.conversation_id,
        user_id=user.id,
        db=db,
        stream=True,
    )
    generator = result["stream_generator"]
    return StreamingResponse(generator, media_type="text/event-stream")
