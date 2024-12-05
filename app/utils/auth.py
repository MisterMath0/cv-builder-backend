# app/utils/auth.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, status
from app.config import settings
import secrets
from .email import send_verification_email_
import logging
from fastapi.responses import JSONResponse
from fastapi import Response


# Password hashing config
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token types
TOKEN_TYPES = {
    "access": "access",
    "refresh": "refresh",
    "reset": "reset",
    "verification": "verification"
}

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def create_token(
    data: dict,
    token_type: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default expiration times based on token type
        if token_type == TOKEN_TYPES["access"]:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        elif token_type == TOKEN_TYPES["refresh"]:
            expire = datetime.utcnow() + timedelta(days=30)
        elif token_type == TOKEN_TYPES["reset"]:
            expire = datetime.utcnow() + timedelta(hours=24)
        elif token_type == TOKEN_TYPES["verification"]:
            expire = datetime.utcnow() + timedelta(hours=48)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "type": token_type,
        "iat": datetime.utcnow(),
        "jti": secrets.token_hex(8)  # Unique token ID
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
# Define constants for token types and error messages
TOKEN_TYPES = {
    "access": "access",
    "refresh": "refresh",
    "reset": "reset",
    "verification": "verification",
}

ERROR_MESSAGES = {
    "invalid_token": "Invalid or expired token.",
    "missing_token": "Authorization token is missing.",
    "unauthorized": "Unauthorized access.",
}

def verify_token(
    token: str, 
    secret_key: str, 
    algorithm: str, 
    expected_type: Optional[str] = None
) -> Dict:
    """
    Verify a JWT token, including its type and expiration.
    :param token: The JWT token to verify.
    :param secret_key: Secret key for decoding the token.
    :param algorithm: Algorithm used for encoding/decoding the token.
    :param expected_type: (Optional) Expected token type to validate against.
    :return: Decoded token payload if valid.
    """
    try:
        # Decode the token
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        
        # Check for token expiration
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.utcfromtimestamp(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES["invalid_token"]
            )
        
        # Verify the token type
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected '{expected_type}', got '{token_type}'."
            )

        # Additional security check: ensure unique token ID (jti) exists
        if "jti" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES["invalid_token"]
            )
        
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{ERROR_MESSAGES['invalid_token']} {str(e)}"
        )
def create_access_token(user_id: str) -> str:
    """
    Create an access token with a short expiration time.
    """
    expiration = timedelta(days=7)  # Access token is valid for 15 minutes
    expire = datetime.utcnow() + expiration
    to_encode = {"sub": user_id, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token with a longer expiration time.
    """
    expiration = timedelta(days=7)  # Refresh token is valid for 7 days
    expire = datetime.utcnow() + expiration
    to_encode = {"sub": user_id, "exp": expire, "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    return verify_token(token, TOKEN_TYPES["access"])

def verify_refresh_token(token: str) -> dict:
    return verify_token(token, TOKEN_TYPES["refresh"])

def get_password_reset_token(email: str) -> str:
    return create_token({"sub": email}, TOKEN_TYPES["reset"])

def verify_password_reset_token(token: str) -> dict:
    return verify_token(token, TOKEN_TYPES["reset"])

def create_email_verification_token(email: str) -> str:
    return create_token({"sub": email}, TOKEN_TYPES["verification"])

def verify_email_verification_token(token: str) -> dict:
    return verify_token(token, TOKEN_TYPES["verification"])

async def send_verification_email(email: str, token: str):
    logging.info(f"Sending email to {email}")
    logging.info(f"Token: {token}")

    # Prepare the verification URL
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    # Define the subject and template
    subject = "Verify Your Email"
    template = "email_verification.html"  # Make sure the template is available, or load it dynamically
    data = {
        "verify_url": verify_url,
        "expires_in": "48 hours"
    }

    # Call the modified send_verification_email in email.py
    await send_verification_email_(
        email=email,
        token=token,
        subject=subject,
        template=template,
        data=data
    )


async def send_password_reset_email(email: str, token: str, base_url: str):
    reset_url = f"{base_url}/reset-password?token={token}"
    await send_verification_email(
        email=email,
        subject="Password Reset Request",
        template="password_reset.html",
        data={
            "reset_url": reset_url,
            "expires_in": "24 hours"
        }
    )

def validate_password_strength(password: str) -> bool:
    """
    Validate password strength
    Returns True if password meets requirements
    """
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True

# Optional: Token blacklist (for logged out tokens)
_token_blacklist = set()

def revoke_token(token: str):
    """Add a token to the blacklist"""
    _token_blacklist.add(token)

def is_token_revoked(token: str) -> bool:
    """Check if a token is blacklisted"""
    return token in _token_blacklist
def clear_token_cookie(response: JSONResponse):
    response.set_cookie(
        "token", 
        "", 
        expires=datetime.utcnow(),  # Set expiry to the past
        httponly=True, 
        secure=True, 
        samesite="Strict"
    )
    return response


def clear_token_cookie(response: Response) -> Response:
    """
    Clears the JWT cookie from the response. This ensures the client cannot send the token after logout.
    """
    response.delete_cookie("access_token")  # Assuming you store the token in the 'access_token' cookie
    return response