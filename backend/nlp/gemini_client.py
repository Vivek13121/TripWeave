"""
Gemini API client with robust rate limiting and error handling.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

DEFAULT_MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

_GEMINI_CALL_SEMAPHORE = asyncio.Semaphore(1)
_LAST_REQUEST_TIME = 0
_MIN_REQUEST_INTERVAL = 2.0  # Increased to 2 seconds between calls
_API_CALL_COUNTER = 0  # Track total API calls


async def _wait_for_rate_limit():
    global _LAST_REQUEST_TIME
    current_time = time.time()
    time_since_last = current_time - _LAST_REQUEST_TIME
    if time_since_last < _MIN_REQUEST_INTERVAL:
        await asyncio.sleep(_MIN_REQUEST_INTERVAL - time_since_last)
    _LAST_REQUEST_TIME = time.time()


async def generate_text(
    prompt: str,
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    generation_config: Optional[dict[str, Any]] = None,
    retry_on_429_once: bool = True,
    max_retries: int = 1,
    timeout: float = 15.0,
    use_google_search: bool = False
) -> str:
    global _API_CALL_COUNTER
    _API_CALL_COUNTER += 1
    search_mode = "with Google Search" if use_google_search else "standard"
    print(f"🤖 [GEMINI] generate_text called (Call #{_API_CALL_COUNTER}, {search_mode}), model={model_name}, timeout={timeout}s")
    if generation_config is None:
        generation_config = {"temperature": 0.1, "max_output_tokens": 4096}
    
    # Enable Google Search grounding if requested
    # Note: Google Search grounding uses a different API - Tool object from google.generativeai.types
    
    async with _GEMINI_CALL_SEMAPHORE:
        print(f"🔒 [GEMINI] Acquired semaphore, waiting for rate limit...")
        await _wait_for_rate_limit()
        print(f"✅ [GEMINI] Rate limit check passed, making API call...")
        
        for attempt in range(max_retries):
            try:
                # Initialize model with or without Google Search tool
                if use_google_search:
                    print(f"🔍 [GEMINI] Initializing model with Google Search grounding...")
                    try:
                        # Use the correct Tool import for Google Search
                        from google.generativeai.types import Tool
                        # Correct tool name: google_search (not google_search_retrieval)
                        google_search_tool = Tool(google_search={})
                        model = genai.GenerativeModel(model_name, tools=[google_search_tool])
                        print(f"✅ [GEMINI] Model initialized with Google Search tool")
                    except Exception as tool_error:
                        print(f"⚠️ [GEMINI] Failed to initialize Google Search tool: {tool_error}")
                        print(f"🔄 [GEMINI] Falling back to standard model without search...")
                        model = genai.GenerativeModel(model_name)
                else:
                    model = genai.GenerativeModel(model_name)
                
                print(f"🚀 [GEMINI] API call attempt {attempt + 1}/{max_retries}")
                
                # Make the API call
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt, generation_config=generation_config),
                    timeout=timeout
                )
                
                if response and response.text:
                    print(f"✅ [GEMINI] Success! Got response: {len(response.text)} chars")
                    return response.text.strip()
                else:
                    print(f"⚠️ [GEMINI] Empty response from API")
                    raise Exception("Empty response")
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"⏳ [GEMINI] Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ [GEMINI] Max retries on timeout")
                    raise Exception("Timeout")
            except Exception as e:
                error_msg = str(e).lower()
                print(f"⚠️ [GEMINI] Error on attempt {attempt + 1}: {type(e).__name__}: {e}")
                if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                    # Don't retry on rate limit - fail immediately to prevent quota exhaustion
                    print(f"❌ [GEMINI] RATE LIMIT HIT - Failing immediately to preserve quota")
                    raise Exception("Rate limit exceeded - not retrying")
                elif attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    print(f"🔄 [GEMINI] Retrying after {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ [GEMINI] Final failure: {e}")
                    raise Exception(f"Failed: {e}")
        raise Exception("Max retries exceeded")
