"""Shared utilities."""
import json
import re


def extract_json(text: str) -> dict:
    """
    Extract JSON from LLM response that may contain preamble text.
    Gemma and other local models often say 'Sure! Here is the JSON:'
    before the actual JSON block.
    """
    text = text.strip()

    # Try direct parse first (clean response)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block ```json ... ```
    code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # Try extracting first { ... } block
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in response: {text[:300]}")