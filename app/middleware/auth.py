# app/middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..config import settings
from ..models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def verify_token(token: str, expected_type: str) -> dict:
    try:
        # Decode the token and validate its type (e.g., "verification" or "access")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        
        if token_type != expected_type:
            raise HTTPException(status_code=400, detail="Invalid token type.")
        
        # Ensure token expiration check (optional, depending on your use case)
        expiration = payload.get("exp")
        if expiration and datetime.utcfromtimestamp(expiration) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Token expired.")
        
        return payload
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token.")
# Optional: for endpoints that can work with or without authentication
def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None