"""Health check router."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz():
    """Simple health check endpoint."""
    return {"ok": True}
