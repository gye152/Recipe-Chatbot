# 🍳 Yemek Tarifi Chatbotu — MVP

AI destekli yemek tarifi üretici. Kullanıcının malzemelerini, beslenme tercihini ve süre kısıtını alarak OpenAI ile kişiselleştirilmiş tarifler üretir. Dış kaynak olarak TheMealDB API kullanır.

## 🏗️ Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI (Python 3.11) |
| AI | OpenAI API (tool calling) |
| Recipe API | TheMealDB (ücretsiz, anahtar gerektirmez) |
| Deploy | Docker + docker-compose |

## ⚙️ Kurulum

### 1. Depoyu klonlayın / dizine gidin

```bash
cd recipe-chatbot/backend
```

### 2. `.env` dosyasını oluşturun

```bash
cp .env.example .env
# .env dosyasını düzenleyin ve OPENAI_API_KEY değerini girin
```

**Gerekli değişken:**

| Değişken | Açıklama | Varsayılan |
|----------|----------|------------|
| `OPENAI_API_KEY` | OpenAI API anahtarınız | *(zorunlu)* |
| `OPENAI_MODEL` | Kullanılacak model | `gpt-4o` |
| `RECIPE_API_BASE_URL` | TheMealDB base URL | `https://www.themealdb.com/api/json/v1/1` |
| `LOG_LEVEL` | Log seviyesi | `info` |

### 3a. Yerel çalıştırma

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3b. Docker ile çalıştırma

```bash
cd ..  # recipe-chatbot kök dizinine
docker-compose up --build
```

Uygulama: **http://localhost:8000**

---

## 📡 API Endpoints

### `GET /healthz`

Sağlık kontrolü.

```bash
curl http://localhost:8000/healthz
```

```json
{"ok": true}
```

---

### `POST /chat`

AI şeften tarif iste.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Domates, soğan ve zeytinyağı var. 20 dakikada vegan bir tarif öner.",
    "diet_type": "vegan",
    "ingredients": ["domates", "soğan", "zeytinyağı"],
    "max_time_minutes": 20
  }'
```

**İstek gövdesi:**

| Alan | Tip | Zorunlu | Açıklama |
|------|-----|---------|----------|
| `message` | string | ✅ | Kullanıcı mesajı |
| `diet_type` | `"vegan"` \| `"normal"` | ❌ | Beslenme tipi (varsayılan: normal) |
| `ingredients` | string[] | ❌ | Eldeki malzemeler |
| `allergies` | string[] | ❌ | Alerjenler |
| `max_time_minutes` | int | ❌ | Maksimum süre (dakika) |
| `cuisine` | string | ❌ | Mutfak tercihi |

**Örnek yanıt:**

```json
{
  "reply": "...",
  "recipe": {
    "recipe_name": "Zeytinyağlı Domates Sote",
    "ingredients": [
      "3 domates",
      "1 soğan",
      "2 yemek kaşığı zeytinyağı",
      "Tuz",
      "Karabiber"
    ],
    "steps": [
      "Soğanı ince doğrayın ve zeytinyağında pembeleşene kadar kavurun.",
      "Domatesleri küp küp doğrayıp ekleyin.",
      "Kısık ateşte 15 dakika pişirin.",
      "Tuz ve karabiber ile tatlandırın."
    ],
    "time_minutes": 20,
    "missing_ingredients": [],
    "notes": "Yanında çıtır ekmek ile servis edebilirsiniz.",
    "sources": []
  }
}
```

---

### `POST /recipes/search`

TheMealDB'den tarif ara (doğrudan).

```bash
curl -X POST http://localhost:8000/recipes/search \
  -H "Content-Type: application/json" \
  -d '{"query": "pasta", "vegan": false}'
```

**İstek gövdesi:**

| Alan | Tip | Zorunlu | Açıklama |
|------|-----|---------|----------|
| `query` | string | ✅ | Arama sorgusu |
| `vegan` | bool | ❌ | Vegan filtresi (varsayılan: false) |
| `max_time_minutes` | int | ❌ | Süre filtresi |

---

## 🧪 Örnek Senaryolar

### Senaryo 1: Vegan + 20 dakika + eldeki malzemeler

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Elimde domates, soğan, sarımsak ve makarna var. 20 dakikada yapılacak vegan bir tarif öner.",
    "diet_type": "vegan",
    "ingredients": ["domates", "soğan", "sarımsak", "makarna"],
    "max_time_minutes": 20
  }'
```

AI, yalnızca bu malzemelerle (+ opsiyonel baharatlar) vegan tarif üretir. `missing_ingredients` alanında eksik varsa listeler.

### Senaryo 2: Normal + dış kaynak tarif getirme (tool calling)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tavuklu bir yemek yapmak istiyorum, webden örnek tarif bul ve bana öner.",
    "diet_type": "normal",
    "ingredients": ["tavuk", "pirinç", "biber"]
  }'
```

AI, `search_recipes` tool'unu çağırır → TheMealDB'den tavuk tarifleri çeker → sonuçları kullanarak özelleştirilmiş tarif önerir. `sources` alanında dış kaynak bilgisi yer alır.

---

## 📁 Proje Yapısı

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, middleware, routers
│   ├── config.py           # Pydantic Settings (.env)
│   ├── schemas.py          # Request/Response modelleri
│   ├── routers/
│   │   ├── health.py       # GET /healthz
│   │   ├── chat.py         # POST /chat
│   │   └── recipes.py      # POST /recipes/search
│   ├── services/
│   │   ├── llm_service.py      # OpenAI + tool calling
│   │   ├── recipe_provider.py  # TheMealDB + mock fallback
│   │   └── tool_router.py      # Tool call dispatcher
│   └── static/
│       └── index.html      # Opsiyonel web UI
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## 🔒 Güvenlik

- API anahtarları **asla** kod içinde tutulmaz; `.env` dosyasından yüklenir.
- `.env` dosyasını `.gitignore`'a eklemeyi unutmayın.
- CORS varsayılan olarak tüm origin'lere açıktır; production'da kısıtlayın.

## 📝 Lisans

MIT
