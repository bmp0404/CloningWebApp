# talks to a local ollama model
# if ollama isn't running we just spit back a stub so the rest of the flow works

import httpx

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "llama3"      

# fallback html when ollama isn't reachable
def _stub_html(dom: str) -> str:
    return f"""
<!doctype html>
<html><head><title>stub clone</title></head>
<body style='font-family:sans-serif;padding:2rem'>
  <h1>stub clone (ollama not running)</h1>
  <p>showing the first chunk of scraped dom ↓</p>
  <pre style='white-space:pre-wrap;background:#eee;padding:1rem'>{dom[:2000]}</pre>
</body></html>
"""

async def generate_clone_html(dom: str, shot_b64: str) -> str:
    """
    dom  : raw dom html string
    shot_b64 : screenshot in base64 (trimmed to fit context)
    returns single html file produced by the ollama model (or stub)
    """
    # build the prompt asking for just the html, no extra comments
    prompt = (
        "recreate this site as one html file with inline css. "
        "keep layout and colors sorta similar. "
        "you can replace real images with placeholders. "
        "do not add any explanatory notes at the end—only output the final html.\n\n"
        "<DOM>\n" + dom[:12000] + "\n</DOM>\n\n"
        "<SCREENSHOT_BASE64>\n" + shot_b64[:8000] + "\n</SCREENSHOT_BASE64>"
    )

    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "you output clean html only"},
            {"role": "user",   "content": prompt}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=90) as cli:
            r = await cli.post(OLLAMA_URL, json=body)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"]

            # strip any trailing "Note that ..." comments
            marker = "Note that"
            if marker in raw:
                # keep everything before the marker
                cleaned = raw.split(marker)[0].rstrip()
                return cleaned

            return raw

    except Exception:
        # ollama probably isn't running -> return stub so we can still demo
        return _stub_html(dom)
