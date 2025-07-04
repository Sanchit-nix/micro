from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.v1.api_router import api_router
from core.error_handler import http_error_handler, validation_exception_handler
from core.config import settings
from db.connection import connect_to_mongo, close_mongo_connection
from db.session import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # PostgreSQL: Create tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("PostgreSQL tables created")
    except Exception as e:
        print(f"PostgreSQL init failed: {e}")

    # MongoDB: Connect
    try:
        await connect_to_mongo()
        print(" MongoDB connected")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

    yield

    # MongoDB: Disconnect
    try:
        await close_mongo_connection()
        print("MongoDB connection closed")
    except Exception as e:
        print(f"Error closing MongoDB: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # GET, PUT, POST, DELETE, etc.
    allow_headers=["*"],
)


app.include_router(api_router)
