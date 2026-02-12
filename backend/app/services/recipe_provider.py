"""Recipe provider — TheMealDB integration with mock fallback."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings
from app.schemas import RecipeResult, RecipeSource

logger = logging.getLogger(__name__)

# ── Animal-product blacklist (for vegan filtering) ─────────────────────────────

ANIMAL_PRODUCTS = {
    "chicken", "beef", "lamb", "pork", "turkey", "duck", "fish", "salmon",
    "tuna", "shrimp", "prawn", "crab", "lobster", "squid", "anchovy",
    "bacon", "sausage", "ham", "mince", "steak", "veal",
    "milk", "cream", "butter", "cheese", "yogurt", "yoghurt", "egg", "eggs",
    "honey", "ghee", "lard", "suet", "gelatin", "gelatine",
    "whey", "casein", "mayonnaise",
    # Turkish equivalents
    "et", "tavuk", "dana", "kuzu", "balık", "süt", "krema", "tereyağı",
    "peynir", "yoğurt", "yumurta", "bal", "kaymak",
}


def _is_vegan_safe(ingredients: list[str]) -> bool:
    """Return True if no animal product is found in the ingredient list."""
    for ingredient in ingredients:
        lower = ingredient.lower().strip()
        for animal in ANIMAL_PRODUCTS:
            if animal in lower:
                return False
    return True


def _parse_meal(meal: dict) -> RecipeResult:
    """Convert a TheMealDB meal object into our RecipeResult schema."""
    ingredients: list[str] = []
    for i in range(1, 21):
        ing = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if ing:
            ingredients.append(f"{measure} {ing}".strip())

    steps_raw = (meal.get("strInstructions") or "").strip()
    steps = [s.strip() for s in steps_raw.replace("\r\n", "\n").split("\n") if s.strip()]

    source_url = meal.get("strSource") or meal.get("strYoutube") or ""
    sources = []
    if source_url:
        sources.append(RecipeSource(name="TheMealDB", url=source_url))

    return RecipeResult(
        recipe_name=meal.get("strMeal", ""),
        ingredients=ingredients,
        steps=steps,
        time_minutes=None,
        missing_ingredients=[],
        notes=f"Category: {meal.get('strCategory', 'N/A')} | Area: {meal.get('strArea', 'N/A')}",
        sources=sources,
    )


# ── Mock recipes for fallback / testing ────────────────────────────────────────

MOCK_RECIPES: list[RecipeResult] = [
    RecipeResult(
        recipe_name="Domates Çorbası",
        ingredients=["4 domates", "1 soğan", "2 yemek kaşığı zeytinyağı", "Tuz", "Karabiber", "Su"],
        steps=[
            "Soğanı doğrayıp zeytinyağında kavurun.",
            "Domatesleri ekleyip 5 dakika pişirin.",
            "Su ekleyin ve 15 dakika kaynatın.",
            "Blender ile pürüzsüz hale getirin.",
            "Tuz ve karabiber ile tatlandırın.",
        ],
        time_minutes=25,
        missing_ingredients=[],
        notes="Klasik Türk çorbası. Vegan-uyumlu.",
        sources=[RecipeSource(name="Mock Provider", url="")],
    ),
    RecipeResult(
        recipe_name="Veggie Stir Fry",
        ingredients=["1 bell pepper", "1 zucchini", "1 carrot", "Soy sauce", "Olive oil", "Garlic"],
        steps=[
            "Slice all vegetables thinly.",
            "Heat olive oil in a wok.",
            "Sauté garlic for 30 seconds.",
            "Add vegetables and stir-fry for 5 minutes.",
            "Add soy sauce and toss well.",
        ],
        time_minutes=15,
        missing_ingredients=[],
        notes="Quick vegan stir-fry.",
        sources=[RecipeSource(name="Mock Provider", url="")],
    ),
]


async def search_recipes(
    query: str,
    vegan: bool = False,
    max_time_minutes: Optional[int] = None,
) -> list[RecipeResult]:
    """Search TheMealDB for recipes. Falls back to mock data on failure."""
    try:
        return await _search_themealdb(query, vegan, max_time_minutes)
    except Exception as exc:
        logger.warning("TheMealDB unavailable (%s), using mock fallback.", exc)
        return _search_mock(query, vegan)


async def _search_themealdb(
    query: str,
    vegan: bool,
    max_time_minutes: Optional[int],
) -> list[RecipeResult]:
    """Call TheMealDB search endpoint."""
    url = f"{settings.recipe_api_base_url}/search.php"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"s": query})
        resp.raise_for_status()
        data = resp.json()

    meals = data.get("meals") or []
    results: list[RecipeResult] = []
    for meal in meals:
        recipe = _parse_meal(meal)
        if vegan and not _is_vegan_safe(recipe.ingredients):
            continue
        results.append(recipe)

    return results[:10]  # cap to 10


def _search_mock(query: str, vegan: bool) -> list[RecipeResult]:
    """Return deterministic mock recipes (for dev/testing or API failure)."""
    results = []
    for r in MOCK_RECIPES:
        if vegan and not _is_vegan_safe(r.ingredients):
            continue
        results.append(r)
    return results
