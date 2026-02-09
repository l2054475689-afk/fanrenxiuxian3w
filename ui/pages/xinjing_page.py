"""
心境系统页面 v2
美化版：蓝紫渐变头部、绿色正面卡片、暗红心魔卡片、手动柱状图统计、优化对话框
"""
import flet as ft
from services.spirit_service import SpiritService
from services.constants import Colors as C, SPIRIT_LEVELS
from ui.styles import card_container, section_title


class XinjingPage(ft.Column):
    """心境系统页"""

    def __init__(self, page: ft.Page, spirit_service: SpiritService):
        super().__init__()
        self._page = page
        self.svc = spirit_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._current_tab = 0

    def build(self):
        status = self.svc.get_spirit_status()
        self.controls = [
            # 心境状态头部
            self._spirit_header(status),
            # Tab 切换
            self._tab_bar(),
            # 内容区
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
                # 顶行：标题 + 等级名
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
                # 大号数值
                ft.Text(
                    f"{status['value']}",
                    size=56, weight=ft.FontWeight.BOLD, color="white",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=4),
                # 进度条
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
        """Tab 切换栏"""

        tab_labels = ["正面修炼", "心魔", "统计"]
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
            content=ft.Row(tabs, alignment=ft.MainAxisAlignment.CENTER, spacing=0),
        )

    def _build_content(self) -> ft.Container:
        """根据 tab 构建内容"""
        if self._current_tab == 0:
            return self._positive_tab()
        elif self._current_tab == 1:
            return self._demon_tab()
        else:
            return self._stats_tab()

    # ─── 正面修炼 Tab ───────────────────────────────────────
    def _positive_tab(self) -> ft.Column:
        """正面修炼 Tab — 绿色边框卡片"""
        tasks = self.svc.get_positive_tasks()
        items = []
        for task in tasks:
            completed = self.svc._check_task_completed(task)
            items.append(self._task_card(task, completed))

        items.append(self._add_task_button("positive"))
        return ft.Column(items, spacing=0)

    def _task_card(self, task: dict, completed: bool = False) -> ft.Container:
        """正面任务卡片 — 绿色边框，完成打勾变灰，连续打卡🔥"""
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

        # 连续打卡信息
        streak_text = ""
        if task["enable_streak"]:
            streak = self.svc.db.get_streak(task["id"])
            if streak and streak["current_streak"] > 0:
                streak_text = f" 🔥{streak['current_streak']}天"

        # 颜色方案
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
                    ft.Text(
                        task["name"] + streak_text,
                        size=15, weight=ft.FontWeight.W_500,
                        color=text_color,
                    ),
                    ft.Text(
                        " · ".join(effect_parts),
                        size=12, color=C.SUCCESS if not completed else C.TEXT_HINT,
                    ),
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=icon,
                    icon_color=icon_color,
                    icon_size=28,
                    on_click=None if (completed and task["submission_type"] == "daily_checkin") else on_complete,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=C.TEXT_HINT,
                    icon_size=20,
                    on_click=on_delete,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=14, right=6, top=10, bottom=10),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14,
            bgcolor=bg_color,
            border=ft.Border.all(1.5, border_color),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=6,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            on_click=on_complete if not completed else None,
        )

    # ─── 心魔 Tab ───────────────────────────────────────────
    def _demon_tab(self) -> ft.Column:
        """心魔 Tab — 暗红色调"""
        tasks = self.svc.get_demon_tasks()
        items = [self._demon_card(task) for task in tasks]
        items.append(self._add_task_button("demon"))
        return ft.Column(items, spacing=0)

    def _demon_card(self, task: dict) -> ft.Container:
        """心魔任务卡片 — 暗红色调，警告感"""
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
                    ft.TextButton("删除", on_click=confirm_delete,
                                  style=ft.ButtonStyle(color=C.ERROR)),
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
                    width=44, height=44,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.12, C.ERROR),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(
                        task["name"], size=15,
                        weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        " · ".join(effect_parts),
                        size=12, color=C.ERROR,
                    ),
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.WARNING_AMBER_ROUNDED,
                    icon_color="#ff1744",
                    icon_size=28,
                    on_click=on_demon,
                    style=ft.ButtonStyle(
                        overlay_color=ft.Colors.with_opacity(0.12, C.ERROR),
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=C.TEXT_HINT,
                    icon_size=20,
                    on_click=on_delete,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(left=14, right=6, top=10, bottom=10),
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.03, C.ERROR),
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.35, C.ERROR)),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=6,
                color=ft.Colors.with_opacity(0.06, C.ERROR),
                offset=ft.Offset(0, 2),
            ),
        )

    # ─── 统计 Tab ───────────────────────────────────────────
    def _stats_tab(self) -> ft.Column:
        """统计 Tab — 手动柱状图"""
        summary = self.svc.get_today_summary()
        stats_7d = self.svc.get_statistics(7)
        stats_30d = self.svc.get_statistics(30)

        return ft.Column([
            # 今日摘要
            section_title("今日"),
            self._summary_card(summary),

            # 7日柱状图
            section_title("近7天趋势"),
            self._stats_bar_chart(7),

            # 数据卡片
            section_title("近7天"),
            self._stats_data_card(stats_7d),

            section_title("近30天"),
            self._stats_data_card(stats_30d),
        ], spacing=0)

    def _summary_card(self, summary: dict) -> ft.Container:
        """今日摘要卡片"""
        items = [
            ("✅", str(summary["positive_count"]), "正面", C.SUCCESS),
            ("👿", str(summary["demon_count"]), "心魔", C.ERROR),
            ("🧘", f"{summary['total_spirit_change']:+d}", "净心境", "#667eea"),
        ]
        return ft.Container(
            content=ft.Row(
                [self._stat_item(e, v, l, c) for e, v, l, c in items],
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

    def _stats_bar_chart(self, days: int) -> ft.Container:
        """统计柱状图 — 手动容器柱状图（替代 ft.BarChart）"""
        trend = self.svc.get_spirit_trend(days)
        if not trend:
            return ft.Container(
                content=ft.Text("暂无数据", size=13, color=C.TEXT_HINT),
                padding=20,
            )

        max_val = max(max(abs(d["change"]), 1) for d in trend)
        chart_height = 110

        def _bar(value, color, width=18):
            h = max(2, (abs(value) / max(max_val, 1)) * chart_height)
            return ft.Container(
                width=width,
                height=h,
                bgcolor=color,
                border_radius=ft.BorderRadius.only(top_left=4, top_right=4),
                tooltip=f"{value:+d}",
            )

        bar_columns = []
        for d in trend:
            change = d["change"]
            color = C.SUCCESS if change >= 0 else C.ERROR
            bar_columns.append(
                ft.Column(
                    [
                        _bar(change, color),
                        ft.Text(d["date"], size=8, color=C.TEXT_HINT,
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
            height=chart_height + 26,
            border=ft.Border.only(
                bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, ft.Colors.BLACK)),
            ),
        )

        legend = ft.Row([
            ft.Row([
                ft.Container(width=10, height=10, bgcolor=C.SUCCESS, border_radius=2),
                ft.Text("正面", size=10, color=C.TEXT_HINT),
            ], spacing=4),
            ft.Row([
                ft.Container(width=10, height=10, bgcolor=C.ERROR, border_radius=2),
                ft.Text("负面", size=10, color=C.TEXT_HINT),
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

    def _stats_data_card(self, stats: dict) -> ft.Container:
        """统计数据卡片"""
        items = [
            ("⬆️", str(stats["positive_total"]), "正面总计", C.SUCCESS),
            ("⬇️", str(stats["demon_total"]), "心魔总计", C.ERROR),
            ("📊", f"{stats['net_spirit']:+d}", "净变化", "#667eea"),
        ]
        return ft.Container(
            content=ft.Row(
                [self._stat_item(e, v, l, c) for e, v, l, c in items],
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

    # ─── 添加任务按钮 ───────────────────────────────────────
    def _add_task_button(self, task_type: str) -> ft.Container:
        """添加任务按钮"""
        is_positive = task_type == "positive"
        accent = C.SUCCESS if is_positive else C.ERROR

        def on_add(e):
            self._show_add_dialog(task_type)

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=accent, size=20),
                ft.Text(
                    "添加修炼任务" if is_positive else "添加心魔",
                    size=14, color=accent, weight=ft.FontWeight.W_500,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=14, margin=ft.Margin.symmetric(horizontal=16, vertical=8),
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.35, accent)),
            border_radius=14,
            on_click=on_add,
        )

    # ─── 添加任务对话框 — 优化布局 ──────────────────────────
    def _show_add_dialog(self, task_type: str):
        """显示添加任务对话框 — 更好的布局"""
        is_positive = task_type == "positive"
        accent = C.SUCCESS if is_positive else C.ERROR

        name_field = ft.TextField(
            label="任务名称", autofocus=True,
            border_radius=10,
            prefix_icon=ft.Icons.EDIT_NOTE,
        )
        spirit_field = ft.TextField(
            label="心境值", value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            prefix_icon=ft.Icons.SELF_IMPROVEMENT,
            width=140,
        )
        blood_field = ft.TextField(
            label="血量值", value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            prefix_icon=ft.Icons.FAVORITE,
            width=140,
        )
        streak_check = ft.Checkbox(label="连续打卡追踪 🔥", value=False)
        sub_type = ft.Dropdown(
            label="提交方式", value="daily_checkin",
            border_radius=10,
            options=[
                ft.dropdown.Option("daily_checkin", "每日打卡"),
                ft.dropdown.Option("repeatable", "可重复"),
            ],
        )

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            spirit_val = int(spirit_field.value or "1")
            blood_val = int(blood_field.value or "0")

            if is_positive:
                self.svc.create_positive_task(
                    name=name, spirit_effect=spirit_val, blood_effect=blood_val,
                    submission_type=sub_type.value, enable_streak=streak_check.value,
                )
            else:
                self.svc.create_demon_task(name=name, spirit_effect=spirit_val, blood_effect=blood_val)

            dlg.open = False

            self._page.update()
            self._refresh()

        # 构建内容
        content_controls = [
            name_field,
            ft.Container(height=4),
            ft.Row([spirit_field, blood_field], spacing=10),
        ]
        if is_positive:
            content_controls.extend([
                ft.Container(height=4),
                sub_type,
                streak_check,
            ])

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(
                    ft.Icons.ADD_TASK if is_positive else ft.Icons.WARNING_AMBER,
                    color=accent, size=24,
                ),
                ft.Text(
                    "添加修炼任务" if is_positive else "添加心魔",
                    size=18, weight=ft.FontWeight.W_600,
                ),
            ], spacing=8),
            content=ft.Column(content_controls, tight=True, spacing=8, width=300),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.Button(
                    "保存",
                    on_click=on_save,
                    bgcolor=accent,
                    color="white",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
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
        """刷新页面"""
        self.controls.clear()
        self.build()
        try:
            self.update()
        except RuntimeError:
            pass


# 给 SpiritService 加个辅助方法引用
SpiritService._check_task_completed = lambda self, task: self.db.is_task_completed_today(task["id"]) if task["submission_type"] == "daily_checkin" else False
