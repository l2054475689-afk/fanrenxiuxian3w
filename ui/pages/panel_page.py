"""
个人面板页面 — 生命仪表盘 v2
美化版：深红渐变血量卡、心境+灵石双渐变卡、圆形境界进度、手动柱状图趋势
"""
import math
import flet as ft
from services.panel_service import PanelService
from services.constants import Colors as C, get_spirit_level
from ui.styles import card_container, gradient_card, section_title


class PanelPage(ft.Column):
    """个人面板页"""

    def __init__(self, page: ft.Page, panel_service: PanelService, kline_service=None):
        super().__init__()
        self._page = page
        self.svc = panel_service
        self.kline_svc = kline_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._seconds_text = None  # 秒数跳动文本引用
        self._blood_seconds = 0    # 当前剩余秒数
        self._timer_running = False
        self._kline_mode = 0       # 0=任务K线, 1=心灵K线

    def build(self):
        dashboard = self.svc.get_dashboard()
        if not dashboard:
            return ft.Container(
                content=ft.Text("请先完成初始化设置", size=18, text_align=ft.TextAlign.CENTER),
                alignment=ft.Alignment(0, 0), expand=True,
            )

        blood = dashboard["blood"]
        spirit = dashboard["spirit"]
        today = dashboard["today"]
        lingshi = dashboard["lingshi"]
        realm = dashboard["realm"]

        self.controls = [
            # 顶部标题
            ft.Container(
                content=ft.Row([
                    ft.Text("凡人修仙3w天", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text("⚡ 修炼中", size=11, color="white"),
                        bgcolor="#667eea",
                        border_radius=12,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.only(left=20, right=20, top=16, bottom=8),
            ),

            # 血量卡片 — 深红渐变
            self._blood_card(blood),

            # 心境 + 灵石 双渐变卡
            ft.Container(
                content=ft.Row([
                    ft.Container(self._spirit_mini_card(spirit), expand=1),
                    ft.Container(self._lingshi_mini_card(lingshi), expand=1),
                ], spacing=10),
                padding=ft.Padding.symmetric(horizontal=16),
                margin=ft.Margin.only(top=6),
            ),

            # 境界进度 — 圆形指示器
            self._realm_card(realm) if realm else ft.Container(),

            # 今日概览
            section_title("今日修炼"),
            self._today_card(today),

            # K线人生（替代七日趋势）
            section_title("K线人生"),
            self._kline_toggle(),
            self._kline_chart(),

            ft.Container(height=80),  # 底部留白
        ]

    # ─── 血量卡片 ───────────────────────────────────────────
    def _blood_card(self, blood: dict) -> ft.Container:
        """血量倒计时卡片 — 深红渐变，大号天数"""
        remaining_days = blood["remaining_days"]
        remaining_years = blood["remaining_years"]
        remaining_minutes = blood["remaining_minutes"]
        progress = blood["progress_remaining"]
        self._blood_seconds = remaining_minutes * 60  # 转换为秒

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Text("❤️", size=18),
                        ft.Text("生命血量", size=15, weight=ft.FontWeight.W_600, color="white"),
                    ], spacing=6),
                    ft.Container(
                        content=ft.Text(
                            f"≈ {remaining_years}年",
                            size=12, color="white", weight=ft.FontWeight.W_500,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.25, "white"),
                        border_radius=10,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=4),
                # 大号天数
                ft.Row([
                    ft.Text(
                        f"{remaining_days:,}",
                        size=52, weight=ft.FontWeight.BOLD, color="white",
                    ),
                    ft.Text("天", size=20, color=ft.Colors.with_opacity(0.8, "white"),
                             weight=ft.FontWeight.W_500),
                ], alignment=ft.MainAxisAlignment.CENTER,
                   vertical_alignment=ft.CrossAxisAlignment.END, spacing=4),
                # 秒数（每秒跳动）
                self._blood_seconds_display(),
                ft.Container(height=6),
                # 进度条
                ft.ProgressBar(
                    value=progress, height=8,
                    color="white", bgcolor=ft.Colors.with_opacity(0.2, "white"),
                    border_radius=4,
                ),
                ft.Row([
                    ft.Text("已逝", size=10, color=ft.Colors.with_opacity(0.5, "white")),
                    ft.Text(
                        f"{progress * 100:.1f}% 剩余",
                        size=10, color=ft.Colors.with_opacity(0.7, "white"),
                        weight=ft.FontWeight.W_500,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            margin=ft.Margin.symmetric(horizontal=16, vertical=6),
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#8b0000", "#c0392b", "#e74c3c"],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=16,
                color=ft.Colors.with_opacity(0.3, "#e74c3c"),
                offset=ft.Offset(0, 4),
            ),
        )

    def _blood_seconds_display(self) -> ft.Container:
        """秒数显示（每秒跳动）"""
        self._seconds_text = ft.Text(
            f"⏱ {self._blood_seconds:,} 秒",
            size=13, color=ft.Colors.with_opacity(0.7, "white"),
            text_align=ft.TextAlign.CENTER,
        )
        # 启动定时器
        if not self._timer_running:
            self._timer_running = True
            self._start_seconds_timer()
        return ft.Container(content=self._seconds_text)

    def _start_seconds_timer(self):
        """每秒递减血量秒数"""
        import threading
        def tick():
            while self._timer_running and self._blood_seconds > 0:
                import time
                time.sleep(1)
                self._blood_seconds -= 1
                if self._seconds_text:
                    self._seconds_text.value = f"⏱ {self._blood_seconds:,} 秒"
                    try:
                        self._seconds_text.update()
                    except Exception:
                        self._timer_running = False
                        break
        t = threading.Thread(target=tick, daemon=True)
        t.start()

    # ─── 心境迷你卡 ─────────────────────────────────────────
    def _spirit_mini_card(self, spirit: dict) -> ft.Container:
        """心境迷你卡片 — 蓝紫渐变"""
        return ft.Container(
            content=ft.Column([
                ft.Text("🧘 心境", size=11, color=ft.Colors.with_opacity(0.85, "white"),
                         weight=ft.FontWeight.W_500),
                ft.Text(
                    spirit["level_name"], size=13,
                    weight=ft.FontWeight.BOLD, color="white",
                ),
                ft.Text(
                    f"{spirit['value']}", size=28,
                    weight=ft.FontWeight.BOLD, color="white",
                ),
                ft.ProgressBar(
                    value=spirit["progress"], height=4,
                    color="white",
                    bgcolor=ft.Colors.with_opacity(0.25, "white"),
                    border_radius=2,
                ),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14,
            border_radius=14,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#667eea", "#764ba2"],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=10,
                color=ft.Colors.with_opacity(0.2, "#667eea"),
                offset=ft.Offset(0, 3),
            ),
        )

    # ─── 灵石迷你卡 ─────────────────────────────────────────
    def _lingshi_mini_card(self, lingshi: dict) -> ft.Container:
        """灵石迷你卡片 — 金色渐变"""
        balance = lingshi["balance"]
        return ft.Container(
            content=ft.Column([
                ft.Text("💰 灵石", size=11, color=ft.Colors.with_opacity(0.85, "#5a3e00"),
                         weight=ft.FontWeight.W_500),
                ft.Text("余额", size=11, color=ft.Colors.with_opacity(0.7, "#5a3e00")),
                ft.Text(
                    f"{balance:,.0f}", size=28,
                    weight=ft.FontWeight.BOLD, color="#5a3e00",
                ),
                ft.Row([
                    ft.Text(f"↑{lingshi['income']:,.0f}", size=10, color="#2e7d32"),
                    ft.Text(f"↓{lingshi['expense']:,.0f}", size=10, color="#c62828"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14,
            border_radius=14,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#f6d365", "#fda085"],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=10,
                color=ft.Colors.with_opacity(0.2, "#f6d365"),
                offset=ft.Offset(0, 3),
            ),
        )

    # ─── 境界进度 — 圆形指示器 ──────────────────────────────
    def _realm_card(self, realm: dict) -> ft.Container:
        """境界进度卡片 — 圆形进度环"""
        pct = realm["progress"]
        pct_text = f"{pct * 100:.0f}%"

        # 圆形进度环用 Canvas 绘制
        ring_size = 56

        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        f"⚔️ {realm['name']}",
                        size=17, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        f"已完成 {realm['completed']}/{realm['total']} 任务",
                        size=12, color=C.TEXT_SECONDARY,
                    ),
                    ft.Container(height=4),
                    ft.ProgressBar(
                        value=pct, height=6,
                        color=C.PRIMARY, bgcolor=ft.Colors.with_opacity(0.12, C.PRIMARY),
                        border_radius=3,
                    ),
                ], spacing=2, expand=True),
                # 圆形百分比
                ft.Stack(
                    controls=[
                        ft.Container(
                            width=ring_size, height=ring_size,
                            border_radius=ring_size // 2,
                            border=ft.Border.all(5, ft.Colors.with_opacity(0.12, C.PRIMARY)),
                        ),
                        ft.Container(
                            width=ring_size, height=ring_size,
                            border_radius=ring_size // 2,
                            border=ft.Border.all(5, C.PRIMARY),
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        ),
                        ft.Container(
                            content=ft.Text(
                                pct_text, size=14,
                                weight=ft.FontWeight.BOLD, color=C.PRIMARY,
                            ),
                            alignment=ft.Alignment(0, 0),
                            width=ring_size, height=ring_size,
                        ),
                    ],
                    width=ring_size, height=ring_size,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
            padding=16,
            margin=ft.Margin.symmetric(horizontal=16, vertical=6),
            border_radius=14,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=8,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    # ─── 今日概览 ───────────────────────────────────────────
    def _today_card(self, today: dict) -> ft.Container:
        """今日概览 — 4 指标横排"""
        items = [
            ("✅", f"{today['positive_count']}", "正面", C.SUCCESS),
            ("👿", f"{today['demon_count']}", "心魔", C.ERROR),
            ("🧘", f"{today['spirit_change']:+d}", "心境", "#667eea"),
            ("❤️", f"{today['blood_change']:+d}", "血量", C.LIFE_RED),
        ]
        return ft.Container(
            content=ft.Row(
                [self._stat_item(emoji, val, label, color) for emoji, val, label, color in items],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            padding=16,
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=8,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    def _stat_item(self, emoji: str, value: str, label: str, accent: str = C.TEXT_PRIMARY) -> ft.Column:
        """统计项 — 带颜色强调"""
        return ft.Column([
            ft.Text(emoji, size=22),
            ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=accent),
            ft.Text(label, size=11, color=C.TEXT_HINT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3)

    # ─── 7日趋势 — 手动柱状图 ─────────────────────────────────
    def _trend_chart(self) -> ft.Container:
        """7日趋势图 — 手动容器柱状图（替代 ft.BarChart）"""
        trend = self.svc.get_weekly_trend()
        if not trend:
            return ft.Container(
                content=ft.Text("暂无数据", size=13, color=C.TEXT_HINT,
                                text_align=ft.TextAlign.CENTER),
                padding=20,
                margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            )

        max_val = max(max(abs(d["positive"]), abs(d["demon"]), 1) for d in trend)
        chart_height = 120

        def _bar(value, color, width=14):
            h = max(2, (abs(value) / max(max_val, 1)) * chart_height)
            return ft.Container(
                width=width,
                height=h,
                bgcolor=color,
                border_radius=ft.BorderRadius.only(top_left=4, top_right=4),
                tooltip=str(value),
            )

        bar_columns = []
        for d in trend:
            bar_columns.append(
                ft.Column(
                    [
                        ft.Row(
                            [_bar(d["positive"], C.SUCCESS), _bar(d["demon"], C.ERROR)],
                            spacing=2,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Text(d["date"], size=9, color=C.TEXT_HINT,
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.END,
                    spacing=4,
                )
            )

        chart = ft.Container(
            content=ft.Row(
                bar_columns,
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            height=chart_height + 30,
            border=ft.Border.only(
                bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, ft.Colors.BLACK)),
            ),
        )

        # 图例
        legend = ft.Row([
            ft.Row([
                ft.Container(width=10, height=10, bgcolor=C.SUCCESS, border_radius=2),
                ft.Text("正面", size=10, color=C.TEXT_HINT),
            ], spacing=4),
            ft.Row([
                ft.Container(width=10, height=10, bgcolor=C.ERROR, border_radius=2),
                ft.Text("心魔", size=10, color=C.TEXT_HINT),
            ], spacing=4),
        ], spacing=16, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([chart, legend], spacing=8),
            padding=ft.Padding.only(left=8, right=16, top=8, bottom=12),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=8,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    # ─── K线人生 ─────────────────────────────────────────────

    def _kline_toggle(self) -> ft.Container:
        """K线切换按钮：任务K线 / 心灵K线"""
        def switch(idx):
            self._kline_mode = idx
            self._refresh()

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(
                        "📊 任务K线", size=13,
                        weight=ft.FontWeight.BOLD if self._kline_mode == 0 else ft.FontWeight.W_400,
                        color="white" if self._kline_mode == 0 else C.TEXT_SECONDARY,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                    border_radius=16,
                    bgcolor=C.PRIMARY if self._kline_mode == 0 else ft.Colors.with_opacity(0.08, C.TEXT_HINT),
                    on_click=lambda e: switch(0),
                ),
                ft.Container(
                    content=ft.Text(
                        "🧘 心灵K线", size=13,
                        weight=ft.FontWeight.BOLD if self._kline_mode == 1 else ft.FontWeight.W_400,
                        color="white" if self._kline_mode == 1 else C.TEXT_SECONDARY,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                    border_radius=16,
                    bgcolor="#764ba2" if self._kline_mode == 1 else ft.Colors.with_opacity(0.08, C.TEXT_HINT),
                    on_click=lambda e: switch(1),
                ),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=16, vertical=4),
        )

    def _kline_chart(self) -> ft.Container:
        """K线图"""
        if self._kline_mode == 0:
            return self._task_kline()
        else:
            return self._spirit_kline()

    def _task_kline(self) -> ft.Container:
        """任务K线：日常任务、修炼任务、副本任务完成数量"""
        trend = self.svc.get_weekly_trend()
        if not trend:
            return ft.Container(
                content=ft.Text("暂无数据", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                padding=20, margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            )

        max_val = max(max(d["positive"], d["demon"], 1) for d in trend)
        chart_height = 120

        def _bar(value, color, width=14):
            h = max(2, (abs(value) / max(max_val, 1)) * chart_height)
            return ft.Container(
                width=width, height=h, bgcolor=color,
                border_radius=ft.BorderRadius.only(top_left=4, top_right=4),
                tooltip=str(value),
            )

        bar_columns = []
        for d in trend:
            bar_columns.append(
                ft.Column([
                    ft.Row(
                        [_bar(d["positive"], C.SUCCESS, 10), _bar(d["demon"], C.ERROR, 10)],
                        spacing=2, alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(d["date"], size=9, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   alignment=ft.MainAxisAlignment.END, spacing=4)
            )

        chart = ft.Container(
            content=ft.Row(bar_columns, alignment=ft.MainAxisAlignment.SPACE_AROUND,
                           vertical_alignment=ft.CrossAxisAlignment.END),
            height=chart_height + 30,
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, ft.Colors.BLACK))),
        )

        legend = ft.Row([
            ft.Row([ft.Container(width=10, height=10, bgcolor=C.SUCCESS, border_radius=2),
                    ft.Text("正面/日常", size=10, color=C.TEXT_HINT)], spacing=4),
            ft.Row([ft.Container(width=10, height=10, bgcolor=C.ERROR, border_radius=2),
                    ft.Text("心魔", size=10, color=C.TEXT_HINT)], spacing=4),
        ], spacing=16, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([chart, legend], spacing=8),
            padding=ft.Padding.only(left=8, right=16, top=8, bottom=12),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14, bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

    def _spirit_kline(self) -> ft.Container:
        """心灵K线：心境值 OHLC 蜡烛图"""
        if not self.kline_svc:
            return ft.Container(
                content=ft.Text("K线服务未初始化", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                padding=20, margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            )

        scores = self.kline_svc.get_scores(days=14)
        if not scores:
            return ft.Container(
                content=ft.Text("暂无K线数据", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                padding=20, margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            )

        # 找范围
        all_vals = []
        for s in scores:
            all_vals.extend([s["high_spirit"], s["low_spirit"]])
        y_min = min(all_vals) - 20
        y_max = max(all_vals) + 20
        y_range = max(y_max - y_min, 1)
        chart_height = 140

        def y_pos(val):
            return chart_height - ((val - y_min) / y_range * chart_height)

        candles = []
        for s in scores:
            o = s["open_spirit"]
            c = s["close_spirit"]
            h = s["high_spirit"]
            l = s["low_spirit"]
            is_up = c >= o
            color = "#26a69a" if is_up else "#ef5350"
            body_top = min(o, c)
            body_bot = max(o, c)
            body_h = max(2, (body_bot - body_top) / y_range * chart_height)
            wick_h = max(1, (h - l) / y_range * chart_height)
            body_offset = y_pos(body_bot)
            wick_offset = y_pos(h)

            d_str = str(s["score_date"])[-5:]  # MM-DD

            candles.append(
                ft.Column([
                    ft.Container(height=max(0, wick_offset)),
                    # 上影线
                    ft.Container(width=1, height=max(1, y_pos(max(o, c)) - wick_offset), bgcolor=color),
                    # 实体
                    ft.Container(width=10, height=body_h, bgcolor=color, border_radius=1,
                                 tooltip=f"开{o} 收{c} 高{h} 低{l}"),
                    # 下影线
                    ft.Container(width=1, height=max(1, y_pos(l) - y_pos(min(o, c)) - body_h), bgcolor=color),
                    ft.Container(expand=True),
                    ft.Text(d_str, size=8, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            )

        chart = ft.Container(
            content=ft.Row(candles, alignment=ft.MainAxisAlignment.SPACE_AROUND,
                           vertical_alignment=ft.CrossAxisAlignment.START),
            height=chart_height + 30,
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, ft.Colors.BLACK))),
        )

        legend = ft.Row([
            ft.Row([ft.Container(width=10, height=10, bgcolor="#26a69a", border_radius=2),
                    ft.Text("上涨", size=10, color=C.TEXT_HINT)], spacing=4),
            ft.Row([ft.Container(width=10, height=10, bgcolor="#ef5350", border_radius=2),
                    ft.Text("下跌", size=10, color=C.TEXT_HINT)], spacing=4),
        ], spacing=16, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([chart, legend], spacing=8),
            padding=ft.Padding.only(left=8, right=16, top=8, bottom=12),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14, bgcolor="#1e222d",
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

    def _refresh(self):
        self._timer_running = False  # 停止旧定时器
        self.controls.clear()
        self.build()
        try:
            self.update()
        except RuntimeError:
            pass
