"""Pydantic models for request/response schemas."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class DietType(str, Enum):
    vegan = "vegan"
    normal = "normal"


# ── Request Models ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Kullanıcının mesajı")
    diet_type: DietType = Field(DietType.normal, description="Beslenme tipi: vegan veya normal")
    ingredients: list[str] = Field(default_factory=list, description="Eldeki malzemeler")
    allergies: list[str] = Field(default_factory=list, description="Alerjenler (opsiyonel)")
    max_time_minutes: Optional[int] = Field(None, ge=1, description="Maksimum süre (dakika)")
    cuisine: Optional[str] = Field(None, description="Mutfak tercihi (opsiyonel)")


class RecipeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Arama sorgusu")
    vegan: bool = Field(False, description="Sadece vegan tarifler")
    max_time_minutes: Optional[int] = Field(None, ge=1, description="Maksimum süre (dakika)")


# ── Response Models ────────────────────────────────────────────────────────────

class RecipeSource(BaseModel):
    name: str = ""
    url: str = ""


class RecipeResult(BaseModel):
    recipe_name: str = ""
    ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    time_minutes: Optional[int] = None
    missing_ingredients: list[str] = Field(default_factory=list)
    notes: str = ""
    sources: list[RecipeSource] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str = ""
    recipe: Optional[RecipeResult] = None


class RecipeSearchResponse(BaseModel):
    results: list[RecipeResult] = Field(default_factory=list)
