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
from services.daily_task_service import DailyTaskService
from services.kline_service import KlineService
from services.constants import Colors as C

from ui.styles import (
    ALIGN_CENTER, ALIGN_TOP_LEFT, ALIGN_BOTTOM_RIGHT,
    ALIGN_TOP_CENTER, ALIGN_BOTTOM_CENTER, ALIGN_CENTER_LEFT, ALIGN_CENTER_RIGHT,
    XiuxianColors, gradient_purple_gold, shadow_glow, shadow_soft,
    anim_default, anim_smooth, anim_fade,
    styled_textfield, primary_button,
    decorative_circle, star_particle,
)

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
    daily_task_svc = DailyTaskService(db)
    kline_svc = KlineService(db)

    # 注入K线服务引用到心境服务
    spirit_svc.kline_svc = kline_svc

    # 检查是否首次启动
    config = db.get_user_config()
    if not config:
        _show_onboarding(page, db, lambda: _show_main(
            page, db, spirit_svc, realm_svc, lingshi_svc, tongyu_svc, panel_svc, daily_task_svc, kline_svc
        ))
    else:
        _show_main(page, db, spirit_svc, realm_svc, lingshi_svc, tongyu_svc, panel_svc, daily_task_svc, kline_svc)


def _show_onboarding(page: ft.Page, db: DatabaseManager, on_complete):
    """首次启动引导 — 修仙主题"""

    # 输入框
    year_field = styled_textfield(
        label="出生年份",
        hint_text="例如：1998",
        keyboard_type=ft.KeyboardType.NUMBER,
        text_align=ft.TextAlign.CENTER,
        text_size=22,
        width=260,
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
            _sb = ft.SnackBar(ft.Text("请输入有效的年份"), bgcolor=C.ERROR)
            _sb.open = True
            page.overlay.append(_sb)
            page.update()

    # 装饰性背景元素
    bg_decorations = [
        # 大光晕
        decorative_circle(size=200, color="#ffffff", opacity=0.04, top=-40, right=-60),
        decorative_circle(size=160, color="#fbbf24", opacity=0.03, bottom=120, left=-40),
        decorative_circle(size=100, color="#a78bfa", opacity=0.06, top=200, right=20),
        # 星光粒子
        star_particle(size=3, color="#fbbf24", opacity=0.7, top=80, left=50),
        star_particle(size=4, color="#ffffff", opacity=0.5, top=150, left=300),
        star_particle(size=3, color="#fbbf24", opacity=0.6, top=280, left=80),
        star_particle(size=5, color="#ffffff", opacity=0.4, top=350, left=250),
        star_particle(size=3, color="#c4b5fd", opacity=0.7, top=450, left=120),
        star_particle(size=4, color="#fbbf24", opacity=0.5, top=520, left=320),
        star_particle(size=3, color="#ffffff", opacity=0.6, top=600, left=60),
        star_particle(size=4, color="#c4b5fd", opacity=0.5, top=680, left=280),
    ]

    # 主内容
    main_content = ft.Column(
        [
            ft.Container(height=80),
            # 图标区域 — 带发光效果
            ft.Container(
                content=ft.Text("⚔️", size=72, text_align=ft.TextAlign.CENTER),
                width=120,
                height=120,
                border_radius=60,
                bgcolor=ft.Colors.with_opacity(0.1, "#ffffff"),
                alignment=ALIGN_CENTER,
                shadow=shadow_glow(color=XiuxianColors.GOLD_BRIGHT, opacity=0.25, blur=30),
                animate=anim_fade(),
            ),
            ft.Container(height=8),
            # 标题
            ft.Text(
                "凡人修仙3w天",
                size=30,
                weight=ft.FontWeight.W_800,
                text_align=ft.TextAlign.CENTER,
                color="#ffffff",
            ),
            # 副标题
            ft.Text(
                "人生如修仙，三万天的修炼之旅",
                size=14,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.with_opacity(0.7, "#ffffff"),
            ),
            ft.Container(height=4),
            # 分隔装饰线
            ft.Container(
                width=60,
                height=2,
                border_radius=1,
                bgcolor=ft.Colors.with_opacity(0.3, XiuxianColors.GOLD_BRIGHT),
            ),
            ft.Container(height=36),
            # 提示文字
            ft.Text(
                "✦ 请输入你的出生年份 ✦",
                size=15,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.with_opacity(0.85, "#ffffff"),
                weight=ft.FontWeight.W_500,
            ),
            ft.Container(height=8),
            # 输入框
            ft.Container(
                content=year_field,
                width=260,
            ),
            ft.Container(height=24),
            # 开始按钮
            primary_button("踏入仙途", on_click=on_start, width=220, height=50),
            ft.Container(height=40),
            # 底部点缀文字
            ft.Text(
                "— 道可道，非常道 —",
                size=12,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.with_opacity(0.35, "#ffffff"),
                italic=True,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )

    # 组合：渐变背景 + 装饰 + 内容
    page.add(
        ft.Container(
            content=ft.Stack(
                [
                    # 装饰层
                    *bg_decorations,
                    # 内容层
                    ft.Container(
                        content=main_content,
                        expand=True,
                        alignment=ALIGN_CENTER,
                    ),
                ],
            ),
            expand=True,
            gradient=gradient_purple_gold(),
        )
    )


def _show_main(page: ft.Page, db, spirit_svc, realm_svc, lingshi_svc, tongyu_svc, panel_svc, daily_task_svc, kline_svc):
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
                pages[index] = XinjingPage(page, spirit_svc, daily_task_svc, kline_svc)
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
    ft.run(main, port=8000)
