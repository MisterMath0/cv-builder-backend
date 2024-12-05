# app/utils/redis_helper.py
import redis
from jose import jwt
from datetime import datetime
from ..config import settings
from typing import Optional

# Create Redis connection
r = redis.StrictRedis(
    host=settings.REDISHOST, 
    port=settings.REDISPORT, 
    db=0, 
    decode_responses=True
)

def blacklist_token(token: str, secret_key: str, algorithm: str = "HS256"):
    """
    Store token in Redis blacklist with proper TTL based on token expiration
    """
    try:
        # Decode token to get expiry time
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        token_exp = datetime.fromtimestamp(payload['exp'])
        
        # Calculate TTL (time until token expires)
        ttl = max(0, int((token_exp - datetime.utcnow()).total_seconds()))
        
        # Store in Redis with TTL
        if ttl > 0:
            r.setex(
                f"blacklisted_token:{token}", 
                ttl,
                "blacklisted"
            )
            print(f"Token blacklisted successfully with TTL: {ttl} seconds")
            return True
        return False
    except jwt.ExpiredSignatureError:
        print("Token already expired, no need to blacklist")
        return False
    except Exception as e:
        print(f"Error blacklisting token: {str(e)}")
        return False

def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted in Redis
    """
    try:
        key = f"blacklisted_token:{token}"
        exists = r.exists(key)
        if exists:
            # Optionally get TTL for debugging
            ttl = r.ttl(key)
            print(f"Found blacklisted token with TTL: {ttl} seconds")
        return exists
    except Exception as e:
        print(f"Error checking token blacklist: {str(e)}")
        return False

def clear_expired_tokens():
    """
    Utility function to manually clear expired tokens if needed
    """
    try:
        pattern = "blacklisted_token:*"
        keys = r.keys(pattern)
        expired = 0
        for key in keys:
            if r.ttl(key) <= 0:
                r.delete(key)
                expired += 1
        print(f"Cleared {expired} expired tokens")
    except Exception as e:
        print(f"Error clearing expired tokens: {str(e)}")

# Optional: health check function
def check_redis_connection() -> bool:
    """
    Check if Redis connection is working
    """
    try:
        return r.ping()
    except Exception as e:
        print(f"Redis connection error: {str(e)}")
        return False