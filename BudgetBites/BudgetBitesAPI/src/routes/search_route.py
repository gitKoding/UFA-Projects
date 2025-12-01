from fastapi import APIRouter
from ..validation.schemas import SearchRequest, SearchResponse
from ..services.search_service import SearchService

router = APIRouter(prefix="/api/v1", tags=["search"])

def get_service() -> SearchService:
    # Lazy instantiation avoids startup crashes when external API keys missing.
    # Could be enhanced with caching (singleton) if desired.
    return SearchService()

@router.post("/search", response_model=SearchResponse)
async def search_products(payload: SearchRequest) -> SearchResponse:
    service = get_service()
    return await service.search(payload)
