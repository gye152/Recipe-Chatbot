"""LLM service — OpenAI chat completion with tool-calling support."""

from __future__ import annotations

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings
from app.schemas import ChatRequest, ChatResponse, DietType, RecipeResult
from app.services import tool_router

logger = logging.getLogger(__name__)

# ── OpenAI client (lazy singleton) ─────────────────────────────────────────────

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Sen profesyonel bir şef ve beslenme uzmanısın. Görevin kullanıcının verdiği malzemeler, \
beslenme tercihleri ve zaman kısıtlamalarına göre yemek tarifi üretmek.

Kurallar:
- Kullanıcının elindeki malzemelere mutlaka öncelik ver.
- Eksik malzeme varsa alternatif öner ve "missing_ingredients" alanına yaz.
- Eğer kullanıcı "vegan" seçtiyse, KESINLIKLE hayvansal ürün (et, süt, yumurta, tereyağı, \
peynir, yoğurt, bal vb.) kullanma.
- Kullanıcı örnekler / web tarifler isterse "search_recipes" aracını çağır.
- Her zaman Türkçe yanıt ver (kullanıcı İngilizce yazarsa da Türkçe cevap ver).
- Yanıtını aşağıdaki JSON şemasına uygun olarak döndür, ek metin ekleme:

{
  "recipe_name": "Tarif adı",
  "ingredients": ["malzeme1", "malzeme2"],
  "steps": ["adım1", "adım2"],
  "time_minutes": 30,
  "missing_ingredients": ["eksik1"],
  "notes": "Notlar ve öneriler",
  "sources": [{"name": "kaynak adı", "url": "URL"}]
}

Eğer kullanıcının mesajı tarif istemekle ilgili değilse, kısa ve yardımsever bir yanıt ver \
ve recipe alanlarını boş bırak.
"""

# ── Tool definitions for OpenAI ────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": (
                "Dış kaynaklardan (TheMealDB) tarif örnekleri arar. "
                "Kullanıcı örnek tarif istediğinde veya ilham almak istediğinde çağır."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Aranacak yemek adı veya anahtar kelime (İngilizce tercih edilir).",
                    },
                    "vegan": {
                        "type": "boolean",
                        "description": "True ise sadece vegan tarifler döner.",
                    },
                    "max_time_minutes": {
                        "type": "integer",
                        "description": "Maksimum hazırlık süresi (dakika). Opsiyonel.",
                    },
                },
                "required": ["query", "vegan"],
            },
        },
    }
]

# ── Main chat function ─────────────────────────────────────────────────────────


async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat request through OpenAI with optional tool calling."""

    client = _get_client()

    # Build user message with structured context
    user_content = _build_user_message(request)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    # First completion
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.7,
    )

    assistant_message = response.choices[0].message

    # Handle tool calls (loop until no more tool calls)
    max_iterations = 5
    iteration = 0
    while assistant_message.tool_calls and iteration < max_iterations:
        iteration += 1
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            logger.info(
                "Tool call: %s(%s)", tool_call.function.name, tool_call.function.arguments
            )
            result = await tool_router.execute_tool_call(
                tool_call.function.name, tool_call.function.arguments
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
        )
        assistant_message = response.choices[0].message

    # Parse the final response
    raw_content = assistant_message.content or ""
    return _parse_response(raw_content)


def _build_user_message(request: ChatRequest) -> str:
    """Build a detailed user message from the ChatRequest fields."""
    parts = [request.message]

    if request.ingredients:
        parts.append(f"\nEldeki malzemeler: {', '.join(request.ingredients)}")

    parts.append(f"\nBeslenme tipi: {request.diet_type.value}")

    if request.allergies:
        parts.append(f"Alerjiler: {', '.join(request.allergies)}")

    if request.max_time_minutes:
        parts.append(f"Maksimum süre: {request.max_time_minutes} dakika")

    if request.cuisine:
        parts.append(f"Mutfak tercihi: {request.cuisine}")

    return "\n".join(parts)


def _parse_response(raw: str) -> ChatResponse:
    """Try to extract structured RecipeResult from the AI response."""
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines[1:] if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
        recipe = RecipeResult.model_validate(data)
        return ChatResponse(reply=raw, recipe=recipe)
    except (json.JSONDecodeError, Exception) as exc:
        logger.debug("Could not parse structured recipe from response: %s", exc)
        return ChatResponse(reply=raw, recipe=None)
