"""JWT Token 编解码"""

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from src.config import settings

ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret_key


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
