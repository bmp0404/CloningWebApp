# llm.py

import httpx
import re
from typing import List

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "llama3"  # change if you pulled a different model
CHUNK_SIZE = 8000 # max chars per chunk
TIMEOUT = 90 # http timeout in seconds


def _stub_html(html_http: str) -> str:
    # fallback html if ollama is down
    return f"""<!doctype html>
<html>
  <head><title>stub clone</title></head>
  <body style='font-family:sans-serif;padding:2rem'>
    <h1>stub clone (ollama not running)</h1>
    <pre>{html_http[:2000]}</pre>
  </body>
</html>"""


def chunk(text: str, size: int) -> List[str]:
    # simple splitter
    return [text[i:i+size] for i in range(0, len(text), size)]


def call_ollama(messages: List[dict], stop: List[str] = None) -> str:
    # send chat request to ollama and clean backticks
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
    # strip markdown fences
    content = re.sub(r"^```[\s\S]*?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return content


def generate_clone_html(html_http: str, dom_playwright: str, shot_b64: str) -> str:
    # build or merge html in chunks via ollama
    try:
        source = dom_playwright or html_http
        source = source[:CHUNK_SIZE * 5]
        parts = chunk(source, CHUNK_SIZE)
        accumulated_html = ""

        for idx, part in enumerate(parts):
            if idx == 0:
                # first chunk: create full doc
                system_msg = (
                    "you are an html cloning assistant."
                    " reply with only the raw html, no explanations or fences."
                    " start with <!DOCTYPE html> and <html>."
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
                # merge new chunk
                system_msg = (
                    "you are an html merging assistant."
                    " reply with only the merged html document."
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
        # if anything fails, return a stub
        return _stub_html(html_http)
