from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoint import router
app = FastAPI()

app.include_router(router, prefix="/api", tags=["multi_language_translation"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],  # GET, PUT, POST, DELETE, etc.
    allow_headers=["*"],
)

