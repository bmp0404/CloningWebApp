# scraper.py

import subprocess
import sys
import httpx

def get_page_context(url: str):
    """
    1) Attempt Playwright subprocess (DOM + screenshot)
    2) Always fetch raw HTML via httpx
    3) Return (html_http, dom_playwright, shot_b64)
    4) On any failure, fall back gracefully
    """

    dom_playwright = None
    shot_b64 = ""

    # Try Playwright subprocess for DOM + screenshot
    try:
        print(">>> spawning helper for Playwright (dom + screenshot)")
        proc = subprocess.run(
            [sys.executable, "app/playwright_helper_full.py", url],
            capture_output=True,
            text=True,
            timeout=60
        )
        if proc.returncode != 0:
            print(">>> helper stderr:", proc.stderr.strip())
            raise Exception("playwright_helper_full failed")

        out = proc.stdout
        if "===DOM_START===" not in out or "===DOM_END===" not in out:
            print(">>> invalid helper output format (missing markers)", out[:200])
            raise Exception("invalid helper output format")

        # split out the DOM and the base64 screenshot
        parts = out.split("===DOM_END===\n", 1)
        dom_section = parts[0].split("===DOM_START===\n", 1)[1].rstrip()
        shot_b64 = parts[1].strip()

        dom_playwright = dom_section
        print(f">>> helper returned dom_playwright length={len(dom_section)} chars, shot_b64 length={len(shot_b64)} chars")

    except Exception as e:
        print(">>> Playwright subprocess failed, error:", e)

    # Always fetch raw HTML via httpx
    html_http = ""
    try:
        print(">>> attempting httpx GET for raw HTML")
        r = httpx.get(url, timeout=15)
        r.raise_for_status()
        html_http = r.text
        print(f">>> httpx GET succeeded, html_http length={len(html_http)} chars")
    except Exception as e:
        print(">>> httpx GET failed, error:", e)
        # If DOM from Playwright exists, use it as html_http fallback
        if dom_playwright is not None:
            html_http = dom_playwright
            print(">>> using dom_playwright as html_http fallback")
        else:
            # Last-resort stub
            stub = "<!doctype html><html><body><p>could not fetch page content</p></body></html>"
            html_http = stub
            dom_playwright = stub
            print(">>> returning stub for both html_http and dom_playwright")

    # if playwright never succeeded (dom_playwright is still None), set it to html_http
    if dom_playwright is None:
        dom_playwright = html_http
        print(">>> dom_playwright was None → set to html_http length=", len(html_http))


    return html_http, dom_playwright, shot_b64
