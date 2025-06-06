# fastapi entry point
# exposes /clone so the next.js front end can hit it
import sys
print(">>> FastAPI interpreter:", sys.executable)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .scraper import get_page_context
from .llm import generate_clone_html
import traceback


app = FastAPI(title="orchids clone api")

# allow the next.js dev server to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down later
    allow_methods=["*"],
    allow_headers=["*"],
)

# simple health ping
@app.get("/")
def root():
    return {"ok": True}

# --- cloning endpoint ---

class CloneIn(BaseModel):
    url: str

class CloneOut(BaseModel):
    html: str

@app.post("/clone", response_model=CloneOut)
async def clone_site(data: CloneIn):
    print(">>> /clone was called with URL", data.url)
    try:
        dom, shot_b64 = await get_page_context(data.url)
        html = await generate_clone_html(dom, shot_b64)
        return {"html": html}
    except Exception as e:
        # print the full traceback to diagnose the error
        print(">>> error inside /clone:")
        traceback.print_exc()
        # re-raise with detail so the front end still gets a 500
        raise HTTPException(status_code=500, detail=str(e))


# run with:  uvicorn app.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
