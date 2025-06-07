# main.py

import sys
print(">>> fastapi running under:", sys.executable)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .scraper import get_page_context
from .llm import generate_clone_html
import traceback

app = FastAPI(title="orchids clone api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend domain in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

class CloneIn(BaseModel):
    url: str

class CloneOut(BaseModel):
    html: str

@app.post("/clone", response_model=CloneOut)
def clone_site(data: CloneIn):
    print(">>> /clone called with", data.url)
    try:
        # fetch html, dom snapshot, and screenshot
        html_http, dom_playwright, shot_b64 = get_page_context(data.url)
        # generate the cloned page html
        html = generate_clone_html(html_http, dom_playwright, shot_b64)
        return {"html": html}
    except Exception as e:
        # log error and return 500
        print(">>> error inside /clone")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # start the server
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
