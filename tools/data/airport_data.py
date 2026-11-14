"""
Static Airport & Location Reference Data.
Contains aliases, flagship airports, and city-to-IATA mappings.
Can be updated independently or replaced by a database lookup in the future.
"""

COUNTRY_ALIASES = {
    "india": "IN",
    "bharat": "IN",
    "usa": "US",
    "u.s.a": "US",
    "u.s.": "US",
    "america": "US",
    "united states": "US",
    "uk": "GB",
    "u.k.": "GB",
    "britain": "GB",
    "england": "GB",
    "uae": "AE",
    "dubai": "AE",
    "thailand": "TH",
    "singapore": "SG",
    "malaysia": "MY",
    "maldives": "MV",
    "sri lanka": "LK",
    "indonesia": "ID",
    "bali": "ID",
    "vietnam": "VN",
    "nepal": "NP",
    "bhutan": "BT",
    "mauritius": "MU",
    "switzerland": "CH",
    "swiss": "CH",
    "south korea": "KR",
    "korea": "KR",
    "japan": "JP",
    "china": "CN",
    "qatar": "QA",
    "saudi arabia": "SA",
    "saudi": "SA",
    "turkey": "TR",
    "russia": "RU",
    "bangladesh": "BD",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "netherlands": "NL",
    "amsterdam": "NL",
    "greece": "GR",
    "egypt": "EG",
    "oman": "OM",
}


# Preferred main airport for country-level search
COUNTRY_MAIN_AIRPORT = {
    "IN": "DEL",  # India - Indira Gandhi International Airport (Delhi hub)
    "AE": "DXB",  # UAE - Dubai
    "TH": "BKK",  # Thailand - Bangkok Suvarnabhumi
    "SG": "SIN",  # Singapore - Changi
    "MY": "KUL",  # Malaysia - Kuala Lumpur
    "MV": "MLE",  # Maldives - Male Velana
    "LK": "CMB",  # Sri Lanka - Colombo Bandaranaike
    "ID": "DPS",  # Indonesia - Bali Ngurah Rai
    "VN": "HAN",  # Vietnam - Hanoi Noi Bai
    "NP": "KTM",  # Nepal - Kathmandu Tribhuvan
    "BT": "PBH",  # Bhutan - Paro
    "MU": "MRU",  # Mauritius - Sir Seewoosagur Ramgoolam
    "CH": "ZRH",  # Switzerland - Zurich
    "GB": "LHR",  # UK - London Heathrow
    "US": "JFK",  # USA - New York JFK
    "FR": "CDG",  # France - Paris Charles de Gaulle
    "DE": "FRA",  # Germany - Frankfurt
    "IT": "FCO",  # Italy - Rome Fiumicino
    "ES": "MAD",  # Spain - Madrid Barajas
    "NL": "AMS",  # Netherlands - Amsterdam Schiphol
    "TR": "IST",  # Turkey - Istanbul
    "QA": "DOH",  # Qatar - Doha Hamad
    "SA": "JED",  # Saudi Arabia - Jeddah King Abdulaziz
    "OM": "MCT",  # Oman - Muscat
    "JP": "NRT",  # Japan - Tokyo Narita
    "KR": "ICN",  # South Korea - Incheon
    "CN": "PEK",  # China - Beijing Capital
    "AU": "SYD",  # Australia - Sydney Kingsford Smith
    "CA": "YYZ",  # Canada - Toronto Pearson
    "RU": "SVO",  # Russia - Moscow Sheremetyevo
    "BD": "DAC",  # Bangladesh - Dhaka Hazrat Shahjalal
}


CITY_MAIN_AIRPORT = {
    # Major Indian Metro & Hub Cities
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "ahmedabad": "AMD",
    "pune": "PNQ",

    # Popular Indian Tourist Destinations & State Hubs
    "goa": "GOI",
    "north goa": "GOX",
    "south goa": "GOI",
    "jaipur": "JAI",
    "rajasthan": "JAI",
    "udaipur": "UDR",
    "jodhpur": "JDH",
    "kochi": "COK",
    "cochin": "COK",
    "kerala": "COK",
    "trivandrum": "TRV",
    "thiruvananthapuram": "TRV",
    "calicut": "CCJ",
    "kozhikode": "CCJ",
    "srinagar": "SXR",
    "kashmir": "SXR",
    "leh": "IXL",
    "ladakh": "IXL",
    "varanasi": "VNS",
    "banaras": "VNS",
    "kashi": "VNS",
    "lucknow": "LKO",
    "ayodhya": "AYJ",
    "amritsar": "ATQ",
    "chandigarh": "IXC",
    "shimla": "IXC",
    "manali": "KUU",
    "kullu": "KUU",
    "dharamsala": "DHM",
    "dehradun": "DED",
    "rishikesh": "DED",
    "mussoorie": "DED",
    "uttarakhand": "DED",
    "guwahati": "GAU",
    "assam": "GAU",
    "bhubaneswar": "BBI",
    "odisha": "BBI",
    "indore": "IDR",
    "bhopal": "BHO",
    "patna": "PAT",
    "ranchi": "IXR",
    "bagdogra": "IXB",
    "darjeeling": "IXB",
    "sikkim": "IXB",
    "port blair": "IXZ",
    "andaman": "IXZ",
    "visakhapatnam": "VTZ",
    "vizag": "VTZ",
    "vijayawada": "VGA",
    "coimbatore": "CJB",
    "madurai": "IXM",
    "tirupati": "TIR",
    "mangalore": "IXE",
    "surat": "STV",
    "vadodara": "BDQ",
    "raipur": "RPR",
    "nagpur": "NAG",
    "agra": "AGR",

    # Key International Travel Destinations
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "bangkok": "BKK",
    "phuket": "HKT",
    "singapore": "SIN",
    "kuala lumpur": "KUL",
    "bali": "DPS",
    "male": "MLE",
    "colombo": "CMB",
    "kathmandu": "KTM",
    "hanoi": "HAN",
    "ho chi minh": "SGN",
    "london": "LHR",
    "paris": "CDG",
    "new york": "JFK",
    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",
    "doha": "DOH",
    "istanbul": "IST",
    "toronto": "YYZ",
    "sydney": "SYD",
    "rome": "FCO",
    "madrid": "MAD",
    "frankfurt": "FRA",
    "zurich": "ZRH",
    "amsterdam": "AMS",
    "dhaka": "DAC",
}

