"""Local smoke test for SearchService.

Usage:
  - Run directly: python my_local_test.py
  - Or from VS Code Debug: select this file and run.

Notes:
  - SearchService.search is async and expects a SearchRequest model, not a dict.
  - This script normalizes common field synonyms and runs the coroutine properly.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.services.search_service import SearchService
from src.validation.schemas import SearchRequest


async def main() -> None:
    service = SearchService()

    # Sample data (camelCase/synonyms accepted by SearchRequest model)
    # Get user input for search parameters
    product_name = input("Enter product name: ").strip()
    # city = input("Enter city (optional): ").strip() or None
    # state = input("Enter state (optional): ").strip() or None
    zip_code = input("Enter zip code: ").strip()
    min_store_results = input("Enter minimum store results: ").strip()
    radius_miles = input("Enter radius miles: ").strip()
    
    sample_query = {
      "productName": product_name,
      "zipCode": zip_code if zip_code else None,
      "minStoreResults": min_store_results if min_store_results else None,
      "radiusMiles": radius_miles if radius_miles else None,
    }
    
    # Add optional fields if provided
    # if city:
    #   sample_query["city"] = city
    # if state:
    #   sample_query["state"] = state
    # if zip_code:
    #   try:
    #     sample_query["zip"] = int(zip_code)
    #   except ValueError:
    #     print("Invalid zip code, ignoring...")

    try:
        req = SearchRequest.model_validate(sample_query)
        result = await service.search(req)
        print("Search Results:")
        print(result.model_dump())
    except Exception as e:
        print(f"Error running search_service: {e}")

if __name__ == "__main__":
    asyncio.run(main())