# app/api/protected_route.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models.user import User
from ..middleware.auth import get_current_user
from ..database import get_db

router = APIRouter()

@router.get("/protected-data")
def get_protected_data(
    current_user: User = Depends(get_current_user),  # Protecting the route with middleware
    db: Session = Depends(get_db)
):
    return {"message": f"Hello {current_user.full_name}, this is protected data!"}
