"""
心境系统 Service 层
职责：正面任务/心魔任务的业务逻辑
"""
from datetime import datetime, date, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from services.constants import (
    SPIRIT_MIN, SPIRIT_MAX, SPIRIT_LEVELS,
    get_spirit_level, get_spirit_progress, clamp_spirit
)


class SpiritService:
    """心境系统服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.kline_svc = None  # 由 main.py 注入 KlineService 引用

    def _notify_kline(self, old_spirit: int, new_spirit: int):
        """通知K线服务心境值变动"""
        if self.kline_svc and old_spirit != new_spirit:
            self.kline_svc.on_spirit_change(old_spirit, new_spirit)

    # === 任务管理 ===

    def get_positive_tasks(self) -> list[dict]:
        """获取正面修炼任务"""
        return self.db.get_tasks_by_type("positive")

    def get_demon_tasks(self) -> list[dict]:
        """获取心魔任务"""
        return self.db.get_tasks_by_type("demon")

    def create_positive_task(self, name: str, spirit_effect: int,
                             blood_effect: int = 0, emoji: str = "⭐",
                             submission_type: str = "daily_checkin",
                             enable_streak: bool = False) -> dict:
        """创建正面任务"""
        if spirit_effect < 0:
            raise ValueError("正面任务心境值不能为负")
        return self.db.create_task(
            name=name, task_type="positive",
            spirit_effect=spirit_effect, blood_effect=blood_effect,
            emoji=emoji, submission_type=submission_type,
            enable_streak=enable_streak,
        )

    def create_demon_task(self, name: str, spirit_effect: int,
                          blood_effect: int = 0, emoji: str = "👿") -> dict:
        """创建心魔任务（强制负值、repeatable）"""
        return self.db.create_task(
            name=name, task_type="demon",
            spirit_effect=-abs(spirit_effect),
            blood_effect=-abs(blood_effect) if blood_effect != 0 else 0,
            emoji=emoji, submission_type="repeatable",
            enable_streak=False,
        )

    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        return self.db.delete_task(task_id)

    def reorder_tasks(self, task_ids: list[int]) -> None:
        """重新排序"""
        self.db.reorder_tasks(task_ids)

    # === 任务完成 ===

    def complete_daily_task(self, task_id: int) -> dict:
        """完成每日打卡任务（每天只能一次）"""
        task = self.db.get_task(task_id)
        if not task:
            return {"success": False, "message": "任务不存在"}
        if task["submission_type"] != "daily_checkin":
            return {"success": False, "message": "非每日打卡任务"}
        if self.db.is_task_completed_today(task_id):
            return {"success": False, "message": "今日已完成该任务"}

        # 记录变动前的心境值
        config = self.db.get_user_config()
        old_spirit = config["current_spirit"] if config else 0

        record = self.db.add_task_record(
            task_id=task_id, task_name=task["name"],
            spirit_change=task["spirit_effect"], blood_change=task["blood_effect"],
        )

        # 通知K线服务
        self._notify_kline(old_spirit, record["new_spirit"])

        # 更新连续打卡
        streak = None
        if task["enable_streak"]:
            streak = self.db.update_streak(task_id)

        return {
            "success": True,
            "record": record,
            "streak": streak,
            "message": f"完成「{task['name']}」心境{task['spirit_effect']:+d}",
        }

    def complete_repeatable_task(self, task_id: int) -> dict:
        """完成可重复任务"""
        task = self.db.get_task(task_id)
        if not task:
            return {"success": False, "message": "任务不存在"}

        # 记录变动前的心境值
        config = self.db.get_user_config()
        old_spirit = config["current_spirit"] if config else 0

        record = self.db.add_task_record(
            task_id=task_id, task_name=task["name"],
            spirit_change=task["spirit_effect"], blood_change=task["blood_effect"],
        )

        # 通知K线服务
        self._notify_kline(old_spirit, record["new_spirit"])

        return {
            "success": True,
            "record": record,
            "message": f"完成「{task['name']}」心境{task['spirit_effect']:+d}",
        }

    def record_demon(self, task_id: int) -> dict:
        """记录心魔事件（不可撤销）"""
        task = self.db.get_task(task_id)
        if not task:
            return {"success": False, "message": "任务不存在"}
        if task["task_type"] != "demon":
            return {"success": False, "message": "非心魔任务"}

        # 记录变动前的心境值
        config = self.db.get_user_config()
        old_spirit = config["current_spirit"] if config else 0

        record = self.db.add_task_record(
            task_id=task_id, task_name=task["name"],
            spirit_change=task["spirit_effect"], blood_change=task["blood_effect"],
        )

        # 通知K线服务
        self._notify_kline(old_spirit, record["new_spirit"])

        return {
            "success": True,
            "record": record,
            "message": f"心魔「{task['name']}」心境{task['spirit_effect']:+d}",
        }

    def undo_task(self, record_id: int) -> dict:
        """撤销任务（仅限当天的非心魔任务）"""
        result = self.db.undo_task_record(record_id)
        if not result:
            return {"success": False, "message": "无法撤销（非当天或已撤销）"}
        return {"success": True, "result": result, "message": "已撤销"}

    # === 状态查询 ===

    def get_spirit_status(self) -> Optional[dict]:
        """获取当前心境状态"""
        config = self.db.get_user_config()
        if not config:
            return None
        value = config["current_spirit"]
        level = get_spirit_level(value)
        progress = get_spirit_progress(value)
        # 找下一级
        idx = SPIRIT_LEVELS.index(level)
        next_level = SPIRIT_LEVELS[idx + 1] if idx < len(SPIRIT_LEVELS) - 1 else None

        return {
            "value": value,
            "level_name": level["name"],
            "level_color": level["color"],
            "progress": progress,
            "next_level_name": next_level["name"] if next_level else None,
            "points_to_next": next_level["min"] - value if next_level else 0,
            "min": SPIRIT_MIN,
            "max": SPIRIT_MAX,
        }

    def get_today_summary(self) -> dict:
        """获取今日心境摘要"""
        records = self.db.get_today_records()
        positive_count = sum(1 for r in records if r["spirit_change"] > 0)
        demon_count = sum(1 for r in records if r["spirit_change"] < 0)
        total_spirit = sum(r["spirit_change"] for r in records)
        total_blood = sum(r["blood_change"] for r in records)

        return {
            "positive_count": positive_count,
            "demon_count": demon_count,
            "total_spirit_change": total_spirit,
            "total_blood_change": total_blood,
            "total_records": len(records),
            "records": records,
        }

    def get_statistics(self, days: int = 7) -> dict:
        """获取统计数据"""
        end = date.today()
        start = end - timedelta(days=days)
        records = self.db.get_records_in_range(start, end)

        positive_total = sum(r["spirit_change"] for r in records if r["spirit_change"] > 0)
        demon_total = sum(abs(r["spirit_change"]) for r in records if r["spirit_change"] < 0)
        positive_count = sum(1 for r in records if r["spirit_change"] > 0)
        demon_count = sum(1 for r in records if r["spirit_change"] < 0)

        return {
            "days": days,
            "positive_total": positive_total,
            "demon_total": demon_total,
            "positive_count": positive_count,
            "demon_count": demon_count,
            "net_spirit": positive_total - demon_total,
        }

    def get_spirit_trend(self, days: int = 30) -> list[dict]:
        """获取心境变化趋势（每日净变化）"""
        end = date.today()
        start = end - timedelta(days=days - 1)
        records = self.db.get_records_in_range(start, end)

        # 按日期分组
        daily = {}
        for i in range(days):
            d = start + timedelta(days=i)
            daily[str(d)] = 0

        for r in records:
            day_key = str(r["completed_at"].date()) if isinstance(r["completed_at"], datetime) else str(r["completed_at"])[:10]
            if day_key in daily:
                daily[day_key] += r["spirit_change"]

        # 计算累计值（从当前值反推）
        config = self.db.get_user_config()
        current = config["current_spirit"] if config else 0

        trend = []
        sorted_days = sorted(daily.keys())
        # 从最后一天反推
        cumulative = current
        values = []
        for d in reversed(sorted_days):
            values.append((d, cumulative))
            cumulative -= daily[d]
        values.reverse()

        for d, v in values:
            trend.append({
                "date": d[5:],  # MM-DD
                "value": v,
                "change": daily[d],
            })

        return trend
