# FastAPI Logging, Rate Limiting and Authentication

Completed FastAPI assignment with API-key authentication, per-user sliding-window rate limits, rotating file and terminal logging, Pydantic validation, and Groq through the OpenAI-compatible client.

## Run on Windows PowerShell

```powershell
uv sync
Copy-Item .env.example .env
```

Set your private Groq key as `OPENAI_API_KEY` in `.env`. Keep `OPENAI_BASE_URL=https://api.groq.com/openai/v1`. The configured model is `openai/gpt-oss-20b`.

```powershell
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs, click **Authorize**, and enter a development key.

| Development key | User | Requests per minute |
| --- | --- | --- |
| `dev-key-123` | ahmed | 10 |
| `dev-key-456` | ali | 5 |
| `dev-key-789` | mona | 3 |

These development keys authenticate to this application. Your private Groq key is used only by the provider client. `.env` is excluded from Git.

## Endpoints

- `POST /generate`: authenticated, rate-limited text generation.
- `POST /summarize`: authenticated, rate-limited summarization.
- `GET /usage`: authenticated usage status without consuming a request slot.
- `GET /health`: health check.
- `GET /`: application information.

Example generation body:

```json
{"text": "Explain FastAPI in one sentence."}
```

Missing credentials return 401, unknown credentials return 403, invalid input returns 422, and exceeding the rate limit returns 429. Authenticated invalid requests can consume a slot because rate limiting runs as a dependency. Counts are held in memory and reset when the process restarts.

## Verify

```powershell
uv run --frozen --with httpx python verify_assignment.py
```

The checks mock model calls without changing the application's Groq configuration. They cover authentication, validation, rate limiting, usage, timestamp expiry, logging, and OpenAPI security. Logs are written to `logs/insight_api.log` and the terminal. The Swagger verification screenshot is included as `swagger-verification.png`.
