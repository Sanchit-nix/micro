from speech_to_text import endpoint as stt_endpoint
from text_to_speech import endpoint as tts_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.include_router(stt_endpoint.router, prefix="/api",tags=['speech_to_text'])
app.include_router(tts_endpoint.router, prefix="/api",tags=['text_to_speech'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],  # GET, PUT, POST, DELETE, etc.
    allow_headers=["*"],
)

