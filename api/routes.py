import logging
import uuid
import time
import httpx
import hashlib
import os
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException

from schemas.request_models import (
    ChatRequest, ChatResponse,
    RAGQueryRequest, RAGQueryResponse, ChunkResponse,
    UploadResponse, HealthResponse,
    GmailResponse, GmailSummarizeRequest,
    CodeGenerateRequest, CodeGenerateResponse,
    CodeCriticRequest, CodeCriticResponse,
    UserSignUpRequest, UserLoginRequest, GoogleAuthRequest
)
from config.settings import settings
from rag.chunking import process_document
from rag.vector_store import add_documents, get_retriever
from memory.memory_manager import handle_message, check_and_save_fact, get_context
from tools.gmail_tools import fetch_recent_emails, fetch_single_email
from memory.postgres_memory import (
    create_local_user,
    get_user_by_email,
    get_or_create_google_user
)

# Agents
from agents.orchestrator import run_orchestrator
from agents.rag_agent import run_rag_agent
from agents.gmail_agent import run_gmail_agent
from agents.code_generator import run_code_generator
from agents.code_critic import run_code_critic

logger = logging.getLogger(__name__)
router = APIRouter()


def format_friendly_error(e: Exception) -> str:
    err_str = str(e)
    if "credit_balance_exhausted" in err_str or "insufficient_quota" in err_str:
        return (
            "OpenAI Account Out of Credits ($0.00 remaining): Your OpenAI API key has no credits. "
            "Please add billing credits at https://platform.openai.com/settings/organization/billing/ "
            "or switch to a free provider in the top bar (such as Google Gemini, Groq, or OpenRouter)."
        )
    if "invalid_api_key" in err_str or "Incorrect API key provided" in err_str:
        return (
            "Invalid API Key: The key provided was rejected by the provider. "
            "If you entered a custom key in the top bar, please clear it to use your .env key, "
            "or make sure your OpenAI key starts with 'sk-'."
        )
    if "is not found for API version" in err_str or ("models/" in err_str and "is not found" in err_str) or "is no longer available" in err_str:
        return (
            "Gemini Model Retired or Not Found: Please use an active model like 'gemini-3.6-flash' in the Model input or .env."
        )
    if "Missing Authentication header" in err_str:
        return (
            "Missing API Key: Please provide an API key in the top bar or configure LLM_API_KEY in your .env file."
        )
    return err_str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")


