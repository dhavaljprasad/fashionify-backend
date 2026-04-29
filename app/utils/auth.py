from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from typing import Dict, Optional, Any
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status

from app.config.variables import ConfigVariables


async def verify_google_creds(creds: str):
    try:
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            creds,
            request,
            ConfigVariables.GOOGLE_CLIENT_ID,
        )

        if id_info.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            raise ValueError("Wrong issuer")
        return id_info
    except Exception as e:
        print("Unexpected error occured verifying creds as:", e)


def create_access_token(data: Dict):
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=int(ConfigVariables.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            ConfigVariables.JWT_SECRET,
            algorithm=ConfigVariables.JWT_ALGORITHM,
        )
        return encoded_jwt
    except Exception as e:
        print("Unexpected error occured creating access token as:", e)
        return False


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate our JWT access token.
    Raises HTTPException(401) if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            ConfigVariables.JWT_SECRET,
            algorithms=[ConfigVariables.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
        )

    # Optional extra check on exp (jose already checks exp if present)
    exp: Optional[int] = payload.get("exp")
    if exp is not None:
        if datetime.now(timezone.utc).timestamp() >= exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )

    return payload
