"""
个人面板页面 — 生命仪表盘
"""
import flet as ft
from services.panel_service import PanelService
from services.constants import Colors as C, get_spirit_level
from ui.styles import card_container, gradient_card, section_title


class PanelPage(ft.Column):
    """个人面板页"""

    def __init__(self, page: ft.Page, panel_service: PanelService):
        super().__init__()
        self.page = page
        self.svc = panel_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    def build(self):
        dashboard = self.svc.get_dashboard()
        if not dashboard:
            return ft.Container(
                content=ft.Text("请先完成初始化设置", size=18, text_align=ft.TextAlign.CENTER),
                alignment=ft.alignment.center, expand=True,
            )

        blood = dashboard["blood"]
        spirit = dashboard["spirit"]
        today = dashboard["today"]
        lingshi = dashboard["lingshi"]
        realm = dashboard["realm"]

        self.controls = [
            # 顶部标题
            ft.Container(
                content=ft.Text("凡人修仙3w天", size=20, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                padding=ft.padding.only(left=20, top=16, bottom=8),
            ),

            # 血量卡片
            self._blood_card(blood),

            # 心境 + 灵石 双卡
            ft.Container(
                content=ft.Row([
                    ft.Container(self._spirit_mini_card(spirit), expand=1),
                    ft.Container(self._lingshi_mini_card(lingshi), expand=1),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=16),
                margin=ft.margin.only(top=4),
            ),

            # 境界进度
            self._realm_card(realm) if realm else ft.Container(),

            # 今日概览
            section_title("今日修炼"),
            self._today_card(today),

            # 7日趋势
            section_title("七日趋势"),
            self._trend_card(),

            ft.Container(height=80),  # 底部留白
        ]

    def _blood_card(self, blood: dict) -> ft.Container:
        """血量倒计时卡片"""
        remaining_days = blood["remaining_days"]
        remaining_years = blood["remaining_years"]
        progress = blood["progress_remaining"]

        return gradient_card(
            content=ft.Column([
                ft.Row([
                    ft.Text("❤️ 生命血量", size=14, color="white70"),
                    ft.Text(f"{remaining_years}年", size=14, color="white70"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"{remaining_days:,} 天", size=36, weight=ft.FontWeight.BOLD, color="white"),
                ft.Text(f"{blood['remaining_minutes']:,} 分钟", size=14, color="white70"),
                ft.ProgressBar(
                    value=progress, height=6,
                    color="white", bgcolor="white24",
                ),
            ], spacing=6),
            colors=[C.LIFE_RED, "#ee5a6f"],
        )

    def _spirit_mini_card(self, spirit: dict) -> ft.Container:
        """心境迷你卡片"""
        return card_container(
            content=ft.Column([
                ft.Text("🧘 心境", size=12, color=C.TEXT_HINT),
                ft.Text(spirit["level_name"], size=16, weight=ft.FontWeight.BOLD, color=spirit["level_color"]),
                ft.Text(f"{spirit['value']}", size=24, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                ft.ProgressBar(
                    value=spirit["progress"], height=4,
                    color=spirit["level_color"], bgcolor=ft.Colors.with_opacity(0.15, spirit["level_color"]),
                ),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.margin.only(top=4),
        )

    def _lingshi_mini_card(self, lingshi: dict) -> ft.Container:
        """灵石迷你卡片"""
        balance = lingshi["balance"]
        return card_container(
            content=ft.Column([
                ft.Text("💰 灵石", size=12, color=C.TEXT_HINT),
                ft.Text("余额", size=12, color=C.TEXT_SECONDARY),
                ft.Text(f"{balance:,.0f}", size=24, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                ft.Row([
                    ft.Text(f"入{lingshi['income']:,.0f}", size=10, color=C.SUCCESS),
                    ft.Text(f"出{lingshi['expense']:,.0f}", size=10, color=C.ERROR),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.margin.only(top=4),
        )

    def _realm_card(self, realm: dict) -> ft.Container:
        """境界进度卡片"""
        return card_container(
            content=ft.Row([
                ft.Text("⚔️", size=24),
                ft.Column([
                    ft.Text(realm["name"], size=16, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                    ft.Text(f"{realm['completed']}/{realm['total']} 任务", size=12, color=C.TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.Stack([
                    ft.CircleAvatar(
                        radius=22, bgcolor=ft.Colors.with_opacity(0.1, C.PRIMARY),
                    ),
                    ft.Container(
                        content=ft.Text(f"{realm['progress']*100:.0f}%", size=11, weight=ft.FontWeight.BOLD, color=C.PRIMARY),
                        alignment=ft.alignment.center, width=44, height=44,
                    ),
                ]),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    def _today_card(self, today: dict) -> ft.Container:
        """今日概览卡片"""
        return card_container(
            content=ft.Row([
                self._stat_item("✅", f"{today['positive_count']}", "正面"),
                self._stat_item("👿", f"{today['demon_count']}", "心魔"),
                self._stat_item("🧘", f"{today['spirit_change']:+d}", "心境"),
                self._stat_item("❤️", f"{today['blood_change']:+d}", "血量"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        )

    def _stat_item(self, emoji: str, value: str, label: str) -> ft.Column:
        """统计项"""
        return ft.Column([
            ft.Text(emoji, size=20),
            ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
            ft.Text(label, size=11, color=C.TEXT_HINT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    def _trend_card(self) -> ft.Container:
        """7日趋势图"""
        trend = self.svc.get_weekly_trend()
        if not trend:
            return ft.Container()

        max_val = max(max(abs(d["positive"]), abs(d["demon"])) for d in trend) or 1

        bars = []
        for d in trend:
            bars.append(
                ft.Column([
                    ft.Container(
                        height=max(2, d["positive"] / max_val * 50),
                        width=20, bgcolor=C.SUCCESS, border_radius=4,
                    ) if d["positive"] > 0 else ft.Container(height=2, width=20),
                    ft.Container(
                        height=max(2, d["demon"] / max_val * 50),
                        width=20, bgcolor=C.ERROR, border_radius=4,
                    ) if d["demon"] > 0 else ft.Container(height=2, width=20),
                    ft.Text(d["date"], size=9, color=C.TEXT_HINT),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
            )

        return card_container(
            content=ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_AROUND),
        )
