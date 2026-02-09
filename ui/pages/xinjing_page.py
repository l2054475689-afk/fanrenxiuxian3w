"""
心境系统页面 v2
美化版：蓝紫渐变头部、绿色正面卡片、暗红心魔卡片、日常任务、K线人生、手动柱状图统计、优化对话框
"""
from datetime import date, timedelta
import flet as ft
from services.spirit_service import SpiritService
from services.daily_task_service import DailyTaskService
from services.kline_service import KlineService
from services.constants import Colors as C, SPIRIT_LEVELS, SPIRIT_MIN, SPIRIT_MAX
from ui.styles import card_container, section_title

# K线颜色
KLINE_GREEN = "#26a69a"
KLINE_RED = "#ef5350"
KLINE_CHART_HEIGHT = 200
CHART_BG = "#1e222d"
MA_COLOR = "#fbbf24"
Y_MIN = SPIRIT_MIN
Y_MAX = SPIRIT_MAX


class XinjingPage(ft.Column):
    """心境系统页"""

    def __init__(self, page: ft.Page, spirit_service: SpiritService, daily_task_service: DailyTaskService, kline_service: KlineService):
        super().__init__()
        self._page = page
        self.svc = spirit_service
        self.daily_svc = daily_task_service
        self.kline_svc = kline_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._current_tab = 0
        self._kline_display_days = 14

    def build(self):
        status = self.svc.get_spirit_status()
        self.controls = [
            self._spirit_header(status),
            self._tab_bar(),
            self._build_content(),
            ft.Container(height=80),
        ]

    # ─── 心境头部 — 蓝紫渐变 ────────────────────────────────
    def _spirit_header(self, status: dict) -> ft.Container:
        """心境状态头部 — 蓝紫渐变，大号数值"""
        if not status:
            return ft.Container()

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Text("🧘", size=22),
                        ft.Text("心境", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ], spacing=6),
                    ft.Container(
                        content=ft.Text(
                            status["level_name"], size=14,
                            weight=ft.FontWeight.BOLD, color="white",
                        ),
                        bgcolor=ft.Colors.with_opacity(0.3, "white"),
                        border_radius=14,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=4),
                ft.Text(
                    f"{status['value']}",
                    size=56, weight=ft.FontWeight.BOLD, color="white",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=4),
                ft.ProgressBar(
                    value=status["progress"], height=8,
                    color="white",
                    bgcolor=ft.Colors.with_opacity(0.2, "white"),
                    border_radius=4,
                ),
                ft.Row([
                    ft.Text(f"{status['min']}", size=11, color=ft.Colors.with_opacity(0.5, "white")),
                    ft.Text(
                        f"距{status['next_level_name']}还需 {status['points_to_next']}"
                        if status["next_level_name"] else "✨ 已达最高境界",
                        size=12, color=ft.Colors.with_opacity(0.85, "white"),
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(f"{status['max']}", size=11, color=ft.Colors.with_opacity(0.5, "white")),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=20, right=20, top=20, bottom=16),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#667eea", "#764ba2"],
            ),
        )

    # ─── Tab 栏 ─────────────────────────────────────────────
    def _on_tab_click(self, idx):
        self._current_tab = idx
        self._refresh()

    def _tab_bar(self) -> ft.Container:
        tab_labels = ["正面修炼", "心魔", "日常任务", "K线人生", "统计"]
        tabs = []
        for i, label in enumerate(tab_labels):
            is_sel = (i == self._current_tab)
            tabs.append(ft.Container(
                content=ft.Text(label, size=14, weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL,
                                color=C.PRIMARY if is_sel else C.TEXT_HINT),
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                border=ft.Border(bottom=ft.BorderSide(2, C.PRIMARY) if is_sel else ft.BorderSide(0, "transparent")),
                on_click=lambda e, idx=i: self._on_tab_click(idx),
                ink=True,
            ))
        return ft.Container(
            content=ft.Row(tabs, alignment=ft.MainAxisAlignment.CENTER, spacing=0,
                           scroll=ft.ScrollMode.AUTO),
        )

    def _build_content(self) -> ft.Container:
        if self._current_tab == 0:
            return self._positive_tab()
        elif self._current_tab == 1:
            return self._demon_tab()
        elif self._current_tab == 2:
            return self._daily_tab()
        elif self._current_tab == 3:
            return self._kline_tab()
        else:
            return self._stats_tab()

    # ─── 正面修炼 Tab ───────────────────────────────────────
    def _positive_tab(self) -> ft.Column:
        tasks = self.svc.get_positive_tasks()
        items = []
        for task in tasks:
            completed = self.svc._check_task_completed(task)
            items.append(self._task_card(task, completed))
        items.append(self._add_task_button("positive"))
        return ft.Column(items, spacing=0)

    def _task_card(self, task: dict, completed: bool = False) -> ft.Container:
        def on_complete(e):
            if task["submission_type"] == "daily_checkin":
                result = self.svc.complete_daily_task(task["id"])
            else:
                result = self.svc.complete_repeatable_task(task["id"])
            if result["success"]:
                _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
            else:
                _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=C.WARNING)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
            self._refresh()

        def on_delete(e):
            def confirm_delete(e):
                self.svc.delete_task(task["id"])
                dlg.open = False
                self._page.update()
                _sb = ft.SnackBar(ft.Text(f"已删除: {task['name']}"), bgcolor=C.WARNING)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
                self._refresh()
            dlg = ft.AlertDialog(
                title=ft.Text("确认删除"),
                content=ft.Text(f"确定要删除任务「{task['name']}」吗？"),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                    ft.TextButton("删除", on_click=confirm_delete,
                                  style=ft.ButtonStyle(color=C.ERROR)),
                ],
            )
            self._page.show_dialog(dlg)

        streak_text = ""
        if task["enable_streak"]:
            streak = self.svc.db.get_streak(task["id"])
            if streak and streak["current_streak"] > 0:
                streak_text = f" 🔥{streak['current_streak']}天"

        if completed:
            border_color = ft.Colors.with_opacity(0.2, C.SUCCESS)
            bg_color = ft.Colors.with_opacity(0.04, C.SUCCESS)
            text_color = C.TEXT_HINT
            icon = ft.Icons.CHECK_CIRCLE
            icon_color = C.SUCCESS
        else:
            border_color = ft.Colors.with_opacity(0.5, C.SUCCESS)
            bg_color = C.CARD_LIGHT
            text_color = C.TEXT_PRIMARY
            icon = ft.Icons.RADIO_BUTTON_UNCHECKED
            icon_color = C.TEXT_HINT

        effect_parts = [f"心境{task['spirit_effect']:+d}"]
        if task["blood_effect"]:
            effect_parts.append(f"血量{task['blood_effect']:+d}")

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(task["emoji"], size=26),
                    width=44, height=44,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.08, C.SUCCESS),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(task["name"] + streak_text, size=15, weight=ft.FontWeight.W_500, color=text_color),
                    ft.Text(" · ".join(effect_parts), size=12, color=C.SUCCESS if not completed else C.TEXT_HINT),
                ], spacing=2, expand=True),
                ft.IconButton(icon=icon, icon_color=icon_color, icon_size=28,
                              on_click=None if (completed and task["submission_type"] == "daily_checkin") else on_complete),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=C.TEXT_HINT, icon_size=20, on_click=on_delete),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=14, right=6, top=10, bottom=10),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14, bgcolor=bg_color,
            border=ft.Border.all(1.5, border_color),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=6,
                                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
            on_click=on_complete if not completed else None,
        )

    # ─── 心魔 Tab ───────────────────────────────────────────
    def _demon_tab(self) -> ft.Column:
        tasks = self.svc.get_demon_tasks()
        items = [self._demon_card(task) for task in tasks]
        items.append(self._add_task_button("demon"))
        return ft.Column(items, spacing=0)

    def _demon_card(self, task: dict) -> ft.Container:
        today_count = self.svc.db.get_task_today_count(task["id"])

        def on_demon(e):
            result = self.svc.record_demon(task["id"])
            if result["success"]:
                _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=C.ERROR)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
            self._refresh()

        def on_delete(e):
            def confirm_delete(e):
                self.svc.delete_task(task["id"])
                dlg.open = False
                self._page.update()
                _sb = ft.SnackBar(ft.Text(f"已删除: {task['name']}"), bgcolor=C.WARNING)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
                self._refresh()
            dlg = ft.AlertDialog(
                title=ft.Text("确认删除"),
                content=ft.Text(f"确定要删除心魔「{task['name']}」吗？"),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                    ft.TextButton("删除", on_click=confirm_delete, style=ft.ButtonStyle(color=C.ERROR)),
                ],
            )
            self._page.show_dialog(dlg)

        effect_parts = [f"心境{task['spirit_effect']:+d}"]
        if task["blood_effect"]:
            effect_parts.append(f"血量{task['blood_effect']:+d}")
        if today_count > 0:
            effect_parts.append(f"今日{today_count}次")

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(task["emoji"], size=26),
                    width=44, height=44, border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.12, C.ERROR),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(task["name"], size=15, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Text(" · ".join(effect_parts), size=12, color=C.ERROR),
                ], spacing=2, expand=True),
                ft.IconButton(icon=ft.Icons.WARNING_AMBER_ROUNDED, icon_color="#ff1744", icon_size=28,
                              on_click=on_demon,
                              style=ft.ButtonStyle(overlay_color=ft.Colors.with_opacity(0.12, C.ERROR))),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=C.TEXT_HINT, icon_size=20, on_click=on_delete),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=14, right=6, top=10, bottom=10),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.03, C.ERROR),
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.35, C.ERROR)),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=6,
                                color=ft.Colors.with_opacity(0.06, C.ERROR), offset=ft.Offset(0, 2)),
        )

    # ─── 日常任务 Tab ───────────────────────────────────────
    def _daily_tab(self) -> ft.Column:
        tasks = self.daily_svc.get_today_tasks()
        completion = self.daily_svc.get_today_completion_rate()
        items = []
        items.append(self._daily_completion_card(completion))
        main_tasks = [t for t in tasks if t["category"] == "main"]
        side_tasks = [t for t in tasks if t["category"] == "side"]
        if main_tasks:
            items.append(ft.Container(
                content=ft.Row([
                    ft.Text("📋", size=16),
                    ft.Text("主线任务", size=15, weight=ft.FontWeight.W_600, color="#667eea"),
                    ft.Text(f"({len(main_tasks)})", size=13, color=C.TEXT_HINT),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.only(left=20, top=12, bottom=4),
            ))
            for task in main_tasks:
                items.append(self._daily_task_card(task, is_main=True))
        if side_tasks:
            items.append(ft.Container(
                content=ft.Row([
                    ft.Text("🏠", size=16),
                    ft.Text("支线任务", size=15, weight=ft.FontWeight.W_600, color="#f59e0b"),
                    ft.Text(f"({len(side_tasks)})", size=13, color=C.TEXT_HINT),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.only(left=20, top=12, bottom=4),
            ))
            for task in side_tasks:
                items.append(self._daily_task_card(task, is_main=False))
        if not main_tasks and not side_tasks:
            items.append(ft.Container(
                content=ft.Column([
                    ft.Text("📝", size=40, text_align=ft.TextAlign.CENTER),
                    ft.Text("今天还没有任务", size=15, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                    ft.Text("点击下方按钮添加", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                padding=40, alignment=ft.Alignment(0, 0),
            ))
        items.append(self._daily_add_button())
        return ft.Column(items, spacing=0)

    def _daily_completion_card(self, completion: dict) -> ft.Container:
        total = completion["total"]
        completed = completion["completed"]
        rate = completion["rate"]
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📊 今日进度", size=15, weight=ft.FontWeight.W_600, color="white"),
                    ft.Text(f"{completed}/{total}", size=15, weight=ft.FontWeight.BOLD, color="white"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                ft.ProgressBar(value=rate, height=10, color="white",
                               bgcolor=ft.Colors.with_opacity(0.25, "white"), border_radius=5),
                ft.Container(height=4),
                ft.Text(f"完成率 {rate * 100:.0f}%" if total > 0 else "暂无任务",
                         size=12, color=ft.Colors.with_opacity(0.85, "white"), text_align=ft.TextAlign.CENTER),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
            margin=ft.Margin.symmetric(horizontal=16, vertical=8),
            border_radius=14,
            gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                                       colors=["#667eea", "#764ba2"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=12,
                                color=ft.Colors.with_opacity(0.2, "#667eea"), offset=ft.Offset(0, 4)),
        )

    def _daily_task_card(self, task: dict, is_main: bool = True) -> ft.Container:
        completed = task["is_completed"]
        accent = "#667eea" if is_main else "#f59e0b"
        emoji = "📋" if is_main else "🏠"
        priority = task["priority"]
        priority_map = {"high": ("高", C.ERROR), "medium": ("中", "#667eea"), "low": ("低", C.TEXT_HINT)}
        pri_label, pri_color = priority_map.get(priority, ("中", "#667eea"))

        def on_toggle(e):
            if completed:
                result = self.daily_svc.uncomplete_daily_task(task["id"])
            else:
                result = self.daily_svc.complete_daily_task(task["id"])
            if result["success"]:
                _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS if not completed else C.WARNING)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
            self._refresh()

        def on_delete(e):
            def confirm_delete(e):
                result = self.daily_svc.delete_daily_task(task["id"])
                dlg.open = False
                self._page.update()
                _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=C.WARNING)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
                self._refresh()
            dlg = ft.AlertDialog(
                title=ft.Text("确认删除"),
                content=ft.Text(f"确定要删除任务「{task['name']}」吗？"),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                    ft.TextButton("删除", on_click=confirm_delete, style=ft.ButtonStyle(color=C.ERROR)),
                ],
            )
            self._page.show_dialog(dlg)

        if completed:
            border_color = ft.Colors.with_opacity(0.15, accent)
            bg_color = ft.Colors.with_opacity(0.04, "#999999")
            text_color = C.TEXT_HINT
            icon = ft.Icons.CHECK_CIRCLE
            icon_color = C.SUCCESS
        else:
            border_color = ft.Colors.with_opacity(0.4, accent)
            bg_color = C.CARD_LIGHT
            text_color = C.TEXT_PRIMARY
            icon = ft.Icons.RADIO_BUTTON_UNCHECKED
            icon_color = C.TEXT_HINT

        if completed:
            name_text = ft.Text(task["name"], size=15, weight=ft.FontWeight.W_500, color=text_color,
                                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH))
        else:
            name_text = ft.Text(task["name"], size=15, weight=ft.FontWeight.W_500, color=text_color)

        name_row = ft.Row([
            name_text,
            ft.Container(
                content=ft.Text(pri_label, size=10, weight=ft.FontWeight.BOLD, color="white"),
                bgcolor=pri_color, border_radius=8,
                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            ),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        info_parts = []
        if task.get("notes"):
            info_parts.append(task["notes"])
        info_row = ft.Text(" · ".join(info_parts), size=12, color=C.TEXT_HINT) if info_parts else None
        middle_col_controls = [name_row]
        if info_row:
            middle_col_controls.append(info_row)

        return ft.Container(
            content=ft.Row([
                ft.Container(content=ft.Text(emoji, size=26), width=44, height=44, border_radius=12,
                             bgcolor=ft.Colors.with_opacity(0.08, accent), alignment=ft.Alignment(0, 0)),
                ft.Column(middle_col_controls, spacing=2, expand=True),
                ft.IconButton(icon=icon, icon_color=icon_color, icon_size=28, on_click=on_toggle),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=C.TEXT_HINT, icon_size=20, on_click=on_delete),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=14, right=6, top=10, bottom=10),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14, bgcolor=bg_color,
            border=ft.Border.all(1.5, border_color),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=6,
                                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
            on_click=on_toggle,
        )

    def _daily_add_button(self) -> ft.Container:
        accent = "#667eea"
        def on_add(e):
            self._show_daily_add_dialog()
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=accent, size=20),
                ft.Text("添加日常任务", size=14, color=accent, weight=ft.FontWeight.W_500),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=14, margin=ft.Margin.symmetric(horizontal=16, vertical=8),
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.35, accent)),
            border_radius=14, on_click=on_add,
        )

    def _show_daily_add_dialog(self):
        name_field = ft.TextField(label="任务名称", autofocus=True, border_radius=10, prefix_icon=ft.Icons.EDIT_NOTE)
        category_dd = ft.Dropdown(label="分类", value="main", border_radius=10,
                                   options=[ft.dropdown.Option("main", "主线任务"), ft.dropdown.Option("side", "支线任务")])
        priority_dd = ft.Dropdown(label="优先级", value="medium", border_radius=10,
                                   options=[ft.dropdown.Option("high", "高"), ft.dropdown.Option("medium", "中"), ft.dropdown.Option("low", "低")])
        notes_field = ft.TextField(label="备注（可选）", border_radius=10, prefix_icon=ft.Icons.NOTES,
                                    multiline=True, min_lines=1, max_lines=3)
        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            self.daily_svc.create_daily_task(name=name, category=category_dd.value,
                                              priority=priority_dd.value, notes=notes_field.value.strip() or None)
            dlg.open = False
            self._page.update()
            self._refresh()
        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.ADD_TASK, color="#667eea", size=24),
                           ft.Text("添加日常任务", size=18, weight=ft.FontWeight.W_600)], spacing=8),
            content=ft.Column([name_field, ft.Container(height=4), ft.Row([category_dd, priority_dd], spacing=10),
                                ft.Container(height=4), notes_field], tight=True, spacing=8, width=300),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.Button("保存", on_click=on_save, bgcolor="#667eea", color="white",
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)

    # ─── K线人生 Tab ──────────────────────────────────────────
    def _kline_tab(self) -> ft.Column:
        today_score = self.kline_svc.get_today_score()
        scores = self.kline_svc.get_scores(days=self._kline_display_days)
        weekly_avg = self.kline_svc.get_weekly_avg()
        return ft.Column([
            self._kline_today_card(today_score),
            self._kline_range_selector(),
            self._kline_chart(scores, weekly_avg),
            section_title("历史记录"),
            self._kline_score_list(scores),
        ], spacing=0)

    def _kline_today_card(self, today) -> ft.Container:
        if not today:
            return card_container(
                ft.Column([
                    ft.Text("今日尚无心境变动", size=16, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                    ft.Text("完成心境任务后自动生成K线数据", size=13, color=C.TEXT_SECONDARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            )
        open_v, close_v = today["open_spirit"], today["close_spirit"]
        high_v, low_v = today["high_spirit"], today["low_spirit"]
        count = today["change_count"]
        is_up = close_v >= open_v
        change = close_v - open_v
        bg_colors = [KLINE_GREEN, "#1b5e20"] if is_up else [KLINE_RED, "#b71c1c"]
        items = [self._kline_score_item("开盘", open_v), self._kline_score_item("收盘", close_v),
                 self._kline_score_item("最高", high_v), self._kline_score_item("最低", low_v)]
        change_text = f"{'+'if change>=0 else ''}{change}"
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("今日心境", size=14, color=ft.Colors.with_opacity(0.8, "white")),
                        ft.Text(change_text, size=13, weight=ft.FontWeight.W_600, color="white")],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=4),
                ft.Row(items, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=4),
                ft.Row([ft.Text(f"变动 {count} 次", size=12, color=ft.Colors.with_opacity(0.7, "white"))],
                       alignment=ft.MainAxisAlignment.CENTER),
            ]),
            padding=16, margin=ft.Margin.symmetric(horizontal=16, vertical=4), border_radius=12,
            gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=bg_colors),
        )

    def _kline_score_item(self, label, value) -> ft.Column:
        return ft.Column([
            ft.Text(label, size=11, color=ft.Colors.with_opacity(0.7, "white")),
            ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD, color="white"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    def _kline_range_selector(self) -> ft.Container:
        def on_select(days):
            def handler(e):
                self._kline_display_days = days
                self._refresh()
            return handler
        buttons = []
        for d in [7, 14, 30]:
            is_active = self._kline_display_days == d
            buttons.append(ft.Container(
                content=ft.Text(f"{d}天", size=13,
                                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                                color="white" if is_active else C.TEXT_SECONDARY),
                bgcolor=C.PRIMARY if is_active else ft.Colors.with_opacity(0.08, C.TEXT_PRIMARY),
                border_radius=16, padding=ft.Padding.symmetric(horizontal=16, vertical=6),
                on_click=on_select(d),
            ))
        return ft.Container(
            content=ft.Row(buttons, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            padding=ft.Padding.symmetric(vertical=8),
        )

    def _kline_chart(self, scores, weekly_avg) -> ft.Container:
        from ui.styles import ALIGN_CENTER as _AC
        if not scores:
            return card_container(
                ft.Container(content=ft.Text("暂无数据，完成心境任务后自动生成", size=14,
                                              color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                             height=KLINE_CHART_HEIGHT, alignment=_AC),
            )
        score_map = {s["score_date"]: s for s in scores}
        avg_map = {a["date"]: a["avg"] for a in weekly_avg}
        end = date.today()
        days = self._kline_display_days
        all_dates = [end - timedelta(days=days - 1 - i) for i in range(days)]
        candle_width = max(8, min(20, (350 - 40) // days))
        gap = max(2, (350 - 40 - candle_width * days) // max(1, days - 1))
        body_width = max(6, candle_width - 2)
        wick_width = 2
        y_range = Y_MAX - Y_MIN

        def y_of(val):
            clamped = max(Y_MIN, min(Y_MAX, val))
            return KLINE_CHART_HEIGHT - ((clamped - Y_MIN) / y_range * KLINE_CHART_HEIGHT)

        candles, ma_dots, x_labels = [], [], []
        for i, d in enumerate(all_dates):
            x_pos = 20 + i * (candle_width + gap)
            sc = score_map.get(d)
            if sc:
                o, c, h, l = sc["open_spirit"], sc["close_spirit"], sc["high_spirit"], sc["low_spirit"]
                color = KLINE_GREEN if c >= o else KLINE_RED
                body_top = y_of(max(o, c))
                body_bottom = y_of(min(o, c))
                body_h = max(2, body_bottom - body_top)
                wick_top = y_of(h)
                wick_bottom = y_of(l)
                wick_h = max(1, wick_bottom - wick_top)
                candles.append(ft.Container(width=wick_width, height=wick_h, bgcolor=color,
                                            left=x_pos + (body_width - wick_width) / 2, top=wick_top))
                candles.append(ft.Container(width=body_width, height=body_h, bgcolor=color,
                                            border_radius=2, left=x_pos, top=body_top))
            avg_val = avg_map.get(d)
            if avg_val is not None:
                ma_y = y_of(avg_val)
                ma_dots.append(ft.Container(width=4, height=4, border_radius=2, bgcolor=MA_COLOR,
                                            left=x_pos + body_width / 2 - 2, top=ma_y - 2))
            show_label = (i % max(1, days // 7) == 0) or i == days - 1
            if show_label:
                x_labels.append(ft.Container(
                    content=ft.Text(f"{d.month}/{d.day}", size=9, color=C.TEXT_HINT),
                    left=x_pos - 6, top=KLINE_CHART_HEIGHT + 4))

        y_labels = []
        for val in [Y_MIN, -100, 0, 100, 200, 320, Y_MAX]:
            y = y_of(val)
            y_labels.append(ft.Container(content=ft.Text(str(val), size=8, color=C.TEXT_HINT), left=0, top=y - 6))
            y_labels.append(ft.Container(width=350, height=1,
                                          bgcolor=ft.Colors.with_opacity(0.1, C.TEXT_HINT), left=16, top=y))

        chart_stack = ft.Stack([*y_labels, *candles, *ma_dots, *x_labels], width=400, height=KLINE_CHART_HEIGHT + 24)
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
                ft.Container(content=chart_stack, bgcolor=CHART_BG, border_radius=8,
                             padding=ft.Padding.only(top=8, bottom=8, left=4, right=4),
                             clip_behavior=ft.ClipBehavior.HARD_EDGE),
                ft.Container(content=legend, padding=ft.Padding.only(top=4)),
            ]),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
        )

    def _kline_score_list(self, scores) -> ft.Container:
        if not scores:
            return card_container(
                ft.Text("暂无记录", size=14, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER))
        rows = []
        sorted_scores = sorted(scores, key=lambda x: x["score_date"], reverse=True)
        for sc in sorted_scores:
            o, c = sc["open_spirit"], sc["close_spirit"]
            h, l, count = sc["high_spirit"], sc["low_spirit"], sc["change_count"]
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
                on_click=lambda e, s=sc: self._show_kline_detail_dialog(s),
            )
            rows.append(row)
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
            border_radius=8, bgcolor=C.CARD_LIGHT, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def _show_kline_detail_dialog(self, score_data):
        d = score_data["score_date"]
        o, c = score_data["open_spirit"], score_data["close_spirit"]
        h, l = score_data["high_spirit"], score_data["low_spirit"]
        count = score_data["change_count"]
        change = c - o
        is_up = change >= 0
        notes = score_data.get("notes") or "无"

        def on_delete(e):
            self.kline_svc.delete_score(score_data["id"])
            dlg.open = False
            self._page.update()
            self._refresh()
            _sb = ft.SnackBar(ft.Text("🗑️ 已删除"), bgcolor=C.WARNING)
            _sb.open = True
            self._page.overlay.append(_sb)
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"{d.month}/{d.day} 心境K线", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("开盘:", size=14, color=C.TEXT_SECONDARY, width=60), ft.Text(str(o), size=14, color=C.TEXT_PRIMARY)]),
                    ft.Row([ft.Text("收盘:", size=14, color=C.TEXT_SECONDARY, width=60), ft.Text(str(c), size=14, color=C.TEXT_PRIMARY)]),
                    ft.Row([ft.Text("最高:", size=14, color=C.TEXT_SECONDARY, width=60), ft.Text(str(h), size=14, color=C.TEXT_PRIMARY)]),
                    ft.Row([ft.Text("最低:", size=14, color=C.TEXT_SECONDARY, width=60), ft.Text(str(l), size=14, color=C.TEXT_PRIMARY)]),
                    ft.Row([ft.Text("涨跌:", size=14, color=C.TEXT_SECONDARY, width=60),
                            ft.Text(f"{change:+d}", size=14, color=KLINE_GREEN if is_up else KLINE_RED, weight=ft.FontWeight.W_600)]),
                    ft.Row([ft.Text("变动:", size=14, color=C.TEXT_SECONDARY, width=60), ft.Text(f"{count} 次", size=14, color=C.TEXT_PRIMARY)]),
                    ft.Container(height=4),
                    ft.Text(f"备注: {notes}", size=13, color=C.TEXT_HINT),
                ], spacing=6), width=280,
            ),
            actions=[
                ft.Button("删除", on_click=on_delete),
                ft.Button("关闭", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
            ],
        )
        self._page.show_dialog(dlg)

    # ─── 统计 Tab ───────────────────────────────────────────
    def _stats_tab(self) -> ft.Column:
        summary = self.svc.get_today_summary()
        stats_7d = self.svc.get_statistics(7)
        stats_30d = self.svc.get_statistics(30)
        return ft.Column([
            section_title("今日"), self._summary_card(summary),
            section_title("近7天趋势"), self._stats_bar_chart(7),
            section_title("近7天"), self._stats_data_card(stats_7d),
            section_title("近30天"), self._stats_data_card(stats_30d),
        ], spacing=0)

    def _summary_card(self, summary: dict) -> ft.Container:
        items = [
            ("✅", str(summary["positive_count"]), "正面", C.SUCCESS),
            ("👿", str(summary["demon_count"]), "心魔", C.ERROR),
            ("🧘", f"{summary['total_spirit_change']:+d}", "净心境", "#667eea"),
        ]
        return ft.Container(
            content=ft.Row([self._stat_item(e, v, l, c) for e, v, l, c in items],
                           alignment=ft.MainAxisAlignment.SPACE_AROUND),
            padding=16, margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14, bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

    def _stats_bar_chart(self, days: int) -> ft.Container:
        trend = self.svc.get_spirit_trend(days)
        if not trend:
            return ft.Container(content=ft.Text("暂无数据", size=13, color=C.TEXT_HINT), padding=20)
        max_val = max(max(abs(d["change"]), 1) for d in trend)
        chart_height = 110

        def _bar(value, color, width=18):
            h = max(2, (abs(value) / max(max_val, 1)) * chart_height)
            return ft.Container(width=width, height=h, bgcolor=color,
                                border_radius=ft.BorderRadius.only(top_left=4, top_right=4), tooltip=f"{value:+d}")

        bar_columns = []
        for d in trend:
            change = d["change"]
            color = C.SUCCESS if change >= 0 else C.ERROR
            bar_columns.append(ft.Column([
                _bar(change, color),
                ft.Text(d["date"], size=8, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.END, spacing=4))

        chart = ft.Container(
            content=ft.Row(bar_columns, alignment=ft.MainAxisAlignment.SPACE_AROUND,
                           vertical_alignment=ft.CrossAxisAlignment.END),
            height=chart_height + 26,
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, ft.Colors.BLACK))),
        )
        legend = ft.Row([
            ft.Row([ft.Container(width=10, height=10, bgcolor=C.SUCCESS, border_radius=2),
                    ft.Text("正面", size=10, color=C.TEXT_HINT)], spacing=4),
            ft.Row([ft.Container(width=10, height=10, bgcolor=C.ERROR, border_radius=2),
                    ft.Text("负面", size=10, color=C.TEXT_HINT)], spacing=4),
        ], spacing=16, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([chart, legend], spacing=8),
            padding=ft.Padding.only(left=8, right=16, top=8, bottom=12),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14, bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

    def _stats_data_card(self, stats: dict) -> ft.Container:
        items = [
            ("⬆️", str(stats["positive_total"]), "正面总计", C.SUCCESS),
            ("⬇️", str(stats["demon_total"]), "心魔总计", C.ERROR),
            ("📊", f"{stats['net_spirit']:+d}", "净变化", "#667eea"),
        ]
        return ft.Container(
            content=ft.Row([self._stat_item(e, v, l, c) for e, v, l, c in items],
                           alignment=ft.MainAxisAlignment.SPACE_AROUND),
            padding=16, margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14, bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

    # ─── 添加任务按钮 ───────────────────────────────────────
    def _add_task_button(self, task_type: str) -> ft.Container:
        is_positive = task_type == "positive"
        accent = C.SUCCESS if is_positive else C.ERROR
        def on_add(e):
            self._show_add_dialog(task_type)
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=accent, size=20),
                ft.Text("添加修炼任务" if is_positive else "添加心魔", size=14, color=accent, weight=ft.FontWeight.W_500),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=14, margin=ft.Margin.symmetric(horizontal=16, vertical=8),
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.35, accent)),
            border_radius=14, on_click=on_add,
        )

    def _show_add_dialog(self, task_type: str):
        is_positive = task_type == "positive"
        accent = C.SUCCESS if is_positive else C.ERROR
        name_field = ft.TextField(label="任务名称", autofocus=True, border_radius=10, prefix_icon=ft.Icons.EDIT_NOTE)
        spirit_field = ft.TextField(label="心境值", value="1", keyboard_type=ft.KeyboardType.NUMBER,
                                     border_radius=10, prefix_icon=ft.Icons.SELF_IMPROVEMENT, width=140)
        blood_field = ft.TextField(label="血量值", value="0", keyboard_type=ft.KeyboardType.NUMBER,
                                    border_radius=10, prefix_icon=ft.Icons.FAVORITE, width=140)
        streak_check = ft.Checkbox(label="连续打卡追踪 🔥", value=False)
        sub_type = ft.Dropdown(label="提交方式", value="daily_checkin", border_radius=10,
                                options=[ft.dropdown.Option("daily_checkin", "每日打卡"),
                                         ft.dropdown.Option("repeatable", "可重复")])
        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            spirit_val = int(spirit_field.value or "1")
            blood_val = int(blood_field.value or "0")
            if is_positive:
                self.svc.create_positive_task(name=name, spirit_effect=spirit_val, blood_effect=blood_val,
                                               submission_type=sub_type.value, enable_streak=streak_check.value)
            else:
                self.svc.create_demon_task(name=name, spirit_effect=spirit_val, blood_effect=blood_val)
            dlg.open = False
            self._page.update()
            self._refresh()

        content_controls = [name_field, ft.Container(height=4), ft.Row([spirit_field, blood_field], spacing=10)]
        if is_positive:
            content_controls.extend([ft.Container(height=4), sub_type, streak_check])

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ADD_TASK if is_positive else ft.Icons.WARNING_AMBER, color=accent, size=24),
                ft.Text("添加修炼任务" if is_positive else "添加心魔", size=18, weight=ft.FontWeight.W_600),
            ], spacing=8),
            content=ft.Column(content_controls, tight=True, spacing=8, width=300),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.Button("保存", on_click=on_save, bgcolor=accent, color="white",
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)

    # ─── 辅助 ───────────────────────────────────────────────
    def _stat_item(self, emoji: str, value: str, label: str, accent: str = C.TEXT_PRIMARY) -> ft.Column:
        return ft.Column([
            ft.Text(emoji, size=20),
            ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=accent),
            ft.Text(label, size=11, color=C.TEXT_HINT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    def _refresh(self):
        self.controls.clear()
        self.build()
        try:
            self.update()
        except RuntimeError:
            pass


# 给 SpiritService 加个辅助方法引用
SpiritService._check_task_completed = lambda self, task: self.db.is_task_completed_today(task["id"]) if task["submission_type"] == "daily_checkin" else False
