from typing import Callable, Awaitable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.auth import decode_access_token  # your helper


PUBLIC_PREFIXES = "/auth"  # auth routes: login, register, etc.


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable],
    ):
        # Let CORS preflight pass
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # Public routes (no auth)
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # Extract Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization token"},
            )

        token = auth_header.split(" ", 1)[1].strip()

        # Validate token and decode payload
        try:
            payload = decode_access_token(
                token
            )  # should raise HTTPException(401) if invalid/expired
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        # Attach to request.state so routes can read it
        request.state.user = payload

        return await call_next(request)
