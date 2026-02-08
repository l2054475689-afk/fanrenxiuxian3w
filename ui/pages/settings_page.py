"""
设置页面
"""
import flet as ft
from services.constants import Colors as C
from ui.styles import card_container, section_title


class SettingsPage(ft.Column):
    """设置页"""

    def __init__(self, page: ft.Page, db_manager):
        super().__init__()
        self.page = page
        self.db = db_manager
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    def build(self):
        config = self.db.get_user_config()

        self.controls = [
            ft.Container(
                content=ft.Text("⚙️ 设置", size=20, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                padding=ft.padding.only(left=20, top=16, bottom=8),
            ),

            # 基本设置
            section_title("基本设置"),
            self._setting_item("出生年份", str(config["birth_year"]) if config else "未设置",
                               ft.Icons.CAKE, lambda e: self._edit_birth_year()),
            self._setting_item("目标灵石", f"{config['target_money']:,}" if config else "5,000,000",
                               ft.Icons.FLAG, lambda e: self._edit_target()),

            # AI 设置
            section_title("AI 接口"),
            self._setting_item("AI 提供商", self._get_ai_provider(),
                               ft.Icons.SMART_TOY, lambda e: self._edit_ai_config()),

            # 显示设置
            section_title("显示"),
            self._toggle_item("深色模式", config.get("dark_mode", False) if config else False,
                              ft.Icons.DARK_MODE, self._toggle_dark_mode),

            # 数据管理
            section_title("数据管理"),
            self._setting_item("备份数据", "导出数据库", ft.Icons.BACKUP, lambda e: self._backup()),
            self._setting_item("恢复数据", "从备份恢复", ft.Icons.RESTORE, lambda e: self._restore()),

            # 关于
            section_title("关于"),
            self._setting_item("版本", "1.0.0", ft.Icons.INFO_OUTLINE, None),
            self._setting_item("凡人修仙3w天", "个人生命管理应用", ft.Icons.FAVORITE, None),

            # 危险操作
            section_title("危险操作"),
            ft.Container(
                content=ft.TextButton(
                    "重置应用", icon=ft.Icons.DELETE_FOREVER,
                    style=ft.ButtonStyle(color=C.ERROR),
                    on_click=lambda e: self._confirm_reset(),
                ),
                padding=ft.padding.symmetric(horizontal=20),
            ),

            ft.Container(height=80),
        ]

    def _setting_item(self, title: str, subtitle: str, icon, on_click) -> ft.Container:
        """设置项"""
        return card_container(
            content=ft.Row([
                ft.Icon(icon, color=C.PRIMARY, size=22) if icon else ft.Container(width=22),
                ft.Column([
                    ft.Text(title, size=15, color=C.TEXT_PRIMARY),
                    ft.Text(subtitle, size=12, color=C.TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C.TEXT_HINT, size=20) if on_click else ft.Container(),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=on_click,
        )

    def _toggle_item(self, title: str, value: bool, icon, on_change) -> ft.Container:
        """开关设置项"""
        return card_container(
            content=ft.Row([
                ft.Icon(icon, color=C.PRIMARY, size=22),
                ft.Text(title, size=15, color=C.TEXT_PRIMARY, expand=True),
                ft.Switch(value=value, on_change=on_change, active_color=C.PRIMARY),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    def _get_ai_provider(self) -> str:
        config = self.db.get_active_ai_config()
        return config["provider"] if config else "未配置"

    def _toggle_dark_mode(self, e):
        is_dark = e.control.value
        self.page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        self.page.update()

    def _edit_birth_year(self):
        field = ft.TextField(label="出生年份", keyboard_type=ft.KeyboardType.NUMBER)

        def on_save(e):
            try:
                year = int(field.value)
                if 1900 < year < 2100:
                    self.db.init_user_config(year)
                    self.page.close(dlg)
                    self._refresh()
            except ValueError:
                pass

        dlg = ft.AlertDialog(
            title=ft.Text("设置出生年份"),
            content=field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self.page.open(dlg)

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
                    self.page.close(dlg)
                    self._refresh()
            except ValueError:
                pass

        dlg = ft.AlertDialog(
            title=ft.Text("设置目标灵石"),
            content=field,
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self.page.open(dlg)

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
            self.page.close(dlg)
            self.page.open(ft.SnackBar(ft.Text("AI 配置已保存"), bgcolor=C.SUCCESS))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("AI 接口设置"),
            content=ft.Column([provider_dd, key_field, base_field, model_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _backup(self):
        import shutil
        from utils.path_helper import get_backup_dir
        backup_dir = get_backup_dir(self.page)
        from datetime import datetime
        backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy2(self.db.db_path, str(backup_file))
            self.page.open(ft.SnackBar(ft.Text(f"备份成功: {backup_file.name}"), bgcolor=C.SUCCESS))
        except Exception as ex:
            self.page.open(ft.SnackBar(ft.Text(f"备份失败: {ex}"), bgcolor=C.ERROR))

    def _restore(self):
        self.page.open(ft.SnackBar(ft.Text("恢复功能开发中"), bgcolor=C.WARNING))

    def _confirm_reset(self):
        def on_confirm(e):
            # 危险操作：重置数据库
            from database.models import Base
            Base.metadata.drop_all(self.db.engine)
            Base.metadata.create_all(self.db.engine)
            self.page.close(dlg)
            self.page.open(ft.SnackBar(ft.Text("应用已重置"), bgcolor=C.WARNING))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("⚠️ 确认重置"),
            content=ft.Text("此操作将删除所有数据，不可恢复！"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("确认重置", on_click=on_confirm, style=ft.ButtonStyle(color=C.ERROR)),
            ],
        )
        self.page.open(dlg)

    def _refresh(self):
        self.controls.clear()
        self.build()
        self.update()
