"""Shared utilities."""
import json
import re


def extract_json(text: str) -> dict:
    """
    Extract and parse a JSON object from an LLM response.

    Handles three common failure modes:
      1. Preamble text before the JSON  ("Sure! Here is the JSON: {...}")
      2. Markdown code fences           ("```json\\n{...}\\n```")
      3. Truncated JSON                 (LLM hit max_tokens budget mid-response)

    Truncation recovery: if the JSON is incomplete (missing closing brackets),
    we close any open string literal then close open objects/arrays in LIFO
    order so json.loads() can salvage the partial data with whatever fields
    were fully written before the cut-off.
    """
    text = text.strip()

    # 1. Try direct parse (clean response)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Try extracting from markdown code block ```json ... ```
    code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Extract the first { ... } block (greedy — captures as much as possible)
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    candidate = json_match.group() if json_match else text

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 4. Truncation recovery — attempt to close the incomplete JSON and re-parse
    repaired = _repair_truncated_json(candidate)
    if repaired:
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in response: {text[:300]}")


def _repair_truncated_json(text: str) -> str | None:
    """
    Attempt to close a JSON object that was cut off mid-stream by the LLM.

    Strategy:
      - Walk the string tracking open braces/brackets and whether we are inside
        a string literal (honoring backslash escapes).
      - After the walk, if we ended inside a string, close the string first.
      - Strip any trailing comma (invalid before a closing bracket in JSON).
      - Close open arrays and objects in LIFO order.

    Returns the repaired string, or None if the input doesn't look like JSON.
    """
    if not text or '{' not in text:
        return None

    # Start from the first opening brace
    start = text.index('{')
    fragment = text[start:]

    in_string = False
    escape_next = False
    stack: list[str] = []   # tracks '{' and '[' in open order

    for char in fragment:
        if escape_next:
            escape_next = False
            continue
        if char == '\\' and in_string:
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char in ('{', '['):
            stack.append(char)
        elif char in ('}', ']'):
            if stack:
                stack.pop()

    # Close an open string literal first
    suffix = '"' if in_string else ''
    repaired = (fragment + suffix).rstrip()

    # Strip trailing commas (invalid in JSON before a closing bracket)
    while repaired.endswith(','):
        repaired = repaired[:-1].rstrip()

    # Close all still-open containers in LIFO order
    for opener in reversed(stack):
        repaired += '}' if opener == '{' else ']'

    return repaired