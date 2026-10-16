import logging
import time

from fastapi import Depends, FastAPI

from .config import settings
from .schemas import (
    GenerateRequest,
    ModelResponse,
    SummarizeRequest,
)
from .services.fake_llm import FakeLLMClient
from .services.llm import OpenAILLMClient
from .utils.logging_config import setup_logging
from .utils.rate_limit import limiter, rate_limit_dependency
from .utils.security import verify_api_key

setup_logging()

logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info(f"{settings.app_name} starting up")
logger.info("=" * 60)

if settings.openai_base_url == "fake":
    logger.info("Using FakeLLMClient (offline mode)")
    llm = FakeLLMClient()
else:
    llm = OpenAILLMClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

app = FastAPI()


@app.post("/summarize", tags=["Text"])
async def summarize(
    req: SummarizeRequest,
    user: str = Depends(rate_limit_dependency),
) -> ModelResponse:
    logger.info(f"summarize | user={user} | model={req.model} | len={len(req.text)}")
    start = time.perf_counter()

    success = True
    out = ""
    
    try:
        out = llm.chat(
            req.text,
            req.model,
            req.temperature,
            system_prompt=f"Summarize the user's text in less than or equal to {req.max_words} words.",
        )
    except Exception as e:  # noqa: BLE001
        success = False
        out = f"Error: {e}"

    return ModelResponse(
        endpoint="/summarize",
        user=user,
        input_text=req.text,
        output_text=out,
        model_used=req.model,
        processing_time_ms=round((time.perf_counter() - start) * 1000, 2),
        success=success,
    )


@app.post("/generate", tags=["Text"])
async def generate(
    req: GenerateRequest,
    user: str = Depends(rate_limit_dependency),
) -> ModelResponse:
    logger.info(
        f"generate | user={user} | model={req.model} | temp={req.temperature:.2f}"
    )
    start = time.perf_counter()

    success = True
    out = ""

    try:
        out = llm.chat(req.text, req.model, req.temperature)
    except Exception as e:  # noqa: BLE001
        success = False
        out = f"Error: {e}"

    return ModelResponse(
        endpoint="/generate",
        user=user,
        input_text=req.text,
        output_text=out,
        model_used=req.model,
        processing_time_ms=round((time.perf_counter() - start) * 1000, 2),
        success=success,
    )


@app.get("/usage")
async def usage(user_id: str = Depends(verify_api_key)) -> dict:
    resolved_limit = settings.rate_limits.get(user_id, settings.rate_limit_per_minute)
    return limiter.status(user_id, limit=resolved_limit)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/usage",
            "/summarize",
            "/generate",
        ],
    }
