"""
K线人生图 Service 层
职责：自动从心境系统生成K线数据（开盘/收盘/最高/最低）
"""
from datetime import date, timedelta
from typing import Optional

from database.db_manager import DatabaseManager


class KlineService:
    """K线人生图服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def on_spirit_change(self, old_spirit: int, new_spirit: int) -> None:
        """心境值变动时调用，自动更新今日K线数据

        Args:
            old_spirit: 变动前的心境值
            new_spirit: 变动后的心境值
        """
        today = date.today()
        existing = self.db.get_daily_score(today)

        if not existing:
            # 今天第一次变动：open=变动前的值, close=变动后的值
            self.db.upsert_daily_score(
                today,
                open_spirit=old_spirit,
                close_spirit=new_spirit,
                high_spirit=max(old_spirit, new_spirit),
                low_spirit=min(old_spirit, new_spirit),
                change_count=1,
            )
        else:
            # 已有记录：更新 close, high, low, change_count
            self.db.upsert_daily_score(
                today,
                close_spirit=new_spirit,
                high_spirit=max(existing["high_spirit"], new_spirit),
                low_spirit=min(existing["low_spirit"], new_spirit),
                change_count=existing["change_count"] + 1,
            )

    def init_today(self, current_spirit: int) -> None:
        """初始化今天的开盘价（如果还没有记录）

        Args:
            current_spirit: 当前心境值
        """
        today = date.today()
        existing = self.db.get_daily_score(today)
        if not existing:
            self.db.upsert_daily_score(
                today,
                open_spirit=current_spirit,
                close_spirit=current_spirit,
                high_spirit=current_spirit,
                low_spirit=current_spirit,
                change_count=0,
            )

    def get_today_score(self) -> Optional[dict]:
        """获取今天的评分"""
        return self.db.get_daily_score(date.today())

    def get_scores(self, days: int = 30) -> list[dict]:
        """获取最近N天的评分列表"""
        end = date.today()
        start = end - timedelta(days=days - 1)
        return self.db.get_daily_scores(start, end)

    def get_weekly_avg(self) -> list[dict]:
        """计算7日均线数据，返回最近30天每天的7日均值"""
        scores = self.get_scores(days=37)  # 多取7天用于计算
        # 构建日期->收盘价映射
        score_map = {}
        for s in scores:
            close = s.get("close_spirit")
            if close is not None:
                score_map[s["score_date"]] = close

        result = []
        end = date.today()
        for i in range(30):
            d = end - timedelta(days=29 - i)
            vals = []
            for j in range(7):
                dd = d - timedelta(days=j)
                if dd in score_map:
                    vals.append(score_map[dd])
            avg = sum(vals) / len(vals) if vals else None
            result.append({"date": d, "avg": round(avg, 1) if avg is not None else None})
        return result

    def delete_score(self, score_id: int) -> bool:
        """删除评分"""
        return self.db.delete_daily_score(score_id)
