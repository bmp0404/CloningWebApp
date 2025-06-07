# playwright_helper_full.py

# helper to fetch and clean up the page dom, then grab a screenshot
import sys
import io
import base64
from typing import List
from playwright.sync_api import sync_playwright

# ensure utf-8 output on windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# settings
CHAR_LIMIT = 75_000    # max chars from cleaned dom
CHUNK_SIZE = 25_000    # size per output chunk
TIMEOUT_MS = 45_000    # nav timeout in ms

# js snippet to strip scripts, comments, inline attrs, and flatten styles
JS_PURGE = """() => {
  const clone = document.documentElement.cloneNode(true);
  // drop scripts & noscripts
  clone.querySelectorAll('script, noscript').forEach(n => n.remove());
  // turn style tags into text
  clone.querySelectorAll('style').forEach(st => {
    const txt = document.createTextNode(st.innerText);
    st.replaceWith(txt);
  });
  // remove html comments
  const walker = document.createTreeWalker(clone, NodeFilter.SHOW_COMMENT);
  let node;
  while ((node = walker.nextNode())) node.remove();
  // strip data-* and on* attrs
  clone.querySelectorAll('*').forEach(el => {
    [...el.attributes].forEach(attr => {
      if (attr.name.startsWith('data-') || attr.name.startsWith('on')) {
        el.removeAttribute(attr.name);
      }
    });
  });
  return clone.outerHTML;
}"""


def chunk(text: str, size: int) -> List[str]:
    # simple splitter
    return [text[i:i+size] for i in range(0, len(text), size)]


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

        dom_raw = page.evaluate(JS_PURGE)
        png_bytes = page.screenshot(full_page=True)
        browser.close()

    # keep it to char limit and make ascii-safe
    dom_trimmed = dom_raw[:CHAR_LIMIT]
    dom_safe = dom_trimmed.encode("ascii", "backslashreplace").decode("ascii")
    dom_chunks = chunk(dom_safe, CHUNK_SIZE)

    # output dom and screenshot markers
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
