import os
import time
from typing import List, Optional, Any
import httpx

from tools.models.flight_models import FlightSearchParams, FlightInfo, AirportPoint
from tools.providers.base_provider import BaseFlightProvider


class AviationStackProvider(BaseFlightProvider):
    """
    Production-grade AviationStack provider with:
    - Async and sync HTTP support via httpx
    - Retry logic with exponential backoff
    - Automatic client-side arrival filtering for free-tier limitations
    - Pydantic model mapping
    """

    BASE_URL = "https://api.aviationstack.com/v1/flights"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0, max_retries: int = 3):
        self.api_key = api_key or os.getenv("AVIATIONSTACK_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "AviationStack"

    def _build_params(self, params: FlightSearchParams) -> dict:
        query_params: dict[str, Any] = {
            "access_key": self.api_key,
            "limit": min(params.limit, 100),
        }
        if params.dep_iata:
            query_params["dep_iata"] = params.dep_iata
        if params.arr_iata:
            query_params["arr_iata"] = params.arr_iata
        return query_params

    def _parse_flight_item(self, item: dict) -> FlightInfo:
        dep = item.get("departure") or {}
        arr = item.get("arrival") or {}

        departure_point = AirportPoint(
            airport=dep.get("airport") or "Unknown departure airport",
            iata=dep.get("iata") or "Unknown",
            terminal=dep.get("terminal") or "N/A",
            gate=dep.get("gate") or "N/A",
            scheduled=dep.get("scheduled") or "Unknown",
            delay_minutes=dep.get("delay"),
        )

        arrival_point = AirportPoint(
            airport=arr.get("airport") or "Unknown arrival airport",
            iata=arr.get("iata") or "Unknown",
            terminal=arr.get("terminal") or "N/A",
            gate=arr.get("gate") or "N/A",
            scheduled=arr.get("scheduled") or "Unknown",
            delay_minutes=arr.get("delay"),
        )

        airline_name = (item.get("airline") or {}).get("name") or "Unknown airline"
        flight_number = (item.get("flight") or {}).get("iata") or "Unknown flight number"
        status = item.get("flight_status") or "scheduled"

        return FlightInfo(
            airline=airline_name,
            flight_number=flight_number,
            status=status,
            departure=departure_point,
            arrival=arrival_point,
        )

    def _filter_and_convert(self, raw_data: list, params: FlightSearchParams) -> List[FlightInfo]:
        flights: List[FlightInfo] = []

        # If arr_iata was specified, filter out flights that do not match the destination
        if params.arr_iata and raw_data:
            exact_matched = [
                item for item in raw_data
                if (item.get("arrival") or {}).get("iata") == params.arr_iata
            ]
            if exact_matched:
                raw_data = exact_matched

        for item in raw_data[:params.limit]:
            flights.append(self._parse_flight_item(item))

        return flights

    def search(self, params: FlightSearchParams) -> List[FlightInfo]:
        if not self.api_key:
            raise ValueError("AVIATIONSTACK_API_KEY is not configured.")

        query_params = self._build_params(params)
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(self.BASE_URL, params=query_params)
                    data = response.json()

                    if "error" in data:
                        err = data["error"]
                        raise RuntimeError(f"API Error {err.get('code')}: {err.get('message')}")

                    raw_flights = data.get("data", [])
                    return self._filter_and_convert(raw_flights, params)

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                time.sleep(0.5 * (2 ** (attempt - 1)))  # Exponential backoff
            except Exception as e:
                raise e

        raise RuntimeError(f"AviationStack failed after {self.max_retries} retries: {last_error}")

    async def search_async(self, params: FlightSearchParams) -> List[FlightInfo]:
        if not self.api_key:
            raise ValueError("AVIATIONSTACK_API_KEY is not configured.")

        query_params = self._build_params(params)
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.BASE_URL, params=query_params)
                    data = response.json()

                    if "error" in data:
                        err = data["error"]
                        raise RuntimeError(f"API Error {err.get('code')}: {err.get('message')}")

                    raw_flights = data.get("data", [])
                    return self._filter_and_convert(raw_flights, params)

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
                import asyncio
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
            except Exception as e:
                raise e

        raise RuntimeError(f"AviationStack failed after {self.max_retries} retries: {last_error}")

