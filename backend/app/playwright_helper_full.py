# playwright_helper_full.py

"""Playwright helper that fetches a page, purges heavy/unsafe nodes, chunks
large HTML, and prints a lean DOM between ORIGINAL markers expected by the
backend (===DOM_START=== / ===DOM_END===). A base‑64 screenshot follows.
"""

import sys
import io
import base64
from typing import List
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Console‑safety helpers
# ---------------------------------------------------------------------------
# Force UTF‑8 on Windows so back‑slash‑escaped sequences survive the journey.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHAR_LIMIT   = 75_000   # total max chars we keep from the purged DOM
CHUNK_SIZE   = 25_000    # how many chars per printed chunk
TIMEOUT_MS   = 45_000    # navigation timeout

# JavaScript snippet that removes <script>, <noscript>, comments, converts
# <style> tags to text, and strips bulky data-* / on* attributes.
JS_PURGE = """() => {
  const clone = document.documentElement.cloneNode(true);

  // 1) remove <script> and <noscript>
  clone.querySelectorAll('script, noscript').forEach(n => n.remove());

  // 2) flatten <style> -> text (keep CSS rules, drop tag wrapper)
  clone.querySelectorAll('style').forEach(st => {
    const txt = document.createTextNode(st.innerText);
    st.replaceWith(txt);
  });

  // 3) strip HTML comments
  const walker = document.createTreeWalker(clone, NodeFilter.SHOW_COMMENT);
  let node;
  while ((node = walker.nextNode())) node.remove();

  // 4) remove data-* and inline JS attributes
  clone.querySelectorAll('*').forEach(el => {
    [...el.attributes].forEach(attr => {
      if (attr.name.startsWith('data-') || attr.name.startsWith('on')) {
        el.removeAttribute(attr.name);
      }
    });
  });

  return clone.outerHTML;
}"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chunk(text: str, size: int) -> List[str]:
    """Split *text* into chunks of at most *size* characters."""
    return [text[i : i + size] for i in range(0, len(text), size)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("ERROR: missing URL", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(url, timeout=TIMEOUT_MS)
        page.wait_for_load_state("networkidle")

        # Purge + serialise DOM inside the browser context
        dom_raw: str = page.evaluate(JS_PURGE)

        # Screenshot before we close everything
        png_bytes: bytes = page.screenshot(full_page=True)
        browser.close()

    # ---------------------------------------------------------------------
    # Post‑processing: limit size, escape non‑ASCII, chunk
    # ---------------------------------------------------------------------
    dom_trimmed = dom_raw[:CHAR_LIMIT]
    dom_safe    = dom_trimmed.encode("ascii", "backslashreplace").decode("ascii")
    dom_chunks  = chunk(dom_safe, CHUNK_SIZE)

    # ---------------------------------------------------------------------
    # Emit using ORIGINAL markers so existing backend parser recognises them
    # ---------------------------------------------------------------------
    sys.stdout.write("===DOM_START===\n")
    for part in dom_chunks:
        sys.stdout.write(part)
    sys.stdout.write("\n===DOM_END===\n")

    sys.stdout.write("===SCREENSHOT_BASE64_START===\n")
    sys.stdout.write(base64.b64encode(png_bytes).decode())
    sys.stdout.write("\n===SCREENSHOT_BASE64_END===\n")

    sys.stdout.flush()


if __name__ == "__main__":
    main()
