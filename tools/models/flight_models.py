from typing import Optional, List
from pydantic import BaseModel, Field


class AirportPoint(BaseModel):
    """Represents a departure or arrival airport touchpoint."""
    airport: str = Field(default="Unknown airport")
    iata: str = Field(default="Unknown")
    terminal: Optional[str] = Field(default="N/A")
    gate: Optional[str] = Field(default="N/A")
    scheduled: Optional[str] = Field(default="Unknown")
    delay_minutes: Optional[int] = Field(default=None)

    @property
    def delay_text(self) -> str:
        if self.delay_minutes is not None:
            return f"{self.delay_minutes} minutes"
        return "N/A"


class FlightInfo(BaseModel):
    """Domain model representing a flight offer or status."""
    airline: str = Field(default="Unknown airline")
    flight_number: str = Field(default="Unknown")
    status: str = Field(default="scheduled")
    departure: AirportPoint
    arrival: AirportPoint
    price: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None)

    def to_markdown(self) -> str:
        price_str = f"\nPrice: {self.currency} {self.price}" if self.price else ""
        return f"""
Airline: {self.airline}
Flight: {self.flight_number}
Status: {self.status}{price_str}

Departure:
- Airport: {self.departure.airport}
- IATA: {self.departure.iata}
- Terminal: {self.departure.terminal}
- Gate: {self.departure.gate}
- Scheduled: {self.departure.scheduled}
- Delay: {self.departure.delay_text}

Arrival:
- Airport: {self.arrival.airport}
- IATA: {self.arrival.iata}
- Terminal: {self.arrival.terminal}
- Gate: {self.arrival.gate}
- Scheduled: {self.arrival.scheduled}
- Delay: {self.arrival.delay_text}
""".strip()


class FlightSearchParams(BaseModel):
    """Parameters for flight lookup."""
    dep_iata: Optional[str] = None
    arr_iata: Optional[str] = None
    date: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class FlightSearchResult(BaseModel):
    """Unified container for search results."""
    success: bool = True
    route_info: str = "Global live flights"
    dep_iata: Optional[str] = None
    arr_iata: Optional[str] = None
    flights: List[FlightInfo] = Field(default_factory=list)
    error_message: Optional[str] = None
    cached: bool = False

    def to_markdown(self) -> str:
        if not self.success and self.error_message:
            return self.error_message

        if not self.flights:
            route_text = ""
            if self.dep_iata and self.arr_iata:
                route_text = f" for route {self.dep_iata} to {self.arr_iata}"
            elif self.dep_iata:
                route_text = f" from {self.dep_iata}"
            elif self.arr_iata:
                route_text = f" to {self.arr_iata}"

            return (
                f"No live flight data found{route_text}.\n\n"
                "Note: AviationStack provides live/status flight data, not ticket prices. "
                "For actual fare prices, use a flight-pricing API such as Amadeus."
            )

        cache_badge = " (cached)" if self.cached else ""
        header = f"{self.route_info}{cache_badge}\n\n"
        body = "\n\n---\n\n".join(flight.to_markdown() for flight in self.flights)
        return f"{header}{body}"

