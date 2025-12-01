# BudgetBitesAPI

FastAPI service that returns a list of stores with pricing for a requested product, using Google's Gemini for discovery and Google Places for optional enrichment.

## Features
- Pydantic v2 models with flexible input parsing: accepts snake_case, camelCase, and synonyms (e.g., `zip`, `zipcode`, `postalCode`).
- Validation: product name required; either (city and state) or `zip_code` required.
- Numeric tolerance: numeric fields received as numbers for otherwise-string fields (e.g., `product_price`, `unit_quantity`, addresses) are coerced to strings.
- Calls Gemini (model configurable) with structured prompts and expects JSON.
- Optional enrichment via Google Places (address, website), with per-request cap.
- Robust error handling and consistent response schema.

## Configuration
- Main file: `config/default.yaml`
  - `app`:
    - `name`: Logical service name
    - `version`: API version string
    - `host`: Bind host (default `0.0.0.0`)
    - `port`: Bind port (default `8082`)
    - `min_store_results`: Minimum stores to request from Gemini
    - `api_name`: API display name included in responses (default `UFA - Budget Bite API`)
  - `providers.google.generative_ai`:
    - `api_key`: Gemini API key
    - `model`: Gemini model (default `gemini-2.5-flash`)
  - `providers.google.places`:
    - `api_key`: Places API key
  - `queries.zip_template`, `queries.city_state_template`: Prompt templates
  - `places`: Enrichment controls (`enable_enrichment`, `enrich_mode`, `max_enrich_per_request`)

- Environment overrides (highest precedence):
  - `GOOGLE_GEMINI_API_KEY`
  - `GOOGLE_GEMINI_MODEL`
  - `GOOGLE_PLACES_API_KEY`

## Run (Windows PowerShell)
```powershell
# 1) Create and activate a venv (optional but recommended)
python -m venv .venv
\.\.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt

# 3) Set your secrets (replace with your keys)
$env:GOOGLE_GEMINI_API_KEY = "<your_ai_key>"
$env:GOOGLE_PLACES_API_KEY = "<your_places_key>"

# 4a) Start via uvicorn module (hot reload)
python -m uvicorn src.server.app:app --host 0.0.0.0 --port 8082 --reload

# 4b) Or run the app file directly (uses config port)
python .\src\server\app.py
```

## API
### Health
GET `/health`

Returns basic service info and status.

### Search
POST `/api/v1/search`

Request body (snake_case):
```json
{
  "product_name": "milk",
  "city_name": "Seattle",
  "state_name": "WA"
}
```
or (with zip code):
```json
{
  "product_name": "eggs",
  "zip_code": "98101"
}
```

Also accepted: camelCase and synonyms, e.g. `productName`, `city`, `state`, `zip`, `zipcode`, `postalCode`.

Example response schema:
```json
{
  "stores_list": [
    {
      "product_name": "eggs",
      "product_price": "$2.99",
      "unit_quantity": "12 ct",
      "store_details": {
        "store_name": "Local Market",
        "store_address": "123 Main St, Seattle, WA 98101",
        "distance_from_zipcode": "1.2 mi",
        "website": "https://localmarket.example.com"
      }
    }
  ],
  "status_info": {
    "http_code": 200,
    "reason_code": "OK",
    "reason_status": "success",
    "reason_details": "Search completed successfully. Returned N stores."
  },
  "prompt_used": "...", 
  "api_name": "UFA - Budget Bite API"
}
```

## Debugging
- VS Code debug configs are included for launching the app and uvicorn.
- Set breakpoints in `src/services/search_service.py` or route handlers.
- For local tests, see `tests/` for examples using `httpx` and `pytest-asyncio`.

## Testing
```powershell
python -m pytest -q
```

## Notes
- The service requests JSON-only responses from Gemini. If it returns non-JSON text, the API will respond with an error status and an empty list.
- Places enrichment is capped per request to limit quota usage.
- On unhandled errors, responses include a `status_info` failure and `api_name` for easier tracing.

## TODO Items
  1. Validate input request
          product name need to be characters only, it cannot have special chars - done
          valid zipcode need to be passed, check for format and validity - done
          city & state combination should be valid - out of scope
  2. Add info/warning/error logging across the app
  3. Status code and their reason details for various usecases like...
          Gemini service call failed
          Incorrect json returned from Gemini
          Unable to parse json
          Unable to establish servicee connection
          Invalid input passed