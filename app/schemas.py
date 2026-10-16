from pydantic import BaseModel, Field, field_validator

from .config import settings

# ---------- Requests ----------


class BaseTextRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Input text (1–5000 characters).",
    )

    @field_validator("text")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty or whitespace-only.")
        return v.strip()


class GenerateRequest(BaseTextRequest):
    model: str = Field(default=settings.allowed_models[0])
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    @field_validator("model")
    @classmethod
    def _valid_model(cls, v: str) -> str:
        if v not in settings.allowed_models:
            raise ValueError(f"model must be one of {list(settings.allowed_models)}.")
        return v


class SummarizeRequest(GenerateRequest):
    max_words: int = Field(default=150, ge=50, le=500)


# ---------- Responses ----------


class ModelResponse(BaseModel):
    endpoint: str
    user: str
    input_text: str
    output_text: str
    model_used: str
    processing_time_ms: float
    success: bool
