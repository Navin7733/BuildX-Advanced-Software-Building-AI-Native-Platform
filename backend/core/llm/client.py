"""
OpenRouter LLM Client
Wraps LangChain's ChatOpenAI to use OpenRouter.
"""
import logging
from django.conf import settings
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def get_llm(model: str = None, temperature: float = 0.7, max_tokens: int = 4000) -> ChatOpenAI:
    """
    Get a LangChain ChatModel instance configured for OpenRouter.
    Defaults to LLM_DEFAULT_MODEL if not specified.
    """
    model_name = model or settings.LLM_DEFAULT_MODEL
    
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY is not set. LLM calls will fail.")
        
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=settings.OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://buildx.dev", # OpenRouter requires this
            "X-Title": "BuildX AI Platform",
        }
    )
