"""截图所有页面"""
import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright

PAGES = [
    (0, "panel", "面板"),
    (1, "xinjing", "心境"),
    (2, "jingjie", "境界"),
    (3, "lingshi", "灵石"),
    (4, "tongyu", "统御"),
    (5, "settings", "设置"),
]

async def screenshot_page(idx, name, label):
    port = 8550 + idx
    proc = subprocess.Popen(
        [sys.executable, "tests/page_server.py", str(idx)],
        cwd="/root/.openclaw/workspace/fanrenxiuxian3w",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    await asyncio.sleep(10)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 400, "height": 800})
            await page.goto(f"http://localhost:{port}", wait_until="networkidle", timeout=20000)
            await asyncio.sleep(5)
            path = f"/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/{idx:02d}_{name}.png"
            await page.screenshot(path=path, full_page=True)
            print(f"✅ {label}页 → {name}.png")
            await browser.close()
    finally:
        proc.terminate()
        proc.wait()

async def main():
    for idx, name, label in PAGES:
        await screenshot_page(idx, name, label)
    print("\n🎉 全部截图完成！")

asyncio.run(main())
