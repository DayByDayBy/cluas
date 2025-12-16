"""
Unified server entrypoint.
- React frontend at /
- Gradio UI at /gradio
- API at /api/*
"""

import os
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from gradio import mount_gradio_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cluas Huginn",
    description="A dialectic deliberation engine - API for React frontend",
    version="0.1.0",
)

# CORS middleware (dev only; in production same-origin so not strictly needed)
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()
if ENVIRONMENT == "development":
    cors_origins = [
        o.strip()
        for o in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:7860,http://127.0.0.1:7860",
        ).split(",")
        if o.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

# API routes
from src.api.routes import router as api_router
app.include_router(api_router)

# Mount Gradio at /gradio
from src.gradio.app import my_gradio_app, theme, CUSTOM_CSS
mount_gradio_app(app, my_gradio_app, path="/gradio")

# Serve React build (production) - mount last so API routes take precedence
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    logger.info(f"Serving React frontend from {FRONTEND_DIR}")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    logger.warning(
        f"React frontend not found at {FRONTEND_DIR}. "
        "Run 'npm run build' in frontend/ to build it. "
        "For dev, run the Vite dev server separately."
    )
    
    # Fallback: redirect root to Gradio
    from fastapi.responses import RedirectResponse
    
    @app.get("/")
    async def redirect_to_gradio():
        return RedirectResponse(url="/gradio")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 7860))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"  React frontend: http://localhost:{port}/")
    logger.info(f"  Gradio UI: http://localhost:{port}/gradio")
    logger.info(f"  API: http://localhost:{port}/api/")
    
    uvicorn.run(app, host=host, port=port)
