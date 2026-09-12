from langchain.vectorstores import Chroma
from rag.embeddings import get_embeddings
from config.settings import settings


def add_documents(chunks):
    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=settings.CHROMA_COLLECTION_NAME,
        persist_directory=settings.CHROMA_PERSIST_DIR
    )

def get_retriever(top_k = 4):
    vectorstore = Chroma(
        embedding_function=get_embeddings(),
        collection_name=settings.CHROMA_COLLECTION_NAME,
        persist_directory=settings.CHROMA_PERSIST_DIR
    ) # "hey ChromaDB, find me the 4 most relevant pieces for this query" query provided in rag_agent
    retriever = vectorstore.as_retriever(
        search_kwargs = {"k":top_k}
    )
    return retriever