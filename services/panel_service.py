"""
个人面板 Service 层
职责：血量倒计时、仪表盘数据聚合
"""
from datetime import datetime, date, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from services.constants import (
    DEFAULT_LIFESPAN_YEARS, BLOOD_TICK_MINUTES, BLOOD_TICK_AMOUNT,
    get_spirit_level, get_spirit_progress
)


class PanelService:
    """个人面板服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_blood_status(self) -> Optional[dict]:
        """获取血量状态（实时计算）"""
        config = self.db.get_user_config()
        if not config:
            return None

        birth_year = config["birth_year"]
        initial_blood = config["initial_blood"]

        # 实时计算：从出生到现在已过去的分钟数
        now = datetime.now()
        birth_start = datetime(birth_year, 1, 1)
        total_lifespan_minutes = DEFAULT_LIFESPAN_YEARS * 365 * 24 * 60

        elapsed_minutes = int((now - birth_start).total_seconds() / 60)
        remaining_minutes = total_lifespan_minutes - elapsed_minutes

        # 加上任务带来的血量变化（current_blood - initial_blood 就是净变化）
        blood_delta = config["current_blood"] - initial_blood
        remaining_minutes += blood_delta

        remaining_minutes = max(0, remaining_minutes)

        remaining_days = remaining_minutes / (24 * 60)
        remaining_years = remaining_days / 365

        # 生命进度
        progress_used = elapsed_minutes / total_lifespan_minutes
        progress_remaining = 1 - progress_used

        return {
            "remaining_minutes": remaining_minutes,
            "remaining_days": int(remaining_days),
            "remaining_years": round(remaining_years, 1),
            "total_lifespan_minutes": total_lifespan_minutes,
            "elapsed_minutes": elapsed_minutes,
            "progress_used": min(1.0, max(0.0, progress_used)),
            "progress_remaining": max(0.0, progress_remaining),
            "blood_delta": blood_delta,
            "is_alive": remaining_minutes > 0,
        }

    def get_dashboard(self) -> Optional[dict]:
        """获取仪表盘全部数据"""
        config = self.db.get_user_config()
        if not config:
            return None

        blood = self.get_blood_status()
        spirit_value = config["current_spirit"]
        spirit_level = get_spirit_level(spirit_value)
        spirit_progress = get_spirit_progress(spirit_value)

        # 今日数据
        today_records = self.db.get_today_records()
        today_spirit = sum(r["spirit_change"] for r in today_records)
        today_blood = sum(r["blood_change"] for r in today_records)
        today_positive = sum(1 for r in today_records if r["spirit_change"] > 0)
        today_demon = sum(1 for r in today_records if r["spirit_change"] < 0)

        # 灵石余额
        balance = self.db.get_balance()

        # 境界进度
        realm = self.db.get_active_realm("main")
        realm_info = None
        if realm:
            total_subs = 0
            completed_subs = 0
            for sk in realm.get("skills", []):
                for st in sk.get("sub_tasks", []):
                    total_subs += 1
                    if st["is_completed"]:
                        completed_subs += 1
            realm_info = {
                "name": realm["name"],
                "progress": completed_subs / total_subs if total_subs > 0 else 0,
                "completed": completed_subs,
                "total": total_subs,
            }

        return {
            "blood": blood,
            "spirit": {
                "value": spirit_value,
                "level_name": spirit_level["name"],
                "level_color": spirit_level["color"],
                "progress": spirit_progress,
            },
            "today": {
                "total_tasks": len(today_records),
                "positive_count": today_positive,
                "demon_count": today_demon,
                "spirit_change": today_spirit,
                "blood_change": today_blood,
            },
            "lingshi": {
                "balance": balance["balance"],
                "income": balance["income"],
                "expense": balance["expense"],
            },
            "realm": realm_info,
        }

    def get_weekly_trend(self) -> list[dict]:
        """获取7日心境趋势"""
        end = date.today()
        start = end - timedelta(days=6)
        records = self.db.get_records_in_range(start, end)

        daily = {}
        for i in range(7):
            d = start + timedelta(days=i)
            daily[str(d)] = {"positive": 0, "demon": 0, "net": 0}

        for r in records:
            day_key = str(r["completed_at"].date()) if isinstance(r["completed_at"], datetime) else str(r["completed_at"])[:10]
            if day_key in daily:
                if r["spirit_change"] > 0:
                    daily[day_key]["positive"] += r["spirit_change"]
                else:
                    daily[day_key]["demon"] += abs(r["spirit_change"])
                daily[day_key]["net"] += r["spirit_change"]

        return [
            {"date": k[5:], "positive": v["positive"], "demon": v["demon"], "net": v["net"]}
            for k, v in sorted(daily.items())
        ]