@router.get("/config/llm")
async def get_llm_configuration():
    """
    Returns the auto-detected LLM provider, active model, and key presence from .env.
    Enables frontend to synchronize automatically.
    """
    cfg = settings.get_llm_config()
    return {
        "provider": cfg["provider"],
        "model": cfg["model"],
        "has_key": bool(cfg.get("api_key")),
        "temperature": cfg.get("temperature", 0.7),
        "max_tokens": cfg.get("max_tokens", 4096),
        "base_url": cfg.get("base_url")
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        context = get_context(session_id)
        facts_saved = check_and_save_fact(session_id, request.message)

        handle_message(session_id, "user", request.message)
        
        # Invoke orchestrator with dynamic settings, agent mode, and transient api key
        response = run_orchestrator(
            user_message=request.message,
            context=context,
            provider=request.provider,
            model_name=request.model,
            agent_mode=request.agent_mode,
            api_key=request.api_key
        )

        if facts_saved:
            response = f"Got it, I'll remember that.\n\n{response}"

        handle_message(session_id, "assistant", response)
        
        return ChatResponse(
            response=response,
            agent_used="orchestrator",
            session_id=session_id
        )

    except Exception as e:
        friendly = format_friendly_error(e)
        logger.error(f"Error in chat endpoint: {friendly}", exc_info=True)
        raise HTTPException(status_code=400, detail=friendly)


@router.post("/upload", response_model=UploadResponse)
@router.post("/rag/ingest", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        chunks = await process_document(file)
        add_documents(chunks)
        return UploadResponse(
            message="Document uploaded successfully",
            filename=file.filename,
            chunks_stored=len(chunks)
        )
    except Exception as e:
        logger.error(f"Error in upload_document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    try:
        # Retrieve chunks for reference
        retriever = get_retriever(top_k=request.top_k)
        docs = retriever.invoke(request.query)
        
        chunks = []
        sources = []
        for doc in docs:
            source = doc.metadata.get("source", "unknown")
            sources.append(source)
            chunks.append(ChunkResponse(
                content=doc.page_content,
                score=doc.metadata.get("score"),
                source=source
            ))
            
        # Get LLM generated answer with dynamic api key support
        answer = run_rag_agent(
            query=request.query,
            top_k=request.top_k,
            provider=request.provider,
            model_name=request.model,
            api_key=request.api_key
        )
        
        return RAGQueryResponse(
            answer=answer,
            sources=list(set(sources)),
            chunks=chunks
        )
    except Exception as e:
        friendly = format_friendly_error(e)
        logger.error(f"Error in rag_query: {friendly}", exc_info=True)
        raise HTTPException(status_code=400, detail=friendly)


@router.get("/gmail/list")
async def gmail_list(max_results: int = 10, label: str = "INBOX", q: Optional[str] = None):
    try:
        emails = fetch_recent_emails(max_results=max_results, label=label, q=q)
        if isinstance(emails, str) and emails.startswith("error"):
            raise HTTPException(status_code=500, detail=emails)
        return emails
    except Exception as e:
        logger.error(f"Error in gmail_list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gmail/get/{msg_id}")
async def gmail_get(msg_id: str):
    try:
        email = fetch_single_email(msg_id)
        if isinstance(email, str) and email.startswith("error"):
            raise HTTPException(status_code=500, detail=email)
        return email
    except Exception as e:
        logger.error(f"Error in gmail_get: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gmail/summary")
@router.post("/gmail/summarize")
async def gmail_summarize(request: Optional[GmailSummarizeRequest] = None):
    try:
        emails_to_summarize = None
        
        if request and request.email_ids:
            # Fetch specific email details
            emails_to_summarize = []
            for email_id in request.email_ids:
                email = fetch_single_email(email_id)
                if isinstance(email, dict):
                    emails_to_summarize.append(email)
        
        # Call the Gmail Agent summary pipeline with transient api key
        summary = run_gmail_agent(
            max_email=10,
            provider=request.provider if request else None,
            model_name=request.model if request else None,
            emails=emails_to_summarize,
            api_key=request.api_key if request else None
        )
        return GmailResponse(summary=summary)
    except Exception as e:
        friendly = format_friendly_error(e)
        logger.error(f"Error in gmail_summarize: {friendly}", exc_info=True)
        raise HTTPException(status_code=400, detail=friendly)


@router.post("/code/generate", response_model=CodeGenerateResponse)
async def code_generate(request: CodeGenerateRequest):
    try:
        code_output = run_code_generator(
            query=request.query,
            project_context=request.project_context,
            feedback=request.feedback,
            provider=request.provider,
            model_name=request.model,
            api_key=request.api_key
        )
        return CodeGenerateResponse(code=code_output)
    except Exception as e:
        friendly = format_friendly_error(e)
        logger.error(f"Error in code_generate: {friendly}", exc_info=True)
        raise HTTPException(status_code=400, detail=friendly)


@router.post("/code/critic", response_model=CodeCriticResponse)
async def code_critic(request: CodeCriticRequest):
    try:
        critic_output = run_code_critic(
            user_request=request.user_request,
            generated_code=request.generated_code,
            provider=request.provider,
            model_name=request.model,
            api_key=request.api_key
        )
        return CodeCriticResponse(
            approved=critic_output.get("approved", False),
            code=critic_output.get("code", request.generated_code),
            feedback=critic_output.get("feedback", "")
        )
    except Exception as e:
        friendly = format_friendly_error(e)
        logger.error(f"Error in code_critic: {friendly}", exc_info=True)
        raise HTTPException(status_code=400, detail=friendly)


@router.get("/agents/status")
async def agents_status():
    status = {}

    # Check Redis
    try:
        t0 = time.time()
        from memory.redis_memory import client as redis_client
        redis_client.ping()
        redis_latency = int((time.time() - t0) * 1000)
        status["redis"] = {"status": "connected", "latency": redis_latency}
    except Exception as e:
        status["redis"] = {"status": "error", "latency": 0, "error": str(e)}

    # Check Postgres
    try:
        t0 = time.time()
        from memory.postgres_memory import get_connection
        conn = get_connection()
        conn.close()
        pg_latency = int((time.time() - t0) * 1000)
        status["postgresql"] = {"status": "connected", "latency": pg_latency}
    except Exception as e:
        status["postgresql"] = {"status": "error", "latency": 0, "error": str(e)}

    # Check ChromaDB
    try:
        t0 = time.time()
        # Perform a basic check
        get_retriever(top_k=1)
        chroma_latency = int((time.time() - t0) * 1000)
        status["chromadb"] = {"status": "connected", "latency": chroma_latency}
    except Exception as e:
        status["chromadb"] = {"status": "error", "latency": 0, "error": str(e)}

    # Check Ollama only if configured as the provider
    if getattr(settings, "LLM_PROVIDER", "").lower() == "ollama":
        try:
            t0 = time.time()
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://localhost:11434", timeout=0.5)
                ollama_latency = int((time.time() - t0) * 1000)
                status["ollama"] = {"status": "connected" if resp.status_code == 200 else "disconnected", "latency": ollama_latency}
        except Exception:
            status["ollama"] = {"status": "disconnected", "latency": 0}
    else:
        status["ollama"] = {"status": "disconnected", "latency": 0}

    # Backend Agents status (idle states)
    status["orchestrator"] = {"status": "idle", "latency": 45, "last_action": "Listening for prompts"}
    status["rag_agent"] = {"status": "idle", "latency": 80, "last_action": "Ready to query indexes"}
    status["gmail_agent"] = {"status": "idle", "latency": 150, "last_action": "Monitoring messages"}
    status["code_generator"] = {"status": "idle", "latency": 110, "last_action": "Synthesizing code"}
    status["code_critic"] = {"status": "idle", "latency": 130, "last_action": "Evaluating scripts"}

    # Cloud LLM endpoints presence based on active settings
    cfg = settings.get_llm_config()
    detected_prov = cfg["provider"]
    has_key = bool(cfg.get("api_key"))

    status["openai"] = {
        "status": "connected" if (settings.OPENAI_API_KEY or (has_key and detected_prov == "openai")) else "disconnected",
        "latency": 150
    }
    status["anthropic"] = {
        "status": "connected" if (settings.ANTHROPIC_API_KEY or (has_key and detected_prov == "anthropic")) else "disconnected",
        "latency": 180
    }
    status["gemini"] = {
        "status": "connected" if (settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY or (has_key and detected_prov == "google")) else "disconnected",
        "latency": 220
    }
    status["groq"] = {
        "status": "connected" if (settings.GROQ_API_KEY or (has_key and detected_prov == "groq")) else "disconnected",
        "latency": 120
    }
    base_url = cfg.get("base_url") or ""
    status["openrouter"] = {
        "status": "connected" if (settings.OPENROUTER_API_KEY or (has_key and detected_prov == "openrouter") or "openrouter.ai" in base_url) else "disconnected",
        "latency": 160
    }

    return status


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    try:
        salt_hex, key_hex = stored_password.split(':')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return new_key == key
    except Exception:
        return False


@router.post("/auth/signup")
async def signup(request: UserSignUpRequest):
    try:
        # Check if PostgreSQL is available
        from memory.postgres_memory import check_postgres_availability
        if not check_postgres_availability():
            raise HTTPException(
                status_code=503, 
                detail="Authentication service is unavailable. PostgreSQL database is not connected. Please contact the administrator or run the app without authentication features."
            )
        
        existing = get_user_by_email(request.email)
        if existing:
            raise HTTPException(status_code=400, detail="A user with this email already exists.")
        
        pw_hash = hash_password(request.password)
        user = create_local_user(request.email, pw_hash, request.name)
        return user
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in signup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/login")
async def login_local(request: UserLoginRequest):
    try:
        # Check if PostgreSQL is available
        from memory.postgres_memory import check_postgres_availability
        if not check_postgres_availability():
            raise HTTPException(
                status_code=503, 
                detail="Authentication service is unavailable. PostgreSQL database is not connected."
            )
        
        user = get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        
        if user["auth_provider"] != "local":
            raise HTTPException(status_code=400, detail=f"Please sign in using your {user['auth_provider']} account.")
            
        if not verify_password(user["password_hash"], request.password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
            
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user["picture"],
            "auth_provider": user["auth_provider"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/google")
async def google_auth(request: GoogleAuthRequest):
    try:
        # Check if PostgreSQL is available
        from memory.postgres_memory import check_postgres_availability
        if not check_postgres_availability():
            raise HTTPException(
                status_code=503, 
                detail="Authentication service is unavailable. PostgreSQL database is not connected."
            )
        
        user = get_or_create_google_user(request.email, request.name, request.picture)
        return user
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in google_auth: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))