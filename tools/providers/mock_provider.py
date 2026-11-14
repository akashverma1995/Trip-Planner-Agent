from typing import List
from tools.models.flight_models import FlightSearchParams, FlightInfo, AirportPoint
from tools.providers.base_provider import BaseFlightProvider


class MockFlightProvider(BaseFlightProvider):
    """
    Mock flight provider for offline development, integration tests, and CI/CD pipelines.
    Guarantees zero API credit consumption during testing.
    """

    @property
    def name(self) -> str:
        return "MockProvider"

    def _generate_mock_flights(self, params: FlightSearchParams) -> List[FlightInfo]:
        dep = params.dep_iata or "BLR"
        arr = params.arr_iata or "DEL"

        return [
            FlightInfo(
                airline="Mock Air International",
                flight_number="MK-101",
                status="scheduled",
                departure=AirportPoint(
                    airport=f"{dep} International Airport",
                    iata=dep,
                    terminal="T1",
                    gate="A4",
                    scheduled="2026-11-20T10:00:00Z",
                    delay_minutes=0,
                ),
                arrival=AirportPoint(
                    airport=f"{arr} International Airport",
                    iata=arr,
                    terminal="T3",
                    gate="B12",
                    scheduled="2026-11-20T12:45:00Z",
                    delay_minutes=0,
                ),
                price=145.0,
                currency="USD",
            ),
            FlightInfo(
                airline="Express Airways",
                flight_number="EX-204",
                status="scheduled",
                departure=AirportPoint(
                    airport=f"{dep} International Airport",
                    iata=dep,
                    terminal="T2",
                    gate="C8",
                    scheduled="2026-11-20T14:30:00Z",
                    delay_minutes=15,
                ),
                arrival=AirportPoint(
                    airport=f"{arr} International Airport",
                    iata=arr,
                    terminal="T2",
                    gate="D5",
                    scheduled="2026-11-20T17:15:00Z",
                    delay_minutes=10,
                ),
                price=180.0,
                currency="USD",
            ),
        ][:params.limit]

    def search(self, params: FlightSearchParams) -> List[FlightInfo]:
        return self._generate_mock_flights(params)

    async def search_async(self, params: FlightSearchParams) -> List[FlightInfo]:
        return self._generate_mock_flights(params)

