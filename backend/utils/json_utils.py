import json
import re
from typing import Any


def extract_json_block(text: str) -> str:
    text = text.strip()

    # Remove markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    # Find the first JSON object or array
    obj_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if obj_match:
        return obj_match.group(1)

    arr_match = re.search(r"(\[.*\])", text, flags=re.DOTALL)
    if arr_match:
        return arr_match.group(1)

    return text


def safe_load_json(text: str) -> Any:
    payload = extract_json_block(text)
    return json.loads(payload)