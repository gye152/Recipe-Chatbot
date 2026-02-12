"""Recipe search router — direct access to the recipe provider."""

from fastapi import APIRouter, HTTPException

from app.schemas import RecipeSearchRequest, RecipeSearchResponse
from app.services import recipe_provider

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/search", response_model=RecipeSearchResponse)
async def search_recipes(body: RecipeSearchRequest):
    """Search external recipe APIs for matching recipes."""
    try:
        results = await recipe_provider.search_recipes(
            query=body.query,
            vegan=body.vegan,
            max_time_minutes=body.max_time_minutes,
        )
        return RecipeSearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recipe search failed: {exc}")
