from typing import Callable, Awaitable

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.auth import decode_access_token

COOKIE_NAME = "access_token"

# Only backend API routes that should NOT require auth
PUBLIC_PATHS = [
    "/auth/sign-in",
    "/auth/logout",
    "/health",
]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable],
    ):
        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # Allow public routes
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # 🔥 Read token from cookie
        token = request.cookies.get(COOKIE_NAME)

        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        # 🔥 Validate token
        try:
            payload = decode_access_token(token)
        except HTTPException as e:
            return JSONResponse(
                status_code=401,
                content={"detail": e.detail},
            )
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        # Attach user payload to request
        request.state.user = payload

        return await call_next(request)
