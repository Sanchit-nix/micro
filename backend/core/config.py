import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AIaaS"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    MODEL_DIR: str = "ml_models/deployed"
    
    # JWT/secret key settings
    # SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your_secret_key')
    POSTGRES_CONNECTION_STRING: str
    # = os.getenv
    # ("POSTGRES_CONNECTION_STRING",
    #   "postgresql://user:password@localhost:5432/aiaas")
    MONGODB_CONNECTION_STRING: str  
    # os.getenv(
    #     "MONGODB_CONNECTION_STRING", 
    #     "mongodb://admin:adminpassword@localhost:27017"
    # )
    DATABASE_NAME: str = "aiaas"

    class Config:
        env_file = ".env"
        extra = "forbid" 

settings = Settings()
