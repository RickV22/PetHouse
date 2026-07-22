from fastapi import APIRouter, Depends, HTTPException, Query, status
import traceback
from app.ai.config.loader import AIConfig
from app.ai.domain.exceptions import SQLValidationError
from app.ai.infrastructure.exceptions import (
    AIProviderAuthError,
    AIProviderConnectionError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    MCPConnectionError,
    MCPExecutionError,
    MCPInvalidResponseError,
    MCPTimeoutError,
)
from app.ai.presentation.dependencies.ai_dependencies import (
    _load_config,
    get_admin_assistant_use_case,
    require_ai_assistant,
)
from app.ai.presentation.dto.ask_request import AskRequest
from app.ai.presentation.dto.ask_response import AskResponse
from app.ai.presentation.dto.history_response import HistoryResponse
from app.ai.presentation.mappers.ai_mapper import (
    to_ask_response,
    to_history_response,
)
from app.ai.use_cases.admin_assistant import AdminAssistantUseCase
from app.models.user_model import User

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])


@router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    current_user: User = Depends(require_ai_assistant),
    use_case: AdminAssistantUseCase = Depends(get_admin_assistant_use_case),
    config: AIConfig = Depends(_load_config),
) -> AskResponse:
    question = body.question

    if not question or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question must not be empty",
        )

    if len(question) > config.max_question_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question exceeds maximum length of {config.max_question_length} characters",
        )

    try:
        result = await use_case.ask(question, str(current_user.id))
    except SQLValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AIProviderTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"AI provider timed out: {e}",
        )
    except AIProviderAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"AI provider authentication failed: {e}",
        )
    except (AIProviderRateLimitError, AIProviderConnectionError, AIProviderError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except (MCPTimeoutError, MCPConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e),
        )
    except (MCPExecutionError, MCPInvalidResponseError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    
    except Exception as e:
        print("ERROR REAL:", repr(e))
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )
    

    return to_ask_response(result)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=20, ge=1),
    current_user: User = Depends(require_ai_assistant),
    use_case: AdminAssistantUseCase = Depends(get_admin_assistant_use_case),
) -> HistoryResponse:
    try:
        interactions = await use_case.get_history(
            str(current_user.id), limit=limit
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )

    return to_history_response(interactions)
