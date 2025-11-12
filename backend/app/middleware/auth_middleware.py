from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.jwt_service import verify_token
from app.schemas.auth_schemas import UserOut

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/auth"):
            response = await call_next(request)
            return response

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(status_code=401, content={"detail": "Authorization header missing"})

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
            
            payload = verify_token(token)
            request.state.user = payload
        except Exception as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})

        response = await call_next(request)
        return response

def get_current_user(request: Request) -> UserOut:
    user = request.state.user
    return UserOut(**user)

async def require_authenticated(request: Request) -> UserOut:
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return get_current_user(request)