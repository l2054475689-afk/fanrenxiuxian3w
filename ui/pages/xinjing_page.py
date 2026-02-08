"""
心境系统页面
"""
import flet as ft
from services.spirit_service import SpiritService
from services.constants import Colors as C, SPIRIT_LEVELS
from ui.styles import card_container, section_title


class XinjingPage(ft.Column):
    """心境系统页"""

    def __init__(self, page: ft.Page, spirit_service: SpiritService):
        super().__init__()
        self.page = page
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

    def _spirit_header(self, status: dict) -> ft.Container:
        """心境状态头部"""
        if not status:
            return ft.Container()
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🧘 心境", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text(status["level_name"], size=16, color="white70"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"{status['value']}", size=48, weight=ft.FontWeight.BOLD, color="white"),
                ft.ProgressBar(
                    value=status["progress"], height=8,
                    color="white", bgcolor="white24",
                ),
                ft.Row([
                    ft.Text(f"{status['min']}", size=11, color="white54"),
                    ft.Text(
                        f"距{status['next_level_name']}还需 {status['points_to_next']}" if status["next_level_name"] else "已达最高境界",
                        size=11, color="white70",
                    ),
                    ft.Text(f"{status['max']}", size=11, color="white54"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=6),
            padding=20,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
                colors=[C.SPIRIT_BLUE, "#00f2fe"],
            ),
        )

    def _tab_bar(self) -> ft.Container:
        """Tab 切换栏"""
        def on_tab(e):
            self._current_tab = e.control.selected_index
            self._refresh()

        return ft.Container(
            content=ft.Tabs(
                selected_index=self._current_tab,
                on_change=on_tab,
                tabs=[
                    ft.Tab(text="正面修炼"),
                    ft.Tab(text="心魔"),
                    ft.Tab(text="统计"),
                ],
                indicator_color=C.PRIMARY,
                label_color=C.PRIMARY,
                unselected_label_color=C.TEXT_HINT,
            ),
        )

    def _build_content(self) -> ft.Container:
        """根据 tab 构建内容"""
        if self._current_tab == 0:
            return self._positive_tab()
        elif self._current_tab == 1:
            return self._demon_tab()
        else:
            return self._stats_tab()

    def _positive_tab(self) -> ft.Column:
        """正面修炼 Tab"""
        tasks = self.svc.get_positive_tasks()
        items = []
        for task in tasks:
            completed = self.svc.get_spirit_status() and self.svc._check_task_completed(task)
            items.append(self._task_card(task, completed))

        items.append(self._add_task_button("positive"))
        return ft.Column(items, spacing=0)

    def _demon_tab(self) -> ft.Column:
        """心魔 Tab"""
        tasks = self.svc.get_demon_tasks()
        items = [self._demon_card(task) for task in tasks]
        items.append(self._add_task_button("demon"))
        return ft.Column(items, spacing=0)

    def _stats_tab(self) -> ft.Column:
        """统计 Tab"""
        summary = self.svc.get_today_summary()
        stats_7d = self.svc.get_statistics(7)
        stats_30d = self.svc.get_statistics(30)

        return ft.Column([
            section_title("今日"),
            card_container(ft.Row([
                self._stat_item("✅", str(summary["positive_count"]), "正面"),
                self._stat_item("👿", str(summary["demon_count"]), "心魔"),
                self._stat_item("🧘", f"{summary['total_spirit_change']:+d}", "净心境"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)),

            section_title("近7天"),
            card_container(ft.Row([
                self._stat_item("⬆️", str(stats_7d["positive_total"]), "正面总计"),
                self._stat_item("⬇️", str(stats_7d["demon_total"]), "心魔总计"),
                self._stat_item("📊", f"{stats_7d['net_spirit']:+d}", "净变化"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)),

            section_title("近30天"),
            card_container(ft.Row([
                self._stat_item("⬆️", str(stats_30d["positive_total"]), "正面总计"),
                self._stat_item("⬇️", str(stats_30d["demon_total"]), "心魔总计"),
                self._stat_item("📊", f"{stats_30d['net_spirit']:+d}", "净变化"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)),
        ], spacing=0)

    def _task_card(self, task: dict, completed: bool = False) -> ft.Container:
        """正面任务卡片"""
        def on_complete(e):
            if task["submission_type"] == "daily_checkin":
                result = self.svc.complete_daily_task(task["id"])
            else:
                result = self.svc.complete_repeatable_task(task["id"])
            if result["success"]:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS))
            else:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.WARNING))
            self._refresh()

        streak_info = ""
        if task["enable_streak"]:
            streak = self.svc.db.get_streak(task["id"])
            if streak:
                streak_info = f" 🔥{streak['current_streak']}天"

        return card_container(
            content=ft.Row([
                ft.Text(task["emoji"], size=28),
                ft.Column([
                    ft.Text(
                        task["name"] + streak_info,
                        size=15, weight=ft.FontWeight.W_500,
                        color=C.TEXT_HINT if completed else C.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        f"心境{task['spirit_effect']:+d}" +
                        (f" 血量{task['blood_effect']:+d}" if task["blood_effect"] else ""),
                        size=12, color=C.SUCCESS,
                    ),
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.CHECK_CIRCLE if completed else ft.Icons.RADIO_BUTTON_UNCHECKED,
                    icon_color=C.SUCCESS if completed else C.TEXT_HINT,
                    icon_size=28,
                    on_click=None if completed and task["submission_type"] == "daily_checkin" else on_complete,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=on_complete if not completed else None,
        )

    def _demon_card(self, task: dict) -> ft.Container:
        """心魔任务卡片"""
        today_count = self.svc.db.get_task_today_count(task["id"])

        def on_demon(e):
            result = self.svc.record_demon(task["id"])
            if result["success"]:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.ERROR))
            self._refresh()

        return card_container(
            content=ft.Row([
                ft.Text(task["emoji"], size=28),
                ft.Column([
                    ft.Text(task["name"], size=15, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Text(
                        f"心境{task['spirit_effect']:+d}" +
                        (f" 血量{task['blood_effect']:+d}" if task["blood_effect"] else "") +
                        (f" (今日{today_count}次)" if today_count > 0 else ""),
                        size=12, color=C.ERROR,
                    ),
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.WARNING_AMBER_ROUNDED,
                    icon_color=C.ERROR, icon_size=28,
                    on_click=on_demon,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    def _add_task_button(self, task_type: str) -> ft.Container:
        """添加任务按钮"""
        def on_add(e):
            self._show_add_dialog(task_type)

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=C.PRIMARY, size=20),
                ft.Text(
                    "添加修炼任务" if task_type == "positive" else "添加心魔",
                    size=14, color=C.PRIMARY,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=16, margin=ft.margin.symmetric(horizontal=16, vertical=8),
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, C.PRIMARY)),
            border_radius=12,
            on_click=on_add,
        )

    def _show_add_dialog(self, task_type: str):
        """显示添加任务对话框"""
        name_field = ft.TextField(label="任务名称", autofocus=True)
        spirit_field = ft.TextField(label="心境值", value="1", keyboard_type=ft.KeyboardType.NUMBER)
        blood_field = ft.TextField(label="血量值", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        streak_check = ft.Checkbox(label="连续打卡追踪", value=False)
        sub_type = ft.Dropdown(
            label="提交方式", value="daily_checkin",
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

            if task_type == "positive":
                self.svc.create_positive_task(
                    name=name, spirit_effect=spirit_val, blood_effect=blood_val,
                    submission_type=sub_type.value, enable_streak=streak_check.value,
                )
            else:
                self.svc.create_demon_task(name=name, spirit_effect=spirit_val, blood_effect=blood_val)

            self.page.close(dlg)
            self._refresh()

        content_controls = [name_field, spirit_field, blood_field]
        if task_type == "positive":
            content_controls.extend([sub_type, streak_check])

        dlg = ft.AlertDialog(
            title=ft.Text("添加修炼任务" if task_type == "positive" else "添加心魔"),
            content=ft.Column(content_controls, tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _check_task_completed(self, task: dict) -> bool:
        """检查任务是否已完成"""
        if task["submission_type"] == "daily_checkin":
            return self.svc.db.is_task_completed_today(task["id"])
        return False

    def _stat_item(self, emoji: str, value: str, label: str) -> ft.Column:
        return ft.Column([
            ft.Text(emoji, size=20),
            ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
            ft.Text(label, size=11, color=C.TEXT_HINT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    def _refresh(self):
        """刷新页面"""
        self.controls.clear()
        self.build()
        self.update()


# 给 SpiritService 加个辅助方法引用
SpiritService._check_task_completed = lambda self, task: self.db.is_task_completed_today(task["id"]) if task["submission_type"] == "daily_checkin" else False
