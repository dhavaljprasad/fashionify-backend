from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from typing import Dict, Optional, Any
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status

from app.config.variables import ConfigVariables


# ---------------------------
# Google Credential Verification
# ---------------------------
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
        print("❌ Google verify error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credentials",
        )


# ---------------------------
# Create JWT Access Token
# ---------------------------
def create_access_token(data: Dict):
    try:
        to_encode = data.copy()

        expire = datetime.now(timezone.utc) + timedelta(
            minutes=int(ConfigVariables.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        # 🔥 FIX: exp must be UNIX timestamp (int)
        to_encode.update({"exp": int(expire.timestamp())})

        encoded_jwt = jwt.encode(
            to_encode,
            ConfigVariables.JWT_SECRET,
            algorithm=ConfigVariables.JWT_ALGORITHM,
        )

        return encoded_jwt

    except Exception as e:
        print("❌ Token creation error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token",
        )


# ---------------------------
# Decode + Validate JWT
# ---------------------------
def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            ConfigVariables.JWT_SECRET,
            algorithms=[ConfigVariables.JWT_ALGORITHM],
        )

    except JWTError as e:
        print("❌ JWT decode error:", str(e))  # 🔥 VERY IMPORTANT
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )

    # Extra safety check (optional, jose already checks exp)
    exp: Optional[int] = payload.get("exp")
    if exp is not None:
        if datetime.now(timezone.utc).timestamp() >= exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )

    return payload
