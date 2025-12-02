"""Top-level API routes for the backend service.

Start by putting simple endpoints here (like `/health`), and later you can
split things into feature-specific route modules and include them in `main.py`.
"""

from fastapi import APIRouter

from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    """Simple health endpoint to verify the API is running."""
    return HealthResponse(status="ok")
