from __future__ import annotations

from fastapi import params, types
import httpx
import json
import re
from typing import Any, Dict, List
from google import genai
from google.genai import types
from ..utils.config import get_setting
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GeminiServiceError(Exception):
    pass

class GeminiService:
    def __init__(self) -> None:
        self.api_key = get_setting("providers.google.generative_ai.api_key")
        self.model = get_setting("providers.google.generative_ai.model")
        # Defer hard failures until call time so app can start without keys (e.g., health checks)
        if not self.api_key:
            logger.warning("Gemini API key not configured; search calls will fail until provided.")
        if not self.model:
            logger.warning("Gemini model not configured; using placeholder 'gemini-2.5-flash'.")
            self.model = "gemini-2.5-flash"
        self.timeout = get_setting("app.http_client_timeout_seconds", 15)

    async def generate_store_list(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Calls the Gemini model with a structured prompt expecting JSON array of store objects.
        Returns a list of dicts on success.
        """
        if not self.api_key:
            raise GeminiServiceError("Gemini API key missing")
        client = genai.Client(api_key=self.api_key)

        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        config = types.GenerateContentConfig(
            tools=[grounding_tool]
        )

        try:
            resp = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:  # google-genai raises library-specific exceptions
            logger.error("Gemini client error: %s", exc)
            raise GeminiServiceError("Failed to call Gemini API") from exc

        # Extract text content from response object (google-genai returns a rich object, not httpx.Response)
        try:
            text_with_citations = self.add_citations(resp)
        except Exception as exc:
            # Fallback: attempt to use plain text if available
            raw_text = getattr(resp, "text", None)
            if not raw_text:
                logger.error("Unexpected Gemini response type; no text available: %r", resp)
                raise GeminiServiceError("Unexpected response format from Gemini API") from exc
            text_with_citations = raw_text
        # Attempt to locate JSON substring
        parsed = self._parse_important_nodes(text_with_citations)
        return parsed

    def add_citations(self, response):
        text = response.text
        
        # Check if grounding metadata exists and is not None
        try:
            if (hasattr(response, 'candidates') and 
                len(response.candidates) > 0 and 
                hasattr(response.candidates[0], 'grounding_metadata') and 
                response.candidates[0].grounding_metadata is not None):
                
                grounding_metadata = response.candidates[0].grounding_metadata
                supports = getattr(grounding_metadata, 'grounding_supports', None)
                chunks = getattr(grounding_metadata, 'grounding_chunks', None)
                
                # Only proceed if we have both supports and chunks
                if supports is not None and chunks is not None:
                    # Sort supports by end_index in descending order to avoid shifting issues when inserting.
                    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

                    for support in sorted_supports:
                        end_index = support.segment.end_index
                        if support.grounding_chunk_indices:
                            # Create citation string like [1](link1)[2](link2)
                            citation_links = []
                            for i in support.grounding_chunk_indices:
                                if i < len(chunks):
                                    uri = chunks[i].web.uri
                                    citation_links.append(f"[{i + 1}]({uri})")

                            citation_string = ", ".join(citation_links)
                            text = text[:end_index] + citation_string + text[end_index:]
                else:
                    print("Note: No grounding metadata available for citations.")
            else:
                print("Note: No grounding metadata found in response.")
        except Exception as e:
            print(f"Warning: Error processing citations: {e}")
        
        return text

    def _parse_important_nodes(self, text_with_citations):
        """
        Parse and display important nodes from the text_with_citations variable.
        Extracts key information like stores, prices, and search details.
        """    
        try:
            # Extract JSON from the text (handles markdown code blocks)
            json_match = re.search(r'```json\n(.*?)\n```', text_with_citations, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON without markdown formatting
                json_text = text_with_citations
            
            # Parse the JSON data with error handling
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as json_error:
                print(f"Warning: JSON parsing error: {json_error}")
                print("Attempting to fix common JSON issues...")
                
                # Try to fix common JSON issues
                fixed_json = json_text
                
                # Fix trailing commas
                fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                
                # Fix unescaped quotes in strings
                fixed_json = re.sub(r'(?<!\\)"(?=(?:[^"\\]|\\.)*"[^"]*$)', '\\"', fixed_json)
                
                # Try parsing again
                try:
                    data = json.loads(fixed_json)
                    print("Successfully parsed JSON after fixing common issues.")
                except json.JSONDecodeError:
                    print("Could not fix JSON automatically. Using empty data structure.")
                    data = []
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Raw text content preview:")
            print(text_with_citations[:500] + "..." if len(text_with_citations) > 500 else text_with_citations)
        except Exception as e:
            print(f"Error displaying important nodes: {e}")
            print("Raw text content preview:")
            print(text_with_citations[:500] + "..." if len(text_with_citations) > 500 else text_with_citations)
        return data