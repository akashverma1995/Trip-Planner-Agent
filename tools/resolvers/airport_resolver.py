import re
from typing import Optional, Tuple, List
import airportsdata
import pycountry

from tools.data.airport_data import (
    COUNTRY_ALIASES,
    COUNTRY_MAIN_AIRPORT,
    CITY_MAIN_AIRPORT,
)


class AirportResolver:
    """
    Dedicated geocoding and NLP route parser service.
    Translates free-form location text into standardized IATA 3-letter codes.
    """

    def __init__(self):
        self.airports = airportsdata.load("IATA")

    @staticmethod
    def clean_text(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        stop_words = {
            "flight", "flights", "ticket", "tickets", "trip", "travel",
            "plan", "complete", "days", "day", "including", "hotel",
            "hotels", "sightseeing", "under", "budget", "info", "information"
        }
        words = [w for w in text.split() if w not in stop_words]
        return " ".join(words).strip()

    def country_name_to_code(self, text: str) -> Optional[str]:
        cleaned = self.clean_text(text)

        if cleaned in COUNTRY_ALIASES:
            return COUNTRY_ALIASES[cleaned]

        try:
            country = pycountry.countries.lookup(cleaned)
            return country.alpha_2
        except LookupError:
            pass

        for country in pycountry.countries:
            if country.name.lower() in cleaned:
                return country.alpha_2

        for alias, code in COUNTRY_ALIASES.items():
            if alias in cleaned:
                return code

        return None

    def airport_country_matches(self, airport: dict, country_code: str) -> bool:
        airport_country = str(airport.get("country", "")).upper().strip()
        if airport_country == country_code:
            return True

        try:
            country = pycountry.countries.get(alpha_2=country_code)
            if country and airport_country.lower() == country.name.lower():
                return True
        except Exception:
            pass

        return False

    def get_best_airport_for_country(self, country_code: str) -> Optional[str]:
        preferred = COUNTRY_MAIN_AIRPORT.get(country_code)
        if preferred and preferred in self.airports:
            return preferred

        candidates = []
        for iata, airport in self.airports.items():
            if not iata:
                continue

            if self.airport_country_matches(airport, country_code):
                name = str(airport.get("name", "")).lower()
                city = str(airport.get("city", "")).lower()
                score = 0
                if "international" in name:
                    score += 50
                if "intl" in name:
                    score += 40
                if "capital" in name:
                    score += 20
                if city:
                    score += 5
                candidates.append((score, iata))

        if not candidates:
            return None

        candidates.sort(reverse=True)
        return candidates[0][1]

    def resolve_location_to_iata(self, location: str) -> Optional[str]:
        """
        Hierarchical resolver:
        1. 3-letter IATA code directly
        2. Preferred City / State Dictionary
        3. Country Preferred Airport
        4. Fuzzy Airport Database Match
        """
        if not location:
            return None

        raw_location = location.strip()

        # Direct 3-letter IATA code
        if re.fullmatch(r"[A-Za-z]{3}", raw_location):
            code = raw_location.upper()
            if code in self.airports:
                return code

        location_clean = self.clean_text(raw_location)
        if not location_clean:
            return None

        # Preferred city / state match
        if location_clean in CITY_MAIN_AIRPORT:
            return CITY_MAIN_AIRPORT[location_clean]

        # Preferred country match
        country_code = self.country_name_to_code(location_clean)
        if country_code:
            airport = self.get_best_airport_for_country(country_code)
            if airport:
                return airport

        # Fuzzy search across full airport database
        city_matches = []
        for iata, airport in self.airports.items():
            city = str(airport.get("city", "")).lower().strip()
            name = str(airport.get("name", "")).lower().strip()
            score = 0

            if city == location_clean:
                score += 100
            elif location_clean in city:
                score += 70

            if location_clean in name:
                score += 50

            if "international" in name:
                score += 10

            if score > 0:
                city_matches.append((score, iata))

        if city_matches:
            city_matches.sort(reverse=True)
            return city_matches[0][1]

        return None

    def find_location_mentions(self, query: str) -> List[str]:
        q = query.lower()
        mentions = []

        for alias in COUNTRY_ALIASES:
            if re.search(rf"\b{re.escape(alias)}\b", q):
                mentions.append(alias)

        for country in pycountry.countries:
            name = country.name.lower()
            if len(name) >= 4 and re.search(rf"\b{re.escape(name)}\b", q):
                mentions.append(name)

        for city in CITY_MAIN_AIRPORT:
            if re.search(rf"\b{re.escape(city)}\b", q):
                mentions.append(city)

        unique_mentions = []
        for item in mentions:
            if item not in unique_mentions:
                unique_mentions.append(item)

        return unique_mentions

    def parse_route(self, query: str, default_origin: str = "BLR") -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts origin and destination IATA codes from natural language query.
        """
        q = query.strip()
        q_lower = q.lower()

        # Global queries
        global_keywords = [
            "all country", "all countries", "global flight", "global flights",
            "all flight", "all flights", "worldwide flight", "worldwide flights",
        ]
        if any(keyword in q_lower for keyword in global_keywords):
            return None, None

        # Direct IATA codes (e.g. DXB to DEL)
        codes = re.findall(r"\b[A-Z]{3}\b", q)
        if len(codes) >= 2:
            return codes[0].upper(), codes[1].upper()

        # Pattern: from X to Y
        match = re.search(
            r"\bfrom\s+(.+?)\s+\bto\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            dep = self.resolve_location_to_iata(match.group(1))
            arr = self.resolve_location_to_iata(match.group(2))
            if dep or arr:
                return dep, arr

        # Pattern: to Y from X
        match = re.search(
            r"\bto\s+(.+?)\s+\bfrom\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
            q_lower,
        )
        if match:
            arr = self.resolve_location_to_iata(match.group(1))
            dep = self.resolve_location_to_iata(match.group(2))
            if dep or arr:
                return dep, arr

        # Pattern: <destination> (trip|travel|tour|vacation|visit) from <origin>
        match = re.search(
            r"(.+?)\s+(?:trip|travel|tour|vacation|visit|holiday)\s+from\s+(.+?)(?:[.!?]|$)",
            q_lower,
        )
        if match:
            arr = self.resolve_location_to_iata(match.group(1))
            dep = self.resolve_location_to_iata(match.group(2))
            if dep or arr:
                return dep, arr

        # Pattern: X to Y
        match = re.search(r"\b([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:[.!?]|$)", q_lower)
        if match:
            dep = self.resolve_location_to_iata(match.group(1))
            arr = self.resolve_location_to_iata(match.group(2))
            if dep and arr:
                return dep, arr

        # Pattern: from X
        match = re.search(r"\bfrom\s+(.+?)(?:[.!?]|$)", q_lower)
        if match:
            origin_text = match.group(1)
            dep = self.resolve_location_to_iata(origin_text)
            mentions = self.find_location_mentions(q)
            other_mentions = [m for m in mentions if self.clean_text(m) not in self.clean_text(origin_text)]
            if other_mentions:
                arr = self.resolve_location_to_iata(other_mentions[0])
                return dep, arr
            return dep, None

        # Pattern: to X
        match = re.search(r"\bto\s+(.+?)(?:[.!?]|$)", q_lower)
        if match:
            arr = self.resolve_location_to_iata(match.group(1))
            return None, arr

        # Mentions heuristic
        mentions = self.find_location_mentions(q)
        if len(mentions) >= 2:
            from_mention = None
            to_mention = None
            for m in mentions:
                if re.search(rf"\bfrom\s+{re.escape(m)}\b", q_lower):
                    from_mention = m
                elif re.search(rf"\bto\s+{re.escape(m)}\b", q_lower):
                    to_mention = m

            if from_mention and to_mention:
                return self.resolve_location_to_iata(from_mention), self.resolve_location_to_iata(to_mention)
            elif from_mention:
                other = [m for m in mentions if m != from_mention][0]
                return self.resolve_location_to_iata(from_mention), self.resolve_location_to_iata(other)
            elif to_mention:
                other = [m for m in mentions if m != to_mention][0]
                return self.resolve_location_to_iata(other), self.resolve_location_to_iata(to_mention)
            else:
                return self.resolve_location_to_iata(mentions[0]), self.resolve_location_to_iata(mentions[1])

        if len(mentions) == 1:
            loc = mentions[0]
            if re.search(rf"\bfrom\s+{re.escape(loc)}\b", q_lower):
                return self.resolve_location_to_iata(loc), None
            return default_origin, self.resolve_location_to_iata(loc)

        return None, None

