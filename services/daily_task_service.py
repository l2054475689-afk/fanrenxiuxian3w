"""
日常任务 Service 层
职责：日常任务的 CRUD 和统计
"""
from datetime import datetime, date
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import DailyTask


class DailyTaskService:
    """日常任务服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_daily_task(self, name: str, category: str = "main",
                          priority: str = "medium", deadline: datetime = None,
                          notes: str = None) -> dict:
        """创建日常任务"""
        with self.db.session_scope() as s:
            task = DailyTask(
                name=name,
                category=category,
                priority=priority,
                deadline=deadline,
                notes=notes,
                created_date=date.today(),
            )
            s.add(task)
            s.flush()
            return self._task_to_dict(task)

    def complete_daily_task(self, task_id: int) -> dict:
        """完成日常任务"""
        with self.db.session_scope() as s:
            task = s.query(DailyTask).filter(DailyTask.id == task_id).first()
            if not task:
                return {"success": False, "message": "任务不存在"}
            task.is_completed = True
            task.completed_at = datetime.now()
            s.flush()
            return {"success": True, "message": f"✅ 完成: {task.name}", "task": self._task_to_dict(task)}

    def uncomplete_daily_task(self, task_id: int) -> dict:
        """取消完成日常任务"""
        with self.db.session_scope() as s:
            task = s.query(DailyTask).filter(DailyTask.id == task_id).first()
            if not task:
                return {"success": False, "message": "任务不存在"}
            task.is_completed = False
            task.completed_at = None
            s.flush()
            return {"success": True, "message": f"已取消完成: {task.name}", "task": self._task_to_dict(task)}

    def delete_daily_task(self, task_id: int) -> dict:
        """删除日常任务"""
        with self.db.session_scope() as s:
            task = s.query(DailyTask).filter(DailyTask.id == task_id).first()
            if not task:
                return {"success": False, "message": "任务不存在"}
            name = task.name
            s.delete(task)
        return {"success": True, "message": f"已删除: {name}"}

    def get_today_tasks(self) -> list[dict]:
        """获取所有日常任务（不按日期过滤，任务持久保存）
        每天重置完成状态但不删除任务本身"""
        today = date.today()
        with self.db.session_scope() as s:
            tasks = s.query(DailyTask).order_by(
                DailyTask.is_completed,
                DailyTask.priority.desc(),
                DailyTask.created_at,
            ).all()
            result = []
            for t in tasks:
                d = self._task_to_dict(t)
                # 如果完成日期不是今天，重置完成状态（新的一天）
                if t.is_completed and t.completed_at:
                    completed_date = t.completed_at.date() if hasattr(t.completed_at, 'date') else t.completed_at
                    if completed_date != today:
                        t.is_completed = False
                        t.completed_at = None
                        d = self._task_to_dict(t)
                result.append(d)
            return result

    def get_today_completion_rate(self) -> dict:
        """获取今日完成率（基于所有日常任务，今天是否完成）"""
        today = date.today()
        with self.db.session_scope() as s:
            tasks = s.query(DailyTask).all()
            total = len(tasks)
            completed = 0
            for t in tasks:
                if t.is_completed and t.completed_at:
                    completed_date = t.completed_at.date() if hasattr(t.completed_at, 'date') else t.completed_at
                    if completed_date == today:
                        completed += 1
            rate = completed / total if total > 0 else 0
            return {
                "total": total,
                "completed": completed,
                "rate": rate,
            }

    @staticmethod
    def _task_to_dict(task: DailyTask) -> dict:
        return {
            "id": task.id,
            "name": task.name,
            "category": task.category,
            "priority": task.priority,
            "deadline": task.deadline,
            "notes": task.notes,
            "is_completed": task.is_completed,
            "completed_at": task.completed_at,
            "created_date": task.created_date,
            "created_at": task.created_at,
        }
