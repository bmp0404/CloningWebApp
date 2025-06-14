
import httpx
import re
from typing import List

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "llama3"       # change if you pulled a different model
CHUNK_SIZE = 8000            # max chars per chunk
TIMEOUT = 90                 # seconds for HTTP requests


def _stub_html(html_http: str) -> str:
    return f"""<!doctype html>
<html>
  <head><title>stub clone</title></head>
  <body style='font-family:sans-serif;padding:2rem'>
    <h1>stub clone (ollama not running)</h1>
    <pre>{html_http[:2000]}</pre>
  </body>
</html>"""


def chunk(text: str, size: int) -> List[str]:
    """Split text into a list of chunks each at most size characters."""
    return [text[i:i+size] for i in range(0, len(text), size)]


def call_ollama(messages: List[dict], stop: List[str] = None) -> str:
    """Send a chat completion request to Ollama and return the cleaned content."""
    body = {
        "model": MODEL_NAME,
        "temperature": 0,
        "top_p": 0.1,
        "messages": messages,
        "max_tokens": 4000,
    }
    if stop:
        body["stop"] = stop
    r = httpx.post(OLLAMA_URL, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    # remove markdown fences if present
    content = re.sub(r"^```[\s\S]*?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return content


def generate_clone_html(html_http: str, dom_playwright: str, shot_b64: str) -> str:
    
    # splits the HTML/DOM into chunks, sends the first chunk to generate a full HTML
    
    try:
        source = dom_playwright or html_http
        # limit total input to avoid overflow
        source = source[:CHUNK_SIZE * 5]
        parts = chunk(source, CHUNK_SIZE)
        accumulated_html = ""

        for idx, part in enumerate(parts):
            if idx == 0:
                # First chunk: generate full document
                system_msg = (
                    "You are an HTML cloning assistant.  "
                    "Respond with _only_ the raw HTML document—no explanations, no code fences, no headers.  "
                    "Begin with `<!DOCTYPE html>` and `<html>` tags.  "
                    "Discard any content that comes before the doctype.  "
                    "If the input chunk contains CSS rules, place them inside a `<style>` element in `<head>`—do not emit them as plain text.  "
                    "Use inline CSS on elements as needed, and placeholders for images."
                )
                user_msg = f"HTML_CHUNK:\n{part}"
                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                    {"role": "user", "content": f"SCREENSHOT_BASE64 (ignore): {shot_b64[:2000]}"}
                ]
                html_resp = call_ollama(messages, stop=["</html>"])
                if not html_resp.endswith("</html>"):
                    html_resp += "</html>"
                accumulated_html = html_resp
            else:
                # Subsequent chunks: merge into existing HTML
                system_msg = (
                    "You are an HTML merging assistant.  "
                    "Respond with _only_ the merged HTML document—no commentary or fences.  "
                    "Do not re-emit `<!DOCTYPE html>` or `<html>` tags; just integrate the new fragment.  "
                    "If the fragment includes CSS, merge it into the existing `<style>` in `<head>` or convert to inline styles—do not print standalone CSS."
                )
                user_msg = f"EXISTING_HTML:\n{accumulated_html}\nNEW_CHUNK:\n{part}"
                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
                merge_resp = call_ollama(messages, stop=["</html>"])
                if not merge_resp.endswith("</html>"):
                    merge_resp += "</html>"
                accumulated_html = merge_resp

        return accumulated_html
    except Exception:
        return _stub_html(html_http)
