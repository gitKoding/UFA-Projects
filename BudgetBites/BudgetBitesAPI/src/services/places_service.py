from __future__ import annotations

import httpx
from typing import Any, Dict, Optional
from ..utils.config import get_setting
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PlacesServiceError(Exception):
    pass

class PlacesService:
    def __init__(self) -> None:
        self.api_key = get_setting("providers.google.places.api_key") or get_setting("providers.google.generative_ai.api_key")
        if not self.api_key:
            raise PlacesServiceError("Google Places API key missing")
        self.timeout = get_setting("app.http_client_timeout_seconds", 15)
        self.text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    async def search_place(self, query: str) -> Optional[Dict[str, Any]]:
        params = {"query": query, "key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(self.text_search_url, params=params)
            except httpx.HTTPError as exc:
                logger.error("Places Text Search HTTP error: %s", exc)
                raise PlacesServiceError("Failed to call Places Text Search") from exc
        if resp.status_code != 200:
            logger.warning("Places Text Search non-200 %s: %s", resp.status_code, resp.text)
            return None
        data = resp.json()
        results = data.get("results", [])
        return results[0] if results else None

    async def get_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        params = {
            "place_id": place_id,
            "fields": "formatted_address,website,name,url",
            "key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(self.details_url, params=params)
            except httpx.HTTPError as exc:
                logger.error("Places Details HTTP error: %s", exc)
                raise PlacesServiceError("Failed to call Places Details") from exc
        if resp.status_code != 200:
            logger.warning("Places Details non-200 %s: %s", resp.status_code, resp.text)
            return None
        data = resp.json()
        if data.get("status") != "OK":
            return None
        return data.get("result")
