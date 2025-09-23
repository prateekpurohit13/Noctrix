import requests
import json
from typing import Dict, Any

OLLAMA_API_URL = "http://localhost:11434/api/generate"
FAST_MODEL = "gemma:2b"
SMART_MODEL = "mistral"

def get_llm_response(system_prompt: str, user_prompt: str,  model_name: str = SMART_MODEL, timeout: int = 120, retries: int = 2) -> Dict[str, Any]:
    full_prompt = f"{system_prompt}\n\n{user_prompt}"   
    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "format": "json",
        "stream": False
    }

    for attempt in range(retries):
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
            response.raise_for_status()
            response_json = response.json()
            llm_output_str = response_json.get("response", "{}")
            parsed_data = json.loads(llm_output_str)
            return parsed_data

        except requests.exceptions.RequestException as e:
            print(f"  -> ERROR: LLM request failed on attempt {attempt + 1}: {e}")
            if attempt + 1 == retries:
                raise ConnectionError("LLM service is unavailable after multiple retries.") from e
        except json.JSONDecodeError as e:
            print(f"  -> ERROR: Failed to decode JSON from LLM response on attempt {attempt + 1}: {e}")
            print(f"  -> Raw LLM Output: {llm_output_str}")
            if attempt + 1 == retries:
                raise ValueError("LLM returned invalid JSON after multiple retries.") from e
        except Exception as e:
            print(f"  -> ERROR: An unexpected error occurred during LLM call on attempt {attempt + 1}: {e}")
            if attempt + 1 == retries:
                raise

    return {}