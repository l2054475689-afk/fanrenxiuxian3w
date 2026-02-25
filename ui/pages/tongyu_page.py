"""
统御系统页面 — 美化版 v2
"""
import flet as ft
from datetime import date
from services.tongyu_service import TongyuService
from services.constants import Colors as C, RELATIONSHIP_TYPES, PERSONALITY_DIMENSIONS, COMMUNICATION_STYLES, IMPRESSION_TAGS, EMOTION_TAGS
from ui.styles import card_container, section_title


class TongyuPage(ft.Column):
    """统御系统页"""

    def __init__(self, page: ft.Page, tongyu_service: TongyuService):
        super().__init__()
        self._page = page
        self.svc = tongyu_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._selected_person_id = None

    # ── colours ──────────────────────────────────────────
    _PURPLE_START = "#667eea"
    _PURPLE_END   = "#764ba2"
    _REL_COLORS = {
        "家人": "#e91e63",
        "朋友": "#2196f3",
        "同事": "#ff9800",
        "导师": "#9c27b0",
        "同学": "#4caf50",
        "其他": "#607d8b",
    }

    # ── build ────────────────────────────────────────────
    def build(self):
        if self._selected_person_id:
            self._build_person_detail()
        else:
            self._build_people_list()

    # ══════════════════════════════════════════════════════
    # 人物列表视图
    # ══════════════════════════════════════════════════════
    def _build_people_list(self):
        people = self.svc.get_people()
        stats = self.svc.get_relationship_stats()

        self.controls = [
            # ── 页面标题 ──
            ft.Container(
                content=ft.Row([
                    ft.Text("👥", size=24),
                    ft.Text("统御", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(f"{stats['total_people']}人", size=13, color="white", weight=ft.FontWeight.W_500),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        border_radius=12,
                        bgcolor=C.PRIMARY,
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.only(left=20, right=20, top=20, bottom=12),
            ),

            # ── 统计卡片 ──
            ft.Container(
                content=ft.Row([
                    self._stat_card("👥", str(stats["total_people"]), "总人数", "#e3f2fd"),
                    self._stat_card("💬", str(stats["monthly_interactions"]), "本月互动", "#e8f5e9"),
                    self._stat_card("🎂", str(len(self.svc.get_upcoming_birthdays())), "近期生日", "#fff3e0"),
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                padding=ft.Padding.symmetric(horizontal=12),
            ),
        ]

        # ── 生日提醒 ──
        birthdays = self.svc.get_upcoming_birthdays()
        if birthdays:
            self.controls.append(self._section_header("🎂", "即将到来的生日"))
            for b in birthdays:
                self.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(b["avatar_emoji"], size=24),
                                width=44, height=44, border_radius=22,
                                bgcolor=ft.Colors.with_opacity(0.1, "#e91e63"),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column([
                                ft.Text(b["name"], size=14, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                                ft.Text(b["birthday"], size=12, color=C.TEXT_HINT),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    f"{b['days_until']}天后" if b["days_until"] > 0 else "今天!",
                                    size=12, weight=ft.FontWeight.BOLD,
                                    color="#e91e63" if b["days_until"] <= 3 else C.WARNING,
                                ),
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                border_radius=12,
                                bgcolor=ft.Colors.with_opacity(0.1, "#e91e63"),
                            ),
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
                )

        # ── 人物列表 ──
        self.controls.append(self._section_header("📇", "人物档案"))
        for p in people:
            self.controls.append(self._person_card(p))

        # ── 添加按钮 ──
        self.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=C.PRIMARY, size=20),
                    ft.Text("添加人物", size=14, weight=ft.FontWeight.W_500, color=C.PRIMARY),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                padding=16,
                margin=ft.Margin.symmetric(horizontal=16, vertical=8),
                border=ft.Border.all(1.5, ft.Colors.with_opacity(0.35, C.PRIMARY)),
                border_radius=12,
                on_click=lambda e: self._show_add_person(),
            )
        )
        self.controls.append(ft.Container(height=80))

    # ══════════════════════════════════════════════════════
    # 人物详情视图
    # ══════════════════════════════════════════════════════
    def _build_person_detail(self):
        detail = self.svc.get_person_detail(self._selected_person_id)
        if not detail:
            self._selected_person_id = None
            self._build_people_list()
            return

        events = self.svc.get_events(self._selected_person_id)
        rel_color = self._REL_COLORS.get(detail["relationship_type"], C.PRIMARY)

        self.controls = [
            # ── 返回 + 头部 ──
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_IOS_NEW, icon_size=20,
                            icon_color=C.TEXT_PRIMARY,
                            on_click=lambda e: self._go_back(),
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE, icon_size=20,
                            icon_color=C.ERROR,
                            on_click=lambda e: self._confirm_delete_person(detail),
                        ),
                    ]),
                    # 大头像 + 名字
                    ft.Column([
                        ft.Container(
                            content=ft.Text(detail["avatar_emoji"], size=48),
                            width=80, height=80, border_radius=40,
                            bgcolor=ft.Colors.with_opacity(0.1, rel_color),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(detail["name"], size=22, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                        ft.Container(
                            content=ft.Text(
                                detail["relationship_type"], size=12,
                                weight=ft.FontWeight.W_500, color="white",
                            ),
                            padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                            border_radius=14,
                            bgcolor=rel_color,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                ]),
                padding=ft.Padding.only(left=8, right=8, top=8, bottom=16),
            ),

            # ── 基本信息 ──
            ft.Container(
                content=ft.Row([
                    self._info_chip("🎂", "生日", detail["birthday"] or "未记录"),
                    self._info_chip("🧠", "性格", detail.get("personality") or "未记录"),
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                padding=ft.Padding.symmetric(horizontal=16, vertical=4),
            ),

            # ── 性格标签 ──
            self._section_header("🧠", "性格标签"),
            self._personality_chips(detail.get("personality_tags", [])),

            # ── 相处要点 ──
            self._section_header("📝", "相处要点"),
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        detail.get("notes") or "暂无记录，点击编辑",
                        size=14,
                        color=C.TEXT_PRIMARY if detail.get("notes") else C.TEXT_HINT,
                    ),
                    ft.Container(
                        content=ft.Text("编辑", size=13, color=C.PRIMARY, weight=ft.FontWeight.W_500),
                        on_click=lambda e: self._edit_notes(detail),
                        padding=ft.Padding.only(top=8),
                    ),
                ]),
                padding=16,
                margin=ft.Margin.symmetric(horizontal=16, vertical=4),
                border_radius=12,
                bgcolor=C.CARD_LIGHT,
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=6,
                    color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2),
                ),
            ),

            # ── 事件时间线 ──
            self._section_header("📖", "互动事件"),
        ]

        if events:
            for idx, ev in enumerate(events):
                self.controls.append(self._event_timeline_item(ev, is_last=(idx == len(events) - 1)))
        else:
            self.controls.append(
                ft.Container(
                    content=ft.Text("暂无互动记录", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                    padding=20,
                    margin=ft.Margin.symmetric(horizontal=16),
                )
            )

        self.controls.append(
            ft.Container(
                content=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD, color="white", size=18),
                        ft.Text("记录新事件", size=14, weight=ft.FontWeight.W_600, color="white"),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                    padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                    border_radius=24,
                    bgcolor=C.PRIMARY,
                    on_click=lambda e: self._show_add_event(),
                    shadow=ft.BoxShadow(
                        spread_radius=0, blur_radius=8,
                        color=ft.Colors.with_opacity(0.25, C.PRIMARY),
                        offset=ft.Offset(0, 2),
                    ),
                ),
                alignment=ft.Alignment.CENTER,
                padding=16,
            )
        )
        self.controls.append(ft.Container(height=80))

    # ── 组件 ─────────────────────────────────────────────

    def _section_header(self, emoji: str, title: str) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text(emoji, size=18),
                ft.Text(title, size=18, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
            ], spacing=6),
            padding=ft.Padding.only(left=20, top=16, bottom=6),
        )

    def _stat_card(self, emoji: str, value: str, label: str, bg_color: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(emoji, size=22),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                ft.Text(label, size=11, color=C.TEXT_HINT),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border_radius=14,
            bgcolor=bg_color,
            expand=True,
        )

    def _person_card(self, person: dict) -> ft.Container:
        rel_color = self._REL_COLORS.get(person["relationship_type"], C.PRIMARY)
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(person["avatar_emoji"], size=28),
                    width=50, height=50, border_radius=25,
                    bgcolor=ft.Colors.with_opacity(0.1, rel_color),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(person["name"], size=16, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text(
                            person["relationship_type"], size=10,
                            color=rel_color, weight=ft.FontWeight.W_500,
                        ),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                        border_radius=8,
                        bgcolor=ft.Colors.with_opacity(0.1, rel_color),
                    ),
                ], spacing=4, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C.TEXT_HINT, size=20),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14,
            margin=ft.Margin.symmetric(horizontal=16, vertical=3),
            border_radius=14,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=6,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            on_click=lambda e, pid=person["id"]: self._select_person(pid),
        )

    def _info_chip(self, emoji: str, label: str, value: str) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text(emoji, size=16),
                ft.Column([
                    ft.Text(label, size=11, color=C.TEXT_HINT),
                    ft.Text(value, size=13, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                ], spacing=1),
            ], spacing=8),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=12,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=4,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 1),
            ),
        )

    def _personality_chips(self, tags: list) -> ft.Container:
        if not tags:
            return ft.Container(
                content=ft.Text("暂无标签", size=13, color=C.TEXT_HINT),
                padding=ft.Padding.symmetric(horizontal=20, vertical=8),
            )

        chips = []
        for t in tags:
            if t["category"] == "dimension":
                dim = next((d for d in PERSONALITY_DIMENSIONS if d["name"] == t["tag_name"]), None)
                if dim:
                    label = f"{dim['left']}↔{dim['right']}: {t['tag_value']}"
                    chips.append(ft.Chip(
                        label=ft.Text(label, size=11),
                        bgcolor=ft.Colors.with_opacity(0.08, C.PRIMARY),
                    ))
            elif t["category"] == "communication":
                chips.append(ft.Chip(
                    label=ft.Text(t["tag_name"], size=11),
                    bgcolor=ft.Colors.with_opacity(0.08, C.SUCCESS),
                ))
            else:
                chips.append(ft.Chip(
                    label=ft.Text(f"#{t['tag_name']}", size=11),
                    bgcolor=ft.Colors.with_opacity(0.08, C.WARNING),
                ))

        return ft.Container(
            content=ft.Row(chips, wrap=True, spacing=6, run_spacing=6),
            padding=ft.Padding.symmetric(horizontal=16, vertical=4),
        )

    def _event_timeline_item(self, event: dict, is_last: bool = False) -> ft.Container:
        tags = event.get("impression_tags", [])
        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except Exception:
                tags = []

        tag_chips = []
        for t in (tags[:4] if tags else []):
            tag_chips.append(
                ft.Container(
                    content=ft.Text(t, size=10, color=C.PRIMARY),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.08, C.PRIMARY),
                )
            )

        is_completed = event.get("is_completed", False)
        dot_color = C.SUCCESS if is_completed else C.PRIMARY

        return ft.Container(
            content=ft.Row([
                # 时间线竖线 + 圆点
                ft.Column([
                    ft.Container(
                        width=10, height=10, border_radius=5,
                        bgcolor=dot_color,
                    ),
                    ft.Container(
                        width=2, height=60,
                        bgcolor=ft.Colors.with_opacity(0.15, C.PRIMARY),
                    ) if not is_last else ft.Container(width=2),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                # 内容
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"📅 {event['event_date']}", size=12, color=C.TEXT_HINT),
                            ft.Container(
                                content=ft.Text(
                                    "✅ 已完成" if is_completed else "⏳ 进行中",
                                    size=10, color=C.SUCCESS if is_completed else C.WARNING,
                                ),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                border_radius=8,
                                bgcolor=ft.Colors.with_opacity(0.1, C.SUCCESS if is_completed else C.WARNING),
                                on_click=lambda e, eid=event["id"]: self._toggle_event_completed(eid),
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE, icon_size=14,
                                icon_color=C.TEXT_HINT,
                                on_click=lambda e, eid=event["id"]: self._confirm_delete_event(eid),
                                style=ft.ButtonStyle(padding=0),
                            ),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(
                            event["event_description"], size=14,
                            color=C.TEXT_HINT if is_completed else C.TEXT_PRIMARY,
                            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if is_completed else None,
                        ),
                        ft.Row(tag_chips, spacing=4) if tag_chips else ft.Container(),
                        ft.Text(
                            event.get("key_info") or "",
                            size=12, color=C.TEXT_SECONDARY,
                        ) if event.get("key_info") else ft.Container(),
                    ], spacing=4),
                    padding=ft.Padding.only(left=12, bottom=8),
                    expand=True,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=8),
            padding=ft.Padding.only(left=24, right=16, top=4),
        )

    # ══════════════════════════════════════════════════════
    # 操作
    # ══════════════════════════════════════════════════════

    def _select_person(self, person_id: int):
        self._selected_person_id = person_id
        self._refresh()

    def _go_back(self):
        self._selected_person_id = None
        self._refresh()

    def _show_add_person(self):
        name_field = ft.TextField(label="姓名", autofocus=True)
        type_dd = ft.Dropdown(
            label="关系类型", value=RELATIONSHIP_TYPES[0],
            options=[ft.dropdown.Option(t) for t in RELATIONSHIP_TYPES],
        )
        personality_field = ft.TextField(label="性格描述（可选）")
        birthday_field = ft.TextField(label="生日（可选，格式：2000-01-01）")

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            birthday = None
            if birthday_field.value.strip():
                try:
                    birthday = date.fromisoformat(birthday_field.value.strip())
                except ValueError:
                    pass
            result = self.svc.create_person(
                name, type_dd.value,
                birthday=birthday,
                personality=personality_field.value.strip() or None,
            )
            dlg.open = False
            self._page.update()
            if result["success"]:
                _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("添加人物"),
            content=ft.Column([name_field, type_dd, personality_field, birthday_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("添加", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_add_event(self):
        desc_field = ft.TextField(label="事件描述", autofocus=True, multiline=True)
        location_field = ft.TextField(label="地点（可选）")
        key_info_field = ft.TextField(label="关键信息（可选）", multiline=True)
        completed_cb = ft.Checkbox(label="已完成", value=False)

        def on_save(e):
            desc = desc_field.value.strip()
            if not desc:
                return
            result = self.svc.add_event(
                self._selected_person_id, date.today(), desc,
                location=location_field.value,
                key_info=key_info_field.value,
                is_completed=completed_cb.value,
            )
            dlg.open = False
            self._page.update()
            if result["success"]:
                _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS)
                _sb.open = True
                self._page.overlay.append(_sb)
                self._page.update()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("记录事件"),
            content=ft.Column([desc_field, location_field, key_info_field, completed_cb], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _edit_notes(self, detail: dict):
        notes_field = ft.TextField(
            label="相处要点", value=detail.get("notes") or "",
            multiline=True, min_lines=3, max_lines=10,
        )

        def on_save(e):
            self.svc.update_person(detail["id"], notes=notes_field.value)
            dlg.open = False
            self._page.update()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("编辑相处要点"),
            content=notes_field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _confirm_delete_person(self, detail: dict):
        def on_confirm(e):
            result = self.svc.delete_person(detail["id"])
            dlg.open = False
            self._page.update()
            color = C.WARNING if result["success"] else C.ERROR
            _sb = ft.SnackBar(ft.Text(result["message"]), bgcolor=color)
            _sb.open = True
            self._page.overlay.append(_sb)
            self._page.update()
            self._selected_person_id = None
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("确认删除"),
            content=ft.Text(f"确定要删除人物「{detail['name']}」吗？"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("删除", on_click=on_confirm, style=ft.ButtonStyle(color=C.ERROR)),
            ],
        )
        self._page.show_dialog(dlg)

    def _confirm_delete_event(self, event_id: int):
        def on_confirm(e):
            result = self.svc.delete_event(event_id)
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
            content=ft.Text("确定要删除这条互动记录吗？"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: (setattr(dlg, "open", False), self._page.update())),
                ft.TextButton("删除", on_click=on_confirm, style=ft.ButtonStyle(color=C.ERROR)),
            ],
        )
        self._page.show_dialog(dlg)

    def _toggle_event_completed(self, event_id: int):
        """切换事件完成状态"""
        self.svc.toggle_event_completed(event_id)
        self._refresh()

    def _refresh(self):
        self.controls.clear()
        self.build()
        try:
            self.update()
        except RuntimeError:
            pass
