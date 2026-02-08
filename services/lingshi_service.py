"""
灵石系统 Service 层
职责：收支记录、预算、负债、统计
"""
from datetime import date, datetime, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from services.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES, DEFAULT_TARGET_MONEY


class LingshiService:
    """灵石系统服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    # === 收支记录 ===

    def add_income(self, amount: float, category: str, description: str = None,
                   transaction_date: date = None) -> dict:
        """记录收入"""
        if amount <= 0:
            return {"success": False, "message": "金额必须大于0"}
        txn = self.db.add_transaction("income", amount, category, description, transaction_date)
        return {"success": True, "transaction": txn, "message": f"收入 +{amount:.2f} 灵石"}

    def add_expense(self, amount: float, category: str, description: str = None,
                    transaction_date: date = None) -> dict:
        """记录支出"""
        if amount <= 0:
            return {"success": False, "message": "金额必须大于0"}
        txn = self.db.add_transaction("expense", amount, category, description, transaction_date)

        # 检查预算
        warning = self._check_budget_warning(category)
        msg = f"支出 -{amount:.2f} 灵石"
        if warning:
            msg += f"\n⚠️ {warning}"

        return {"success": True, "transaction": txn, "message": msg}

    def delete_transaction(self, txn_id: int) -> dict:
        """删除收支记录"""
        with self.db.session_scope() as s:
            from database.models import Transaction
            txn = s.query(Transaction).filter(Transaction.id == txn_id).first()
            if not txn:
                return {"success": False, "message": "记录不存在"}
            s.delete(txn)
        return {"success": True, "message": "已删除"}

    # === 查询 ===

    def get_balance(self) -> dict:
        """获取灵石余额"""
        return self.db.get_balance()

    def get_transactions(self, start_date: date = None, end_date: date = None,
                         type: str = None, category: str = None,
                         limit: int = 50) -> list[dict]:
        """查询收支记录"""
        return self.db.get_transactions(start_date, end_date, type, category, limit)

    def get_today_transactions(self) -> list[dict]:
        """获取今日收支"""
        today = date.today()
        return self.db.get_transactions(start_date=today, end_date=today)

    # === 预算 ===

    def set_budget(self, category: str, amount: float, month: str = None) -> dict:
        """设置预算"""
        if not month:
            month = date.today().strftime("%Y-%m")
        if amount <= 0:
            return {"success": False, "message": "预算金额必须大于0"}
        budget = self.db.set_budget(category, amount, month)
        return {"success": True, "budget": budget}

    def get_budget_status(self, month: str = None) -> dict:
        """获取预算执行情况"""
        if not month:
            month = date.today().strftime("%Y-%m")

        budgets = self.db.get_budgets(month)
        # 获取本月支出
        year, mon = month.split("-")
        start = date(int(year), int(mon), 1)
        if int(mon) == 12:
            end = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(int(year), int(mon) + 1, 1) - timedelta(days=1)

        expenses = self.db.get_transactions(start_date=start, end_date=end, type="expense", limit=9999)

        # 按分类汇总支出
        category_spent = {}
        for e in expenses:
            cat = e["category"]
            category_spent[cat] = category_spent.get(cat, 0) + e["amount"]

        total_spent = sum(category_spent.values())

        result = {
            "month": month,
            "total_spent": total_spent,
            "categories": [],
        }

        for b in budgets:
            cat = b["category"]
            spent = category_spent.get(cat, 0)
            remaining = b["amount"] - spent
            result["categories"].append({
                "category": cat,
                "budget": b["amount"],
                "spent": spent,
                "remaining": remaining,
                "percentage": spent / b["amount"] * 100 if b["amount"] > 0 else 0,
                "over_budget": remaining < 0,
            })

        return result

    # === 负债 ===

    def create_debt(self, name: str, total_amount: float,
                    monthly_payment: float, interest_rate: float = 0) -> dict:
        """创建负债"""
        debt = self.db.create_debt(name, total_amount, monthly_payment, interest_rate)
        return {"success": True, "debt": debt}

    def repay_debt(self, debt_id: int, amount: float) -> dict:
        """还款"""
        with self.db.session_scope() as s:
            from database.models import Debt, DebtRepayment
            debt = s.query(Debt).filter(Debt.id == debt_id).first()
            if not debt:
                return {"success": False, "message": "负债不存在"}
            if not debt.is_active:
                return {"success": False, "message": "负债已结清"}

            debt.remaining_amount -= amount
            if debt.remaining_amount <= 0:
                debt.remaining_amount = 0
                debt.is_active = False

            repayment = DebtRepayment(debt_id=debt_id, amount=amount)
            s.add(repayment)
            s.flush()

            return {
                "success": True,
                "remaining": float(debt.remaining_amount),
                "is_cleared": not debt.is_active,
                "message": f"还款 {amount:.2f}，剩余 {debt.remaining_amount:.2f}",
            }

    def get_debts(self) -> list[dict]:
        """获取负债列表"""
        return self.db.get_debts()

    def get_debt_summary(self) -> dict:
        """获取负债汇总"""
        debts = self.db.get_debts()
        total_remaining = sum(d["remaining_amount"] for d in debts)
        total_monthly = sum(d["monthly_payment"] for d in debts)
        return {
            "total_debts": len(debts),
            "total_remaining": total_remaining,
            "total_monthly_payment": total_monthly,
            "debts": debts,
        }

    # === 统计 ===

    def get_monthly_summary(self, month: str = None) -> dict:
        """获取月度收支汇总"""
        if not month:
            month = date.today().strftime("%Y-%m")

        year, mon = month.split("-")
        start = date(int(year), int(mon), 1)
        if int(mon) == 12:
            end = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(int(year), int(mon) + 1, 1) - timedelta(days=1)

        txns = self.db.get_transactions(start_date=start, end_date=end, limit=9999)

        income_total = sum(t["amount"] for t in txns if t["type"] == "income")
        expense_total = sum(t["amount"] for t in txns if t["type"] == "expense")

        # 按分类汇总
        income_by_cat = {}
        expense_by_cat = {}
        for t in txns:
            if t["type"] == "income":
                income_by_cat[t["category"]] = income_by_cat.get(t["category"], 0) + t["amount"]
            else:
                expense_by_cat[t["category"]] = expense_by_cat.get(t["category"], 0) + t["amount"]

        return {
            "month": month,
            "income_total": income_total,
            "expense_total": expense_total,
            "net": income_total - expense_total,
            "income_by_category": income_by_cat,
            "expense_by_category": expense_by_cat,
        }

    def get_goal_progress(self) -> dict:
        """获取灵石目标进度"""
        config = self.db.get_user_config()
        balance = self.db.get_balance()
        target = config["target_money"] if config else DEFAULT_TARGET_MONEY
        current = balance["balance"]
        progress = current / target * 100 if target > 0 else 0

        # 里程碑
        milestones = [100_000, 500_000, 1_000_000, 2_000_000, 5_000_000]
        reached = [m for m in milestones if current >= m]
        next_milestone = next((m for m in milestones if current < m), target)

        return {
            "target": target,
            "current": current,
            "progress": min(100, progress),
            "reached_milestones": reached,
            "next_milestone": next_milestone,
            "to_next": next_milestone - current,
        }

    # === 固定收支 ===

    def create_recurring(self, type: str, amount: float, category: str,
                         description: str = None, frequency: str = "monthly",
                         day_of_month: int = 1) -> dict:
        """创建固定收支"""
        with self.db.session_scope() as s:
            from database.models import RecurringTransaction
            recurring = RecurringTransaction(
                type=type, amount=amount, category=category,
                description=description, frequency=frequency,
                day_of_month=day_of_month,
            )
            s.add(recurring)
            s.flush()
            return {
                "success": True,
                "id": recurring.id,
                "message": f"固定{'收入' if type == 'income' else '支出'} {amount:.2f}/月",
            }

    def apply_recurring_transactions(self) -> list[dict]:
        """执行到期的固定收支"""
        today = date.today()
        applied = []
        with self.db.session_scope() as s:
            from database.models import RecurringTransaction
            recurrings = s.query(RecurringTransaction).filter(
                RecurringTransaction.is_active == True
            ).all()

            for r in recurrings:
                should_apply = False
                if r.frequency == "monthly" and today.day == (r.day_of_month or 1):
                    if not r.last_applied_date or r.last_applied_date.month != today.month:
                        should_apply = True

                if should_apply:
                    r.last_applied_date = today
                    applied.append({
                        "type": r.type, "amount": float(r.amount),
                        "category": r.category, "description": r.description,
                    })

        # 在 session 外添加交易记录
        for a in applied:
            self.db.add_transaction(a["type"], a["amount"], a["category"], a["description"])

        return applied

    # === 内部方法 ===

    def _check_budget_warning(self, category: str) -> Optional[str]:
        """检查是否超预算"""
        month = date.today().strftime("%Y-%m")
        budgets = self.db.get_budgets(month)
        budget = next((b for b in budgets if b["category"] == category), None)
        if not budget:
            return None

        year, mon = month.split("-")
        start = date(int(year), int(mon), 1)
        if int(mon) == 12:
            end = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(int(year), int(mon) + 1, 1) - timedelta(days=1)

        expenses = self.db.get_transactions(start_date=start, end_date=end, type="expense", category=category, limit=9999)
        spent = sum(e["amount"] for e in expenses)

        if spent > budget["amount"]:
            return f"{category}预算已超支 {spent - budget['amount']:.2f} 灵石"
        elif spent > budget["amount"] * 0.8:
            return f"{category}预算已用 {spent / budget['amount'] * 100:.0f}%"
        return None
