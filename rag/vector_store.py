import logging
from typing import Optional
from langchain_community.vectorstores import Chroma
from rag.embeddings import get_embeddings, get_embedding_provider_tag
from config.settings import settings

logger = logging.getLogger(__name__)


def get_collection_name(provider: Optional[str] = None, api_key: Optional[str] = None) -> str:
    tag = get_embedding_provider_tag(provider=provider, api_key=api_key)
    base_name = settings.CHROMA_COLLECTION_NAME or "documents"
    return f"{base_name}_{tag}"


def add_documents(chunks, provider: Optional[str] = None, api_key: Optional[str] = None):
    """
    Index document chunks into ChromaDB under the collection matching the active embedding model.
    """
    if not chunks:
        logger.warning("No chunks provided to add_documents.")
        return

    embedding = get_embeddings(provider=provider, api_key=api_key)
    col_name = get_collection_name(provider=provider, api_key=api_key)
    
    logger.info(f"Adding {len(chunks)} chunks to collection '{col_name}' in '{settings.CHROMA_PERSIST_DIR}'")
    Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        collection_name=col_name,
        persist_directory=settings.CHROMA_PERSIST_DIR
    )


def get_retriever(top_k: int = 4, provider: Optional[str] = None, api_key: Optional[str] = None):
    """
    Return a Chroma retriever targeting the active embedding model's collection.
    """
    embedding = get_embeddings(provider=provider, api_key=api_key)
    col_name = get_collection_name(provider=provider, api_key=api_key)

    vectorstore = Chroma(
        embedding_function=embedding,
        collection_name=col_name,
        persist_directory=settings.CHROMA_PERSIST_DIR
    )
    return vectorstore.as_retriever(search_kwargs={"k": top_k})