"""Pydantic v2 schema definitions for the Budget Bites API.

This module was migrated from v1 compatibility mode to native v2 to eliminate
mixing-mode warnings. It supports flexible input for SearchRequest including
camelCase and common synonyms (city, state, zip, zipcode, postalCode, etc.).
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SearchRequest(BaseModel):
    # No alias attributes to avoid UnsupportedFieldAttributeWarning; we normalize synonyms manually.
    product_name: Optional[str] = Field(None)
    city_name: Optional[str] = Field(None)
    state_name: Optional[str] = Field(None)
    zip_code: Optional[str] = Field(None)
    min_store_results: Optional[str] = Field(None)
    radius_miles: Optional[str] = Field(None)

    @model_validator(mode="before")
    def normalize_and_validate_location(cls, data):  # type: ignore[override]
        if not isinstance(data, dict):
            return data
        synonyms = {
            "productName": "product_name",
            "cityName": "city_name",
            "stateName": "state_name",
            "zipCode": "zip_code",
            "city": "city_name",
            "state": "state_name",
            "zipcode": "zip_code",
            "zip": "zip_code",
            "postalCode": "zip_code",
            "postal_code": "zip_code",
            "minStoreResults": "min_store_results",
            "radiusMiles": "radius_miles",
        }
        for src, dst in synonyms.items():
            if src in data and dst not in data:
                data[dst] = data[src]
        for k in ("product_name", "city_name", "state_name", "zip_code", "min_store_results", "radius_miles"):
            if k in data:
                val = data[k]
                if isinstance(val, (int, float)) and (k == "zip_code" or k == "min_store_results" or k == "radius_miles"):
                    val = str(int(val))
                if isinstance(val, str):
                    val = val.strip()
                data[k] = val
        # city = (data.get("city_name") or "").strip()
        # state = (data.get("state_name") or "").strip()
        # zipc = (data.get("zip_code") or "").strip()
        # if not zipc and not (city and state):
        #     raise ValueError("Either provide zip_code or both city_name and state_name")
        return data

    @field_validator("product_name")
    def product_required(cls, v: str) -> str:  # noqa: N805
        if not v or not v.strip():
        #     raise ValueError("product name is required")
            return v.strip()
        return v

    # @field_validator("zip_code")
    def validate_zip_code(cls, v: str) -> str:  # noqa: N805
        if v and not v.strip():
            return v.strip()
        #     raise ValueError("zip code must be in format 12345 or 12345-6789")
        return v
    
    # @field_validator("min_store_results")
    def coerce_int_fields_to_string(cls, v: str) -> str:  # noqa: N805
        if v and not v.strip():
            return v.strip()
        return v
    
    # @field_validator("radius_miles")
    def validate_positive_int(cls, v: str) -> str:  # noqa: N805
        if v and not v.strip():
            return v.strip()
        return v


class StoreDetails(BaseModel):
    store_name: str
    store_address: str
    distance_from_zipcode: str
    website: str

    @field_validator("store_name", "store_address", "distance_from_zipcode", "website", mode="before")
    def coerce_details_strings(cls, v):  # noqa: N805
        if v is None:
            return v
        if isinstance(v, (int, float)):
            return str(v)
        return v


class StoreItem(BaseModel):
    product_name: str
    product_image: Optional[str] = None
    product_price: str
    unit_quantity: str
    store_details: StoreDetails

    @field_validator("product_price", mode="before")
    def coerce_price_to_string(cls, v):  # noqa: N805
        # Accept numeric inputs (int/float) and coerce to string to avoid validation errors
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @field_validator("product_name", "unit_quantity", mode="before")
    def coerce_item_strings(cls, v):  # noqa: N805
        if isinstance(v, (int, float)):
            return str(v)
        return v


class Request_Object_Validator(BaseModel):
    field: str
    message: str


class ReasonDetails(BaseModel):
    reason_code: str
    reason_status: str
    reason_details: List[Request_Object_Validator]

class StatusInfo(BaseModel):
    http_code: int
    reason_details: List[ReasonDetails]

class SearchResponse(BaseModel):
    stores_list: List[StoreItem]
    status_info: StatusInfo
    prompt_used: Optional[str] = None
    api_name: Optional[str] = None