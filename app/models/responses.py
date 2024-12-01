# app/models/responses.py
from typing import Optional, Any, List
from pydantic import BaseModel

class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[List[str]] = None
