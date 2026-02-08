"""
UI 样式常量
"""
import flet as ft
from services.constants import Colors as C


# 主题
def get_theme(dark: bool = False) -> ft.Theme:
    """获取应用主题"""
    return ft.Theme(
        color_scheme_seed=C.PRIMARY,
        font_family="Noto Sans SC",
    )


# 卡片样式
def card_container(content, gradient=None, padding=16, on_click=None, margin=None):
    """统一卡片容器"""
    return ft.Container(
        content=content,
        padding=padding,
        margin=margin or ft.margin.symmetric(horizontal=16, vertical=4),
        border_radius=12,
        bgcolor=C.CARD_LIGHT if not gradient else None,
        gradient=gradient,
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=8,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        on_click=on_click,
        animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )


def gradient_card(content, colors, padding=16):
    """渐变背景卡片"""
    return card_container(
        content=content,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=colors,
        ),
        padding=padding,
    )


def section_title(text: str):
    """区块标题"""
    return ft.Container(
        content=ft.Text(text, size=16, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
        padding=ft.padding.only(left=20, top=12, bottom=4),
    )
