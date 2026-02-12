# 🍳 Recipe Chatbot

AI destekli yemek tarifi chatbotu. Kullanıcının malzemeleri, beslenme tercihi ve süre kısıtına göre **OpenAI** ile kişiselleştirilmiş tarifler üretir. Dış kaynak olarak **TheMealDB** API kullanır.

## Teknoloji

- **Backend:** FastAPI (Python 3.11)
- **AI:** OpenAI API (tool calling)
- **Tarif Kaynağı:** TheMealDB
- **Deploy:** Docker & Docker Compose

## Hızlı Başlangıç

```bash
# 1. Repo'yu klonlayın
git clone https://github.com/gye152/Recipe-Chatbot.git
cd Recipe-Chatbot

# 2. .env dosyasını oluşturun
cp backend/.env.example backend/.env
# OPENAI_API_KEY değerini girin

# 3. Docker ile çalıştırın
docker-compose up --build
```

Uygulama: **http://localhost:8000**

## API

| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/healthz` | GET | Sağlık kontrolü |
| `/chat` | POST | AI şeften tarif iste |
| `/recipes/search` | POST | TheMealDB'den tarif ara |

Detaylı API dokümantasyonu için → [backend/README.md](backend/README.md)

## Lisans

MIT
