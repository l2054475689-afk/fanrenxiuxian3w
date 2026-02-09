"""
境界系统页面 — 美化版 v2
"""
import flet as ft
from services.realm_service import RealmService
from services.constants import Colors as C
from ui.styles import card_container, gradient_card, section_title


class JingjiePage(ft.Column):
    """境界系统页"""

    def __init__(self, page: ft.Page, realm_service: RealmService):
        super().__init__()
        self._page = page
        self.svc = realm_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._expanded_skills: set = set()  # 展开的技能 id

    # ── colours ──────────────────────────────────────────
    _GOLD_START = "#f6d365"
    _GOLD_END   = "#fda085"
    _DUNGEON_START = "#a18cd1"
    _DUNGEON_END   = "#fbc2eb"

    # ── build ────────────────────────────────────────────
    def build(self):
        main_realm = self.svc.get_active_main_realm()
        dungeon = self.svc.get_active_dungeon()

        self.controls = [
            # ── 页面标题 ──
            ft.Container(
                content=ft.Row([
                    ft.Text("🏔️", size=24),
                    ft.Text("境界", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                ], spacing=8),
                padding=ft.Padding.only(left=20, top=20, bottom=12),
            ),
        ]

        # ── 主境界 ──
        if main_realm:
            self.controls.append(self._realm_hero_card(main_realm))
            self.controls.append(self._realm_skill_tree(main_realm))
        else:
            self.controls.append(self._empty_realm("主境界"))

        # ── 副本 ──
        self.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("🗺️", size=18),
                    ft.Text("副本", size=18, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                ], spacing=6),
                padding=ft.Padding.only(left=20, top=20, bottom=6),
            )
        )
        if dungeon:
            self.controls.append(self._dungeon_hero_card(dungeon))
            self.controls.append(self._realm_skill_tree(dungeon, is_dungeon=True))
        else:
            self.controls.append(self._create_realm_button("dungeon"))

        # ── 已完成 ──
        completed = self.svc.get_completed_realms()
        if completed:
            self.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("🏆", size=18),
                        ft.Text("已完成", size=18, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                    ], spacing=6),
                    padding=ft.Padding.only(left=20, top=20, bottom=6),
                )
            )
            for r in completed:
                self.controls.append(self._completed_realm_card(r))

        self.controls.append(ft.Container(height=80))

    # ── 主境界英雄卡 ─────────────────────────────────────
    def _realm_hero_card(self, realm: dict) -> ft.Container:
        progress = self.svc.get_realm_progress(realm["id"])
        pct = progress["overall_progress"]

        return ft.Container(
            content=ft.Column([
                # 顶部：图标 + 名称 + 百分比
                ft.Row([
                    ft.Container(
                        content=ft.Text("🏔️", size=32),
                        width=56, height=56,
                        border_radius=28,
                        bgcolor=ft.Colors.with_opacity(0.2, "white"),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column([
                        ft.Text(realm["name"], size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(
                            f"{progress['completed_sub_tasks']}/{progress['total_sub_tasks']} 任务完成",
                            size=13, color="white70",
                        ),
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Text(f"{pct:.0f}%", size=22, weight=ft.FontWeight.BOLD, color="white"),
                        padding=ft.Padding.all(8),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                # 进度条
                ft.Container(
                    content=ft.ProgressBar(
                        value=pct / 100, height=8,
                        color="white",
                        bgcolor=ft.Colors.with_opacity(0.25, "white"),
                    ),
                    border_radius=4,
                ),
            ], spacing=12),
            padding=20,
            margin=ft.Margin.symmetric(horizontal=16, vertical=6),
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[C.PRIMARY, C.PRIMARY_DARK],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=16,
                color=ft.Colors.with_opacity(0.25, C.PRIMARY),
                offset=ft.Offset(0, 4),
            ),
        )

    # ── 副本英雄卡 ───────────────────────────────────────
    def _dungeon_hero_card(self, realm: dict) -> ft.Container:
        progress = self.svc.get_realm_progress(realm["id"])
        pct = progress["overall_progress"]

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text("🗺️", size=28),
                        width=50, height=50,
                        border_radius=25,
                        bgcolor=ft.Colors.with_opacity(0.2, "white"),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column([
                        ft.Text(realm["name"], size=18, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(
                            f"{progress['completed_sub_tasks']}/{progress['total_sub_tasks']} 任务",
                            size=12, color="white70",
                        ),
                    ], spacing=2, expand=True),
                    ft.Text(f"{pct:.0f}%", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE, icon_size=20,
                        icon_color=ft.Colors.with_opacity(0.7, "white"),
                        on_click=lambda e, rid=realm["id"], rname=realm["name"]: self._confirm_delete_realm(rid, rname),
                        style=ft.ButtonStyle(padding=0),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(
                    content=ft.ProgressBar(
                        value=pct / 100, height=6,
                        color="white",
                        bgcolor=ft.Colors.with_opacity(0.25, "white"),
                    ),
                    border_radius=3,
                ),
            ], spacing=10),
            padding=18,
            margin=ft.Margin.symmetric(horizontal=16, vertical=6),
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[self._DUNGEON_START, self._DUNGEON_END],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=12,
                color=ft.Colors.with_opacity(0.18, self._DUNGEON_START),
                offset=ft.Offset(0, 4),
            ),
        )

    # ── 技能树 ───────────────────────────────────────────
    def _realm_skill_tree(self, realm: dict, is_dungeon: bool = False) -> ft.Column:
        progress = self.svc.get_realm_progress(realm["id"])
        items = []

        for skill in progress.get("skills", []):
            items.append(self._skill_card(skill, realm["id"], is_dungeon))

        # 添加技能按钮
        items.append(self._add_skill_button(realm["id"]))

        # 晋升按钮
        if progress["overall_progress"] >= realm.get("completion_rate", 100):
            items.append(self._advance_button(realm["id"]))

        return ft.Column(items, spacing=0)

    # ── 技能卡片（可折叠） ───────────────────────────────
    def _skill_card(self, skill: dict, realm_id: int, is_dungeon: bool = False) -> ft.Container:
        sub_tasks = skill.get("sub_tasks", [])
        completed = skill["completed"]
        total = skill["total"]
        is_expanded = skill["id"] in self._expanded_skills
        accent = self._DUNGEON_START if is_dungeon else C.PRIMARY

        # ── 子任务列表 ──
        sub_items = []
        if is_expanded:
            for st in sub_tasks:
                def make_toggle(st_id=st["id"], is_done=st["is_completed"]):
                    def toggle(e):
                        if is_done:
                            self.svc.uncomplete_sub_task(st_id)
                        else:
                            result = self.svc.complete_sub_task(st_id)
                            if result.get("realm_ready_to_advance"):
                                _sb = ft.SnackBar(ft.Text("🎉 所有任务完成！可以晋升了"), bgcolor=C.SUCCESS)
                                _sb.open = True
                                self._page.overlay.append(_sb)
                                self._page.update()
                        self._refresh()
                    return toggle

                sub_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Checkbox(
                                value=st["is_completed"],
                                on_change=make_toggle(),
                                fill_color={
                                    ft.ControlState.SELECTED: C.SUCCESS,
                                },
                            ),
                            ft.Text(
                                st["name"], size=14,
                                color=C.TEXT_HINT if st["is_completed"] else C.TEXT_PRIMARY,
                                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if st["is_completed"] else None,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE, icon_size=16, icon_color=C.TEXT_HINT,
                                on_click=lambda e, sid=st["id"]: self._delete_sub_task(sid),
                                style=ft.ButtonStyle(padding=0),
                            ),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.Padding.only(left=8),
                    )
                )

            # 添加子任务按钮
            sub_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=16, color=accent),
                        ft.Text("添加子任务", size=13, color=accent),
                    ], spacing=6),
                    on_click=lambda e, sid=skill["id"]: self._show_add_sub_task(sid),
                    padding=ft.Padding.only(left=16, top=6, bottom=4),
                )
            )

        # ── 技能头部 ──
        def toggle_expand(e, sid=skill["id"]):
            if sid in self._expanded_skills:
                self._expanded_skills.discard(sid)
            else:
                self._expanded_skills.add(sid)
            self._refresh()

        header = ft.Row([
            ft.Container(
                content=ft.Icon(
                    ft.Icons.CHECK_CIRCLE_ROUNDED if skill["is_completed"] else ft.Icons.RADIO_BUTTON_UNCHECKED,
                    color=C.SUCCESS if skill["is_completed"] else accent,
                    size=24,
                ),
                on_click=toggle_expand,
            ),
            ft.GestureDetector(
                content=ft.Column([
                    ft.Text(
                        skill["name"], size=15, weight=ft.FontWeight.W_600,
                        color=C.TEXT_HINT if skill["is_completed"] else C.TEXT_PRIMARY,
                    ),
                    ft.Container(
                        content=ft.ProgressBar(
                            value=skill["progress"], height=4,
                            color=C.SUCCESS if skill["is_completed"] else accent,
                            bgcolor=ft.Colors.with_opacity(0.12, accent),
                        ),
                        border_radius=2,
                        padding=ft.Padding.only(top=4),
                    ),
                ], spacing=0, expand=True),
                on_tap=toggle_expand,
            ),
            ft.Text(f"{completed}/{total}", size=12, color=C.TEXT_SECONDARY),
            ft.Icon(
                ft.Icons.EXPAND_MORE if not is_expanded else ft.Icons.EXPAND_LESS,
                color=C.TEXT_HINT, size=20,
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=C.TEXT_HINT,
                on_click=lambda e, sid=skill["id"]: self._delete_skill(sid),
                style=ft.ButtonStyle(padding=0),
            ),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)

        return ft.Container(
            content=ft.Column([header] + sub_items, spacing=2),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            margin=ft.Margin.symmetric(horizontal=16, vertical=3),
            border_radius=12,
            bgcolor=C.CARD_LIGHT,
            border=ft.Border.only(
                left=ft.BorderSide(3, C.SUCCESS if skill["is_completed"] else accent),
            ),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=6,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    # ── 空境界 ───────────────────────────────────────────
    def _empty_realm(self, label: str) -> ft.Container:
        realm_type = "main" if label == "主境界" else "dungeon"
        return ft.Container(
            content=ft.Column([
                ft.Text("🏔️", size=48),
                ft.Container(height=4),
                ft.Text(f"暂无{label}", size=16, weight=ft.FontWeight.W_500, color=C.TEXT_SECONDARY),
                ft.Text("开启你的修仙之路", size=13, color=C.TEXT_HINT),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Text(f"创建{label}", size=15, weight=ft.FontWeight.W_600, color="white"),
                    padding=ft.Padding.symmetric(horizontal=28, vertical=12),
                    border_radius=24,
                    gradient=ft.LinearGradient(
                        colors=[C.PRIMARY, C.PRIMARY_DARK],
                    ),
                    on_click=lambda e: self._show_create_realm(realm_type),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=32,
            margin=ft.Margin.symmetric(horizontal=16, vertical=8),
            border_radius=16,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=8,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    # ── 创建副本按钮 ─────────────────────────────────────
    def _create_realm_button(self, realm_type: str) -> ft.Container:
        label = "创建副本" if realm_type == "dungeon" else "创建境界"
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=self._DUNGEON_START, size=20),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color=self._DUNGEON_START),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=16,
            margin=ft.Margin.symmetric(horizontal=16, vertical=6),
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.4, self._DUNGEON_START)),
            border_radius=12,
            on_click=lambda e: self._show_create_realm(realm_type),
        )

    # ── 添加技能按钮 ─────────────────────────────────────
    def _add_skill_button(self, realm_id: int) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, color=C.PRIMARY, size=18),
                ft.Text("添加技能（大任务）", size=13, color=C.PRIMARY, weight=ft.FontWeight.W_500),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            padding=12,
            margin=ft.Margin.symmetric(horizontal=16, vertical=4),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, C.PRIMARY)),
            border_radius=10,
            on_click=lambda e: self._show_add_skill(realm_id),
        )

    # ── 晋升按钮（金色渐变） ─────────────────────────────
    def _advance_button(self, realm_id: int) -> ft.Container:
        def on_advance(e):
            result = self.svc.advance_realm(realm_id)
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

        return ft.Container(
            content=ft.Container(
                content=ft.Row([
                    ft.Text("🎉", size=22),
                    ft.Text("境界晋升", size=18, weight=ft.FontWeight.BOLD, color="#5d4037"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                padding=ft.Padding.symmetric(horizontal=32, vertical=14),
                border_radius=28,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.CENTER_LEFT,
                    end=ft.Alignment.CENTER_RIGHT,
                    colors=[self._GOLD_START, self._GOLD_END],
                ),
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=16,
                    color=ft.Colors.with_opacity(0.35, self._GOLD_START),
                    offset=ft.Offset(0, 4),
                ),
                on_click=on_advance,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=16),
        )

    # ── 已完成境界卡片 ───────────────────────────────────
    def _completed_realm_card(self, realm: dict) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("✅", size=18),
                    width=40, height=40,
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.1, C.SUCCESS),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(realm["name"], size=15, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Text(
                        f"完成于 {str(realm['completed_at'])[:10]}",
                        size=12, color=C.TEXT_HINT,
                    ),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.EMOJI_EVENTS, color="#ffd54f", size=22),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14,
            margin=ft.Margin.symmetric(horizontal=16, vertical=3),
            border_radius=12,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=6,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    # ══════════════════════════════════════════════════════
    # 对话框
    # ══════════════════════════════════════════════════════

    def _show_create_realm(self, realm_type: str):
        name_field = ft.TextField(label="境界名称", autofocus=True)
        desc_field = ft.TextField(label="描述（可选）", multiline=True)

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            result = self.svc.create_realm(name, desc_field.value, realm_type=realm_type)
            dlg.open = False
            self._page.update()
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

        dlg = ft.AlertDialog(
            title=ft.Text("创建境界"),
            content=ft.Column([name_field, desc_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("创建", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_add_skill(self, realm_id: int):
        name_field = ft.TextField(label="技能名称", autofocus=True)

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            self.svc.add_skill(realm_id, name)
            dlg.open = False
            self._page.update()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("添加技能"),
            content=name_field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("添加", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_add_sub_task(self, skill_id: int):
        name_field = ft.TextField(label="子任务名称", autofocus=True)

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            self.svc.add_sub_task(skill_id, name)
            dlg.open = False
            self._page.update()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("添加子任务"),
            content=name_field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("添加", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _delete_skill(self, skill_id: int):
        self.svc.delete_skill(skill_id)
        self._refresh()

    def _delete_sub_task(self, sub_task_id: int):
        self.svc.delete_sub_task(sub_task_id)
        self._refresh()

    def _confirm_delete_realm(self, realm_id: int, realm_name: str):
        def on_confirm(e):
            result = self.svc.delete_realm(realm_id)
            dlg.open = False
            self._page.update()
            color = C.WARNING if result["success"] else C.ERROR
            _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=color)
            _sb.open = True
            self._page.overlay.append(_sb)
            self._page.update()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("确认删除"),
            content=ft.Text(f"确定要删除副本「{realm_name}」及其所有技能和子任务吗？此操作不可恢复。"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("删除", on_click=on_confirm, style=ft.ButtonStyle(color=C.ERROR)),
            ],
        )
        self._page.show_dialog(dlg)

    def _refresh(self):
        self.controls.clear()
        self.build()
        try:
            self.update()
        except RuntimeError:
            pass
