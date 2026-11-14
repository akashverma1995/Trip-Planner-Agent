import time
import threading
from typing import Any, Optional


class FlightCache:
    """
    Thread-safe in-memory cache with Time-To-Live (TTL) expiration.
    Reduces external API costs, avoids rate-limiting, and speeds up repeated queries.
    """

    def __init__(self, default_ttl: int = 1800):  # Default 30 minutes
        self.default_ttl = default_ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            record = self._store.get(key)
            if not record:
                return None
            expires_at, value = record
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl
        with self._lock:
            self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @staticmethod
    def build_cache_key(dep_iata: Optional[str], arr_iata: Optional[str], date: Optional[str] = None) -> str:
        dep = (dep_iata or "ALL").upper()
        arr = (arr_iata or "ALL").upper()
        dt = date or "LATEST"
        return f"flight:{dep}:{arr}:{dt}"

