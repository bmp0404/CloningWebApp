# scraper.py

import base64
import asyncio
import httpx
from playwright.sync_api import sync_playwright

def _scrape_playwright(url: str):
    """
    try to grab html + screenshot with Playwright.
    if it errors, we’ll catch upstream.
    """
    print(">>> attempting playwright for", url)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(url, timeout=30_000)
        page.wait_for_load_state("networkidle")

        dom = page.content()
        png_bytes = page.screenshot(full_page=True)
        shot_b64 = base64.b64encode(png_bytes).decode()

        browser.close()

    print(">>> playwright succeeded for", url)
    return dom, shot_b64

async def get_page_context(url: str):
    """
    1) try Playwright (with logs)
    2) if that fails, try raw HTTP GET
    3) if that fails, return a minimal stub
    """
    # 1) Playwright attempt
    try:
        dom, shot_b64 = await asyncio.to_thread(_scrape_playwright, url)
        return dom, shot_b64

    except Exception as e:
        print(">>> playwright failed for", url, "error:", e)

    # 2) HTTP GET fallback
    try:
        print(">>> attempting httpx GET for", url)
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
            response.raise_for_status()
            dom = response.text

        print(">>> httpx GET succeeded for", url)
        return dom, ""  # no screenshot in this branch

    except Exception as e:
        print(">>> httpx GET failed for", url, "error:", e)

    # 3) Last-resort stub
    print(">>> returning stub HTML for", url)
    stub = "<!doctype html><html><body><p>could not fetch page content</p></body></html>"
    return stub, ""
