"""用 Playwright 截图测试 UI"""
import asyncio
from playwright.async_api import async_playwright

async def screenshot_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 400, "height": 800})

        # 打开首页（引导页）
        await page.goto("http://localhost:8000", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)
        await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/01_onboarding.png")
        print("✅ 截图1: 引导页")

        # 输入出生年份
        inputs = page.locator("input")
        count = await inputs.count()
        print(f"   找到 {count} 个输入框")
        if count > 0:
            await inputs.first.fill("1998")
            await asyncio.sleep(1)
            await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/02_year_input.png")
            print("✅ 截图2: 输入年份")

            # 点击开始修炼
            buttons = page.locator("button")
            btn_count = await buttons.count()
            print(f"   找到 {btn_count} 个按钮")
            for i in range(btn_count):
                text = await buttons.nth(i).inner_text()
                if "修炼" in text or "开始" in text:
                    await buttons.nth(i).click()
                    print(f"   点击: {text}")
                    break

            await asyncio.sleep(5)
            await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/03_panel.png")
            print("✅ 截图3: 面板页")

            # 点击心境 tab
            nav_items = page.locator("text=心境")
            if await nav_items.count() > 0:
                await nav_items.first.click()
                await asyncio.sleep(3)
                await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/04_xinjing.png")
                print("✅ 截图4: 心境页")

            # 点击境界 tab
            nav_items = page.locator("text=境界")
            if await nav_items.count() > 0:
                await nav_items.first.click()
                await asyncio.sleep(3)
                await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/05_jingjie.png")
                print("✅ 截图5: 境界页")

            # 点击灵石 tab
            nav_items = page.locator("text=灵石")
            if await nav_items.count() > 0:
                await nav_items.first.click()
                await asyncio.sleep(3)
                await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/06_lingshi.png")
                print("✅ 截图6: 灵石页")

            # 点击统御 tab
            nav_items = page.locator("text=统御")
            if await nav_items.count() > 0:
                await nav_items.first.click()
                await asyncio.sleep(3)
                await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/07_tongyu.png")
                print("✅ 截图7: 统御页")

            # 点击设置 tab
            nav_items = page.locator("text=设置")
            if await nav_items.count() > 0:
                await nav_items.first.click()
                await asyncio.sleep(3)
                await page.screenshot(path="/root/.openclaw/workspace/fanrenxiuxian3w/screenshots/08_settings.png")
                print("✅ 截图8: 设置页")

        await browser.close()
        print("\n🎉 UI 截图测试完成！")

asyncio.run(screenshot_test())
