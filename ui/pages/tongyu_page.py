"""
统御系统页面
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
        self.page = page
        self.svc = tongyu_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._selected_person_id = None

    def build(self):
        if self._selected_person_id:
            self._build_person_detail()
        else:
            self._build_people_list()

    def _build_people_list(self):
        """人物列表视图"""
        people = self.svc.get_people()
        stats = self.svc.get_relationship_stats()

        self.controls = [
            ft.Container(
                content=ft.Row([
                    ft.Text("👥 统御", size=20, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                    ft.Text(f"{stats['total_people']}人", size=14, color=C.TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(left=20, right=20, top=16, bottom=8),
            ),
            # 统计卡片
            card_container(ft.Row([
                self._stat_item("👥", str(stats["total_people"]), "总人数"),
                self._stat_item("💬", str(stats["monthly_interactions"]), "本月互动"),
                self._stat_item("⚠️", str(stats["neglected"]), "需关注"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)),
        ]

        # 生日提醒
        birthdays = self.svc.get_upcoming_birthdays()
        if birthdays:
            self.controls.append(section_title("🎂 即将到来的生日"))
            for b in birthdays:
                self.controls.append(card_container(
                    content=ft.Row([
                        ft.Text(b["avatar_emoji"], size=24),
                        ft.Column([
                            ft.Text(b["name"], size=14, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                            ft.Text(f"{b['days_until']}天后", size=12, color=C.WARNING),
                        ], spacing=2, expand=True),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ))

        # 人物列表
        self.controls.append(section_title("人物档案"))
        for p in people:
            self.controls.append(self._person_card(p))

        # 添加按钮
        self.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=C.PRIMARY, size=20),
                    ft.Text("添加人物", size=14, color=C.PRIMARY),
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=16, margin=ft.margin.symmetric(horizontal=16, vertical=8),
                border=ft.border.all(1, ft.Colors.with_opacity(0.3, C.PRIMARY)),
                border_radius=12,
                on_click=lambda e: self._show_add_person(),
            )
        )
        self.controls.append(ft.Container(height=80))

    def _build_person_detail(self):
        """人物详情视图"""
        detail = self.svc.get_person_detail(self._selected_person_id)
        if not detail:
            self._selected_person_id = None
            self._build_people_list()
            return

        events = self.svc.get_events(self._selected_person_id)

        self.controls = [
            # 返回按钮
            ft.Container(
                content=ft.Row([
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self._go_back()),
                    ft.Text(f"{detail['avatar_emoji']} {detail['name']}", size=20, weight=ft.FontWeight.BOLD),
                ]),
                padding=ft.padding.only(left=8, top=8),
            ),
            # 基本信息
            card_container(ft.Column([
                ft.Row([
                    ft.Text("关系", size=13, color=C.TEXT_HINT, width=60),
                    ft.Text(detail["relationship_type"], size=14, color=C.TEXT_PRIMARY),
                ]),
                ft.Row([
                    ft.Text("认识", size=13, color=C.TEXT_HINT, width=60),
                    ft.Text(detail["met_date"] or "未记录", size=14, color=C.TEXT_PRIMARY),
                ]),
                ft.Row([
                    ft.Text("生日", size=13, color=C.TEXT_HINT, width=60),
                    ft.Text(detail["birthday"] or "未记录", size=14, color=C.TEXT_PRIMARY),
                ]),
            ], spacing=8)),

            # 性格标签
            section_title("性格标签"),
            self._tags_card(detail.get("personality_tags", [])),

            # 相处要点
            section_title("相处要点"),
            card_container(
                content=ft.Column([
                    ft.Text(detail.get("notes") or "暂无记录，点击编辑", size=14,
                            color=C.TEXT_PRIMARY if detail.get("notes") else C.TEXT_HINT),
                    ft.TextButton("编辑", on_click=lambda e: self._edit_notes(detail)),
                ]),
            ),

            # 事件记录
            section_title("互动事件"),
        ]

        for ev in events:
            self.controls.append(self._event_card(ev))

        self.controls.append(
            ft.Container(
                content=ft.ElevatedButton("记录新事件", icon=ft.Icons.ADD, on_click=lambda e: self._show_add_event()),
                alignment=ft.alignment.center, padding=12,
            )
        )
        self.controls.append(ft.Container(height=80))

    def _person_card(self, person: dict) -> ft.Container:
        """人物卡片"""
        return card_container(
            content=ft.Row([
                ft.Text(person["avatar_emoji"], size=32),
                ft.Column([
                    ft.Text(person["name"], size=16, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Text(person["relationship_type"], size=12, color=C.TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C.TEXT_HINT),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=lambda e, pid=person["id"]: self._select_person(pid),
        )

    def _tags_card(self, tags: list) -> ft.Container:
        """性格标签卡片"""
        if not tags:
            return card_container(
                content=ft.Text("暂无标签", size=13, color=C.TEXT_HINT),
            )

        chips = []
        for t in tags:
            if t["category"] == "dimension":
                dim = next((d for d in PERSONALITY_DIMENSIONS if d["name"] == t["tag_name"]), None)
                if dim:
                    label = f"{dim['left']}↔{dim['right']}: {t['tag_value']}"
                    chips.append(ft.Chip(label=ft.Text(label, size=11), bgcolor=ft.Colors.with_opacity(0.1, C.PRIMARY)))
            elif t["category"] == "communication":
                chips.append(ft.Chip(label=ft.Text(t["tag_name"], size=11), bgcolor=ft.Colors.with_opacity(0.1, C.SUCCESS)))
            else:
                chips.append(ft.Chip(label=ft.Text(f"#{t['tag_name']}", size=11), bgcolor=ft.Colors.with_opacity(0.1, C.WARNING)))

        return card_container(
            content=ft.Row(chips, wrap=True, spacing=4, run_spacing=4),
        )

    def _event_card(self, event: dict) -> ft.Container:
        """事件卡片"""
        tags = event.get("impression_tags", [])
        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except:
                tags = []

        return card_container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"📅 {event['event_date']}", size=12, color=C.TEXT_HINT),
                    ft.Text(event.get("location") or "", size=12, color=C.TEXT_HINT),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(event["event_description"], size=14, color=C.TEXT_PRIMARY),
                ft.Row(
                    [ft.Container(
                        content=ft.Text(t, size=10, color=C.PRIMARY),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=10, bgcolor=ft.Colors.with_opacity(0.1, C.PRIMARY),
                    ) for t in (tags[:4] if tags else [])],
                    spacing=4,
                ) if tags else ft.Container(),
                ft.Text(event.get("key_info") or "", size=12, color=C.TEXT_SECONDARY) if event.get("key_info") else ft.Container(),
            ], spacing=6),
        )

    def _stat_item(self, emoji: str, value: str, label: str) -> ft.Column:
        return ft.Column([
            ft.Text(emoji, size=20),
            ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
            ft.Text(label, size=11, color=C.TEXT_HINT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    # === 操作 ===

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

        def on_save(e):
            name = name_field.value.strip()
            if not name:
                return
            result = self.svc.create_person(name, type_dd.value)
            self.page.close(dlg)
            if result["success"]:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("添加人物"),
            content=ft.Column([name_field, type_dd], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("添加", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _show_add_event(self):
        desc_field = ft.TextField(label="事件描述", autofocus=True, multiline=True)
        location_field = ft.TextField(label="地点（可选）")
        key_info_field = ft.TextField(label="关键信息（可选）", multiline=True)

        def on_save(e):
            desc = desc_field.value.strip()
            if not desc:
                return
            result = self.svc.add_event(
                self._selected_person_id, date.today(), desc,
                location=location_field.value,
                key_info=key_info_field.value,
            )
            self.page.close(dlg)
            if result["success"]:
                self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=C.SUCCESS))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("记录事件"),
            content=ft.Column([desc_field, location_field, key_info_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _edit_notes(self, detail: dict):
        notes_field = ft.TextField(
            label="相处要点", value=detail.get("notes") or "",
            multiline=True, min_lines=3, max_lines=10,
        )

        def on_save(e):
            self.svc.update_person(detail["id"], notes=notes_field.value)
            self.page.close(dlg)
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("编辑相处要点"),
            content=notes_field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _refresh(self):
        self.controls.clear()
        self.build()
        self.update()
