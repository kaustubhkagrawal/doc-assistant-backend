from dotenv import load_dotenv

load_dotenv()

import logging
import os
import uvicorn
import sys

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware


from typing import cast

from alembic.config import Config
import alembic.config
from alembic import script
from alembic.runtime import migration
from sqlalchemy.engine import create_engine, Engine


from llama_index.node_parser.text.utils import split_by_sentence_tokenizer

from app.core.config import settings,AppEnvironment
from app.api.api import api_router
from app.db.wait_for_db import check_database_connection
from app.db.pg_vector import get_vector_store_singleton, CustomPGVectorStore
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

def check_current_head(alembic_cfg: Config, connectable: Engine) -> bool:
    directory = script.ScriptDirectory.from_config(alembic_cfg)
    with connectable.begin() as connection:
        context = migration.MigrationContext.configure(connection)
        return set(context.get_current_heads()) == set(directory.get_heads())

def __setup_logging(log_level: str):
    log_level = getattr(logging, log_level.upper())
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    root_logger.addHandler(stream_handler)
    logger.info("Set up logging with log level %s", log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # first wait for DB to be connectable
    await check_database_connection()
    cfg = Config("alembic.ini")
    # Change DB URL to use psycopg2 driver for this specific check
    db_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
    cfg.set_main_option("sqlalchemy.url", db_url)
    engine = create_engine(db_url, echo=True)
    if not check_current_head(cfg, engine):
        raise Exception(
            "Database is not up to date. Please run `poetry run alembic upgrade head`"
        )
        
    # initialize pg vector store singleton
    vector_store = await get_vector_store_singleton()
    vector_store = cast(CustomPGVectorStore, vector_store)
    await vector_store.run_setup()

    try:
        # Some setup is required to initialize the llama-index sentence splitter
        split_by_sentence_tokenizer()
    except FileExistsError:
        # Sometimes seen in deployments, should be benign.
        logger.info("Tried to re-download NLTK files but already exists.")
    yield
    # This section is run on app shutdown
    await vector_store.close()



app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    origins = settings.BACKEND_CORS_ORIGINS.copy()

    # allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_origin_regex="https://ether-omega.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_PREFIX)



# Handler for status code: 5xx
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "code": exc.status_code,
                "message": exc.detail,
                "error_code": exc.status_code,
            }
        ),
    )


# Handler for erroneous user input. Status code: 4xx
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    msg_parts = []
    for error in exc.errors():
        msg_parts.append(f"{error['input']}: {error['msg']}")
        if "type" in error.keys():
            msg_parts[-1] += f"; {error['type']}"
        if "ctx" in error.keys():
            msg_parts[-1] += f".  {error['ctx']['error']}"

    message = "\n\n".join(msg_parts)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": message,
                "error_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            }
        ),
    )


def start():
    print("Running in AppEnvironment: " + settings.ENVIRONMENT.value)
    __setup_logging(settings.LOG_LEVEL)
    """Launched with `poetry run start` at root level"""
    if settings.RENDER:
        # on render.com deployments, run migrations
        logger.debug("Running migrations")
        alembic_args = ["--raiseerr", "upgrade", "head"]
        alembic.config.main(argv=alembic_args)
        logger.debug("Migrations complete")
    else:
        logger.debug("Skipping migrations")
    live_reload = not settings.RENDER
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=live_reload,
        workers=settings.UVICORN_WORKER_COUNT,
    )


