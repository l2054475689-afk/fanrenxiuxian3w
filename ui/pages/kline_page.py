"""
K线人生图页面 — 自动从心境系统生成的K线蜡烛图
只读展示：K线图 + 今日卡片 + 历史列表 + 删除功能
"""
from datetime import date, timedelta
import flet as ft
from services.kline_service import KlineService
from services.constants import Colors as C, SPIRIT_MIN, SPIRIT_MAX
from ui.styles import card_container, section_title, ALIGN_CENTER

# K线颜色
KLINE_GREEN = "#26a69a"  # 收盘>=开盘（心情变好）
KLINE_RED = "#ef5350"    # 收盘<开盘（心情变差）
CHART_HEIGHT = 200
CHART_BG = "#1e222d"
MA_COLOR = "#fbbf24"

# 心境值范围
Y_MIN = SPIRIT_MIN   # -200
Y_MAX = SPIRIT_MAX   # 640


class KlinePage(ft.Column):
    """K线人生图页（只读展示）"""

    def __init__(self, page: ft.Page, kline_service: KlineService):
        super().__init__()
        self._page = page
        self.svc = kline_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._display_days = 14

    def build(self):
        self._refresh()

    def _refresh(self):
        today_score = self.svc.get_today_score()
        scores = self.svc.get_scores(days=self._display_days)
        weekly_avg = self.svc.get_weekly_avg()

        self.controls = [
            # 顶部标题
            ft.Container(
                content=ft.Row([
                    ft.Text("K线人生图", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text("📊 心境K线", size=11, color="white"),
                        bgcolor="#667eea",
                        border_radius=12,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.only(left=20, right=20, top=16, bottom=8),
            ),
            # 今日卡片
            self._today_card(today_score),
            # 时间范围切换
            self._range_selector(),
            # K线图
            self._kline_chart(scores, weekly_avg),
            # 日期列表
            section_title("历史记录"),
            self._score_list(scores),
            ft.Container(height=80),
        ]

    # ─── 今日卡片 ───
    def _today_card(self, today):
        if not today:
            return card_container(
                ft.Column([
                    ft.Text("今日尚无心境变动", size=16, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                    ft.Text("完成心境任务后自动生成K线数据", size=13, color=C.TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            )

        open_v = today["open_spirit"]
        close_v = today["close_spirit"]
        high_v = today["high_spirit"]
        low_v = today["low_spirit"]
        count = today["change_count"]

        is_up = close_v >= open_v
        change = close_v - open_v
        bg_colors = [KLINE_GREEN, "#1b5e20"] if is_up else [KLINE_RED, "#b71c1c"]

        items = [
            self._score_item("开盘", open_v),
            self._score_item("收盘", close_v),
            self._score_item("最高", high_v),
            self._score_item("最低", low_v),
        ]

        change_text = f"{'+'if change>=0 else ''}{change}"

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("今日心境", size=14, color=ft.Colors.with_opacity(0.8, "white")),
                    ft.Text(change_text, size=13, weight=ft.FontWeight.W_600, color="white"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=4),
                ft.Row(items, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=4),
                ft.Row([
                    ft.Text(f"变动 {count} 次", size=12, color=ft.Colors.with_opacity(0.7, "white")),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ]),
            padding=16,
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=12,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=bg_colors,
            ),
        )

    def _score_item(self, label, value):
        return ft.Column([
            ft.Text(label, size=11, color=ft.Colors.with_opacity(0.7, "white")),
            ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD, color="white"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    # ─── 时间范围切换 ───
    def _range_selector(self):
        def on_select(days):
            def handler(e):
                self._display_days = days
                self._refresh()
                self._page.update()
            return handler

        buttons = []
        for d in [7, 14, 30]:
            is_active = self._display_days == d
            buttons.append(ft.Container(
                content=ft.Text(
                    f"{d}天", size=13,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                    color="white" if is_active else C.TEXT_SECONDARY,
                ),
                bgcolor=C.PRIMARY if is_active else ft.Colors.with_opacity(0.08, C.TEXT_PRIMARY),
                border_radius=16,
                padding=ft.Padding.symmetric(horizontal=16, vertical=6),
                on_click=on_select(d),
            ))

        return ft.Container(
            content=ft.Row(buttons, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            padding=ft.Padding.symmetric(vertical=8),
        )

    # ─── K线图 ───
    def _kline_chart(self, scores, weekly_avg):
        if not scores:
            return card_container(
                ft.Container(
                    content=ft.Text("暂无数据，完成心境任务后自动生成", size=14, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                    height=CHART_HEIGHT, alignment=ALIGN_CENTER,
                ),
            )

        # 构建日期->评分映射
        score_map = {}
        for s in scores:
            score_map[s["score_date"]] = s

        # 构建日期->均线映射
        avg_map = {}
        for a in weekly_avg:
            avg_map[a["date"]] = a["avg"]

        # 生成所有日期
        end = date.today()
        all_dates = [end - timedelta(days=self._display_days - 1 - i) for i in range(self._display_days)]

        candle_width = max(8, min(20, (350 - 40) // self._display_days))
        gap = max(2, (350 - 40 - candle_width * self._display_days) // max(1, self._display_days - 1))
        body_width = max(6, candle_width - 2)
        wick_width = 2

        y_range = Y_MAX - Y_MIN  # 840

        def y_of(val):
            """Y mapping: Y_MIN -> CHART_HEIGHT, Y_MAX -> 0"""
            clamped = max(Y_MIN, min(Y_MAX, val))
            return CHART_HEIGHT - ((clamped - Y_MIN) / y_range * CHART_HEIGHT)

        candles = []
        ma_dots = []
        x_labels = []

        for i, d in enumerate(all_dates):
            x_pos = 20 + i * (candle_width + gap)
            sc = score_map.get(d)

            if sc:
                o = sc["open_spirit"]
                c = sc["close_spirit"]
                h = sc["high_spirit"]
                l = sc["low_spirit"]

                is_up = c >= o
                color = KLINE_GREEN if is_up else KLINE_RED

                body_top = y_of(max(o, c))
                body_bottom = y_of(min(o, c))
                body_h = max(2, body_bottom - body_top)

                wick_top = y_of(h)
                wick_bottom = y_of(l)
                wick_h = max(1, wick_bottom - wick_top)

                # Wick
                candles.append(ft.Container(
                    width=wick_width, height=wick_h,
                    bgcolor=color,
                    left=x_pos + (body_width - wick_width) / 2,
                    top=wick_top,
                ))
                # Body
                candles.append(ft.Container(
                    width=body_width, height=body_h,
                    bgcolor=color,
                    border_radius=2,
                    left=x_pos,
                    top=body_top,
                ))

            # MA dot
            avg_val = avg_map.get(d)
            if avg_val is not None:
                ma_y = y_of(avg_val)
                ma_dots.append(ft.Container(
                    width=4, height=4,
                    border_radius=2,
                    bgcolor=MA_COLOR,
                    left=x_pos + body_width / 2 - 2,
                    top=ma_y - 2,
                ))

            # X label (show every few)
            show_label = (i % max(1, self._display_days // 7) == 0) or i == self._display_days - 1
            if show_label:
                x_labels.append(ft.Container(
                    content=ft.Text(f"{d.month}/{d.day}", size=9, color=C.TEXT_HINT),
                    left=x_pos - 6,
                    top=CHART_HEIGHT + 4,
                ))

        # Y-axis labels — show key spirit values
        y_labels = []
        y_ticks = [Y_MIN, -100, 0, 100, 200, 320, Y_MAX]
        for val in y_ticks:
            y = y_of(val)
            y_labels.append(ft.Container(
                content=ft.Text(str(val), size=8, color=C.TEXT_HINT),
                left=0, top=y - 6,
            ))
            # Grid line
            y_labels.append(ft.Container(
                width=350, height=1,
                bgcolor=ft.Colors.with_opacity(0.1, C.TEXT_HINT),
                left=16, top=y,
            ))

        chart_stack = ft.Stack(
            [*y_labels, *candles, *ma_dots, *x_labels],
            width=400,
            height=CHART_HEIGHT + 24,
        )

        # Legend
        legend = ft.Row([
            ft.Container(width=10, height=10, bgcolor=KLINE_GREEN, border_radius=2),
            ft.Text("心情变好", size=10, color=C.TEXT_SECONDARY),
            ft.Container(width=10, height=10, bgcolor=KLINE_RED, border_radius=2),
            ft.Text("心情变差", size=10, color=C.TEXT_SECONDARY),
            ft.Container(width=10, height=10, bgcolor=MA_COLOR, border_radius=5),
            ft.Text("7日均线", size=10, color=C.TEXT_SECONDARY),
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=chart_stack,
                    bgcolor=CHART_BG,
                    border_radius=8,
                    padding=ft.Padding.only(top=8, bottom=8, left=4, right=4),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Container(content=legend, padding=ft.Padding.only(top=4)),
            ]),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
        )

    # ─── 日期列表 ───
    def _score_list(self, scores):
        if not scores:
            return card_container(
                ft.Text("暂无记录", size=14, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
            )

        rows = []
        sorted_scores = sorted(scores, key=lambda x: x["score_date"], reverse=True)
        for sc in sorted_scores:
            o = sc["open_spirit"]
            c = sc["close_spirit"]
            h = sc["high_spirit"]
            l = sc["low_spirit"]
            count = sc["change_count"]

            change = c - o
            change_str = f"{change:+d}"
            change_color = KLINE_GREEN if change >= 0 else KLINE_RED

            d = sc["score_date"]
            date_str = f"{d.month}/{d.day}"
            notes_str = sc.get("notes") or ""
            if len(notes_str) > 10:
                notes_str = notes_str[:10] + "…"

            row = ft.Container(
                content=ft.Row([
                    ft.Text(date_str, size=12, color=C.TEXT_PRIMARY, width=40),
                    ft.Text(str(o), size=12, color=C.TEXT_PRIMARY, width=35, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(c), size=12, color=C.TEXT_PRIMARY, width=35, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(h), size=12, color=C.TEXT_HINT, width=35, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(l), size=12, color=C.TEXT_HINT, width=35, text_align=ft.TextAlign.CENTER),
                    ft.Text(change_str, size=12, color=change_color, width=40, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(count), size=12, color=C.TEXT_HINT, width=25, text_align=ft.TextAlign.CENTER),
                    ft.Text(notes_str, size=11, color=C.TEXT_HINT, expand=True),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.08, C.TEXT_PRIMARY))),
                on_click=lambda e, s=sc: self._show_detail_dialog(s),
            )
            rows.append(row)

        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Text("日期", size=11, color=C.TEXT_HINT, width=40),
                ft.Text("开", size=11, color=C.TEXT_HINT, width=35, text_align=ft.TextAlign.CENTER),
                ft.Text("收", size=11, color=C.TEXT_HINT, width=35, text_align=ft.TextAlign.CENTER),
                ft.Text("高", size=11, color=C.TEXT_HINT, width=35, text_align=ft.TextAlign.CENTER),
                ft.Text("低", size=11, color=C.TEXT_HINT, width=35, text_align=ft.TextAlign.CENTER),
                ft.Text("涨跌", size=11, color=C.TEXT_HINT, width=40, text_align=ft.TextAlign.CENTER),
                ft.Text("次", size=11, color=C.TEXT_HINT, width=25, text_align=ft.TextAlign.CENTER),
                ft.Text("备注", size=11, color=C.TEXT_HINT, expand=True),
            ], spacing=4),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            bgcolor=ft.Colors.with_opacity(0.04, C.TEXT_PRIMARY),
        )

        return ft.Container(
            content=ft.Column([header, *rows], spacing=0),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=8,
            bgcolor=C.CARD_LIGHT,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    # ─── 详情/删除对话框 ───
    def _show_detail_dialog(self, score_data):
        d = score_data["score_date"]
        o = score_data["open_spirit"]
        c = score_data["close_spirit"]
        h = score_data["high_spirit"]
        l = score_data["low_spirit"]
        count = score_data["change_count"]
        change = c - o
        is_up = change >= 0
        notes = score_data.get("notes") or "无"

        def on_delete(e):
            self.svc.delete_score(score_data["id"])
            dlg.open = False
            self._page.update()
            self._refresh()
            self._page.update()
            _sb = ft.SnackBar(ft.Text("🗑️ 已删除"), bgcolor=C.WARNING)
            _sb.open = True
            self._page.overlay.append(_sb)
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"{d.month}/{d.day} 心境K线", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("开盘:", size=14, color=C.TEXT_SECONDARY, width=60),
                        ft.Text(str(o), size=14, color=C.TEXT_PRIMARY),
                    ]),
                    ft.Row([
                        ft.Text("收盘:", size=14, color=C.TEXT_SECONDARY, width=60),
                        ft.Text(str(c), size=14, color=C.TEXT_PRIMARY),
                    ]),
                    ft.Row([
                        ft.Text("最高:", size=14, color=C.TEXT_SECONDARY, width=60),
                        ft.Text(str(h), size=14, color=C.TEXT_PRIMARY),
                    ]),
                    ft.Row([
                        ft.Text("最低:", size=14, color=C.TEXT_SECONDARY, width=60),
                        ft.Text(str(l), size=14, color=C.TEXT_PRIMARY),
                    ]),
                    ft.Row([
                        ft.Text("涨跌:", size=14, color=C.TEXT_SECONDARY, width=60),
                        ft.Text(
                            f"{change:+d}",
                            size=14,
                            color=KLINE_GREEN if is_up else KLINE_RED,
                            weight=ft.FontWeight.W_600,
                        ),
                    ]),
                    ft.Row([
                        ft.Text("变动:", size=14, color=C.TEXT_SECONDARY, width=60),
                        ft.Text(f"{count} 次", size=14, color=C.TEXT_PRIMARY),
                    ]),
                    ft.Container(height=4),
                    ft.Text(f"备注: {notes}", size=13, color=C.TEXT_HINT),
                ], spacing=6),
                width=280,
            ),
            actions=[
                ft.Button("删除", on_click=on_delete),
                ft.Button("关闭", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
            ],
        )
        self._page.show_dialog(dlg)
