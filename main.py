from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import router as api_router
from app.settings import GLB_OUTPUT_DIR, ALLOWED_CORS_ORIGINS, GLB_CACHE_CONTROL

app = FastAPI(title="Lamp Configurator Backend")

class GlbCacheHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        if request.url.path.startswith("/glb/") and response.status_code == 200:
            response.headers["Cache-Control"] = GLB_CACHE_CONTROL

        return response


app.add_middleware(GlbCacheHeadersMiddleware)

# -----------------------------------------------------
# CORS
# -----------------------------------------------------
# Controlled by ENV in app/settings.py.
# While using ngrok, keep the ngrok origin in the development allowlist.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["Content-Type"],
)

# -----------------------------------------------------
# Static GLB serving
# -----------------------------------------------------

GLB_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/glb",
    StaticFiles(directory=str(GLB_OUTPUT_DIR)),
    name="glb",
)

# -----------------------------------------------------
# API routes
# -----------------------------------------------------

app.include_router(api_router)
