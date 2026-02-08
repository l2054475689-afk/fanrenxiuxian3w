"""
境界系统页面
"""
import flet as ft
from services.realm_service import RealmService
from services.constants import Colors as C
from ui.styles import card_container, section_title


class JingjiePage(ft.Column):
    """境界系统页"""

    def __init__(self, page: ft.Page, realm_service: RealmService):
        super().__init__()
        self.page = page
        self.svc = realm_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    def build(self):
        main_realm = self.svc.get_active_main_realm()
        dungeon = self.svc.get_active_dungeon()

        self.controls = [
            ft.Container(
                content=ft.Text("⚔️ 境界", size=20, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                padding=ft.padding.only(left=20, top=16, bottom=8),
            ),
        ]

        if main_realm:
            self.controls.append(self._realm_detail(main_realm, "主境界"))
        else:
            self.controls.append(self._empty_realm("主境界"))

        # 副本
        section_title_ctrl = section_title("副本")
        self.controls.append(section_title_ctrl)
        if dungeon:
            self.controls.append(self._realm_detail(dungeon, "副本"))
        else:
            self.controls.append(self._create_realm_button("dungeon"))

        # 已完成境界
        completed = self.svc.get_completed_realms()
        if completed:
            self.controls.append(section_title("已完成"))
            for r in completed:
                self.controls.append(self._completed_realm_card(r))

        self.controls.append(ft.Container(height=80))

    def _realm_detail(self, realm: dict, label: str) -> ft.Column:
        """境界详情（含技能树）"""
        progress = self.svc.get_realm_progress(realm["id"])
        items = []

        # 头部
        items.append(card_container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"🏔️ {realm['name']}", size=18, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                    ft.Text(f"{progress['overall_progress']:.0f}%", size=16, weight=ft.FontWeight.BOLD, color=C.PRIMARY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(
                    value=progress["overall_progress"] / 100, height=6,
                    color=C.PRIMARY, bgcolor=ft.Colors.with_opacity(0.15, C.PRIMARY),
                ),
                ft.Text(
                    f"{progress['completed_sub_tasks']}/{progress['total_sub_tasks']} 任务完成",
                    size=12, color=C.TEXT_SECONDARY,
                ),
            ], spacing=8),
        ))

        # 技能树
        for skill in progress.get("skills", []):
            items.append(self._skill_card(skill, realm["id"]))

        # 添加技能按钮
        items.append(self._add_skill_button(realm["id"]))

        # 晋升按钮
        if progress["overall_progress"] >= realm.get("completion_rate", 100):
            items.append(self._advance_button(realm["id"]))

        return ft.Column(items, spacing=0)

    def _skill_card(self, skill: dict, realm_id: int) -> ft.Container:
        """技能（大任务）卡片"""
        sub_tasks = skill.get("sub_tasks", [])
        completed = skill["completed"]
        total = skill["total"]

        sub_items = []
        for st in sub_tasks:
            def make_toggle(st_id=st["id"], is_done=st["is_completed"]):
                def toggle(e):
                    if is_done:
                        self.svc.uncomplete_sub_task(st_id)
                    else:
                        result = self.svc.complete_sub_task(st_id)
                        if result.get("realm_ready_to_advance"):
                            self.page.open(ft.SnackBar(
                                ft.Text("🎉 所有任务完成！可以晋升了"), bgcolor=C.SUCCESS,
                            ))
                    self._refresh()
                return toggle

            sub_items.append(
                ft.Row([
                    ft.Checkbox(
                        value=st["is_completed"],
                        on_change=make_toggle(),
                        fill_color=C.SUCCESS if st["is_completed"] else None,
                    ),
                    ft.Text(
                        st["name"], size=14,
                        color=C.TEXT_HINT if st["is_completed"] else C.TEXT_PRIMARY,
                        text_decoration=ft.TextDecoration.LINE_THROUGH if st["is_completed"] else None,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=C.TEXT_HINT,
                        on_click=lambda e, sid=st["id"]: self._delete_sub_task(sid),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        # 添加子任务
        sub_items.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, size=16, color=C.PRIMARY),
                    ft.Text("添加子任务", size=13, color=C.PRIMARY),
                ]),
                on_click=lambda e, sid=skill["id"]: self._show_add_sub_task(sid),
                padding=ft.padding.only(left=48, top=4, bottom=4),
            )
        )

        return card_container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if skill["is_completed"] else ft.Icons.CIRCLE_OUTLINED,
                        color=C.SUCCESS if skill["is_completed"] else C.TEXT_HINT, size=22,
                    ),
                    ft.Text(
                        skill["name"], size=16, weight=ft.FontWeight.W_600,
                        color=C.TEXT_HINT if skill["is_completed"] else C.TEXT_PRIMARY,
                        expand=True,
                    ),
                    ft.Text(f"{completed}/{total}", size=13, color=C.TEXT_SECONDARY),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=C.TEXT_HINT,
                        on_click=lambda e, sid=skill["id"]: self._delete_skill(sid),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.ProgressBar(
                    value=skill["progress"], height=4,
                    color=C.SUCCESS, bgcolor=ft.Colors.with_opacity(0.1, C.SUCCESS),
                ),
                ft.Column(sub_items, spacing=0),
            ], spacing=6),
        )

    def _empty_realm(self, label: str) -> ft.Container:
        """空境界提示"""
        realm_type = "main" if label == "主境界" else "dungeon"
        return card_container(
            content=ft.Column([
                ft.Text(f"暂无{label}", size=16, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                ft.Text("点击下方创建", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.ElevatedButton(
                    f"创建{label}",
                    icon=ft.Icons.ADD,
                    on_click=lambda e: self._show_create_realm(realm_type),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        )

    def _create_realm_button(self, realm_type: str) -> ft.Container:
        """创建境界按钮"""
        label = "创建副本" if realm_type == "dungeon" else "创建境界"
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=C.PRIMARY, size=20),
                ft.Text(label, size=14, color=C.PRIMARY),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=16, margin=ft.margin.symmetric(horizontal=16, vertical=8),
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, C.PRIMARY)),
            border_radius=12,
            on_click=lambda e: self._show_create_realm(realm_type),
        )

    def _add_skill_button(self, realm_id: int) -> ft.Container:
        """添加技能按钮"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, color=C.PRIMARY, size=18),
                ft.Text("添加技能（大任务）", size=13, color=C.PRIMARY),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=12, margin=ft.margin.symmetric(horizontal=16, vertical=4),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, C.PRIMARY)),
            border_radius=8,
            on_click=lambda e: self._show_add_skill(realm_id),
        )

    def _advance_button(self, realm_id: int) -> ft.Container:
        """晋升按钮"""
        def on_advance(e):
            result = self.svc.advance_realm(realm_id)
            if result["success"]:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS))
            else:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.WARNING))
            self._refresh()

        return ft.Container(
            content=ft.ElevatedButton(
                "🎉 境界晋升",
                bgcolor=C.PRIMARY, color="white",
                on_click=on_advance,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=12),
        )

    def _completed_realm_card(self, realm: dict) -> ft.Container:
        """已完成境界卡片"""
        return card_container(
            content=ft.Row([
                ft.Text("✅", size=20),
                ft.Column([
                    ft.Text(realm["name"], size=15, color=C.TEXT_SECONDARY),
                    ft.Text(f"完成于 {str(realm['completed_at'])[:10]}", size=12, color=C.TEXT_HINT),
                ], spacing=2, expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    # === 对话框 ===

    def _show_create_realm(self, realm_type: str):
        name_field = ft.TextField(label="境界名称", autofocus=True)
        desc_field = ft.TextField(label="描述（可选）", multiline=True)

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            result = self.svc.create_realm(name, desc_field.value, realm_type=realm_type)
            self.page.close(dlg)
            if result["success"]:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS))
            else:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.WARNING))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("创建境界"),
            content=ft.Column([name_field, desc_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("创建", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _show_add_skill(self, realm_id: int):
        name_field = ft.TextField(label="技能名称", autofocus=True)

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            self.svc.add_skill(realm_id, name)
            self.page.close(dlg)
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("添加技能"),
            content=name_field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("添加", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _show_add_sub_task(self, skill_id: int):
        name_field = ft.TextField(label="子任务名称", autofocus=True)

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            self.svc.add_sub_task(skill_id, name)
            self.page.close(dlg)
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("添加子任务"),
            content=name_field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("添加", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _delete_skill(self, skill_id: int):
        self.svc.delete_skill(skill_id)
        self._refresh()

    def _delete_sub_task(self, sub_task_id: int):
        self.svc.delete_sub_task(sub_task_id)
        self._refresh()

    def _refresh(self):
        self.controls.clear()
        self.build()
        self.update()
