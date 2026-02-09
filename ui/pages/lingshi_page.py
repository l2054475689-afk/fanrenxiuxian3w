"""
灵石系统页面 — 美化版 v2
"""
import flet as ft
from datetime import date
from services.lingshi_service import LingshiService
from services.constants import Colors as C, EXPENSE_CATEGORIES, INCOME_CATEGORIES
from ui.styles import card_container, gradient_card, section_title


class LingshiPage(ft.Column):
    """灵石系统页"""

    def __init__(self, page: ft.Page, lingshi_service: LingshiService):
        super().__init__()
        self._page = page
        self.svc = lingshi_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    # ── colours ──────────────────────────────────────────
    _GOLD_START = "#f6d365"
    _GOLD_END   = "#fda085"
    _DEBT_START = "#ff6b6b"
    _DEBT_END   = "#ee5a24"

    # ── build ────────────────────────────────────────────
    def build(self):
        balance = self.svc.get_balance()
        goal = self.svc.get_goal_progress()

        self.controls = [
            # 余额英雄卡
            self._balance_hero(balance),
            # 目标进度（含里程碑）
            self._goal_progress_card(goal),
            # 快捷操作
            self._quick_actions(),
            # 今日收支
            self._section_header("📋", "今日收支"),
            self._today_list(),
            # 预算
            self._section_header("📊", "本月预算"),
            self._budget_card(),
            # 负债
            self._section_header("💳", "负债"),
            self._debt_section(),
            ft.Container(height=80),
        ]

    # ── 区块标题 ─────────────────────────────────────────
    def _section_header(self, emoji: str, title: str) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text(emoji, size=18),
                ft.Text(title, size=18, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
            ], spacing=6),
            padding=ft.Padding.only(left=20, top=20, bottom=6),
        )

    # ── 余额英雄卡 ──────────────────────────────────────
    def _balance_hero(self, balance: dict) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text("💰 灵石余额", size=13, color="white70"),
                ft.Text(
                    f"¥{balance['balance']:,.2f}",
                    size=38, weight=ft.FontWeight.BOLD, color="white",
                    text_align=ft.TextAlign.LEFT,
                ),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        # 收入
                        ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text("↑", size=14, weight=ft.FontWeight.BOLD, color="#66bb6a"),
                                    width=24, height=24, border_radius=12,
                                    bgcolor=ft.Colors.with_opacity(0.2, "white"),
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Text("收入", size=12, color="white70"),
                            ], spacing=6),
                            ft.Text(f"+{balance['income']:,.2f}", size=16, weight=ft.FontWeight.W_600, color="#a5d6a7"),
                        ], spacing=4),
                        # 分隔线
                        ft.Container(width=1, height=40, bgcolor="white24"),
                        # 支出
                        ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text("↓", size=14, weight=ft.FontWeight.BOLD, color="#ef5350"),
                                    width=24, height=24, border_radius=12,
                                    bgcolor=ft.Colors.with_opacity(0.2, "white"),
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Text("支出", size=12, color="white70"),
                            ], spacing=6),
                            ft.Text(f"-{balance['expense']:,.2f}", size=16, weight=ft.FontWeight.W_600, color="#ef9a9a"),
                        ], spacing=4),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    padding=ft.Padding.symmetric(vertical=8),
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.12, "white"),
                ),
            ], spacing=4),
            padding=24,
            margin=ft.Margin.symmetric(horizontal=16, vertical=8),
            border_radius=20,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[self._GOLD_START, self._GOLD_END],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=20,
                color=ft.Colors.with_opacity(0.3, self._GOLD_START),
                offset=ft.Offset(0, 6),
            ),
        )

    # ── 目标进度（含里程碑） ─────────────────────────────
    def _goal_progress_card(self, goal: dict) -> ft.Container:
        pct = goal["progress"]
        milestones = [100_000, 500_000, 1_000_000, 2_000_000, 5_000_000]
        target = goal["target"]

        # 里程碑标记
        milestone_markers = []
        for m in milestones:
            if m <= target:
                pos = m / target if target > 0 else 0
                reached = goal["current"] >= m
                milestone_markers.append(
                    ft.Container(
                        content=ft.Text(
                            self._format_amount_short(m),
                            size=9, color=C.SUCCESS if reached else C.TEXT_HINT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        left=pos * 280 if pos * 280 < 260 else 260,
                        top=0,
                    )
                )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🎯 灵石目标", size=14, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text(f"{pct:.1f}%", size=13, weight=ft.FontWeight.BOLD, color="white"),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                        border_radius=12,
                        bgcolor=C.PRIMARY,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                # 进度条
                ft.Container(
                    content=ft.ProgressBar(
                        value=pct / 100, height=10,
                        color=self._GOLD_START,
                        bgcolor=ft.Colors.with_opacity(0.12, self._GOLD_START),
                    ),
                    border_radius=5,
                ),
                # 里程碑行
                ft.Stack(milestone_markers, height=16) if milestone_markers else ft.Container(),
                ft.Row([
                    ft.Text(f"当前 ¥{goal['current']:,.0f}", size=12, color=C.TEXT_SECONDARY),
                    ft.Text(f"目标 ¥{target:,.0f}", size=12, color=C.TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(
                    f"距下一里程碑还需 ¥{goal['to_next']:,.0f}",
                    size=12, color=C.TEXT_HINT,
                ),
            ], spacing=8),
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

    # ── 快捷操作 ─────────────────────────────────────────
    def _quick_actions(self) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD_CIRCLE, color="white", size=20),
                        ft.Text("记收入", size=14, weight=ft.FontWeight.W_600, color="white"),
                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                    border_radius=24,
                    bgcolor=C.SUCCESS,
                    on_click=lambda e: self._show_add_dialog("income"),
                    expand=True,
                    shadow=ft.BoxShadow(
                        spread_radius=0, blur_radius=8,
                        color=ft.Colors.with_opacity(0.25, C.SUCCESS),
                        offset=ft.Offset(0, 2),
                    ),
                ),
                ft.Container(width=12),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.REMOVE_CIRCLE, color="white", size=20),
                        ft.Text("记支出", size=14, weight=ft.FontWeight.W_600, color="white"),
                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                    border_radius=24,
                    bgcolor=C.ERROR,
                    on_click=lambda e: self._show_add_dialog("expense"),
                    expand=True,
                    shadow=ft.BoxShadow(
                        spread_radius=0, blur_radius=8,
                        color=ft.Colors.with_opacity(0.25, C.ERROR),
                        offset=ft.Offset(0, 2),
                    ),
                ),
            ]),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        )

    # ── 今日收支列表 ─────────────────────────────────────
    def _today_list(self) -> ft.Column:
        txns = self.svc.get_today_transactions()
        if not txns:
            return ft.Container(
                content=ft.Column([
                    ft.Text("📝", size=32),
                    ft.Text("今日暂无收支记录", size=14, color=C.TEXT_HINT),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                padding=24,
                margin=ft.Margin.symmetric(horizontal=16),
                alignment=ft.Alignment.CENTER,
            )

        items = []
        for t in txns:
            is_income = t["type"] == "income"
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text("↑" if is_income else "↓", size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=C.SUCCESS if is_income else C.ERROR),
                            width=36, height=36, border_radius=18,
                            bgcolor=ft.Colors.with_opacity(0.1, C.SUCCESS if is_income else C.ERROR),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column([
                            ft.Text(
                                t["description"] or t["category"],
                                size=14, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY,
                            ),
                            ft.Text(t["category"], size=11, color=C.TEXT_HINT),
                        ], spacing=2, expand=True),
                        ft.Text(
                            f"{'+'if is_income else '-'}¥{t['amount']:,.2f}",
                            size=16, weight=ft.FontWeight.BOLD,
                            color=C.SUCCESS if is_income else C.ERROR,
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                    margin=ft.Margin.symmetric(horizontal=16, vertical=2),
                    border_radius=12,
                    bgcolor=C.CARD_LIGHT,
                    shadow=ft.BoxShadow(
                        spread_radius=0, blur_radius=4,
                        color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                        offset=ft.Offset(0, 1),
                    ),
                )
            )
        return ft.Column(items, spacing=0)

    # ── 预算卡片 ─────────────────────────────────────────
    def _budget_card(self) -> ft.Container:
        status = self.svc.get_budget_status()
        if not status["categories"]:
            return ft.Container(
                content=ft.Column([
                    ft.Text("📊", size=32),
                    ft.Text("暂未设置预算", size=14, color=C.TEXT_HINT),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text("设置预算", size=13, weight=ft.FontWeight.W_500, color=C.PRIMARY),
                        padding=ft.Padding.symmetric(horizontal=20, vertical=8),
                        border_radius=20,
                        border=ft.Border.all(1, C.PRIMARY),
                        on_click=lambda e: self._show_budget_dialog(),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                padding=24,
                margin=ft.Margin.symmetric(horizontal=16),
                alignment=ft.Alignment.CENTER,
            )

        items = []
        for cat in status["categories"]:
            over = cat["over_budget"]
            pct = cat["percentage"]
            if over:
                color = C.ERROR
                status_text = "超支!"
            elif pct > 80:
                color = C.WARNING
                status_text = "注意"
            else:
                color = C.SUCCESS
                status_text = "正常"

            items.append(ft.Column([
                ft.Row([
                    ft.Text(cat["category"], size=14, weight=ft.FontWeight.W_500, color=C.TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text(status_text, size=10, color="white", weight=ft.FontWeight.BOLD),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                        border_radius=8,
                        bgcolor=color,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=ft.ProgressBar(
                        value=min(1, pct / 100), height=8,
                        color=color,
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                    ),
                    border_radius=4,
                ),
                ft.Row([
                    ft.Text(f"已用 ¥{cat['spent']:,.0f}", size=11, color=C.TEXT_SECONDARY),
                    ft.Text(f"预算 ¥{cat['budget']:,.0f}", size=11, color=C.TEXT_HINT),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=4))

        return ft.Container(
            content=ft.Column(items, spacing=14),
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

    # ── 负债区域 ─────────────────────────────────────────
    def _debt_section(self) -> ft.Column:
        summary = self.svc.get_debt_summary()
        if summary["total_debts"] == 0:
            return ft.Container(
                content=ft.Column([
                    ft.Text("🎉", size=32),
                    ft.Text("无负债，自由自在！", size=14, color=C.TEXT_HINT),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                padding=24,
                margin=ft.Margin.symmetric(horizontal=16),
                alignment=ft.Alignment.CENTER,
            )

        items = []
        for d in summary["debts"]:
            total = d["total_amount"]
            remaining = d["remaining_amount"]
            paid = total - remaining
            progress = paid / total if total > 0 else 0

            items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text("💳", size=18),
                                width=40, height=40, border_radius=20,
                                bgcolor=ft.Colors.with_opacity(0.1, C.ERROR),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column([
                                ft.Text(d["name"], size=15, weight=ft.FontWeight.W_600, color=C.TEXT_PRIMARY),
                                ft.Text(f"月供 ¥{d['monthly_payment']:,.0f}", size=12, color=C.TEXT_HINT),
                            ], spacing=2, expand=True),
                            ft.Column([
                                ft.Text(f"¥{remaining:,.0f}", size=16, weight=ft.FontWeight.BOLD, color=C.ERROR),
                                ft.Text("剩余", size=10, color=C.TEXT_HINT),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(height=4),
                        ft.Row([
                            ft.Text(f"已还 {progress*100:.0f}%", size=11, color=C.TEXT_SECONDARY),
                            ft.Text(f"¥{paid:,.0f} / ¥{total:,.0f}", size=11, color=C.TEXT_HINT),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(
                            content=ft.ProgressBar(
                                value=progress, height=6,
                                color=C.PRIMARY,
                                bgcolor=ft.Colors.with_opacity(0.1, C.PRIMARY),
                            ),
                            border_radius=3,
                        ),
                    ], spacing=6),
                    padding=16,
                    margin=ft.Margin.symmetric(horizontal=16, vertical=4),
                    border_radius=14,
                    bgcolor=C.CARD_LIGHT,
                    border=ft.Border.only(
                        left=ft.BorderSide(3, C.ERROR),
                    ),
                    shadow=ft.BoxShadow(
                        spread_radius=0, blur_radius=8,
                        color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                        offset=ft.Offset(0, 2),
                    ),
                )
            )

        # 汇总
        items.insert(0,
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("总负债", size=12, color=C.TEXT_HINT),
                        ft.Text(f"¥{summary['total_remaining']:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=C.ERROR),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Container(width=1, height=40, bgcolor=ft.Colors.with_opacity(0.1, C.TEXT_HINT)),
                    ft.Column([
                        ft.Text("月供合计", size=12, color=C.TEXT_HINT),
                        ft.Text(f"¥{summary['total_monthly_payment']:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=C.TEXT_PRIMARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ]),
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
        )

        return ft.Column(items, spacing=0)

    # ── 工具方法 ─────────────────────────────────────────
    @staticmethod
    def _format_amount_short(amount: float) -> str:
        if amount >= 1_000_000:
            return f"{amount/1_000_000:.0f}M"
        if amount >= 1_000:
            return f"{amount/1_000:.0f}K"
        return f"{amount:.0f}"

    # ══════════════════════════════════════════════════════
    # 对话框
    # ══════════════════════════════════════════════════════

    def _show_add_dialog(self, txn_type: str):
        categories = INCOME_CATEGORIES if txn_type == "income" else EXPENSE_CATEGORIES
        amount_field = ft.TextField(label="金额", autofocus=True, keyboard_type=ft.KeyboardType.NUMBER)
        category_dd = ft.Dropdown(
            label="分类", value=categories[0],
            options=[ft.dropdown.Option(c) for c in categories],
        )
        desc_field = ft.TextField(label="备注（可选）")

        def on_save(e):
            try:
                amount = float(amount_field.value)
            except (ValueError, TypeError):
                return
            if txn_type == "income":
                result = self.svc.add_income(amount, category_dd.value, desc_field.value)
            else:
                result = self.svc.add_expense(amount, category_dd.value, desc_field.value)
            self._page.close(dlg)
            color = C.SUCCESS if result["success"] else C.WARNING
            _sb = ft.SnackBar(ft.SnackBar(ft.Text(result["message"]), bgcolor=color))
            _sb.open = True
            self._page.overlay.append(_sb)
            self._page.update()
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("记收入" if txn_type == "income" else "记支出"),
            content=ft.Column([amount_field, category_dd, desc_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self._page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_budget_dialog(self):
        category_dd = ft.Dropdown(
            label="分类", value=EXPENSE_CATEGORIES[0],
            options=[ft.dropdown.Option(c) for c in EXPENSE_CATEGORIES],
        )
        amount_field = ft.TextField(label="预算金额", keyboard_type=ft.KeyboardType.NUMBER)

        def on_save(e):
            try:
                amount = float(amount_field.value)
            except (ValueError, TypeError):
                return
            self.svc.set_budget(category_dd.value, amount)
            self._page.close(dlg)
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("设置预算"),
            content=ft.Column([category_dd, amount_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self._page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
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
