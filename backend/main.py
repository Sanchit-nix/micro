from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.v1.api_router import api_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.error_handler import http_error_handler, validation_exception_handler
from core.config import settings
from db.connection import connect_to_mongo, close_mongo_connection
from db.session import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("postgreSQL tables created")

    await connect_to_mongo()
    print(" MongoDB connected")

    yield

    await close_mongo_connection()
    print("MongoDB connection closed")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],  # GET, PUT, POST, DELETE, etc.
    allow_headers=["*"],
)

app.include_router(api_router)
