"""
K线人生图 Service 层
职责：每日心情评分的业务逻辑，K线数据管理
"""
import json
from datetime import date, timedelta
from typing import Optional

from database.db_manager import DatabaseManager


class KlineService:
    """K线人生图服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def record_morning(self, score_date: date, score: int) -> dict:
        """记录早上评分（开盘价）"""
        score = max(0, min(100, score))
        existing = self.db.get_daily_score(score_date)
        if existing and existing["morning_score"] is not None:
            # 更新
            return self.db.upsert_daily_score(
                score_date,
                morning_score=score,
                high_score=max(score, existing["high_score"] or score),
                low_score=min(score, existing["low_score"] or score),
            )
        # 新建或首次设置 morning
        return self.db.upsert_daily_score(
            score_date,
            morning_score=score,
            high_score=max(score, (existing or {}).get("high_score") or score),
            low_score=min(score, (existing or {}).get("low_score") or score),
        )

    def record_evening(self, score_date: date, score: int) -> dict:
        """记录晚上评分（收盘价），自动设 high/low"""
        score = max(0, min(100, score))
        existing = self.db.get_daily_score(score_date)
        morning = (existing or {}).get("morning_score")
        if morning is not None:
            high = max(morning, score, (existing or {}).get("high_score") or 0)
            low = min(morning, score, (existing or {}).get("low_score") or 100)
        else:
            high = max(score, (existing or {}).get("high_score") or score)
            low = min(score, (existing or {}).get("low_score") or score)
        return self.db.upsert_daily_score(
            score_date,
            evening_score=score,
            high_score=high,
            low_score=low,
        )

    def update_score(self, score_date: date, morning: int = None, evening: int = None,
                     high: int = None, low: int = None,
                     notes: str = None, tags: str = None) -> dict:
        """手动修改评分"""
        kwargs = {}
        if morning is not None:
            kwargs["morning_score"] = max(0, min(100, morning))
        if evening is not None:
            kwargs["evening_score"] = max(0, min(100, evening))
        if high is not None:
            kwargs["high_score"] = max(0, min(100, high))
        if low is not None:
            kwargs["low_score"] = max(0, min(100, low))
        if notes is not None:
            kwargs["notes"] = notes
        if tags is not None:
            kwargs["tags"] = tags
        return self.db.upsert_daily_score(score_date, **kwargs)

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
            close = s.get("evening_score") or s.get("morning_score")
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
