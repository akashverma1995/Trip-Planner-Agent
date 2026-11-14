import os
import sys
import hashlib
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Ensure parent directory is in sys.path for direct script execution
_parent_dir = str(Path(__file__).resolve().parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

load_dotenv()

from tavily import TavilyClient, AsyncTavilyClient
from tavily.errors import InvalidAPIKeyError, MissingAPIKeyError, UsageLimitExceededError

from tools.models.search_models import SearchResultItem, SearchResponse
from tools.cache.ttl_cache import FlightCache


class TavilyService:
    """
    Enterprise-grade search service wrapping the Tavily API.
    Features:
    - Lazy client initialization (won't crash on import if API key is missing)
    - In-Memory TTL caching (1 hour default to save API credits & reduce latency)
    - Synchronous and asynchronous search methods
    - Typed Pydantic domain models
    - Offline mock fallback for local dev and CI/CD testing
    - Resilient error handling (rate-limit, timeout, network errors)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour cache
        default_max_results: int = 5,
        fallback_to_mock: bool = True,
    ):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.cache = FlightCache(default_ttl=cache_ttl)
        self.default_max_results = default_max_results
        self.fallback_to_mock = fallback_to_mock
        self._sync_client: Optional[TavilyClient] = None
        self._async_client: Optional[AsyncTavilyClient] = None

    def _get_sync_client(self) -> TavilyClient:
        if not self._sync_client:
            if not self.api_key:
                raise MissingAPIKeyError("TAVILY_API_KEY is not set in environment or .env file.")
            self._sync_client = TavilyClient(api_key=self.api_key)
        return self._sync_client

    def _get_async_client(self) -> AsyncTavilyClient:
        if not self._async_client:
            if not self.api_key:
                raise MissingAPIKeyError("TAVILY_API_KEY is not set in environment or .env file.")
            self._async_client = AsyncTavilyClient(api_key=self.api_key)
        return self._async_client

    @staticmethod
    def _build_cache_key(query: str, max_results: int) -> str:
        query_hash = hashlib.md5(query.strip().lower().encode("utf-8")).hexdigest()
        return f"tavily:{query_hash}:{max_results}"

    def _generate_mock_results(self, query: str, max_results: int) -> List[SearchResultItem]:
        """Provides realistic offline mock search results for testing without an API key."""
        return [
            SearchResultItem(
                title=f"Top Recommended Hotels & Stays for {query}",
                url="https://www.booking.com/travel-guide",
                content=(
                    f"Curated list of premium and budget-friendly accommodations for '{query}'. "
                    "Features central locations, free Wi-Fi, breakfast included, and top traveler ratings."
                ),
                score=0.95,
            ),
            SearchResultItem(
                title=f"Ultimate Travel Guide & Attractions for {query}",
                url="https://www.tripadvisor.com/tourism-guide",
                content=(
                    f"Essential travel itinerary and must-visit sightseeing spots for '{query}'. "
                    "Includes local transportation tips, cultural landmarks, and hidden gems."
                ),
                score=0.88,
            ),
            SearchResultItem(
                title=f"Best Neighborhoods & Safe Areas to Stay in {query}",
                url="https://www.lonelyplanet.com/travel-tips",
                content=(
                    "Neighborhood overview detailing proximity to metro stations, shopping districts, "
                    "nightlife, and family-friendly districts for an optimal stay."
                ),
                score=0.82,
            ),
        ][:max_results]

    def _parse_raw_results(self, raw_results: list) -> List[SearchResultItem]:
        items: List[SearchResultItem] = []
        for r in raw_results:
            items.append(
                SearchResultItem(
                    title=r.get("title", "Unknown"),
                    url=r.get("url", ""),
                    content=r.get("content", "").strip(),
                    score=r.get("score"),
                )
            )
        return items

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        bypass_cache: bool = False,
    ) -> SearchResponse:
        """
        Synchronous search with caching and automatic mock fallback.
        """
        limit = max_results or self.default_max_results
        cleaned_query = query.strip()

        if not cleaned_query:
            return SearchResponse(query=query, success=False, error_message="Search query cannot be empty.")

        # Check Cache
        cache_key = self._build_cache_key(cleaned_query, limit)
        if not bypass_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return SearchResponse(
                    query=cleaned_query,
                    results=cached_data,
                    success=True,
                    cached=True,
                )

        # Fallback to Mock if API Key is not configured
        if not self.api_key:
            mock_items = self._generate_mock_results(cleaned_query, limit)
            return SearchResponse(
                query=cleaned_query,
                results=mock_items,
                success=True,
                cached=False,
            )

        # Execute Live Tavily Search
        try:
            client = self._get_sync_client()
            raw_response = client.search(query=cleaned_query, max_results=limit)
            items = self._parse_raw_results(raw_response.get("results", []))
            self.cache.set(cache_key, items)

            return SearchResponse(
                query=cleaned_query,
                results=items,
                success=True,
                cached=False,
            )

        except UsageLimitExceededError:
            return SearchResponse(
                query=cleaned_query,
                success=False,
                error_message="Tavily API monthly usage limit exceeded. Please check your quota.",
            )
        except (InvalidAPIKeyError, MissingAPIKeyError) as e:
            return SearchResponse(
                query=cleaned_query,
                success=False,
                error_message=f"Tavily authentication error: {str(e)}",
            )
        except Exception as exc:
            if self.fallback_to_mock:
                mock_items = self._generate_mock_results(cleaned_query, limit)
                self.cache.set(cache_key, mock_items)
                return SearchResponse(
                    query=cleaned_query,
                    results=mock_items,
                    success=True,
                    cached=False,
                )
            return SearchResponse(
                query=cleaned_query,
                success=False,
                error_message=f"Tavily search failed: {str(exc)}",
            )

    async def search_async(
        self,
        query: str,
        max_results: Optional[int] = None,
        bypass_cache: bool = False,
    ) -> SearchResponse:
        """
        Asynchronous search for non-blocking FastAPI endpoints.
        """
        limit = max_results or self.default_max_results
        cleaned_query = query.strip()

        if not cleaned_query:
            return SearchResponse(query=query, success=False, error_message="Search query cannot be empty.")

        cache_key = self._build_cache_key(cleaned_query, limit)
        if not bypass_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return SearchResponse(
                    query=cleaned_query,
                    results=cached_data,
                    success=True,
                    cached=True,
                )

        if not self.api_key:
            mock_items = self._generate_mock_results(cleaned_query, limit)
            return SearchResponse(
                query=cleaned_query,
                results=mock_items,
                success=True,
                cached=False,
            )

        try:
            client = self._get_async_client()
            raw_response = await client.search(query=cleaned_query, max_results=limit)
            items = self._parse_raw_results(raw_response.get("results", []))
            self.cache.set(cache_key, items)

            return SearchResponse(
                query=cleaned_query,
                results=items,
                success=True,
                cached=False,
            )

        except UsageLimitExceededError:
            return SearchResponse(
                query=cleaned_query,
                success=False,
                error_message="Tavily API monthly usage limit exceeded.",
            )
        except Exception as exc:
            if self.fallback_to_mock:
                mock_items = self._generate_mock_results(cleaned_query, limit)
                self.cache.set(cache_key, mock_items)
                return SearchResponse(
                    query=cleaned_query,
                    results=mock_items,
                    success=True,
                    cached=False,
                )
            return SearchResponse(
                query=cleaned_query,
                success=False,
                error_message=f"Tavily async search failed: {str(exc)}",
            )


# ==============================================================================
# Public API & Backward Compatibility Layer
# ==============================================================================

_tavily_service = TavilyService()


def tavily_search(query: str, max_results: int = 5) -> str:
    """
    Backwards-compatible search function for LangGraph agent (backend.py).
    Returns formatted Markdown string.
    """
    response = _tavily_service.search(query=query, max_results=max_results)
    if not response.success:
        return f"Hotel/Web search error: {response.error_message}"

    formatted_items = []
    for i, item in enumerate(response.results, 1):
        snippet = item.formatted_snippet(max_length=300)
        formatted_items.append(f"{i}. **{item.title}**\n   {item.url}\n   {snippet}")

    return "\n\n".join(formatted_items)


async def tavily_search_async(query: str, max_results: int = 5) -> str:
    """Asynchronous search returning formatted Markdown for FastAPI."""
    response = await _tavily_service.search_async(query=query, max_results=max_results)
    if not response.success:
        return f"Hotel/Web search error: {response.error_message}"

    formatted_items = []
    for i, item in enumerate(response.results, 1):
        snippet = item.formatted_snippet(max_length=300)
        formatted_items.append(f"{i}. **{item.title}**\n   {item.url}\n   {snippet}")

    return "\n\n".join(formatted_items)


def tavily_search_structured(query: str, max_results: int = 5) -> SearchResponse:
    """Structured search returning typed Pydantic SearchResponse model."""
    return _tavily_service.search(query=query, max_results=max_results)


if __name__ == "__main__":
    print("Testing TavilyService (System Design Refactor):\n")
    sample_query = "Best hotels in Tokyo"
    print(f"Query: '{sample_query}'\n")

    # 1. First search (Fetches from live API / Mock)
    result_1 = tavily_search(sample_query)
    print("--- First Search Result ---")
    print(result_1)

    print("\n" + "=" * 60 + "\n")
    print("--- Second Search (Verifying Cache Hit) ---")
    # 2. Second search (Sub-millisecond cache hit)
    structured_res = tavily_search_structured(sample_query)
    print(f"Cached: {structured_res.cached}")
    print(structured_res.to_markdown())
