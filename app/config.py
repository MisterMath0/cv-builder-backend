# app/config.py
from pydantic.v1 import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os
from pydantic import BaseModel

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    PROJECT_NAME: str = "CV Builder API"
    VERSION: str = "1.0.0"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")
    
    # Email Settings (all optional)
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_SERVER: Optional[str] = None
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    USE_CREDENTIALS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
        arbitrary_types_allowed = True

settings = Settings()