# llm.py
"""
Handles the call to the local Ollama instance and makes sure the model
returns ONLY a well-formed HTML document.
"""

import httpx
import re

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "llama3"          # change if you pulled a different model


# --------------------------------------------------------------------------- #
# fallback stub (when Ollama is down or the request errors out)
# --------------------------------------------------------------------------- #
def _stub_html(html_http: str) -> str:
    return f"""
<!doctype html>
<html>
  <head><title>stub clone</title></head>
  <body style='font-family:sans-serif;padding:2rem'>
    <h1>stub clone (ollama not running)</h1>
    <p>snippet of the raw HTML we fetched:</p>
    <pre style='white-space:pre-wrap;background:#eee;padding:1rem'>{html_http[:2000]}</pre>
  </body>
</html>
"""


# --------------------------------------------------------------------------- #
# main entry
# --------------------------------------------------------------------------- #
def generate_clone_html(html_http: str, dom_playwright: str, shot_b64: str) -> str:
    """
    html_http      – raw HTML fetched via httpx GET
    dom_playwright – DOM string after JS execution (Playwright)
    shot_b64       – base-64 PNG screenshot (may be empty)
    """

    # ---- 1. build prompt -------------------------------------------------- #
    system_message = (
        "you output ONE and ONLY ONE complete html document and nothing else."
    )

    user_message = (
        "~> <RAW_HTML>\n"
        + html_http[:12000] +
        "\n</RAW_HTML>\n\n"

        "~> <PLAYWRIGHT_DOM>\n"
        + dom_playwright[:12000] +
        "\n</PLAYWRIGHT_DOM>\n\n"

        "~> <SCREENSHOT_BASE64>\n"
        "visual context only – do *not* embed this string in your final html.\n"
        + shot_b64[:8000] +
        "\n</SCREENSHOT_BASE64>\n\n"

        # explicit instructions
        "recreate the site **exactly as it exists** – do NOT invent new text or sections.\n"
        "- inline all css (no external assets)\n"
        "- replace actual images with simple placeholders\n"
        "‼ respond with the html document ONLY – begin with <!DOCTYPE html> and end with </html>.\n"
        "‼ do NOT wrap the output in back-ticks or markdown fences.\n"
        "‼ do NOT add commentary before or after the html."
    )

    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user",   "content": user_message},
        ],
    }

    # ---- 2. call Ollama --------------------------------------------------- #
    try:
        r = httpx.post(OLLAMA_URL, json=body, timeout=90)
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"]
    except Exception:
        return _stub_html(html_http)

    # ---- 3. post-filter / sanitise --------------------------------------- #
    raw = raw.strip()

    # strip markdown code fences if any
    if raw.startswith("```"):
        raw = re.sub(r"^```[^\n]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    # grab from first <!DOCTYPE or <html to last </html>
    m = re.search(r"(?is)(<!doctype html|<html)(.*)</html>", raw)
    if m:
        cleaned = m.group(0)
    else:
        cleaned = raw  # fallback – maybe the model listened

    return cleaned.strip()
