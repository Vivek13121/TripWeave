// --- Modernized App with Tabs, Timeline, Cards ---
import { useState, useEffect, useRef } from "react";
import "./App.css";
import { validateLocation } from "./cityToIATA";

const TABS = [
  { key: "itinerary", label: "Itinerary Planner" },
  { key: "flights", label: "Flight Search" },
  { key: "hotels", label: "Hotel Search" },
];

function App() {
  // Tab state: default to itinerary, restore from sessionStorage
  const [activeTab, setActiveTab] = useState(() => {
    return sessionStorage.getItem("activeTab") || "itinerary";
  });
  const [messages, setMessages] = useState({
    itinerary: [],
    flights: [],
    hotels: [],
  });
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  // Form state for itinerary planner
  const [itineraryForm, setItineraryForm] = useState({
    number_of_days: 3,
    destination: "",
    travel_style: "balanced",
    budget_level: "medium",
  });
  const [itineraryResult, setItineraryResult] = useState(null);

  // Form state for flight search (one-way only)
  const [flightForm, setFlightForm] = useState({
    origin: "",
    destination: "",
    departure_date: "",
    passengers: 1,
    cabin_class: "economy",
  });
  const [flightResult, setFlightResult] = useState(null);
  const [flightValidationError, setFlightValidationError] = useState(null);

  // Form state for hotel search
  const [hotelForm, setHotelForm] = useState({
    destination: "",
    check_in: "",
    check_out: "",
  });
  const [hotelResult, setHotelResult] = useState(null);

  const [darkMode, setDarkMode] = useState(() => {
    const savedMode = localStorage.getItem("darkMode");
    return savedMode ? JSON.parse(savedMode) : false;
  });
  const inFlightRef = useRef(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    sessionStorage.setItem("activeTab", activeTab);
  }, [activeTab]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeTab]);

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      darkMode ? "dark" : "light"
    );
    localStorage.setItem("darkMode", JSON.stringify(darkMode));
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode((d) => !d);

  const getLoadingMessage = (userMessage) => {
    const lowerMessage = userMessage.toLowerCase();
    if (lowerMessage.includes("flight")) {
      return "Searching flights...";
    } else if (lowerMessage.includes("hotel")) {
      return "Finding hotels...";
    } else if (
      lowerMessage.includes("trip") ||
      lowerMessage.includes("travel")
    ) {
      return "Planning your trip...";
    } else {
      return "Searching...";
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (isSending || inFlightRef.current) return;
    if (!input.trim()) return;
    const userMessage = input.trim();
    inFlightRef.current = true;
    setIsSending(true);
    setMessages((prev) => ({
      ...prev,
      [activeTab]: [
        ...prev[activeTab].filter((msg) => !msg.isLoading),
        { role: "user", content: userMessage },
      ],
    }));
    setInput("");
    // Add loading indicator
    setMessages((prev) => ({
      ...prev,
      [activeTab]: [
        ...prev[activeTab],
        {
          role: "assistant",
          content: getLoadingMessage(userMessage),
          isLoading: true,
        },
      ],
    }));
    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });
      const data = await response.json();
      setMessages((prev) => ({
        ...prev,
        [activeTab]: prev[activeTab].map((msg, idx) =>
          idx === prev[activeTab].length - 1 && msg.isLoading
            ? {
                role: "assistant",
                content:
                  data.response || data.message || "No response received",
                itinerary: data.itinerary,
                flight_results: data.flight_results,
                hotel_results: data.hotel_results,
              }
            : msg
        ),
      }));
    } catch (error) {
      setMessages((prev) => ({
        ...prev,
        [activeTab]: prev[activeTab].map((msg, idx) =>
          idx === prev[activeTab].length - 1 && msg.isLoading
            ? {
                role: "assistant",
                content:
                  "Error: Could not connect to the backend. Please ensure the server is running.",
              }
            : msg
        ),
      }));
    } finally {
      inFlightRef.current = false;
      setIsSending(false);
    }
  };

  const handleItinerarySubmit = async (e) => {
    e.preventDefault();
    if (isSending || !itineraryForm.destination.trim()) return;
    setIsSending(true);
    setItineraryResult({ isLoading: true });
    try {
      // Simulate the sequential input flow by sending messages
      const inputs = [
        itineraryForm.number_of_days.toString(),
        itineraryForm.destination,
        itineraryForm.travel_style,
        itineraryForm.budget_level,
        "yes", // confirmation
      ];
      let currentResponse = null;
      for (const input of inputs) {
        const response = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: input }),
        });
        currentResponse = await response.json();
      }
      setItineraryResult({
        narration: currentResponse.response,
        itinerary: currentResponse.itinerary,
      });
    } catch (error) {
      setItineraryResult({
        narration:
          "Error: Could not connect to the backend. Please ensure the server is running.",
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleFlightSubmit = async (e) => {
    e.preventDefault();
    if (
      isSending ||
      !flightForm.origin.trim() ||
      !flightForm.destination.trim() ||
      !flightForm.departure_date
    )
      return;

    // Clear previous errors
    setFlightValidationError(null);

    // Validate and convert origin to IATA code
    const originValidation = validateLocation(flightForm.origin);
    if (!originValidation.valid) {
      setFlightValidationError(`Origin: ${originValidation.error}`);
      return;
    }

    // Validate and convert destination to IATA code
    const destinationValidation = validateLocation(flightForm.destination);
    if (!destinationValidation.valid) {
      setFlightValidationError(`Destination: ${destinationValidation.error}`);
      return;
    }

    console.log(
      "🔍 [FRONTEND] Origin:",
      flightForm.origin,
      "→",
      originValidation.iata
    );
    console.log(
      "🔍 [FRONTEND] Destination:",
      flightForm.destination,
      "→",
      destinationValidation.iata
    );

    setIsSending(true);
    setFlightResult({ isLoading: true });

    try {
      // Build query with normalized IATA codes and all search parameters
      const query = `Find flights from ${originValidation.iata} to ${destinationValidation.iata} departing on ${flightForm.departure_date} for ${flightForm.passengers} passenger(s) in ${flightForm.cabin_class} class`;

      console.log("📤 [FRONTEND] Sending query:", query);

      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Parse flight results - they may be strings or objects
      let parsedFlights = [];
      if (data.flight_results && Array.isArray(data.flight_results)) {
        parsedFlights = data.flight_results.map((flight) => {
          if (typeof flight === "string") {
            // Parse string format from backend
            return parseFlightString(flight);
          }
          return flight;
        });
      }

      setFlightResult({
        flights: parsedFlights,
        origin: flightForm.origin,
        destination: flightForm.destination,
      });
    } catch (error) {
      console.error("Flight search error:", error);
      setFlightResult({
        error:
          "Could not connect to the backend. Please ensure the server is running.",
        flights: [],
      });
    } finally {
      setIsSending(false);
    }
  };

  // Helper function to parse flight string from backend
  const parseFlightString = (flightStr) => {
    // Example format: "AI 123 | DEL 10:30 → BOM 12:45 | Duration: 2h 15m | Stops: 0 | Price: INR 5000 | Cabin: ECONOMY"
    try {
      const parts = flightStr.split("|").map((p) => p.trim());
      const flightNumber = parts[0] || "";
      const route = parts[1] || "";
      const duration = parts[2]?.replace("Duration:", "").trim() || "";
      const stops = parts[3]?.replace("Stops:", "").trim() || "0";
      const price = parts[4]?.replace("Price:", "").trim() || "";
      const cabin = parts[5]?.replace("Cabin:", "").trim() || "";

      // Parse route
      const routeParts = route.split("→").map((r) => r.trim());
      const departure = routeParts[0]?.split(" ") || [];
      const arrival = routeParts[1]?.split(" ") || [];

      return {
        flight_number: flightNumber,
        departure: {
          airport: departure[0] || "",
          time: departure[1] || "",
        },
        arrival: {
          airport: arrival[0] || "",
          time: arrival[1] || "",
        },
        duration: duration,
        stops: parseInt(stops) || 0,
        price: price,
        cabin: cabin,
        rawString: flightStr,
      };
    } catch (e) {
      return { rawString: flightStr };
    }
  };

  const handleHotelSubmit = async (e) => {
    e.preventDefault();
    if (isSending || !hotelForm.destination.trim()) return;
    setIsSending(true);
    setHotelResult({ isLoading: true });
    try {
      const query = `Find hotels in ${hotelForm.destination} for check-in on ${hotelForm.check_in} and check-out on ${hotelForm.check_out}`;

      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });
      const data = await response.json();
      setHotelResult({
        narration: data.response,
        hotels: data.hotel_results || [],
      });
    } catch (error) {
      setHotelResult({
        narration:
          "Error: Could not connect to the backend. Please ensure the server is running.",
        hotels: [],
      });
    } finally {
      setIsSending(false);
    }
  };

  const formatMessage = (content) => {
    // ...reuse your section formatting logic if needed...
    return content;
  };

  return (
    <div className="chat-container">
      <div className="app-header">
        <div className="header-brand">TripWeave</div>
        <div className="header-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`header-tab${activeTab === tab.key ? " active" : ""}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      <div className="messages-container">
        {activeTab === "itinerary" ? (
          <div className="itinerary-planner-hero">
            <div className="hero-layout">
              <div className="hero-left">
                <h1 className="hero-main-title">
                  PLAN YOUR
                  <br />
                  PERFECT JOURNEY
                </h1>
                <p className="hero-main-subtitle">
                  Create smart, day-by-day travel plans tailored to your style,
                  pace, and budget.
                </p>
                <div className="hero-action-buttons">
                  <button className="action-pill-btn active">
                    <svg
                      className="pill-icon"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <rect
                        x="3"
                        y="4"
                        width="18"
                        height="18"
                        rx="2"
                        ry="2"
                      ></rect>
                      <line x1="16" y1="2" x2="16" y2="6"></line>
                      <line x1="8" y1="2" x2="8" y2="6"></line>
                      <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    Itinerary Planner
                  </button>
                  <button
                    className="action-pill-btn"
                    onClick={() => setActiveTab("flights")}
                    type="button"
                  >
                    <svg
                      className="pill-icon"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"></path>
                    </svg>
                    Flight Search
                  </button>
                  <button
                    className="action-pill-btn"
                    onClick={() => setActiveTab("hotels")}
                    type="button"
                  >
                    <svg
                      className="pill-icon"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M3 21h18"></path>
                      <path d="M9 8h1"></path>
                      <path d="M14 8h1"></path>
                      <path d="M9 12h1"></path>
                      <path d="M14 12h1"></path>
                      <path d="M9 16h1"></path>
                      <path d="M14 16h1"></path>
                      <path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path>
                    </svg>
                    Hotel Search
                  </button>
                </div>
              </div>
              <div className="hero-right">
                <div className="form-card">
                  <form
                    onSubmit={handleItinerarySubmit}
                    className="compact-form"
                  >
                    <div className="form-field">
                      <label htmlFor="destination">Destination</label>
                      <div className="input-with-icon">
                        <svg
                          className="input-icon"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                          <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                        <input
                          type="text"
                          id="destination"
                          value={itineraryForm.destination}
                          onChange={(e) =>
                            setItineraryForm({
                              ...itineraryForm,
                              destination: e.target.value,
                            })
                          }
                          placeholder=""
                          required
                        />
                      </div>
                    </div>
                    <div className="form-field">
                      <label htmlFor="number_of_days">Number of Days</label>
                      <div className="number-stepper">
                        <button
                          type="button"
                          className="stepper-btn"
                          onClick={() =>
                            setItineraryForm({
                              ...itineraryForm,
                              number_of_days: Math.max(
                                1,
                                itineraryForm.number_of_days - 1
                              ),
                            })
                          }
                        >
                          −
                        </button>
                        <input
                          type="text"
                          id="number_of_days"
                          value={itineraryForm.number_of_days}
                          readOnly
                          className="stepper-input"
                        />
                        <button
                          type="button"
                          className="stepper-btn"
                          onClick={() =>
                            setItineraryForm({
                              ...itineraryForm,
                              number_of_days: Math.min(
                                60,
                                itineraryForm.number_of_days + 1
                              ),
                            })
                          }
                        >
                          +
                        </button>
                      </div>
                    </div>
                    <div className="form-field">
                      <label htmlFor="travel_style">Travel Style</label>
                      <div className="select-with-icon">
                        <svg
                          className="input-icon"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
                        </svg>
                        <select
                          id="travel_style"
                          value={itineraryForm.travel_style}
                          onChange={(e) =>
                            setItineraryForm({
                              ...itineraryForm,
                              travel_style: e.target.value,
                            })
                          }
                        >
                          <option value="relaxed">Relaxed</option>
                          <option value="balanced">Balanced</option>
                          <option value="packed">Packed</option>
                        </select>
                        <svg
                          className="dropdown-arrow"
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                      </div>
                    </div>
                    <div className="form-field">
                      <label htmlFor="budget_level">Budget Level</label>
                      <div className="select-with-icon">
                        <svg
                          className="input-icon"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <line x1="12" y1="1" x2="12" y2="23"></line>
                          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                        </svg>
                        <select
                          id="budget_level"
                          value={itineraryForm.budget_level}
                          onChange={(e) =>
                            setItineraryForm({
                              ...itineraryForm,
                              budget_level: e.target.value,
                            })
                          }
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                        </select>
                        <svg
                          className="dropdown-arrow"
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                      </div>
                    </div>
                    <button
                      type="submit"
                      className="generate-btn"
                      disabled={isSending}
                    >
                      {isSending ? "Planning..." : "Generate Itinerary"}
                    </button>
                  </form>
                </div>
              </div>
            </div>
            {itineraryResult && (
              <div className="itinerary-result fade-in">
                {itineraryResult.isLoading ? (
                  <div className="loading-container">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="loading-text">
                      Planning your itinerary...
                    </span>
                  </div>
                ) : itineraryResult.itinerary ? (
                  <ItineraryTimeline
                    itinerary={itineraryResult.itinerary}
                    narration={itineraryResult.narration}
                  />
                ) : (
                  <div className="itinerary-error">
                    {itineraryResult.narration}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : activeTab === "flights" ? (
          <div className="itinerary-planner-hero">
            <div className="hero-content">
              <div className="hero-left">
                <h1 className="hero-title">Search Flights</h1>
                <p className="hero-subtitle">
                  Find the perfect flights for your journey with real-time
                  availability and best prices.
                </p>
              </div>
              <div className="hero-right">
                <div className="form-card">
                  <form onSubmit={handleFlightSubmit} className="compact-form">
                    <div className="form-field">
                      <label>Origin</label>
                      <div className="input-with-icon">
                        <svg
                          className="input-icon"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                          <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                        <input
                          type="text"
                          value={flightForm.origin}
                          onChange={(e) =>
                            setFlightForm({
                              ...flightForm,
                              origin: e.target.value,
                            })
                          }
                          placeholder="e.g., New York, JFK"
                          required
                        />
                      </div>
                    </div>
                    <div className="form-field">
                      <label>Destination</label>
                      <div className="input-with-icon">
                        <svg
                          className="input-icon"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                          <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                        <input
                          type="text"
                          value={flightForm.destination}
                          onChange={(e) =>
                            setFlightForm({
                              ...flightForm,
                              destination: e.target.value,
                            })
                          }
                          placeholder="e.g., Paris, CDG"
                          required
                        />
                      </div>
                    </div>
                    <div className="form-field">
                      <label>Departure Date</label>
                      <div className="input-with-icon">
                        <svg
                          className="input-icon"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <rect
                            x="3"
                            y="4"
                            width="18"
                            height="18"
                            rx="2"
                            ry="2"
                          ></rect>
                          <line x1="16" y1="2" x2="16" y2="6"></line>
                          <line x1="8" y1="2" x2="8" y2="6"></line>
                          <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        <input
                          type="date"
                          value={flightForm.departure_date}
                          onChange={(e) =>
                            setFlightForm({
                              ...flightForm,
                              departure_date: e.target.value,
                            })
                          }
                          required
                        />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-field">
                        <label>Passengers</label>
                        <div className="input-with-icon">
                          <svg
                            className="input-icon"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                          </svg>
                          <input
                            type="number"
                            min="1"
                            max="9"
                            value={flightForm.passengers}
                            onChange={(e) =>
                              setFlightForm({
                                ...flightForm,
                                passengers: e.target.value,
                              })
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="form-field">
                        <label>Cabin Class</label>
                        <div className="select-with-icon">
                          <svg
                            className="input-icon"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M5 12h14"></path>
                            <path d="M12 5l7 7-7 7"></path>
                          </svg>
                          <select
                            value={flightForm.cabin_class}
                            onChange={(e) =>
                              setFlightForm({
                                ...flightForm,
                                cabin_class: e.target.value,
                              })
                            }
                          >
                            <option value="economy">Economy</option>
                            <option value="premium_economy">
                              Premium Economy
                            </option>
                            <option value="business">Business</option>
                            <option value="first">First Class</option>
                          </select>
                          <svg
                            className="dropdown-arrow"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <polyline points="6 9 12 15 18 9"></polyline>
                          </svg>
                        </div>
                      </div>
                    </div>
                    <button
                      type="submit"
                      className="generate-btn"
                      disabled={isSending}
                    >
                      {isSending ? "Searching..." : "Search Flights"}
                    </button>
                  </form>
                  {flightValidationError && (
                    <div className="validation-error-message">
                      {flightValidationError}
                    </div>
                  )}
                </div>
              </div>
            </div>
            {flightResult && (
              <div className="itinerary-result fade-in">
                {flightResult.isLoading ? (
                  <div className="loading-container">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="loading-text">
                      Searching for flights...
                    </span>
                  </div>
                ) : flightResult.error ? (
                  <div className="itinerary-error">{flightResult.error}</div>
                ) : flightResult.flights && flightResult.flights.length > 0 ? (
                  <FlightCards
                    flights={flightResult.flights}
                    origin={flightResult.origin}
                    destination={flightResult.destination}
                  />
                ) : (
                  <div className="no-results-message">
                    <svg
                      className="no-results-icon"
                      width="64"
                      height="64"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"></path>
                    </svg>
                    <h3>No Flights Found</h3>
                    <p>
                      We couldn't find any flights for this route. Try different
                      dates or destinations.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="itinerary-planner-hero">
            <div className="hero-content">
              <div className="hero-left">
                <h1 className="hero-title">Find Hotels</h1>
                <p className="hero-subtitle">
                  Discover the perfect accommodation for your stay with the best
                  rates and amenities.
                </p>
              </div>
              <div className="hero-right">
                <div className="form-card">
                  <form onSubmit={handleHotelSubmit} className="compact-form">
                    <div className="form-field">
                      <label>Destination</label>
                      <div className="input-with-icon">
                        <svg
                          className="input-icon"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                          <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                        <input
                          type="text"
                          value={hotelForm.destination}
                          onChange={(e) =>
                            setHotelForm({
                              ...hotelForm,
                              destination: e.target.value,
                            })
                          }
                          placeholder="e.g., Tokyo, Japan"
                          required
                        />
                      </div>
                    </div>
                    <div className="form-row">
                      <div className="form-field">
                        <label>Check-in Date</label>
                        <div className="input-with-icon">
                          <svg
                            className="input-icon"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <rect
                              x="3"
                              y="4"
                              width="18"
                              height="18"
                              rx="2"
                              ry="2"
                            ></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                          </svg>
                          <input
                            type="date"
                            value={hotelForm.check_in}
                            onChange={(e) =>
                              setHotelForm({
                                ...hotelForm,
                                check_in: e.target.value,
                              })
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="form-field">
                        <label>Check-out Date</label>
                        <div className="input-with-icon">
                          <svg
                            className="input-icon"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <rect
                              x="3"
                              y="4"
                              width="18"
                              height="18"
                              rx="2"
                              ry="2"
                            ></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                          </svg>
                          <input
                            type="date"
                            value={hotelForm.check_out}
                            onChange={(e) =>
                              setHotelForm({
                                ...hotelForm,
                                check_out: e.target.value,
                              })
                            }
                            required
                          />
                        </div>
                      </div>
                    </div>
                    <button
                      type="submit"
                      className="generate-btn"
                      disabled={isSending}
                    >
                      {isSending ? "Searching..." : "Search Hotels"}
                    </button>
                  </form>
                </div>
              </div>
            </div>
            {hotelResult && (
              <div className="itinerary-result fade-in">
                {hotelResult.isLoading ? (
                  <div className="loading-container">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="loading-text">
                      Searching for hotels...
                    </span>
                  </div>
                ) : hotelResult.hotels && hotelResult.hotels.length > 0 ? (
                  <HotelCards
                    hotels={hotelResult.hotels}
                    narration={hotelResult.narration}
                    city={hotelForm.destination}
                  />
                ) : (
                  <div className="itinerary-error">{hotelResult.narration}</div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ItineraryTimeline({ itinerary, narration }) {
  const [expandedDays, setExpandedDays] = useState({});

  if (!Array.isArray(itinerary) || itinerary.length === 0) return null;

  const toggleDay = (dayNum) => {
    setExpandedDays((prev) => ({
      ...prev,
      [dayNum]: !prev[dayNum],
    }));
  };

  const renderSlotContent = (activities, slotName) => {
    if (!activities || activities.length === 0) {
      return (
        <p className="slot-empty-description">
          Free time — enjoy {slotName} at your own pace, rest, or explore
          spontaneously.
        </p>
      );
    }

    return (
      <div className="slot-activities-detailed">
        {activities.map((activity, idx) => (
          <div key={idx} className="activity-item">
            <span className="activity-name">{activity.name}</span>
            {activity.description && (
              <span className="activity-description">
                {" "}
                — {activity.description}
              </span>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="itinerary-result-wrapper">
      {/* Header Section */}
      <div className="itinerary-hero-header">
        <h1 className="itinerary-main-title">Your Personalized Itinerary</h1>
      </div>

      {/* Main Content: Overview on Left, Day-by-Day on Right */}
      <div className="itinerary-main-content">
        {/* Left: Trip Overview */}
        {narration && (
          <div className="overview-section">
            <h2 className="section-title">Trip Overview</h2>
            <div className="section-text">{narration}</div>
          </div>
        )}

        {/* Right: Day-by-Day Plan */}
        <div className="day-by-day-sidebar">
          <h2 className="sidebar-title">Day-by-Day Plan</h2>

          <div className="accordion-days">
            {itinerary.map((day, idx) => {
              const dayNum = day.day;
              const isExpanded = expandedDays[dayNum];

              return (
                <div
                  key={idx}
                  className={`day-accordion-card ${
                    isExpanded ? "expanded" : ""
                  }`}
                >
                  <button
                    className="day-card-header"
                    onClick={() => toggleDay(dayNum)}
                    aria-expanded={isExpanded}
                  >
                    <div className="day-header-content">
                      <h3 className="day-title">
                        Day {dayNum}: {day.title || "Exploring"}
                      </h3>
                      {day.description && (
                        <p className="day-subtitle">{day.description}</p>
                      )}
                    </div>
                    <span className="expand-toggle">
                      {isExpanded ? "▲" : "▼"}
                    </span>
                  </button>

                  {isExpanded && (
                    <div className="day-card-content">
                      <div className="day-info-grid">
                        <div className="day-details">
                          <div className="time-slots-preview">
                            <div className="time-icon-badge">
                              <svg
                                className="time-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <circle cx="12" cy="12" r="5"></circle>
                                <line x1="12" y1="1" x2="12" y2="3"></line>
                                <line x1="12" y1="21" x2="12" y2="23"></line>
                                <line
                                  x1="4.22"
                                  y1="4.22"
                                  x2="5.64"
                                  y2="5.64"
                                ></line>
                                <line
                                  x1="18.36"
                                  y1="18.36"
                                  x2="19.78"
                                  y2="19.78"
                                ></line>
                                <line x1="1" y1="12" x2="3" y2="12"></line>
                                <line x1="21" y1="12" x2="23" y2="12"></line>
                                <line
                                  x1="4.22"
                                  y1="19.78"
                                  x2="5.64"
                                  y2="18.36"
                                ></line>
                                <line
                                  x1="18.36"
                                  y1="5.64"
                                  x2="19.78"
                                  y2="4.22"
                                ></line>
                              </svg>
                              <span>Morning</span>
                            </div>
                            <div className="time-icon-badge">
                              <svg
                                className="time-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <circle cx="12" cy="12" r="5"></circle>
                                <line x1="12" y1="1" x2="12" y2="3"></line>
                              </svg>
                              <span>Afternoon</span>
                            </div>
                            <div className="time-icon-badge">
                              <svg
                                className="time-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                              </svg>
                              <span>Evening</span>
                            </div>
                          </div>

                          <div className="time-slot">
                            <h4 className="slot-header">
                              <svg
                                className="slot-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <circle cx="12" cy="12" r="5"></circle>
                                <line x1="12" y1="1" x2="12" y2="3"></line>
                                <line x1="12" y1="21" x2="12" y2="23"></line>
                                <line
                                  x1="4.22"
                                  y1="4.22"
                                  x2="5.64"
                                  y2="5.64"
                                ></line>
                                <line
                                  x1="18.36"
                                  y1="18.36"
                                  x2="19.78"
                                  y2="19.78"
                                ></line>
                                <line x1="1" y1="12" x2="3" y2="12"></line>
                                <line x1="21" y1="12" x2="23" y2="12"></line>
                                <line
                                  x1="4.22"
                                  y1="19.78"
                                  x2="5.64"
                                  y2="18.36"
                                ></line>
                                <line
                                  x1="18.36"
                                  y1="5.64"
                                  x2="19.78"
                                  y2="4.22"
                                ></line>
                              </svg>
                              Morning
                            </h4>
                            {renderSlotContent(
                              day.slots?.morning,
                              "the morning"
                            )}
                          </div>

                          <div className="time-slot">
                            <h4 className="slot-header">
                              <svg
                                className="slot-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <circle cx="12" cy="12" r="5"></circle>
                                <line x1="12" y1="1" x2="12" y2="3"></line>
                              </svg>
                              Afternoon
                            </h4>
                            {renderSlotContent(
                              day.slots?.afternoon,
                              "the afternoon"
                            )}
                          </div>

                          <div className="time-slot">
                            <h4 className="slot-header">
                              <svg
                                className="slot-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                              </svg>
                              Evening
                            </h4>
                            {renderSlotContent(
                              day.slots?.evening,
                              "the evening"
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function FlightCards({ flights, origin, destination }) {
  if (!Array.isArray(flights) || flights.length === 0) return null;

  return (
    <div className="flight-results-container">
      <div className="results-header">
        <h2 className="results-title">
          {origin} → {destination}
        </h2>
        <p className="results-count">{flights.length} flights found</p>
      </div>

      <div className="flight-cards-grid">
        {flights.map((flight, idx) => (
          <div className="flight-card-modern" key={idx}>
            {flight.rawString && !flight.flight_number ? (
              // Fallback for unparseable strings
              <div className="flight-card-text">{flight.rawString}</div>
            ) : (
              <>
                <div className="flight-card-header">
                  <div className="airline-info">
                    <span className="flight-number">
                      {flight.flight_number || "N/A"}
                    </span>
                    <span className="cabin-class">
                      {flight.cabin || "Economy"}
                    </span>
                  </div>
                  <div className="price-info">
                    <span className="price">{flight.price || "Price N/A"}</span>
                  </div>
                </div>

                <div className="flight-route">
                  <div className="route-segment">
                    <div className="airport-code">
                      {flight.departure?.airport || "N/A"}
                    </div>
                    <div className="flight-time">
                      {flight.departure?.time || "N/A"}
                    </div>
                  </div>

                  <div className="route-middle">
                    <div className="route-line"></div>
                    <svg
                      className="plane-icon"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"></path>
                    </svg>
                    <div className="route-line"></div>
                  </div>

                  <div className="route-segment">
                    <div className="airport-code">
                      {flight.arrival?.airport || "N/A"}
                    </div>
                    <div className="flight-time">
                      {flight.arrival?.time || "N/A"}
                    </div>
                  </div>
                </div>

                <div className="flight-details">
                  <div className="detail-item">
                    <svg
                      className="detail-icon"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    <span>{flight.duration || "N/A"}</span>
                  </div>
                  <div className="detail-item">
                    <svg
                      className="detail-icon"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="1"></circle>
                      <circle cx="12" cy="5" r="1"></circle>
                      <circle cx="12" cy="19" r="1"></circle>
                    </svg>
                    <span>
                      {flight.stops === 0
                        ? "Non-stop"
                        : `${flight.stops} stop${flight.stops > 1 ? "s" : ""}`}
                    </span>
                  </div>
                  {flight.baggage && (
                    <div className="detail-item">
                      <svg
                        className="detail-icon"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M16 20h4a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-4"></path>
                        <rect x="8" y="6" width="8" height="14" rx="2"></rect>
                        <path d="M12 2v4"></path>
                      </svg>
                      <span>{flight.baggage.checked || "N/A"}</span>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function HotelCards({ hotels, narration, city }) {
  if (!Array.isArray(hotels) || hotels.length === 0) return null;

  return (
    <div className="hotel-results-container">
      <div className="results-header">
        <h2 className="results-title">
          {city ? `Hotels in ${city}` : "Hotel Results"}
        </h2>
        <p className="results-count">{hotels.length} hotels found</p>
      </div>

      {narration && <div className="hotel-narration">{narration}</div>}

      <div className="hotel-cards-grid">
        {hotels.map((hotel, idx) => {
          // Handle legacy string format
          if (typeof hotel === "string") {
            return (
              <div className="hotel-card-modern" key={idx}>
                <div className="hotel-card-text">{hotel}</div>
              </div>
            );
          }

          // Modern structured hotel data
          return (
            <div className="hotel-card-modern" key={idx}>
              {hotel.image && (
                <div className="hotel-image-container">
                  <img
                    src={hotel.image}
                    alt={hotel.name || "Hotel"}
                    className="hotel-image"
                    onError={(e) => {
                      e.target.style.display = "none";
                    }}
                  />
                </div>
              )}

              <div className="hotel-card-content">
                <div className="hotel-card-header">
                  <h3 className="hotel-name">
                    {hotel.name || "Hotel Name N/A"}
                  </h3>
                  <div className="hotel-price">
                    {hotel.price || "Price not available"}
                  </div>
                </div>

                {(hotel.rating || hotel.reviews) && (
                  <div className="hotel-rating-section">
                    {hotel.rating && (
                      <div className="hotel-rating">
                        <svg
                          className="star-icon"
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                        >
                          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                        <span className="rating-value">{hotel.rating}</span>
                      </div>
                    )}
                    {hotel.reviews && (
                      <span className="hotel-reviews">
                        ({hotel.reviews} reviews)
                      </span>
                    )}
                  </div>
                )}

                {hotel.amenities && hotel.amenities.length > 0 && (
                  <div className="hotel-amenities">
                    {hotel.amenities.slice(0, 4).map((amenity, i) => (
                      <span key={i} className="amenity-tag">
                        {amenity}
                      </span>
                    ))}
                    {hotel.amenities.length > 4 && (
                      <span className="amenity-tag">
                        +{hotel.amenities.length - 4} more
                      </span>
                    )}
                  </div>
                )}

                {hotel.link && (
                  <a
                    href={hotel.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hotel-link-btn"
                  >
                    View Details
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                      <polyline points="15 3 21 3 21 9"></polyline>
                      <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;
