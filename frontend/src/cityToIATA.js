// City and Country name to IATA airport code mapping
// This utility helps convert user-friendly city names to airport codes

export const cityToIATA = {
  // India
  delhi: "DEL",
  "new delhi": "DEL",
  mumbai: "BOM",
  bombay: "BOM",
  bangalore: "BLR",
  bengaluru: "BLR",
  chennai: "MAA",
  kolkata: "CCU",
  calcutta: "CCU",
  hyderabad: "HYD",
  pune: "PNQ",
  ahmedabad: "AMD",
  jaipur: "JAI",
  lucknow: "LKO",
  goa: "GOI",
  cochin: "COK",
  kochi: "COK",
  trivandrum: "TRV",
  thiruvananthapuram: "TRV",
  india: "DEL",

  // United States
  "new york": "JFK",
  "new york city": "JFK",
  nyc: "JFK",
  "los angeles": "LAX",
  la: "LAX",
  chicago: "ORD",
  "san francisco": "SFO",
  boston: "BOS",
  washington: "DCA",
  "washington dc": "DCA",
  miami: "MIA",
  seattle: "SEA",
  "las vegas": "LAS",
  orlando: "MCO",
  atlanta: "ATL",
  dallas: "DFW",
  houston: "IAH",
  philadelphia: "PHL",
  phoenix: "PHX",
  denver: "DEN",
  detroit: "DTW",
  minneapolis: "MSP",
  "united states": "JFK",
  usa: "JFK",
  america: "JFK",

  // United Kingdom
  london: "LHR",
  manchester: "MAN",
  birmingham: "BHX",
  glasgow: "GLA",
  edinburgh: "EDI",
  uk: "LHR",
  "united kingdom": "LHR",
  england: "LHR",

  // Europe
  paris: "CDG",
  france: "CDG",
  berlin: "BER",
  munich: "MUC",
  frankfurt: "FRA",
  germany: "FRA",
  rome: "FCO",
  milan: "MXP",
  venice: "VCE",
  italy: "FCO",
  madrid: "MAD",
  barcelona: "BCN",
  spain: "MAD",
  amsterdam: "AMS",
  netherlands: "AMS",
  holland: "AMS",
  brussels: "BRU",
  belgium: "BRU",
  zurich: "ZRH",
  geneva: "GVA",
  switzerland: "ZRH",
  vienna: "VIE",
  austria: "VIE",
  prague: "PRG",
  "czech republic": "PRG",
  dublin: "DUB",
  ireland: "DUB",
  lisbon: "LIS",
  portugal: "LIS",
  athens: "ATH",
  greece: "ATH",
  istanbul: "IST",
  turkey: "IST",
  stockholm: "ARN",
  sweden: "ARN",
  copenhagen: "CPH",
  denmark: "CPH",
  oslo: "OSL",
  norway: "OSL",
  helsinki: "HEL",
  finland: "HEL",
  warsaw: "WAW",
  poland: "WAW",

  // Middle East
  dubai: "DXB",
  uae: "DXB",
  "united arab emirates": "DXB",
  "abu dhabi": "AUH",
  doha: "DOH",
  qatar: "DOH",
  riyadh: "RUH",
  jeddah: "JED",
  "saudi arabia": "RUH",
  "tel aviv": "TLV",
  israel: "TLV",
  cairo: "CAI",
  egypt: "CAI",

  // Asia
  singapore: "SIN",
  tokyo: "NRT",
  japan: "NRT",
  osaka: "KIX",
  beijing: "PEK",
  shanghai: "PVG",
  china: "PEK",
  "hong kong": "HKG",
  taipei: "TPE",
  taiwan: "TPE",
  seoul: "ICN",
  "south korea": "ICN",
  korea: "ICN",
  bangkok: "BKK",
  thailand: "BKK",
  "kuala lumpur": "KUL",
  malaysia: "KUL",
  jakarta: "CGK",
  indonesia: "CGK",
  bali: "DPS",
  manila: "MNL",
  philippines: "MNL",
  "ho chi minh": "SGN",
  hanoi: "HAN",
  vietnam: "HAN",

  // Australia & New Zealand
  sydney: "SYD",
  melbourne: "MEL",
  brisbane: "BNE",
  perth: "PER",
  australia: "SYD",
  auckland: "AKL",
  "new zealand": "AKL",

  // South America
  "sao paulo": "GRU",
  "rio de janeiro": "GIG",
  brazil: "GRU",
  "buenos aires": "EZE",
  argentina: "EZE",
  santiago: "SCL",
  chile: "SCL",
  lima: "LIM",
  peru: "LIM",
  bogota: "BOG",
  colombia: "BOG",

  // Canada
  toronto: "YYZ",
  vancouver: "YVR",
  montreal: "YUL",
  calgary: "YYC",
  canada: "YYZ",

  // Africa
  johannesburg: "JNB",
  "cape town": "CPT",
  "south africa": "JNB",
  nairobi: "NBO",
  kenya: "NBO",
  lagos: "LOS",
  nigeria: "LOS",
  casablanca: "CMN",
  morocco: "CMN",
};

/**
 * Convert a city or country name to IATA airport code
 * @param {string} input - City or country name
 * @returns {string|null} - IATA code or null if not found
 */
export function convertToIATA(input) {
  if (!input) return null;

  // Clean the input: trim, lowercase, remove extra spaces
  const cleanInput = input.trim().toLowerCase().replace(/\s+/g, " ");

  // Check if it's already an IATA code (3 uppercase letters)
  if (/^[A-Z]{3}$/.test(input.trim())) {
    return input.trim().toUpperCase();
  }

  // Look up in mapping
  return cityToIATA[cleanInput] || null;
}

/**
 * Validate if a location can be converted to IATA code
 * @param {string} input - City or country name
 * @returns {{valid: boolean, iata: string|null, error: string|null}}
 */
export function validateLocation(input) {
  if (!input || !input.trim()) {
    return {
      valid: false,
      iata: null,
      error: "Location is required",
    };
  }

  const iata = convertToIATA(input);

  if (!iata) {
    return {
      valid: false,
      iata: null,
      error: `Unable to find airport code for "${input}". Please try a major city name.`,
    };
  }

  return {
    valid: true,
    iata: iata,
    error: null,
  };
}
