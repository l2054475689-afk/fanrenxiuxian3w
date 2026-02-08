"""
UI 样式常量与工具函数
凡人修仙3w天 — 修仙主题视觉系统
"""
import flet as ft
from services.constants import Colors as C


# ============ 对齐常量（Flet 0.80 兼容） ============
ALIGN_CENTER = ft.Alignment(0, 0)
ALIGN_TOP_LEFT = ft.Alignment(-1, -1)
ALIGN_TOP_CENTER = ft.Alignment(0, -1)
ALIGN_TOP_RIGHT = ft.Alignment(1, -1)
ALIGN_BOTTOM_LEFT = ft.Alignment(-1, 1)
ALIGN_BOTTOM_CENTER = ft.Alignment(0, 1)
ALIGN_BOTTOM_RIGHT = ft.Alignment(1, 1)
ALIGN_CENTER_LEFT = ft.Alignment(-1, 0)
ALIGN_CENTER_RIGHT = ft.Alignment(1, 0)


# ============ 修仙主题色 ============
class XiuxianColors:
    """修仙主题扩展色板"""
    PURPLE_DEEP = "#2d1b69"
    PURPLE_MAIN = "#667eea"
    PURPLE_LIGHT = "#a78bfa"
    GOLD_BRIGHT = "#fbbf24"
    GOLD_WARM = "#f59e0b"
    GOLD_DARK = "#b45309"
    MIST_BLUE = "#e0e7ff"
    INK_BLACK = "#1e1b4b"
    JADE_GREEN = "#34d399"
    CRIMSON = "#ef4444"
    SPIRIT_GLOW = "#c4b5fd"
    STARLIGHT = "#f5f3ff"


# ============ 渐变预设 ============
def gradient_purple_gold():
    """紫金渐变 — 修仙主题核心渐变"""
    return ft.LinearGradient(
        begin=ALIGN_TOP_LEFT,
        end=ALIGN_BOTTOM_RIGHT,
        colors=["#2d1b69", "#667eea", "#764ba2"],
    )


def gradient_night_sky():
    """夜空渐变 — 深邃背景"""
    return ft.LinearGradient(
        begin=ALIGN_TOP_CENTER,
        end=ALIGN_BOTTOM_CENTER,
        colors=["#0f0c29", "#302b63", "#24243e"],
    )


def gradient_golden_dawn():
    """金色黎明 — 突破/成就"""
    return ft.LinearGradient(
        begin=ALIGN_TOP_LEFT,
        end=ALIGN_BOTTOM_RIGHT,
        colors=["#f6d365", "#fda085"],
    )


def gradient_spirit_flow():
    """灵气流动 — 心境相关"""
    return ft.LinearGradient(
        begin=ALIGN_CENTER_LEFT,
        end=ALIGN_CENTER_RIGHT,
        colors=["#667eea", "#764ba2"],
    )


def gradient_subtle_card():
    """淡雅卡片渐变"""
    return ft.LinearGradient(
        begin=ALIGN_TOP_LEFT,
        end=ALIGN_BOTTOM_RIGHT,
        colors=["#f5f3ff", "#e0e7ff"],
    )


# ============ 阴影预设 ============
def shadow_soft(color=ft.Colors.BLACK, opacity=0.06, blur=8, y_offset=2):
    """柔和阴影"""
    return ft.BoxShadow(
        spread_radius=0,
        blur_radius=blur,
        color=ft.Colors.with_opacity(opacity, color),
        offset=ft.Offset(0, y_offset),
    )


def shadow_elevated(color=ft.Colors.BLACK, opacity=0.12, blur=16, y_offset=4):
    """悬浮阴影 — 更强调"""
    return ft.BoxShadow(
        spread_radius=0,
        blur_radius=blur,
        color=ft.Colors.with_opacity(opacity, color),
        offset=ft.Offset(0, y_offset),
    )


def shadow_glow(color="#667eea", opacity=0.3, blur=20):
    """发光阴影 — 用于高亮元素"""
    return ft.BoxShadow(
        spread_radius=2,
        blur_radius=blur,
        color=ft.Colors.with_opacity(opacity, color),
        offset=ft.Offset(0, 0),
    )


# ============ 动画预设 ============
def anim_default(duration_ms=200):
    """默认动画"""
    return ft.Animation(duration_ms, ft.AnimationCurve.EASE_IN_OUT)


def anim_spring(duration_ms=400):
    """弹性动画"""
    return ft.Animation(duration_ms, ft.AnimationCurve.EASE_OUT_BACK)


def anim_smooth(duration_ms=300):
    """平滑动画"""
    return ft.Animation(duration_ms, ft.AnimationCurve.EASE_OUT)


