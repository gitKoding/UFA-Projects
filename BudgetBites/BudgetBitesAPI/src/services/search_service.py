from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Optional

from ..utils.config import get_setting
from ..utils.logger import get_logger
from ..validation.schemas import ReasonDetails, SearchRequest, StoreDetails, StoreItem, SearchResponse, StatusInfo
from .gemini_service import GeminiService, GeminiServiceError
from .places_service import PlacesService, PlacesServiceError
from ..validation.schemas import Request_Object_Validator

logger = get_logger(__name__)

class SearchService:
    def __init__(self) -> None:
        self.gemini = GeminiService()
        self.places_enabled: bool = bool(get_setting("places.enable_enrichment", True))
        self.enrich_mode: str = get_setting("places.enrich_mode", "missing_only")
        self.max_enrich: int = int(get_setting("places.max_enrich_per_request", 15))

    def _build_prompt(self, req: SearchRequest) -> str:
        min_results = int(str(req.min_store_results).strip())
        if req.zip_code:
            template = get_setting("queries.zip_template")
            prompt_core = template.format(item_name=req.product_name, zipcode=req.zip_code, min_results=min_results, radius_miles=req.radius_miles)
        else:
            template = get_setting("queries.city_state_template")
            prompt_core = template.format(item_name=req.product_name, city_name=req.city_name, state_name=req.state_name, min_results=min_results, radius_miles=req.radius_miles)
        # schema_hint = (
        #     "\nYou must reply with pure JSON. Do not include any commentary or markdown. "
        #     "Return a JSON array of 10-20 items. Each item MUST have exactly these keys: "
        #     "product_name (string), store_name (string), address (string), price (string), unit/quantity (string), website_link (string or empty if unknown)."
        # )
        return prompt_core # + schema_hint

    def _validate_search_request(self, req: SearchRequest) -> Optional[str]:
        """Validate the search request and return error message if invalid."""
        # Early validation patterns for better performance
        PRODUCT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\s]+$")
        ZIP_CODE_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")

        errors = []

        # Validate product name
        product_name = req.product_name.strip() if req.product_name else ""
        if not product_name:
            errors.append(Request_Object_Validator(
                field="product_name",
                message="Product name is required"
            ))
        elif not PRODUCT_NAME_PATTERN.match(product_name):
            errors.append(Request_Object_Validator(
                field="product_name",
                message="Product name contains invalid characters; only letters, numbers, and spaces are allowed"
            ))

        # Validate zip code
        zip_code = req.zip_code.strip() if req.zip_code else ""
        if not zip_code:
            errors.append(Request_Object_Validator(
                field="location",
                message="Zip code is required"
            ))
        elif not ZIP_CODE_PATTERN.match(zip_code):
            errors.append(Request_Object_Validator(
                field="zip_code",
                message="Zip code must be in format 12345 or 12345-6789"
            ))

        # Validate minimum store results setting        
        min_store_results = req.min_store_results.strip() if req.min_store_results else ""
        if not min_store_results or not str(min_store_results).isdigit():
            errors.append(Request_Object_Validator(
                field="min_store_results",
                message="Minimum store results must be a valid number"
            ))

        # Validate radius miles setting
        radius_miles = req.radius_miles.strip() if req.radius_miles else ""
        if not radius_miles or not str(radius_miles).isdigit():
            errors.append(Request_Object_Validator(
                field="radius_miles",
                message="Radius miles must be a valid number"
            ))

        return errors if errors else None

    # Also, create a validation method to check for key fields and their values from default.yaml file
    def _validate_configuration(self) -> Optional[List[Request_Object_Validator]]:
        """Validate required configuration values from default.yaml file."""
        errors = []
        
        llm_api_key = get_setting("providers.google.generative_ai.api_key")
        if not llm_api_key:
            errors.append(Request_Object_Validator(
                field="providers.google.generative_ai.api_key",
                message="Gemini API key configuration is required"
            ))

        llm_model_name = get_setting("providers.google.generative_ai.model")
        if not llm_model_name:
            errors.append(Request_Object_Validator(
                field="providers.google.generative_ai.model",
                message="Gemini model name configuration is required"
            ))
        
        # Check query templates
        zip_template = get_setting("queries.zip_template")
        if not zip_template:
            errors.append(Request_Object_Validator(
                field="queries.zip_template",
                message="Zip code query template is required"
            ))
        
        # city_state_template = get_setting("queries.city_state_template")
        # if not city_state_template:
        #     errors.append(Request_Object_Validator(
        #         field="queries.city_state_template",
        #         message="City/state query template is required"
        #     ))
                
        return errors if errors else None

    async def search(self, req: SearchRequest) -> SearchResponse:
        """
        Search for stores selling a product based on the provided request.
        
        Args:
            req: SearchRequest containing product name and location info
            
        Returns:
            SearchResponse with stores list and status information
        """
        # Early validation and error collection
        validation_errors = self._collect_validation_errors(req)
        
        if validation_errors:
            logger.error("Validation failed with %d errors", len(validation_errors))
            return self._create_error_response(400, "VALIDATION_ERROR", validation_errors)

        # Build prompt and log search details
        prompt = self._build_prompt(req)
        logger.info("Searching for product='%s' location='%s'", 
                    req.product_name, self._format_location(req))

        # Execute Gemini search
        try:
            raw_list = await self.gemini.generate_store_list(prompt)
        except GeminiServiceError as exc:
            logger.error("Gemini search failed: %s", exc)
            error_detail = ReasonDetails(
                reason_code="GEMINI_ERROR",
                reason_status="failure",
                reason_details=[Request_Object_Validator(field="message", message=str(exc))]
            )
            return self._create_error_response(502, "GEMINI_ERROR", [error_detail])

        # Process and map results
        stores = self._process_raw_results(raw_list, req)

        # Enrich with Places API if enabled and we have stores
        if self.places_enabled and stores:
            await self._enrich_with_places(stores, req)

        # Return successful response
        return self._create_success_response(stores, prompt, req)

    def _collect_validation_errors(self, req: SearchRequest) -> List[ReasonDetails]:
        """Collect all validation errors from request and configuration."""
        validation_errors = []

        # Validate search request
        request_errors = self._validate_search_request(req)
        if request_errors:
            validation_errors.append(ReasonDetails(
                reason_code="REQUEST_VALIDATION_ERROR",
                reason_status="failure",
                reason_details=request_errors
            ))

        # Validate configuration
        config_errors = self._validate_configuration()
        if config_errors:
            validation_errors.append(ReasonDetails(
                reason_code="API_CONFIG_VALIDATION_ERROR",
                reason_status="failure",
                reason_details=config_errors
            ))

        return validation_errors

    def _format_location(self, req: SearchRequest) -> str:
        """Format location string for logging."""
        if req.zip_code:
            return req.zip_code
        return f"{req.city_name}, {req.state_name}" if req.city_name and req.state_name else "unknown"

    def _process_raw_results(self, raw_list: Any, req: SearchRequest) -> List[StoreItem]:
        """Process raw Gemini results into StoreItem objects."""
        stores = []
        if isinstance(raw_list, list) and raw_list:
            for item in raw_list:
                stores.append(self._map_raw_item(item))
            if not stores:
                logger.warning("No valid store items found in Gemini response")
            if stores:
                for s in stores:
                    # Attempt to extract numeric price for sorting
                    price_str = s.product_price.replace("$", "").replace(",", "").strip()
                    try:
                        s._sortable_price = float(price_str)
                    except (ValueError, AttributeError):
                        s._sortable_price = float("inf")
                # Sort stores by numeric price if available
                stores.sort(key=lambda s: getattr(s, "_sortable_price", float("inf")))
                # Clean up temporary sortable attribute
                for s in stores:
                    if hasattr(s, "_sortable_price"):
                        delattr(s, "_sortable_price")
                # Limit to top N results as per request (min_store_results)
                limit = int(str(req.min_store_results).strip())
                if limit and len(stores) > limit:
                    stores = stores[:limit]

        return stores

    def _create_error_response(self, http_code: int, reason_code: str, 
                              reason_details: List[ReasonDetails]) -> SearchResponse:
        """Create standardized error response."""
        status = StatusInfo(
            http_code=http_code,
            reason_code=reason_code,
            reason_status="failure",
            reason_details=reason_details
        )
        return SearchResponse(stores_list=[], status_info=status)

    def _create_success_response(self, stores: List[StoreItem], prompt: str, req: SearchRequest) -> SearchResponse:
        """Create successful search response."""
        requested_min = int(str(req.min_store_results).strip()) if req and req.min_store_results else 0
        status = StatusInfo(
            http_code=200,
            reason_details=[ReasonDetails(
            reason_code="OK",
            reason_status="success",
            reason_details=[Request_Object_Validator(
                field="message",
                message=f"Search completed successfully. Found {len(stores)} stores; requested minimum {requested_min}."
            )]
            )]
        )
        
        return SearchResponse(
            stores_list=stores,
            status_info=status,
            prompt_used=prompt,
            api_name=get_setting("app.api_name", "UFA - Budget Bite API")
        )

    def _map_raw_item(self, item: Dict[str, Any]) -> StoreItem:
        # Normalize keys from Gemini output
        product_name = item.get("product_name") or item.get("Product") or ""
        product_image = item.get("product_image") or item.get("item_image") or None
        store_name = item.get("store_name") or item.get("Store") or ""
        address = item.get("address") or item.get("store_address") or ""
        distance_from_zipcode = item.get("distance_from_zipcode") or ""
        price = item.get("price") or item.get("product_price") or ""
        unit_q = item.get("unit/quantity") or item.get("unit_quantity") or item.get("Unit-quantity") or ""
        website = item.get("website_link") or item.get("website") or None
        details = StoreDetails(store_name=store_name, store_address=address, distance_from_zipcode=distance_from_zipcode, website=website)
        return StoreItem(product_name=product_name, product_image=product_image, product_price=price, unit_quantity=unit_q, store_details=details)
    async def _enrich_with_places(self, stores: List[StoreItem], req: SearchRequest) -> None:
        places = PlacesService()
        sem = asyncio.Semaphore(5)

        async def enrich_one(idx: int, store: StoreItem):
            need_address = not store.store_details.store_address or self.enrich_mode == "always"
            need_site = not store.store_details.website or self.enrich_mode == "always"
            if not (need_address or need_site):
                return
            suffix_parts = []
            if req.city_name:
                suffix_parts.append(req.city_name)
            if req.state_name:
                suffix_parts.append(req.state_name)
            if req.zip_code:
                suffix_parts.append(req.zip_code)
            suffix = ", ".join(p for p in suffix_parts if p)
            query = f"{store.store_details.store_name} {suffix}" if suffix else store.store_details.store_name
            async with sem:
                try:
                    found = await places.search_place(query)
                    if not found:
                        return
                    place_id = found.get("place_id")
                    details = await places.get_details(place_id) if place_id else None
                    if details:
                        if need_address and details.get("formatted_address"):
                            store.store_details.store_address = details.get("formatted_address")
                        if need_site and details.get("website"):
                            store.store_details.website = details.get("website")
                except PlacesServiceError as exc:
                    logger.warning("Places enrichment failed for %s: %s", store.store_details.store_name, exc)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning("Unexpected enrichment error for %s: %s", store.store_details.store_name, exc)

        tasks = []
        for idx, s in enumerate(stores[: self.max_enrich]):
            tasks.append(asyncio.create_task(enrich_one(idx, s)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)