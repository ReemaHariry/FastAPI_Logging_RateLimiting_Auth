import asyncio
import contextlib
import io
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
from app import main
from app.config import settings
from app.utils.logging_config import setup_logging
from app.utils.rate_limit import SlidingWindowLimiter, limiter

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
        for path in ("/usage", "/generate", "/summarize"):
            method = client.get if path == "/usage" else client.post
            args = {} if path == "/usage" else {"json": {"text": "Hello"}}
            assert (await method(path, **args)).status_code == 401
            assert (await method(path, headers={"X-API-Key": "unknown"}, **args)).status_code == 403
        for key, user in settings.api_keys.items():
            result = await client.get("/usage", headers={"X-API-Key": key})
            assert result.json() == {"user": user, "limit": settings.rate_limits.get(user, 10), "remaining": settings.rate_limits.get(user, 10)}
        with patch.object(main.llm, "chat", return_value="Test answer") as chat:
            headers = {"X-API-Key": "dev-key-789"}
            codes = [(await client.post("/generate", headers=headers, json={"text": "Hello"})).status_code for _ in range(4)]
            assert codes == [200, 200, 200, 429], codes
            assert chat.call_count == 3
            for _ in range(5):
                assert (await client.get("/usage", headers=headers)).json()["remaining"] == 0
            assert len(limiter.storage["mona"]) == 3
            assert (await client.get("/usage", headers={"X-API-Key": "dev-key-456"})).json()["remaining"] == 5
            limiter.storage.clear()
            for endpoint in ("/generate", "/summarize"):
                assert (await client.post(endpoint, headers=headers, json={"text": "Hello"})).status_code == 200
            assert len(limiter.storage["mona"]) == 2
            for body in ({"text": " "}, {"text": "x", "temperature": 3}, {"text": "x", "model": "bad"}, {"text": "x" * 5001}):
                limiter.storage.clear()
                before = chat.call_count
                assert (await client.post("/generate", headers=headers, json=body)).status_code == 422
                assert chat.call_count == before
        limiter.storage.clear()
    isolated = SlidingWindowLimiter(10, timedelta(minutes=1))
    isolated.storage["test"] = [datetime.now(UTC) - timedelta(seconds=61)]
    assert isolated.status("test")["remaining"] == 10
    isolated.check("test", limit=1)
    assert isolated.status("test", limit=0)["remaining"] == 0
    assert isolated.status("other")["remaining"] == 10
    root = logging.getLogger()
    handlers = root.handlers[:]
    assert setup_logging() is root
    setup_logging()
    assert root.handlers == handlers and len(handlers) == 2
    file_handler = handlers[0]
    assert file_handler.maxBytes == settings.log_max_bytes
    assert file_handler.backupCount == settings.log_backup_count
    assert handlers[0].formatter._fmt == handlers[1].formatter._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    terminal = io.StringIO()
    with contextlib.redirect_stderr(terminal):
        previous = handlers[1].setStream(terminal)
        logging.getLogger("assignment_check").info("logging verification passed")
        handlers[1].setStream(previous)
    file_handler.flush()
    assert "logging verification passed" in terminal.getvalue()
    assert "logging verification passed" in Path(settings.log_file).read_text()
    schema = main.app.openapi()
    assert schema["components"]["securitySchemes"]["APIKeyHeader"]["name"] == "X-API-Key"
    assert schema["paths"]["/usage"]["get"]["security"] == [{"APIKeyHeader": []}]
    print("PASS: authentication, mappings, validation, both protected endpoints, Mona 429, usage, isolation, expiry, overrides, fallback, logging, OpenAPI")

asyncio.run(run())
