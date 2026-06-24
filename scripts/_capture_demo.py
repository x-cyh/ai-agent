"""Capture demo-01.png from running Streamlit app via Playwright."""
from playwright.sync_api import sync_playwright
from pathlib import Path

OUT = Path("report/assets/demo-01.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
    page = ctx.new_page()
    page.goto("http://localhost:8501/Life_Story", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    page.screenshot(path=str(OUT), full_page=False)
    browser.close()

print(f"OK: {OUT} ({OUT.stat().st_size} bytes)")