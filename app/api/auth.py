# app/api/auth.py
from datetime import timedelta
from typing import Optional

from yarl import Query
from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from app.middleware.auth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from app.models.user import User
from ..utils.auth import (
    TOKEN_TYPES,
    clear_token_cookie,
    create_token,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_reset_token,
    verify_password_reset_token,
    send_verification_email,
    send_password_reset_email,
    verify_token,
)
from app.database import get_db
from app.middleware.auth import get_current_user
from app.config import settings
from app.models.responses import ResponseModel
from app.utils.auth import revoke_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Enhanced request schemas
class UserRegister(BaseModel):
    full_name: constr(min_length=2, max_length=50)
    email: EmailStr
    password: constr(min_length=8)
    confirm_password: str

    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!"
            }
        }

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: constr(min_length=8)
    confirm_password: str

class EmailVerification(BaseModel):
    token: str
class EmailRequest(BaseModel):
    email: str
class ResendVerificationRequest(BaseModel):
    email: EmailStr
  
@router.post("/register", response_model=ResponseModel)
async def register(
    user: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user with email verification"""
    # Validate passwords match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords don't match"
        )

    # Check if email exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_active=False  # Inactive until email verification
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate verification token
    verification_token = create_token(
            data={"sub": request.email},
            token_type="verification",
            expires_delta=timedelta(hours=48)
        )
    # Send verification email
    await send_verification_email(user.email, verification_token)

    return ResponseModel(
        success=True,
        message="Registration successful. Please check your email to verify your account.",
        data={"email": user.email}
    )


@router.post("/login", response_model=ResponseModel)
async def login(
    user: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login user and return tokens"""
    try:
        print(f"\n=== Login Attempt ===")
        print(f"Login attempt for email: {user.email}")
        
        # Get user
        db_user = db.query(User).filter(User.email == user.email).first()
        print(f"User found in database: {db_user is not None}")
        
        if not db_user:
            print("Error: Email not registered")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not registered"
            )

        # Verify password
        password_valid = verify_password(user.password, db_user.hashed_password)
        print(f"Password verification result: {password_valid}")
        
        if not password_valid:
            # Log failed attempt
            current_attempts = (db_user.failed_login_attempts or 0) + 1
            print(f"Failed login attempts: {current_attempts}")
            
            db_user.failed_login_attempts = current_attempts
            db.commit()

            if current_attempts >= 5:
                print("Account locked due to too many failed attempts")
                db_user.is_locked = True
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account locked due to too many failed attempts"
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

        # Check if email is verified
        print(f"Email verification status: {db_user.is_active}")
        if not db_user.is_active:
            print("Error: Email not verified")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email first"
            )
        
        # Check if account is locked
        print(f"Account lock status: {db_user.is_locked}")
        if db_user.is_locked:
            print("Error: Account is locked")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked. Please reset your password"
            )
        
        # Reset failed attempts on successful login
        print("Resetting failed attempts and updating last login")
        db_user.failed_login_attempts = 0
        db_user.last_login = func.now()  # Correct usage
        db.commit()

        # Create tokens
        print("Creating access and refresh tokens")
        access_token = create_access_token(data={"sub": db_user.email})
        refresh_token = create_refresh_token(data={"sub": db_user.email})

        # Set cookies if remember_me
        if getattr(user, 'remember_me', False):
            print("Setting remember_me cookie")
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60  # 30 days
            )

        print("Login successful!")
        return ResponseModel(
            success=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": str(db_user.id),
                    "email": db_user.email,
                    "full_name": db_user.full_name,
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error during login: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login"
        )

@router.post("/refresh", response_model=ResponseModel)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    # Try to get refresh token from cookie if not provided
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )

    # Verify refresh token
    email = verify_refresh_token(refresh_token)
    db_user = db.query(User).filter(User.email == email).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Create new tokens
    new_access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})

    # Update cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60
    )

    return ResponseModel(
        success=True,
        message="Token refreshed successfully",
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
    )
# app/api/auth.py

@router.get("/verify-email", response_model=ResponseModel)
async def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        # This matches your verify_token function signature and token creation
        payload = verify_token(
            token=token, 
            secret_key=settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
            expected_type=TOKEN_TYPES["verification"]
        )
        
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        if user.is_active:
            return ResponseModel(success=False, message="Email is already verified.")
        
        user.is_active = True
        db.commit()
        db.refresh(user)
        
        return ResponseModel(success=True, message="Email verified successfully.")
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dev/get-verification-token/{email}")
async def get_verification_token(email: str, db: Session = Depends(get_db)):
    """Development route to get verification token"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Create verification token with correct token type
        token = create_token(
            data={"sub": email},
            token_type="verification",  # Added the missing token_type argument
            expires_delta=timedelta(hours=24)
        )
        
        return {
            "token": token,
            "verification_url": f"{settings.FRONTEND_URL}/verify-email?token={token}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.post("/resend-verification", response_model=ResponseModel)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    print(f"Received request: {request.json()}")  # Log the raw request body for debugging
    try:
        print(f"Looking up user with email: {request.email}")
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if user.is_active:
            raise HTTPException(status_code=400, detail="Email already verified")

        print(f"Creating token for email: {request.email}")
        # Create new verification token
        token = create_token(
            data={"sub": request.email},
            token_type="verification",
            expires_delta=timedelta(hours=48)
        )
        
        print(f"Sending verification email to: {request.email}")
        # Send new verification email
        await send_verification_email(request.email, token)
        
        return ResponseModel(
            success=True,
            message="New verification email sent. Please check your inbox."
        )
        
    except Exception as e:
        import traceback
        print(f"Error in resend_verification: {traceback.format_exc()}")  # Add error logging
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        # Revoke the token (you can implement this according to your storage method, e.g., blacklist)
        revoke_token(token)
        response = JSONResponse(content={"message": "Successfully logged out"}, status_code=200)
        response = clear_token_cookie(response)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error during logout") 
    
         
@router.get("/protected-route")
def protected_route(current_user: User = Depends(get_current_user)):
    """
    A protected route that requires authentication.
    :param current_user: The authenticated user instance.
    :return: A success message and user details.
    """
    return {
        "success": True,
        "message": "Access granted!",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
        },
    }
# Additional endpoints...