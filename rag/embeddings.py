from langchain_openai import OpenAIEmbeddings
from config.settings import settings

def get_embeddings():
    api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
    base_url = settings.LLM_BASE_URL or settings.BASE_URL
    kwargs = {
        "model": settings.EMBEDDING_MODEL,
        "openai_api_key": api_key,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAIEmbeddings(**kwargs)