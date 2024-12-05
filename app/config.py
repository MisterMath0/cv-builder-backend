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
    # settings.py (add Redis configuration)
    REDISHOST = "localhost" or "redis.railway.internal"  # Or your Redis host if using a remote Redis instance
    REDISPORT = 6379  # Default Redis port

    
    # Security
    SECRET_KEY = "e9494e7349ea0eb022e6dff0ae4ec71beff264d2e0c4a6f4cce3e9ca94ccf73a"
    ALGORITHM = "HS256"
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