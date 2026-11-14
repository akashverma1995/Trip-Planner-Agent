from abc import ABC, abstractmethod
from typing import List
from tools.models.flight_models import FlightSearchParams, FlightInfo


class BaseFlightProvider(ABC):
    """
    Abstract interface for flight providers (Strategy Pattern).
    Allows swapping AviationStack with Amadeus, Skyscanner, or Mock providers
    without modifying business logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @abstractmethod
    def search(self, params: FlightSearchParams) -> List[FlightInfo]:
        """Synchronously query the flight provider."""
        pass

    @abstractmethod
    async def search_async(self, params: FlightSearchParams) -> List[FlightInfo]:
        """Asynchronously query the flight provider."""
        pass