def anim_fade(duration_ms=500):
    """淡入淡出"""
    return ft.Animation(duration_ms, ft.AnimationCurve.EASE_IN_OUT)


# ============ 主题 ============
def get_theme(dark: bool = False) -> ft.Theme:
    """获取应用主题"""
    return ft.Theme(
        color_scheme_seed=C.PRIMARY,
        font_family="Noto Sans SC",
    )


# ============ 卡片容器 ============
def card_container(content, gradient=None, padding=16, on_click=None, margin=None,
                   border_radius=12, shadow=None):
    """统一卡片容器"""
    return ft.Container(
        content=content,
        padding=padding,
        margin=margin or ft.margin.symmetric(horizontal=16, vertical=4),
        border_radius=border_radius,
        bgcolor=C.CARD_LIGHT if not gradient else None,
        gradient=gradient,
        shadow=shadow or shadow_soft(),
        on_click=on_click,
        animate=anim_default(),
    )


def gradient_card(content, colors, padding=16, border_radius=12):
    """渐变背景卡片"""
    return card_container(
        content=content,
        gradient=ft.LinearGradient(
            begin=ALIGN_TOP_LEFT,
            end=ALIGN_BOTTOM_RIGHT,
            colors=colors,
        ),
        padding=padding,
        border_radius=border_radius,
    )


def glass_card(content, padding=16, opacity=0.85):
    """毛玻璃风格卡片"""
    return ft.Container(
        content=content,
        padding=padding,
        margin=ft.margin.symmetric(horizontal=16, vertical=4),
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(opacity, "#ffffff"),
        shadow=shadow_soft(opacity=0.08),
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#ffffff")),
        animate=anim_default(),
    )


# ============ 输入框样式 ============
def styled_textfield(label="", hint_text="", keyboard_type=None,
                     text_align=ft.TextAlign.CENTER, text_size=22,
                     width=260, color="#ffffff", label_color=None,
                     hint_color=None, border_color=None,
                     focused_border_color=None, cursor_color=None,
                     filled=False, fill_color=None):
    """修仙主题输入框"""
    return ft.TextField(
        label=label,
        hint_text=hint_text,
        keyboard_type=keyboard_type,
        text_align=text_align,
        text_size=text_size,
        width=width,
        color=color,
        label_style=ft.TextStyle(color=label_color or ft.Colors.with_opacity(0.8, "#ffffff")),
        hint_style=ft.TextStyle(color=hint_color or ft.Colors.with_opacity(0.4, "#ffffff")),
        border_color=border_color or ft.Colors.with_opacity(0.3, "#ffffff"),
        focused_border_color=focused_border_color or XiuxianColors.GOLD_BRIGHT,
        cursor_color=cursor_color or XiuxianColors.GOLD_BRIGHT,
        border_radius=12,
        filled=filled,
        fill_color=fill_color,
    )


# ============ 按钮样式 ============
def primary_button(text, on_click=None, width=220, height=50, icon=None):
    """主要操作按钮 — 金色修仙风"""
    return ft.Container(
        content=ft.Row(
            [
                *([] if not icon else [ft.Icon(icon, color="#2d1b69", size=20)]),
                ft.Text(
                    text,
                    size=17,
                    weight=ft.FontWeight.W_700,
                    color="#2d1b69",
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        width=width,
        height=height,
        border_radius=25,
        gradient=ft.LinearGradient(
            begin=ALIGN_CENTER_LEFT,
            end=ALIGN_CENTER_RIGHT,
            colors=[XiuxianColors.GOLD_BRIGHT, XiuxianColors.GOLD_WARM],
        ),
        shadow=shadow_glow(color=XiuxianColors.GOLD_BRIGHT, opacity=0.4, blur=16),
        alignment=ALIGN_CENTER,
        on_click=on_click,
        animate=anim_default(),
        animate_scale=anim_spring(),
    )


# ============ 区块标题 ============
def section_title(text: str):
    """区块标题"""
    return ft.Container(
        content=ft.Text(text, size=16, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
        padding=ft.padding.only(left=20, top=12, bottom=4),
    )


# ============ 装饰元素 ============
def decorative_circle(size=120, color="#ffffff", opacity=0.05, top=None, left=None,
                      right=None, bottom=None):
    """装饰性圆形 — 用于背景点缀"""
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=ft.Colors.with_opacity(opacity, color),
        top=top,
        left=left,
        right=right,
        bottom=bottom,
    )


def star_particle(size=4, color="#fbbf24", opacity=0.6, top=None, left=None):
    """星光粒子 — 小装饰点"""
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        bgcolor=ft.Colors.with_opacity(opacity, color),
        top=top,
        left=left,
    )
