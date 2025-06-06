"""
import os
import httpx
import dotenv

dotenv.load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

SYSTEM = "You write clean HTML with inlined CSS."
PROMPT = "Recreate the following website as ONE self-contained HTML file. Match layout, colors, and typography. Use placeholders for images.

<DOM>
{dom}
</DOM>

<SCREENSHOT_BASE64>
{shot}
</SCREENSHOT_BASE64>"


async def generate_clone_html(dom: str, shot_b64: str) -> str:
    body = {
        "model" : "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "contetn": PROMPT.format(dom=dom[:12000], shot=shot_b64[:8000])}

        ]
    }
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=body, headers=headers
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

        
"""