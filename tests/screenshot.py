"""截图所有页面"""
import asyncio
from playwright.async_api import async_playwright

async def take_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 400, "height": 800})

        await page.goto("http://localhost:8000", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(8)
        await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/panel.png")
        print("✅ 面板页截图完成")

        await browser.close()

asyncio.run(take_screenshots())
