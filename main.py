"""
凡人修仙3w天 — 主程序入口
"""
import flet as ft

from utils.path_helper import get_database_path
from database.db_manager import DatabaseManager
from services.spirit_service import SpiritService
from services.realm_service import RealmService
from services.lingshi_service import LingshiService
from services.tongyu_service import TongyuService
from services.panel_service import PanelService
from services.constants import Colors as C

from ui.pages.panel_page import PanelPage
from ui.pages.xinjing_page import XinjingPage
from ui.pages.jingjie_page import JingjiePage
from ui.pages.lingshi_page import LingshiPage
from ui.pages.tongyu_page import TongyuPage
from ui.pages.settings_page import SettingsPage


def main(page: ft.Page):
    """应用主入口"""
    # 页面配置
    page.title = "凡人修仙3w天"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.window.width = 400
    page.window.height = 800

    # 初始化数据库
    db_path = get_database_path(page)
    db = DatabaseManager(db_path)

    # 初始化服务
    spirit_svc = SpiritService(db)
    realm_svc = RealmService(db)
    lingshi_svc = LingshiService(db)
    tongyu_svc = TongyuService(db)
    panel_svc = PanelService(db)

    # 检查是否首次启动
    config = db.get_user_config()
    if not config:
        _show_onboarding(page, db, lambda: _show_main(
            page, db, spirit_svc, realm_svc, lingshi_svc, tongyu_svc, panel_svc
        ))
    else:
        _show_main(page, db, spirit_svc, realm_svc, lingshi_svc, tongyu_svc, panel_svc)


def _show_onboarding(page: ft.Page, db: DatabaseManager, on_complete):
    """首次启动引导"""
    year_field = ft.TextField(
        label="出生年份", hint_text="例如：1998",
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.CENTER,
        text_size=24,
    )

    def on_start(e):
        try:
            year = int(year_field.value)
            if 1900 < year < 2100:
                db.init_user_config(year)
                page.controls.clear()
                on_complete()
                page.update()
        except (ValueError, TypeError):
            page.open(ft.SnackBar(ft.Text("请输入有效的年份"), bgcolor=C.ERROR))

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Container(height=80),
                ft.Text("⚔️", size=64, text_align=ft.TextAlign.CENTER),
                ft.Text("凡人修仙3w天", size=28, weight=ft.FontWeight.BOLD,
                         text_align=ft.TextAlign.CENTER, color=C.PRIMARY),
                ft.Text("人生如修仙，三万天的修炼之旅", size=14,
                         text_align=ft.TextAlign.CENTER, color=C.TEXT_SECONDARY),
                ft.Container(height=40),
                ft.Text("你的出生年份是？", size=16, text_align=ft.TextAlign.CENTER, color=C.TEXT_PRIMARY),
                ft.Container(
                    content=year_field,
                    width=200,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "开始修炼",
                    width=200, height=48,
                    bgcolor=C.PRIMARY, color="white",
                    on_click=on_start,
                ),
            ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
    )


def _show_main(page: ft.Page, db, spirit_svc, realm_svc, lingshi_svc, tongyu_svc, panel_svc):
    """显示主界面"""
    # 页面容器
    content_area = ft.Container(expand=True)

    # 页面实例缓存
    pages = {}

    def get_page(index: int):
        if index not in pages:
            if index == 0:
                pages[index] = PanelPage(page, panel_svc)
            elif index == 1:
                pages[index] = XinjingPage(page, spirit_svc)
            elif index == 2:
                pages[index] = JingjiePage(page, realm_svc)
            elif index == 3:
                pages[index] = LingshiPage(page, lingshi_svc)
            elif index == 4:
                pages[index] = TongyuPage(page, tongyu_svc)
            elif index == 5:
                pages[index] = SettingsPage(page, db)
        return pages[index]

    def on_nav_change(e):
        idx = e.control.selected_index
        # 清除缓存强制刷新
        if idx in pages:
            del pages[idx]
        content_area.content = get_page(idx)
        page.update()

    # 底部导航
    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="面板"),
            ft.NavigationBarDestination(icon=ft.Icons.SELF_IMPROVEMENT_OUTLINED, selected_icon=ft.Icons.SELF_IMPROVEMENT, label="心境"),
            ft.NavigationBarDestination(icon=ft.Icons.SCHOOL_OUTLINED, selected_icon=ft.Icons.SCHOOL, label="境界"),
            ft.NavigationBarDestination(icon=ft.Icons.ATTACH_MONEY_OUTLINED, selected_icon=ft.Icons.ATTACH_MONEY, label="灵石"),
            ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINE, selected_icon=ft.Icons.PEOPLE, label="统御"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="设置"),
        ],
        bgcolor=C.CARD_LIGHT,
        indicator_color=ft.Colors.with_opacity(0.15, C.PRIMARY),
    )

    # 初始页面
    content_area.content = get_page(0)

    page.add(
        ft.Column([
            content_area,
            nav_bar,
        ], spacing=0, expand=True)
    )


if __name__ == "__main__":
    ft.run(main)
