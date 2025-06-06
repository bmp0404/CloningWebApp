# test_screenshot.py

import base64
from playwright.sync_api import sync_playwright

def main():
    url = "https://example.com"
    print(f">>> opening {url} in headless browser…")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(url, timeout=30_000)
        page.wait_for_load_state("networkidle")

        # grab raw HTML (just to confirm we can fetch it)
        dom = page.content()
        print(">>> fetched DOM length:", len(dom))

        # take a full-page screenshot
        png_bytes = page.screenshot(full_page=True)
        print(">>> screenshot byte size:", len(png_bytes))

        # save to file so you can inspect it
        with open("example.png", "wb") as f:
            f.write(png_bytes)
        print(">>> saved example.png in the current folder")

        # also print base64 length (what our scraper would send)
        b64 = base64.b64encode(png_bytes).decode()
        print(">>> base64 length:", len(b64))

        browser.close()
    print(">>> finished")

if __name__ == "__main__":
    main()
