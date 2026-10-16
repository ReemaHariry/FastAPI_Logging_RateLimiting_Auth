import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from math import ceil

from fastapi import Depends, HTTPException, status

from app.config import settings
from app.utils.security import verify_api_key

logger = logging.getLogger(__name__)


class SlidingWindowLimiter:
    def __init__(self, limit: int, window: timedelta):
        self.limit = limit
        self.window = window

        # storage: user_id -> list of request timestamps
        self.storage: dict[str, list[datetime]] = defaultdict(list)

    def _recent(self, user_id: str, now: datetime) -> list[datetime]:
        """Get requests only inside the time window."""
        cutoff = now - self.window
        self.storage[user_id] = [t for t in self.storage[user_id] if t > cutoff]
        return self.storage[user_id]

    def check(self, user_id: str, limit: int | None = None) -> int:
        """Record a request, or raise 429 if the user is over the limit.

        `limit` lets the caller override the default per-user limit. When
        `limit` is None the instance-level `self.limit` is used.
        """
        effective_limit = limit if limit is not None else self.limit

        now = datetime.now(tz=UTC)
        recent = self._recent(user_id, now)

        request_count = len(recent)
        if request_count >= effective_limit:
            retry_after = ceil(self.window.total_seconds())
            logger.warning(f"Rate Limit Exceeded for user: {user_id} ({request_count}/{effective_limit})")

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded, maximum {effective_limit} requests per {retry_after}s, try again after {retry_after}s.",
            )

        self.storage[user_id].append(now)
        logger.info(f"Rate Limit check passed for {user_id}: {request_count + 1}/{effective_limit}")
        return request_count + 1

    def status(self, user_id: str, limit: int | None = None) -> dict:
        effective_limit = limit if limit is not None else self.limit
        now = datetime.now(tz=UTC)
        recent = self._recent(user_id, now)
        remaining = max(0, effective_limit - len(recent))
        return {"user": user_id, "limit": effective_limit, "remaining": remaining}


limiter = SlidingWindowLimiter(
    limit=settings.rate_limit_per_minute,
    window=timedelta(minutes=1),
)


async def rate_limit_dependency(user_id: str = Depends(verify_api_key)) -> str:
    resolved_limit = settings.rate_limits.get(user_id, settings.rate_limit_per_minute)
    limiter.check(user_id, limit=resolved_limit)
    return user_id
