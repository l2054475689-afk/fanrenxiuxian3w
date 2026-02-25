"""
单独启动每个页面截图
"""
import flet as ft
import sys, os, asyncio, time, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from database.db_manager import DatabaseManager
from services.spirit_service import SpiritService
from services.realm_service import RealmService
from services.lingshi_service import LingshiService
from services.tongyu_service import TongyuService
from services.panel_service import PanelService

db_path = str(Path.home() / '.fanrenxiuxian' / 'fanrenxiuxian.db')
db = DatabaseManager(db_path)

PAGE_INDEX = int(sys.argv[1]) if len(sys.argv) > 1 else 0

def main(page: ft.Page):
    page.title = "凡人修仙3w天"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 400
    page.window.height = 800

    from ui.pages.panel_page import PanelPage
    from ui.pages.xinjing_page import XinjingPage
    from ui.pages.jingjie_page import JingjiePage
    from ui.pages.lingshi_page import LingshiPage
    from ui.pages.tongyu_page import TongyuPage
    from ui.pages.settings_page import SettingsPage

    pages_map = {
        0: ("panel", lambda: PanelPage(page, PanelService(db))),
        1: ("xinjing", lambda: XinjingPage(page, SpiritService(db))),
        2: ("jingjie", lambda: JingjiePage(page, RealmService(db))),
        3: ("lingshi", lambda: LingshiPage(page, LingshiService(db))),
        4: ("tongyu", lambda: TongyuPage(page, TongyuService(db))),
        5: ("settings", lambda: SettingsPage(page, db)),
    }

    name, factory = pages_map[PAGE_INDEX]
    content = factory()
    page.add(content)

ft.run(main, view=None, port=8550 + PAGE_INDEX)
