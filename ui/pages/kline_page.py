"""
K线人生图页面 — 用K线蜡烛图可视化每日心情
"""
import json
from datetime import date, timedelta
import flet as ft
from services.kline_service import KlineService
from services.constants import Colors as C
from ui.styles import card_container, section_title, ALIGN_CENTER

# 预设标签
PRESET_TAGS = ["工作", "运动", "社交", "学习", "休息", "旅行", "恋爱", "家庭"]

# K线颜色
KLINE_GREEN = "#26a69a"  # 涨（心情变好）
KLINE_RED = "#ef5350"    # 跌（心情变差）
CHART_HEIGHT = 200
CHART_BG = "#1e222d"
MA_COLOR = "#fbbf24"


class KlinePage(ft.Column):
    """K线人生图页"""

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
        yesterday = self.svc.get_scores(days=2)
        yesterday_score = yesterday[0] if len(yesterday) >= 2 and yesterday[0]["score_date"] != date.today() else (yesterday[0] if yesterday and yesterday[0]["score_date"] != date.today() else None)
        weekly_avg = self.svc.get_weekly_avg()

        self.controls = [
            # 顶部标题
            ft.Container(
                content=ft.Row([
                    ft.Text("K线人生图", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text("📊 心情K线", size=11, color="white"),
                        bgcolor="#667eea",
                        border_radius=12,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.only(left=20, right=20, top=16, bottom=8),
            ),
            # 今日评分卡片
            self._today_card(today_score, yesterday_score),
            # 时间范围切换
            self._range_selector(),
            # K线图
            self._kline_chart(scores, weekly_avg),
            # 日期列表
            section_title("历史记录"),
            self._score_list(scores),
            ft.Container(height=80),
        ]

    # ─── 今日评分卡片 ───
    def _today_card(self, today, yesterday):
        if not today or (today["morning_score"] is None and today["evening_score"] is None):
            return card_container(
                ft.Column([
                    ft.Text("今日尚未记录", size=16, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                    ft.Text("记录你的心情，开始今天的K线", size=13, color=C.TEXT_SECONDARY),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text("☀️ 记录今日心情", size=15, weight=ft.FontWeight.W_600, color="white"),
                        bgcolor=KLINE_GREEN,
                        border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                        on_click=lambda e: self._show_record_dialog(),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            )

        morning = today.get("morning_score")
        evening = today.get("evening_score")
        high = today.get("high_score")
        low = today.get("low_score")
        close_val = evening if evening is not None else morning

        # 对比昨天
        yesterday_close = None
        if yesterday:
            yesterday_close = yesterday.get("evening_score") or yesterday.get("morning_score")

        if yesterday_close is not None and close_val is not None:
            change = close_val - yesterday_close
            change_pct = (change / yesterday_close * 100) if yesterday_close != 0 else 0
            is_up = change >= 0
        else:
            change = 0
            change_pct = 0
            is_up = True if morning is not None and evening is not None and evening >= morning else True

        bg_colors = [KLINE_GREEN, "#1b5e20"] if is_up else [KLINE_RED, "#b71c1c"]

        items = []
        if morning is not None:
            items.append(self._score_item("开盘", morning))
        if evening is not None:
            items.append(self._score_item("收盘", evening))
        if high is not None:
            items.append(self._score_item("最高", high))
        if low is not None:
            items.append(self._score_item("最低", low))

        change_text = f"{'+'if change>=0 else ''}{change} ({change_pct:+.1f}%)" if yesterday_close else ""

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("今日心情", size=14, color=ft.Colors.with_opacity(0.8, "white")),
                    ft.Text(change_text, size=13, weight=ft.FontWeight.W_600, color="white") if change_text else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=4),
                ft.Row(items, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=8),
                ft.Row([
                    ft.Container(
                        content=ft.Text("✏️ 编辑", size=12, color="white"),
                        bgcolor=ft.Colors.with_opacity(0.3, "white"),
                        border_radius=12,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                        on_click=lambda e: self._show_record_dialog(today),
                    ),
                ], alignment=ft.MainAxisAlignment.END),
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
                    content=ft.Text("暂无数据，开始记录你的心情吧", size=14, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
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

        candles = []
        ma_dots = []
        x_labels = []

        for i, d in enumerate(all_dates):
            x_pos = 20 + i * (candle_width + gap)
            sc = score_map.get(d)

            if sc and (sc["morning_score"] is not None or sc["evening_score"] is not None):
                o = sc["morning_score"] if sc["morning_score"] is not None else sc["evening_score"]
                c = sc["evening_score"] if sc["evening_score"] is not None else sc["morning_score"]
                h = sc["high_score"] if sc["high_score"] is not None else max(o, c)
                l = sc["low_score"] if sc["low_score"] is not None else min(o, c)

                is_up = c >= o
                color = KLINE_GREEN if is_up else KLINE_RED

                # Y mapping: score 0->CHART_HEIGHT, score 100->0
                def y_of(val):
                    return CHART_HEIGHT - (val / 100.0 * CHART_HEIGHT)

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
                ma_y = CHART_HEIGHT - (avg_val / 100.0 * CHART_HEIGHT)
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

        # MA line connections (simple dots, no lines in pure Container)
        # Y-axis labels
        y_labels = []
        for val in [0, 25, 50, 75, 100]:
            y = CHART_HEIGHT - (val / 100.0 * CHART_HEIGHT)
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
        for i, sc in enumerate(sorted_scores):
            o = sc["morning_score"]
            c = sc["evening_score"]
            h = sc["high_score"]
            l = sc["low_score"]

            close_val = c if c is not None else o
            open_val = o if o is not None else c

            if close_val is not None and open_val is not None and open_val != 0:
                change_pct = (close_val - open_val) / open_val * 100
                change_str = f"{change_pct:+.1f}%"
                change_color = KLINE_GREEN if change_pct >= 0 else KLINE_RED
            else:
                change_str = "-"
                change_color = C.TEXT_HINT

            d = sc["score_date"]
            date_str = f"{d.month}/{d.day}"
            notes_str = sc.get("notes") or ""
            if len(notes_str) > 10:
                notes_str = notes_str[:10] + "…"

            row = ft.Container(
                content=ft.Row([
                    ft.Text(date_str, size=12, color=C.TEXT_PRIMARY, width=40),
                    ft.Text(str(o or "-"), size=12, color=C.TEXT_PRIMARY, width=30, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(c or "-"), size=12, color=C.TEXT_PRIMARY, width=30, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(h or "-"), size=12, color=C.TEXT_HINT, width=30, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(l or "-"), size=12, color=C.TEXT_HINT, width=30, text_align=ft.TextAlign.CENTER),
                    ft.Text(change_str, size=12, color=change_color, width=50, text_align=ft.TextAlign.CENTER),
                    ft.Text(notes_str, size=11, color=C.TEXT_HINT, expand=True),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.08, C.TEXT_PRIMARY))),
                on_click=lambda e, s=sc: self._show_edit_dialog(s),
            )
            rows.append(row)

        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Text("日期", size=11, color=C.TEXT_HINT, width=40),
                ft.Text("开", size=11, color=C.TEXT_HINT, width=30, text_align=ft.TextAlign.CENTER),
                ft.Text("收", size=11, color=C.TEXT_HINT, width=30, text_align=ft.TextAlign.CENTER),
                ft.Text("高", size=11, color=C.TEXT_HINT, width=30, text_align=ft.TextAlign.CENTER),
                ft.Text("低", size=11, color=C.TEXT_HINT, width=30, text_align=ft.TextAlign.CENTER),
                ft.Text("涨跌", size=11, color=C.TEXT_HINT, width=50, text_align=ft.TextAlign.CENTER),
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

    # ─── 记录对话框 ───
    def _show_record_dialog(self, existing=None):
        is_edit = existing is not None
        morning_val = (existing or {}).get("morning_score") or 50
        evening_val = (existing or {}).get("evening_score") or 50
        high_val = (existing or {}).get("high_score")
        low_val = (existing or {}).get("low_score")
        notes_val = (existing or {}).get("notes") or ""
        tags_val = []
        if existing and existing.get("tags"):
            try:
                tags_val = json.loads(existing["tags"])
            except (json.JSONDecodeError, TypeError):
                tags_val = []

        morning_slider = ft.Slider(min=0, max=100, value=morning_val, divisions=100, label="{value}")
        evening_slider = ft.Slider(min=0, max=100, value=evening_val, divisions=100, label="{value}")
        morning_label = ft.Text(f"☀️ 早上心情: {morning_val}", size=14, color=C.TEXT_PRIMARY)
        evening_label = ft.Text(f"🌙 晚上心情: {evening_val}", size=14, color=C.TEXT_PRIMARY)
        notes_field = ft.TextField(
            value=notes_val, label="备注", multiline=True, min_lines=2, max_lines=4,
            border_radius=8, text_size=14,
        )

        selected_tags = list(tags_val)

        def on_morning_change(e):
            morning_label.value = f"☀️ 早上心情: {int(e.control.value)}"
            self._page.update()

        def on_evening_change(e):
            evening_label.value = f"🌙 晚上心情: {int(e.control.value)}"
            self._page.update()

        morning_slider.on_change = on_morning_change
        evening_slider.on_change = on_evening_change

        # Tag chips
        tag_chips_row = ft.Ref[ft.Row]()

        def make_tag_chips():
            chips = []
            for tag in PRESET_TAGS:
                is_sel = tag in selected_tags
                chips.append(ft.Container(
                    content=ft.Text(tag, size=12, color="white" if is_sel else C.TEXT_SECONDARY),
                    bgcolor=C.PRIMARY if is_sel else ft.Colors.with_opacity(0.08, C.TEXT_PRIMARY),
                    border_radius=14,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    on_click=lambda e, t=tag: toggle_tag(t),
                ))
            return chips

        def toggle_tag(tag):
            if tag in selected_tags:
                selected_tags.remove(tag)
            else:
                selected_tags.append(tag)
            tag_chips_row.current.controls = make_tag_chips()
            self._page.update()

        tag_row = ft.Row(
            make_tag_chips(),
            wrap=True, spacing=6, run_spacing=6,
            ref=tag_chips_row,
        )

        def on_save(e):
            m = int(morning_slider.value)
            ev = int(evening_slider.value)
            h = max(m, ev, high_val or 0)
            lo = min(m, ev, low_val or 100)
            tags_json = json.dumps(selected_tags, ensure_ascii=False) if selected_tags else None
            self.svc.update_score(
                date.today(),
                morning=m, evening=ev, high=h, low=lo,
                notes=notes_field.value or None,
                tags=tags_json,
            )
            dlg.open = False
            self._page.update()
            self._refresh()
            self._page.update()
            _sb = ft.SnackBar(ft.Text("✅ 已保存"), bgcolor=C.SUCCESS)
            _sb.open = True
            self._page.overlay.append(_sb)
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("编辑今日心情" if is_edit else "记录今日心情", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    morning_label,
                    morning_slider,
                    evening_label,
                    evening_slider,
                    ft.Text("标签", size=13, color=C.TEXT_SECONDARY),
                    tag_row,
                    ft.Container(height=4),
                    notes_field,
                ], spacing=6, scroll=ft.ScrollMode.AUTO),
                width=320, height=400,
            ),
            actions=[
                ft.Button("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.Button("保存", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    # ─── 编辑/删除对话框 ───
    def _show_edit_dialog(self, score_data):
        d = score_data["score_date"]
        morning_val = score_data.get("morning_score") or 50
        evening_val = score_data.get("evening_score") or 50
        high_val = score_data.get("high_score")
        low_val = score_data.get("low_score")
        notes_val = score_data.get("notes") or ""
        tags_val = []
        if score_data.get("tags"):
            try:
                tags_val = json.loads(score_data["tags"])
            except (json.JSONDecodeError, TypeError):
                tags_val = []

        morning_slider = ft.Slider(min=0, max=100, value=morning_val, divisions=100, label="{value}")
        evening_slider = ft.Slider(min=0, max=100, value=evening_val, divisions=100, label="{value}")
        morning_label = ft.Text(f"☀️ 早上: {morning_val}", size=14, color=C.TEXT_PRIMARY)
        evening_label = ft.Text(f"🌙 晚上: {evening_val}", size=14, color=C.TEXT_PRIMARY)
        notes_field = ft.TextField(
            value=notes_val, label="备注", multiline=True, min_lines=2, max_lines=4,
            border_radius=8, text_size=14,
        )

        selected_tags = list(tags_val)
        tag_chips_row = ft.Ref[ft.Row]()

        def make_tag_chips():
            chips = []
            for tag in PRESET_TAGS:
                is_sel = tag in selected_tags
                chips.append(ft.Container(
                    content=ft.Text(tag, size=12, color="white" if is_sel else C.TEXT_SECONDARY),
                    bgcolor=C.PRIMARY if is_sel else ft.Colors.with_opacity(0.08, C.TEXT_PRIMARY),
                    border_radius=14,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    on_click=lambda e, t=tag: toggle_tag(t),
                ))
            return chips

        def toggle_tag(tag):
            if tag in selected_tags:
                selected_tags.remove(tag)
            else:
                selected_tags.append(tag)
            tag_chips_row.current.controls = make_tag_chips()
            self._page.update()

        def on_morning_change(e):
            morning_label.value = f"☀️ 早上: {int(e.control.value)}"
            self._page.update()

        def on_evening_change(e):
            evening_label.value = f"🌙 晚上: {int(e.control.value)}"
            self._page.update()

        morning_slider.on_change = on_morning_change
        evening_slider.on_change = on_evening_change

        tag_row = ft.Row(make_tag_chips(), wrap=True, spacing=6, run_spacing=6, ref=tag_chips_row)

        def on_save(e):
            m = int(morning_slider.value)
            ev = int(evening_slider.value)
            h = max(m, ev, high_val or 0)
            lo = min(m, ev, low_val or 100)
            tags_json = json.dumps(selected_tags, ensure_ascii=False) if selected_tags else None
            self.svc.update_score(d, morning=m, evening=ev, high=h, low=lo, notes=notes_field.value or None, tags=tags_json)
            dlg.open = False
            self._page.update()
            self._refresh()
            self._page.update()
            _sb = ft.SnackBar(ft.Text("✅ 已更新"), bgcolor=C.SUCCESS)
            _sb.open = True
            self._page.overlay.append(_sb)
            self._page.update()

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
            title=ft.Text(f"编辑 {d.month}/{d.day} 心情", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    morning_label, morning_slider,
                    evening_label, evening_slider,
                    ft.Text("标签", size=13, color=C.TEXT_SECONDARY),
                    tag_row,
                    ft.Container(height=4),
                    notes_field,
                ], spacing=6, scroll=ft.ScrollMode.AUTO),
                width=320, height=400,
            ),
            actions=[
                ft.Button("删除", on_click=on_delete),
                ft.Button("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.Button("保存", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)
