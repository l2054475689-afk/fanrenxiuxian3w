"""
设置页面 — 美化版 v2（iOS 风格分组列表）
"""
import flet as ft
from services.constants import Colors as C
from ui.styles import section_title


class SettingsPage(ft.Column):
    """设置页"""

    def __init__(self, page: ft.Page, db_manager):
        super().__init__()
        self._page = page
        self.db = db_manager
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    def build(self):
        config = self.db.get_user_config()

        self.controls = [
            # ── 页面标题 ──
            ft.Container(
                content=ft.Row([
                    ft.Text("⚙️", size=24),
                    ft.Text("设置", size=22, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                ], spacing=8),
                padding=ft.Padding.only(left=20, top=20, bottom=16),
            ),

            # ── 基本设置 ──
            self._group_header("基本设置"),
            self._group_card([
                self._setting_row(
                    icon=ft.Icons.CAKE_OUTLINED,
                    icon_color="#e91e63",
                    icon_bg="#fce4ec",
                    title="出生年份",
                    subtitle=str(config["birth_year"]) if config else "未设置",
                    on_click=lambda e: self._edit_birth_year(),
                ),
                self._divider(),
                self._setting_row(
                    icon=ft.Icons.FLAG_OUTLINED,
                    icon_color="#ff9800",
                    icon_bg="#fff3e0",
                    title="目标灵石",
                    subtitle=f"¥{config['target_money']:,}" if config else "¥5,000,000",
                    on_click=lambda e: self._edit_target(),
                ),
            ]),

            # ── AI 设置 ──
            self._group_header("AI 接口"),
            self._group_card([
                self._setting_row(
                    icon=ft.Icons.SMART_TOY_OUTLINED,
                    icon_color="#9c27b0",
                    icon_bg="#f3e5f5",
                    title="AI 提供商",
                    subtitle=self._get_ai_provider(),
                    on_click=lambda e: self._edit_ai_config(),
                ),
            ]),

            # ── 显示设置 ──
            self._group_header("显示"),
            self._group_card([
                self._switch_row(
                    icon=ft.Icons.DARK_MODE_OUTLINED,
                    icon_color="#5c6bc0",
                    icon_bg="#e8eaf6",
                    title="深色模式",
                    subtitle="切换深色/浅色主题",
                    value=config.get("dark_mode", False) if config else False,
                    on_change=self._toggle_dark_mode,
                ),
            ]),

            # ── 数据管理 ──
            self._group_header("数据管理"),
            self._group_card([
                self._setting_row(
                    icon=ft.Icons.BACKUP_OUTLINED,
                    icon_color="#43a047",
                    icon_bg="#e8f5e9",
                    title="备份数据",
                    subtitle="导出数据库到本地",
                    on_click=lambda e: self._backup(),
                ),
                self._divider(),
                self._setting_row(
                    icon=ft.Icons.RESTORE_OUTLINED,
                    icon_color="#1e88e5",
                    icon_bg="#e3f2fd",
                    title="恢复数据",
                    subtitle="从备份文件恢复",
                    on_click=lambda e: self._restore(),
                ),
            ]),

            # ── 关于 ──
            self._group_header("关于"),
            self._group_card([
                self._setting_row(
                    icon=ft.Icons.INFO_OUTLINE,
                    icon_color="#78909c",
                    icon_bg="#eceff1",
                    title="版本",
                    subtitle="1.0.0",
                    show_arrow=False,
                ),
                self._divider(),
                self._setting_row(
                    icon=ft.Icons.FAVORITE_OUTLINE,
                    icon_color="#e91e63",
                    icon_bg="#fce4ec",
                    title="凡人修仙3w天",
                    subtitle="个人生命管理应用",
                    show_arrow=False,
                ),
            ]),

            # ── 危险操作 ──
            self._group_header("危险操作"),
            self._group_card([
                self._danger_row(
                    icon=ft.Icons.DELETE_FOREVER_OUTLINED,
                    title="重置应用",
                    subtitle="删除所有数据，不可恢复",
                    on_click=lambda e: self._confirm_reset(),
                ),
            ]),

            ft.Container(height=80),
        ]

    # ══════════════════════════════════════════════════════
    # iOS 风格组件
    # ══════════════════════════════════════════════════════

    def _group_header(self, title: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(title, size=13, color=C.TEXT_HINT, weight=ft.FontWeight.W_500),
            padding=ft.Padding.only(left=32, top=20, bottom=6),
        )

    def _group_card(self, children: list) -> ft.Container:
        return ft.Container(
            content=ft.Column(children, spacing=0),
            margin=ft.Margin.symmetric(horizontal=16),
            border_radius=14,
            bgcolor=C.CARD_LIGHT,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=8,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    def _divider(self) -> ft.Container:
        return ft.Container(
            content=ft.Divider(height=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            padding=ft.Padding.only(left=64),
        )

    def _setting_row(self, icon, icon_color: str, icon_bg: str,
                     title: str, subtitle: str,
                     on_click=None, show_arrow: bool = True) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=icon_color, size=20),
                    width=36, height=36, border_radius=10,
                    bgcolor=icon_bg,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Text(subtitle, size=12, color=C.TEXT_SECONDARY),
                ], spacing=1, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C.TEXT_HINT, size=20) if show_arrow and on_click else ft.Container(width=20),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            on_click=on_click,
        )

    def _switch_row(self, icon, icon_color: str, icon_bg: str,
                    title: str, subtitle: str,
                    value: bool, on_change) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=icon_color, size=20),
                    width=36, height=36, border_radius=10,
                    bgcolor=icon_bg,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Text(subtitle, size=12, color=C.TEXT_SECONDARY),
                ], spacing=1, expand=True),
                ft.Switch(value=value, on_change=on_change, active_color=C.PRIMARY),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        )

    def _danger_row(self, icon, title: str, subtitle: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=C.ERROR, size=20),
                    width=36, height=36, border_radius=10,
                    bgcolor="#ffebee",
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.W_500, color=C.ERROR),
                    ft.Text(subtitle, size=12, color=ft.Colors.with_opacity(0.7, C.ERROR)),
                ], spacing=1, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C.ERROR, size=20),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            on_click=on_click,
        )

    # ══════════════════════════════════════════════════════
    # 操作
    # ══════════════════════════════════════════════════════

    def _get_ai_provider(self) -> str:
        config = self.db.get_active_ai_config()
        return config["provider"] if config else "未配置"

    def _toggle_dark_mode(self, e):
        is_dark = e.control.value
        self._page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        self._page.update()

    def _edit_birth_year(self):
        field = ft.TextField(label="出生年份", keyboard_type=ft.KeyboardType.NUMBER)

        def on_save(e):
            try:
                year = int(field.value)
                if 1900 < year < 2100:
                    self.db.init_user_config(year)
                    self._page.close(dlg)
                    self._refresh()
            except ValueError:
                pass

        dlg = ft.AlertDialog(
            title=ft.Text("设置出生年份"),
            content=field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: self._page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self._page.open(dlg)

    def _edit_target(self):
        field = ft.TextField(label="目标灵石", keyboard_type=ft.KeyboardType.NUMBER)

        def on_save(e):
            try:
                target = int(field.value)
                config = self.db.get_user_config()
                if config:
                    with self.db.session_scope() as s:
                        from database.models import UserConfig
                        uc = s.query(UserConfig).first()
                        if uc:
                            uc.target_money = target
                    self._page.close(dlg)
                    self._refresh()
            except ValueError:
                pass

        dlg = ft.AlertDialog(
            title=ft.Text("设置目标灵石"),
            content=field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: self._page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self._page.open(dlg)

    def _edit_ai_config(self):
        provider_dd = ft.Dropdown(
            label="提供商", value="openai",
            options=[
                ft.dropdown.Option("openai", "OpenAI"),
                ft.dropdown.Option("qianwen", "通义千问"),
                ft.dropdown.Option("wenxin", "文心一言"),
                ft.dropdown.Option("chatglm", "ChatGLM"),
                ft.dropdown.Option("custom", "自定义"),
            ],
        )
        key_field = ft.TextField(label="API Key", password=True)
        base_field = ft.TextField(label="API 地址（可选）")
        model_field = ft.TextField(label="模型名称（可选）")

        def on_save(e):
            self.db.save_ai_config(
                provider=provider_dd.value,
                api_key=key_field.value,
                api_base=base_field.value or None,
                model=model_field.value or None,
            )
            self._page.close(dlg)
            self._page.open(ft.SnackBar(ft.Text("AI 配置已保存"), bgcolor=C.SUCCESS))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("AI 接口设置"),
            content=ft.Column([provider_dd, key_field, base_field, model_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self._page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self._page.open(dlg)

    def _backup(self):
        import shutil
        from utils.path_helper import get_backup_dir
        backup_dir = get_backup_dir(self._page)
        from datetime import datetime
        backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy2(self.db.db_path, str(backup_file))
            self._page.open(ft.SnackBar(ft.Text(f"备份成功: {backup_file.name}"), bgcolor=C.SUCCESS))
        except Exception as ex:
            self._page.open(ft.SnackBar(ft.Text(f"备份失败: {ex}"), bgcolor=C.ERROR))

    def _restore(self):
        self._page.open(ft.SnackBar(ft.Text("恢复功能开发中"), bgcolor=C.WARNING))

    def _confirm_reset(self):
        def on_confirm(e):
            from database.models import Base
            Base.metadata.drop_all(self.db.engine)
            Base.metadata.create_all(self.db.engine)
            self._page.close(dlg)
            self._page.open(ft.SnackBar(ft.Text("应用已重置"), bgcolor=C.WARNING))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("⚠️ 确认重置"),
            content=ft.Text("此操作将删除所有数据，不可恢复！"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self._page.close(dlg)),
                ft.TextButton("确认重置", on_click=on_confirm, style=ft.ButtonStyle(color=C.ERROR)),
            ],
        )
        self._page.open(dlg)

    def _refresh(self):
        self.controls.clear()
        self.build()
        self.update()
