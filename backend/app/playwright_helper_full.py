# playwright_helper_full.py

import sys
import base64
from playwright.sync_api import sync_playwright

def main():
    if len(sys.argv) < 2:
        print("ERROR: missing URL", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle")

        dom = page.content()
        png_bytes = page.screenshot(full_page=True)
        browser.close()

    shot_b64 = base64.b64encode(png_bytes).decode()

    # print DOM between markers, then the base64 screenshot
    sys.stdout.write("===DOM_START===\n")
    sys.stdout.write(dom)
    sys.stdout.write("\n===DOM_END===\n")
    sys.stdout.write(shot_b64)
    sys.stdout.flush()
    sys.exit(0)

if __name__ == "__main__":
    main()
