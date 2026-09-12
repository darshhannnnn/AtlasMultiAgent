"""
RAG Agent with dynamic LLM support
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from llm_provider.llm_initializer import get_llm_model
from rag.vector_store import get_retriever
from typing import Optional


def run_rag_agent(
    query: str,
    top_k: int = 4,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Execute the RAG agent query using the selected LLM provider and model.
    """
    try:
        model = get_llm_model(
            provider=provider,
            model=model_name,
            api_key=api_key,
            temperature=0,
            max_tokens=2048,
        )

        def format_chunks(chunks):
            return "\n\n".join(chunk.page_content for chunk in chunks)

        retriever = get_retriever(top_k=top_k)
        context = format_chunks(retriever.invoke(query))

        prompt_template = ChatPromptTemplate.from_template("""
            Use the following context to answer the question.
            If the answer is not in the context, say "Insufficient context".
            
            Context : {context}
            Question : {question}
        """)

        chain = prompt_template | model | StrOutputParser()
        return chain.invoke({"context": context, "question": query})
    except Exception as e:
        return f"Error occurred while running rag agent {e}"
