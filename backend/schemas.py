from pydantic import BaseModel
from typing import Optional, Union, Any


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    flight_results: list[str] = []
    hotel_results: list[Union[str, dict[str, Any]]] = []
    itinerary: Optional[list] = None


class HealthResponse(BaseModel):
    status: str
    message: str
