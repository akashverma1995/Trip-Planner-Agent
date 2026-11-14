import os
import sys
from pathlib import Path
import certifi
from dotenv import load_dotenv

# Ensure parent directory is in sys.path for direct script execution
_parent_dir = str(Path(__file__).resolve().parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Ensure SSL certs are correctly configured
load_dotenv()
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import Optional
from tools.models.flight_models import FlightSearchResult, FlightInfo, FlightSearchParams
from tools.flight_service import FlightService
from tools.resolvers.airport_resolver import AirportResolver
from tools.cache.ttl_cache import FlightCache
from tools.providers.aviationstack_provider import AviationStackProvider
from tools.providers.mock_provider import MockFlightProvider

# Default singleton instance of the service
_flight_service = FlightService()


def search_flights(query: str, limit: int = 10) -> str:
    """
    Primary backwards-compatible function for LangGraph agent (backend.py).
    Accepts natural language queries and returns Markdown formatted results.
    """
    result = _flight_service.search(query=query, limit=limit)
    return result.to_markdown()


async def search_flights_async(query: str, limit: int = 10) -> str:
    """
    Async flight search for FastAPI endpoints.
    """
    result = await _flight_service.search_async(query=query, limit=limit)
    return result.to_markdown()


def search_flights_structured(
    query: Optional[str] = None,
    dep_iata: Optional[str] = None,
    arr_iata: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 10,
) -> FlightSearchResult:
    """
    Modern structured API returning Pydantic FlightSearchResult model.
    """
    return _flight_service.search(
        query=query,
        dep_iata=dep_iata,
        arr_iata=arr_iata,
        date=date,
        limit=limit,
    )


# Backwards compatibility helpers
def resolve_location_to_iata(location: str) -> Optional[str]:
    return _flight_service.resolver.resolve_location_to_iata(location)


def parse_route(query: str):
    return _flight_service.resolver.parse_route(query, _flight_service.default_origin)


if __name__ == "__main__":
    print("Testing FlightService (Phase 2 Architecture):\n")
    test_query = "Plan a 7 days India trip from Dubai"
    print(f"Query: '{test_query}'\n")
    
    # 1. First search (cache miss - fetches from API / mock)
    response_1 = search_flights(test_query)
    print(response_1)
    
    print("\n" + "=" * 80 + "\n")
    print("Testing In-Memory Caching (Second run should hit cache):\n")
    # 2. Second search (cache hit)
    response_2 = search_flights(test_query)
    print(response_2)
