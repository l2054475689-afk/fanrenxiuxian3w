"""
灵石系统页面
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
        self.page = page
        self.svc = lingshi_service
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    def build(self):
        balance = self.svc.get_balance()
        goal = self.svc.get_goal_progress()

        self.controls = [
            # 余额卡片
            self._balance_card(balance),
            # 目标进度
            self._goal_card(goal),
            # 快捷操作
            self._quick_actions(),
            # 今日收支
            section_title("今日收支"),
            self._today_list(),
            # 预算
            section_title("本月预算"),
            self._budget_card(),
            # 负债
            section_title("负债"),
            self._debt_card(),
            ft.Container(height=80),
        ]

    def _balance_card(self, balance: dict) -> ft.Container:
        """余额卡片"""
        return gradient_card(
            content=ft.Column([
                ft.Text("💰 灵石余额", size=14, color="white70"),
                ft.Text(f"{balance['balance']:,.2f}", size=36, weight=ft.FontWeight.BOLD, color="white"),
                ft.Row([
                    ft.Column([
                        ft.Text("收入", size=11, color="white54"),
                        ft.Text(f"+{balance['income']:,.2f}", size=14, color="#a5d6a7"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(width=1, height=30, bgcolor="white24"),
                    ft.Column([
                        ft.Text("支出", size=11, color="white54"),
                        ft.Text(f"-{balance['expense']:,.2f}", size=14, color="#ef9a9a"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ], spacing=8),
            colors=[C.MONEY_GOLD, "#fda085"],
        )

    def _goal_card(self, goal: dict) -> ft.Container:
        """目标进度"""
        return card_container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🎯 灵石目标", size=14, color=C.TEXT_SECONDARY),
                    ft.Text(f"{goal['progress']:.1f}%", size=14, weight=ft.FontWeight.BOLD, color=C.PRIMARY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(
                    value=goal["progress"] / 100, height=6,
                    color=C.MONEY_GOLD, bgcolor=ft.Colors.with_opacity(0.15, C.MONEY_GOLD),
                ),
                ft.Text(
                    f"距下一里程碑 {goal['next_milestone']:,.0f} 还需 {goal['to_next']:,.0f}",
                    size=12, color=C.TEXT_HINT,
                ),
            ], spacing=6),
        )

    def _quick_actions(self) -> ft.Container:
        """快捷操作按钮"""
        return ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "记收入", icon=ft.Icons.ADD, color=C.SUCCESS,
                    on_click=lambda e: self._show_add_dialog("income"),
                ),
                ft.ElevatedButton(
                    "记支出", icon=ft.Icons.REMOVE, color=C.ERROR,
                    on_click=lambda e: self._show_add_dialog("expense"),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            padding=ft.padding.symmetric(vertical=8),
        )

    def _today_list(self) -> ft.Column:
        """今日收支列表"""
        txns = self.svc.get_today_transactions()
        if not txns:
            return ft.Container(
                content=ft.Text("今日暂无收支记录", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                padding=16, margin=ft.margin.symmetric(horizontal=16),
            )

        items = []
        for t in txns:
            is_income = t["type"] == "income"
            items.append(card_container(
                content=ft.Row([
                    ft.Text("💵" if is_income else "💸", size=20),
                    ft.Column([
                        ft.Text(t["description"] or t["category"], size=14, color=C.TEXT_PRIMARY),
                        ft.Text(t["category"], size=11, color=C.TEXT_HINT),
                    ], spacing=2, expand=True),
                    ft.Text(
                        f"{'+'if is_income else '-'}{t['amount']:,.2f}",
                        size=16, weight=ft.FontWeight.BOLD,
                        color=C.SUCCESS if is_income else C.ERROR,
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ))
        return ft.Column(items, spacing=0)

    def _budget_card(self) -> ft.Container:
        """预算执行情况"""
        status = self.svc.get_budget_status()
        if not status["categories"]:
            return ft.Container(
                content=ft.Column([
                    ft.Text("暂未设置预算", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                    ft.TextButton("设置预算", on_click=lambda e: self._show_budget_dialog()),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=16, margin=ft.margin.symmetric(horizontal=16),
            )

        items = []
        for cat in status["categories"]:
            color = C.ERROR if cat["over_budget"] else (C.WARNING if cat["percentage"] > 80 else C.SUCCESS)
            items.append(ft.Column([
                ft.Row([
                    ft.Text(cat["category"], size=13, color=C.TEXT_PRIMARY),
                    ft.Text(f"{cat['spent']:,.0f}/{cat['budget']:,.0f}", size=12, color=C.TEXT_SECONDARY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(
                    value=min(1, cat["percentage"] / 100), height=4,
                    color=color, bgcolor=ft.Colors.with_opacity(0.1, color),
                ),
            ], spacing=4))

        return card_container(content=ft.Column(items, spacing=8))

    def _debt_card(self) -> ft.Container:
        """负债概览"""
        summary = self.svc.get_debt_summary()
        if summary["total_debts"] == 0:
            return ft.Container(
                content=ft.Text("无负债 🎉", size=13, color=C.TEXT_HINT, text_align=ft.TextAlign.CENTER),
                padding=16, margin=ft.margin.symmetric(horizontal=16),
            )

        items = []
        for d in summary["debts"]:
            progress = 1 - (d["remaining_amount"] / d["total_amount"]) if d["total_amount"] > 0 else 0
            items.append(ft.Column([
                ft.Row([
                    ft.Text(d["name"], size=14, color=C.TEXT_PRIMARY),
                    ft.Text(f"剩余 {d['remaining_amount']:,.0f}", size=12, color=C.ERROR),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=progress, height=4, color=C.PRIMARY, bgcolor=ft.Colors.with_opacity(0.1, C.PRIMARY)),
                ft.Text(f"月供 {d['monthly_payment']:,.0f}", size=11, color=C.TEXT_HINT),
            ], spacing=4))

        return card_container(content=ft.Column(items, spacing=12))

    # === 对话框 ===

    def _show_add_dialog(self, txn_type: str):
        """添加收支对话框"""
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
            self.page.close(dlg)
            color = C.SUCCESS if result["success"] else C.WARNING
            self.page.open(ft.SnackBar(ft.Text(result["message"]), bgcolor=color))
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("记收入" if txn_type == "income" else "记支出"),
            content=ft.Column([amount_field, category_dd, desc_field], tight=True, spacing=8),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("保存", on_click=on_save),
            ],
        )
        self.page.open(dlg)

    def _show_budget_dialog(self):
        """设置预算对话框"""
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
            self.page.close(dlg)
            self._refresh()

        dlg = ft.AlertDialog(
            title=ft.Text("设置预算"),
            content=ft.Column([category_dd, amount_field], tight=True, spacing=8),
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
