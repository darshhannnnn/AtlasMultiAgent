import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config.settings import settings

# Logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready Multi-Agent AI System with RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    logger.info(f"Starting {settings.APP_NAME}")
    try:
        from memory.postgres_memory import init_user_table
        init_user_table()
    except Exception as e:
        logger.error(f"Failed to initialize user database: {e}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down...")
