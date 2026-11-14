import os
from typing import Optional, List
from tools.models.flight_models import (
    FlightSearchParams,
    FlightSearchResult,
    FlightInfo,
)
from tools.resolvers.airport_resolver import AirportResolver
from tools.cache.ttl_cache import FlightCache
from tools.providers.base_provider import BaseFlightProvider
from tools.providers.aviationstack_provider import AviationStackProvider
from tools.providers.mock_provider import MockFlightProvider


class FlightService:
    """
    Central Flight Domain Service (Facade Pattern).
    Coordinates airport resolution, caching, resilient provider calls, and result composition.
    """

    def __init__(
        self,
        provider: Optional[BaseFlightProvider] = None,
        cache: Optional[FlightCache] = None,
        resolver: Optional[AirportResolver] = None,
        default_origin: str = "BLR",
    ):
        self.resolver = resolver or AirportResolver()
        self.cache = cache or FlightCache(default_ttl=1800)  # 30-min cache
        self.default_origin = os.getenv("DEFAULT_ORIGIN_IATA", default_origin)

        # Provider selection with automatic mock fallback if API key is missing
        if provider:
            self.provider = provider
        else:
            api_key = os.getenv("AVIATIONSTACK_API_KEY")
            if api_key:
                self.provider = AviationStackProvider(api_key=api_key)
            else:
                self.provider = MockFlightProvider()

    def _determine_route_info(self, dep_iata: Optional[str], arr_iata: Optional[str]) -> str:
        if dep_iata and arr_iata:
            return f"Live flights from {dep_iata} to {arr_iata}"
        elif dep_iata:
            return f"Live flights from {dep_iata}"
        elif arr_iata:
            return f"Live flights to {arr_iata}"
        return "Global live flights"

    def search(
        self,
        query: Optional[str] = None,
        dep_iata: Optional[str] = None,
        arr_iata: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 10,
        bypass_cache: bool = False,
    ) -> FlightSearchResult:
        """
        Synchronous flight search.
        Accepts either free-form natural language query OR structured IATA parameters.
        """
        # Resolve route if natural language query provided
        if query and (not dep_iata or not arr_iata):
            resolved_dep, resolved_arr = self.resolver.parse_route(query, self.default_origin)
            dep_iata = dep_iata or resolved_dep
            arr_iata = arr_iata or resolved_arr

        # Check Cache
        cache_key = FlightCache.build_cache_key(dep_iata, arr_iata, date)
        if not bypass_cache:
            cached_flights = self.cache.get(cache_key)
            if cached_flights is not None:
                return FlightSearchResult(
                    success=True,
                    route_info=self._determine_route_info(dep_iata, arr_iata),
                    dep_iata=dep_iata,
                    arr_iata=arr_iata,
                    flights=cached_flights,
                    cached=True,
                )

        # Query Provider
        params = FlightSearchParams(
            dep_iata=dep_iata,
            arr_iata=arr_iata,
            date=date,
            limit=limit,
        )

        try:
            flights: List[FlightInfo] = self.provider.search(params)
            # Store in cache
            self.cache.set(cache_key, flights)

            return FlightSearchResult(
                success=True,
                route_info=self._determine_route_info(dep_iata, arr_iata),
                dep_iata=dep_iata,
                arr_iata=arr_iata,
                flights=flights,
                cached=False,
            )
        except Exception as e:
            return FlightSearchResult(
                success=False,
                route_info=self._determine_route_info(dep_iata, arr_iata),
                dep_iata=dep_iata,
                arr_iata=arr_iata,
                error_message=f"Flight search error ({self.provider.name}): {str(e)}",
            )

    async def search_async(
        self,
        query: Optional[str] = None,
        dep_iata: Optional[str] = None,
        arr_iata: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 10,
        bypass_cache: bool = False,
    ) -> FlightSearchResult:
        """
        Asynchronous flight search for non-blocking FastAPI endpoints.
        """
        if query and (not dep_iata or not arr_iata):
            resolved_dep, resolved_arr = self.resolver.parse_route(query, self.default_origin)
            dep_iata = dep_iata or resolved_dep
            arr_iata = arr_iata or resolved_arr

        cache_key = FlightCache.build_cache_key(dep_iata, arr_iata, date)
        if not bypass_cache:
            cached_flights = self.cache.get(cache_key)
            if cached_flights is not None:
                return FlightSearchResult(
                    success=True,
                    route_info=self._determine_route_info(dep_iata, arr_iata),
                    dep_iata=dep_iata,
                    arr_iata=arr_iata,
                    flights=cached_flights,
                    cached=True,
                )

        params = FlightSearchParams(
            dep_iata=dep_iata,
            arr_iata=arr_iata,
            date=date,
            limit=limit,
        )

        try:
            flights: List[FlightInfo] = await self.provider.search_async(params)
            self.cache.set(cache_key, flights)

            return FlightSearchResult(
                success=True,
                route_info=self._determine_route_info(dep_iata, arr_iata),
                dep_iata=dep_iata,
                arr_iata=arr_iata,
                flights=flights,
                cached=False,
            )
        except Exception as e:
            return FlightSearchResult(
                success=False,
                route_info=self._determine_route_info(dep_iata, arr_iata),
                dep_iata=dep_iata,
                arr_iata=arr_iata,
                error_message=f"Flight search error ({self.provider.name}): {str(e)}",
            )

