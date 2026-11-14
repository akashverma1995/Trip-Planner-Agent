import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure parent directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend import run_travel_agent_async, run_travel_agent


# ==============================================================================
# 1. Logging & Telemetry Setup
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("TripMate")


# ==============================================================================
# 2. Modern FastAPI Lifespan Handler
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and graceful shutdown."""
    logger.info("TripMate AI Travel Planner is starting up...")
    yield
    logger.info("TripMate AI Travel Planner is shutting down...")


# ==============================================================================
# 3. Application Initialization & Middleware
# ==============================================================================

app = FastAPI(
    title="TripMate AI",
    description="Enterprise Multi-Agent Travel Planner powered by LangGraph, Groq, and FastAPI",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware (Allows frontend microservices, React, Next.js, and mobile clients)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Telemetry Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Static Files & Jinja2 Templates
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))


# ==============================================================================
# 4. Typed Pydantic Request & Response Schemas
# ==============================================================================

class TravelRequest(BaseModel):
    """Validated user request payload."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Travel request prompt from the user"
    )
    thread_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Unique thread identifier for multi-turn conversation memory"
    )


class TravelResponse(BaseModel):
    """Strict response contract for API consumers."""
    success: bool = True
    thread_id: str
    answer: str
    flight_results: Optional[str] = ""
    hotel_results: Optional[str] = ""
    itinerary: Optional[str] = ""
    llm_calls: int = 0


class ErrorResponse(BaseModel):
    """Standardized error contract."""
    success: bool = False
    error: str


# ==============================================================================
# 5. Core Endpoints
# ==============================================================================

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def home(request: Request):
    """Serves the front-end user interface."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.post(
    "/api/travel",
    response_model=TravelResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["Agent API"]
)
async def travel_planner(request_data: TravelRequest):
    """
    Non-blocking asynchronous endpoint that delegates travel planning
    to the parallel LangGraph agent workflow.
    """
    user_message = request_data.message.strip()

    if not user_message:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": "Message cannot be empty."}
        )

    try:
        # Non-blocking async execution using LangGraph ainvoke
        result = await run_travel_agent_async(
            user_input=user_message,
            thread_id=request_data.thread_id
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "thread_id": result["thread_id"],
                "answer": result["answer"],
                "flight_results": result.get("flight_results", ""),
                "hotel_results": result.get("hotel_results", ""),
                "itinerary": result.get("itinerary", ""),
                "llm_calls": result.get("llm_calls", 0),
            }
        )

    except Exception as exc:
        logger.error(f"Error processing travel request: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": f"Internal agent error: {str(exc)}"
            }
        )


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Production health & readiness probe for orchestrators (Render, K8s, Docker)."""
    return {
        "status": "healthy",
        "app": "TripMate AI",
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "timestamp": int(time.time()),
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Suppresses missing favicon 404 warnings."""
    return JSONResponse(content={})


# ==============================================================================
# 6. Production-Ready Server Launch
# ==============================================================================

if __name__ == "__main__":
    # Reads environment variables for cloud deployment (e.g. Render, Railway, AWS)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development"

    logger.info(f"Starting server on http://{host}:{port} (Dev reload: {is_dev})")
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=is_dev
    )
