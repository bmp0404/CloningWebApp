# scraper.py

import subprocess
import sys
import httpx

def get_page_context(url: str):
    """
    try playwright subprocess for dom + screenshot,
    always httpx GET for html,
    fallback if something breaks
    returns (html_http, dom_playwright, shot_b64)
    """

    dom_playwright = None
    shot_b64 = ""

    # attempt playwright helper
    try:
        print(">>> spawning playwright helper")
        proc = subprocess.run(
            [sys.executable, "app/playwright_helper_full.py", url],
            capture_output=True,
            text=True,
            timeout=60
        )
        if proc.returncode != 0:
            print(">>> helper error:", proc.stderr.strip())
            raise Exception("playwright failed")

        out = proc.stdout
        if "===DOM_START===" not in out:
            print(">>> bad helper output", out[:100])
            raise Exception("invalid helper output")

        # split dom and screenshot from the helper output
        head, tail = out.split("===DOM_END===\n", 1)
        dom_section = head.split("===DOM_START===\n", 1)[1].rstrip()
        shot_b64 = tail.strip()
        dom_playwright = dom_section
        print(f">>> got dom len={len(dom_section)}, shot len={len(shot_b64)}")

    except Exception as e:
        print(">>> playwright step failed:", e)

    # fetch raw html
    html_http = ""
    try:
        print(">>> fetching html via httpx")
        r = httpx.get(url, timeout=15)
        r.raise_for_status()
        html_http = r.text
        print(f">>> httpx html len={len(html_http)}")
    except Exception as e:
        print(">>> httpx failed:", e)
        if dom_playwright:
            html_http = dom_playwright
            print(">>> using dom as html fallback")
        else:
            stub = "<!doctype html><html><body><p>could not fetch page</p></body></html>"
            html_http = stub
            dom_playwright = stub
            print(">>> using stub for html and dom")

    if dom_playwright is None:
        dom_playwright = html_http
        print(">>> dom was none, set to html len=", len(html_http))

    return html_http, dom_playwright, shot_b64
