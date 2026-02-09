"""
数据库管理器 — CRUD 操作层
职责：纯数据操作，不含业务逻辑
"""
from datetime import datetime, date, timedelta
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from database.models import (
    Base, UserConfig, Task, TaskRecord, StreakRecord,
    Realm, Skill, SubTask,
    Transaction, RecurringTransaction, Debt, DebtRepayment, Budget, Milestone,
    Person, PersonalityTag, RelationshipEvent,
    DailyScore,
    AIConfig, create_all_tables
)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionFactory = sessionmaker(bind=self.engine)
        create_all_tables(self.engine)

    @contextmanager
    def session_scope(self):
        """提供事务性 session 上下文管理器"""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ============ 用户配置 ============

    def get_user_config(self) -> Optional[dict]:
        """获取用户配置"""
        with self.session_scope() as s:
            config = s.query(UserConfig).first()
            if not config:
                return None
            return {
                "id": config.id,
                "birth_year": config.birth_year,
                "initial_blood": config.initial_blood,
                "current_blood": config.current_blood,
                "current_spirit": config.current_spirit,
                "target_money": config.target_money,
                "dark_mode": config.dark_mode,
                "created_at": config.created_at,
                "updated_at": config.updated_at,
            }

    def init_user_config(self, birth_year: int, target_money: int = 5_000_000) -> dict:
        """初始化用户配置"""
        from services.constants import DEFAULT_LIFESPAN_YEARS
        now = datetime.now()
        age = now.year - birth_year
        initial_blood = (DEFAULT_LIFESPAN_YEARS - age) * 365 * 24 * 60

        with self.session_scope() as s:
            config = s.query(UserConfig).first()
            if config:
                config.birth_year = birth_year
                config.initial_blood = initial_blood
                config.current_blood = initial_blood
                config.target_money = target_money
                config.updated_at = now
            else:
                config = UserConfig(
                    birth_year=birth_year,
                    initial_blood=initial_blood,
                    current_blood=initial_blood,
                    target_money=target_money,
                )
                s.add(config)
            s.flush()
            return {
                "birth_year": config.birth_year,
                "initial_blood": config.initial_blood,
                "current_blood": config.current_blood,
                "target_money": config.target_money,
            }

    def update_spirit(self, delta: int) -> int:
        """更新心境值，返回更新后的值"""
        from services.constants import clamp_spirit
        with self.session_scope() as s:
            config = s.query(UserConfig).first()
            if not config:
                raise ValueError("用户未初始化")
            config.current_spirit = clamp_spirit(config.current_spirit + delta)
            config.updated_at = datetime.now()
            s.flush()
            return config.current_spirit

    def update_blood(self, delta: int) -> int:
        """更新血量，返回更新后的值"""
        with self.session_scope() as s:
            config = s.query(UserConfig).first()
            if not config:
                raise ValueError("用户未初始化")
            config.current_blood = max(0, config.current_blood + delta)
            config.updated_at = datetime.now()
            s.flush()
            return config.current_blood

    # ============ 任务 CRUD ============

    def create_task(self, name: str, task_type: str, spirit_effect: int,
                    blood_effect: int = 0, emoji: str = "⭐",
                    submission_type: str = "daily_checkin",
                    enable_streak: bool = False) -> dict:
        """创建任务"""
        with self.session_scope() as s:
            task = Task(
                name=name,
                task_type=task_type,
                spirit_effect=spirit_effect,
                blood_effect=blood_effect,
                emoji=emoji,
                submission_type=submission_type,
                enable_streak=enable_streak,
            )
            s.add(task)
            s.flush()
            return self._task_to_dict(task)

    def get_tasks_by_type(self, task_type: str) -> list[dict]:
        """按类型获取任务列表"""
        with self.session_scope() as s:
            tasks = s.query(Task).filter(
                Task.task_type == task_type,
                Task.is_active == True
            ).order_by(Task.sort_order, Task.id).all()
            return [self._task_to_dict(t) for t in tasks]

    def get_task(self, task_id: int) -> Optional[dict]:
        """获取单个任务"""
        with self.session_scope() as s:
            task = s.query(Task).filter(Task.id == task_id).first()
            if not task:
                return None
            return self._task_to_dict(task)

    def delete_task(self, task_id: int) -> bool:
        """删除任务（软删除）"""
        with self.session_scope() as s:
            task = s.query(Task).filter(Task.id == task_id).first()
            if not task:
                return False
            task.is_active = False
            return True

    def reorder_tasks(self, task_ids: list[int]) -> None:
        """批量更新任务排序"""
        with self.session_scope() as s:
            for idx, task_id in enumerate(task_ids):
                task = s.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.sort_order = idx

    # ============ 任务记录 ============

    def add_task_record(self, task_id: int, task_name: str,
                        spirit_change: int, blood_change: int,
                        is_makeup: bool = False, notes: str = None) -> dict:
        """添加任务完成记录"""
        with self.session_scope() as s:
            record = TaskRecord(
                task_id=task_id,
                task_name=task_name,
                spirit_change=spirit_change,
                blood_change=blood_change,
                is_makeup=is_makeup,
                notes=notes,
            )
            s.add(record)
            # 更新心境和血量
            config = s.query(UserConfig).first()
            if config:
                from services.constants import clamp_spirit
                config.current_spirit = clamp_spirit(config.current_spirit + spirit_change)
                config.current_blood = max(0, config.current_blood + blood_change)
                config.updated_at = datetime.now()
            s.flush()
            return {
                "id": record.id,
                "task_id": record.task_id,
                "task_name": record.task_name,
                "spirit_change": record.spirit_change,
                "blood_change": record.blood_change,
                "completed_at": record.completed_at,
                "new_spirit": config.current_spirit if config else 0,
                "new_blood": config.current_blood if config else 0,
            }

    def undo_task_record(self, record_id: int) -> Optional[dict]:
        """撤销任务记录（仅限当天）"""
        with self.session_scope() as s:
            record = s.query(TaskRecord).filter(TaskRecord.id == record_id).first()
            if not record or record.is_undo:
                return None
            # 检查是否当天
            today = date.today()
            if record.completed_at.date() != today:
                return None
            record.is_undo = True
            # 回退心境和血量
            config = s.query(UserConfig).first()
            if config:
                from services.constants import clamp_spirit
                config.current_spirit = clamp_spirit(config.current_spirit - record.spirit_change)
                config.current_blood = max(0, config.current_blood - record.blood_change)
                config.updated_at = datetime.now()
            s.flush()
            return {
                "record_id": record.id,
                "reverted_spirit": record.spirit_change,
                "reverted_blood": record.blood_change,
                "new_spirit": config.current_spirit if config else 0,
                "new_blood": config.current_blood if config else 0,
            }

    def get_today_records(self) -> list[dict]:
        """获取今日任务记录"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        with self.session_scope() as s:
            records = s.query(TaskRecord).filter(
                TaskRecord.completed_at >= today_start,
                TaskRecord.completed_at <= today_end,
                TaskRecord.is_undo == False
            ).all()
            return [self._record_to_dict(r) for r in records]

    def is_task_completed_today(self, task_id: int) -> bool:
        """检查任务今日是否已完成"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        with self.session_scope() as s:
            count = s.query(TaskRecord).filter(
                TaskRecord.task_id == task_id,
                TaskRecord.completed_at >= today_start,
                TaskRecord.completed_at <= today_end,
                TaskRecord.is_undo == False
            ).count()
            return count > 0

    def get_task_today_count(self, task_id: int) -> int:
        """获取任务今日完成次数"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        with self.session_scope() as s:
            return s.query(TaskRecord).filter(
                TaskRecord.task_id == task_id,
                TaskRecord.completed_at >= today_start,
                TaskRecord.completed_at <= today_end,
                TaskRecord.is_undo == False
            ).count()

    def get_records_in_range(self, start_date: date, end_date: date) -> list[dict]:
        """获取日期范围内的记录"""
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        with self.session_scope() as s:
            records = s.query(TaskRecord).filter(
                TaskRecord.completed_at >= start,
                TaskRecord.completed_at <= end,
                TaskRecord.is_undo == False
            ).order_by(TaskRecord.completed_at).all()
            return [self._record_to_dict(r) for r in records]

    # ============ 连续打卡 ============

    def update_streak(self, task_id: int) -> dict:
        """更新连续打卡记录"""
        today = date.today()
        with self.session_scope() as s:
            streak = s.query(StreakRecord).filter(StreakRecord.task_id == task_id).first()
            if not streak:
                streak = StreakRecord(task_id=task_id, current_streak=1, max_streak=1, last_completed_date=today)
                s.add(streak)
            else:
                if streak.last_completed_date == today:
                    pass  # 今天已打卡
                elif streak.last_completed_date == today - timedelta(days=1):
                    streak.current_streak += 1
                    streak.max_streak = max(streak.max_streak, streak.current_streak)
                else:
                    streak.current_streak = 1
                streak.last_completed_date = today
            s.flush()
            return {
                "task_id": task_id,
                "current_streak": streak.current_streak,
                "max_streak": streak.max_streak,
            }

    def get_streak(self, task_id: int) -> Optional[dict]:
        """获取打卡记录"""
        with self.session_scope() as s:
            streak = s.query(StreakRecord).filter(StreakRecord.task_id == task_id).first()
            if not streak:
                return None
            return {
                "task_id": streak.task_id,
                "current_streak": streak.current_streak,
                "max_streak": streak.max_streak,
                "last_completed_date": streak.last_completed_date,
            }

    # ============ 境界系统 ============

    def create_realm(self, name: str, realm_type: str = "main",
                     description: str = None, completion_rate: int = 100,
                     reward_spirit: int = 0) -> dict:
        """创建境界"""
        with self.session_scope() as s:
            realm = Realm(
                name=name,
                realm_type=realm_type,
                description=description,
                completion_rate=completion_rate,
                reward_spirit=reward_spirit,
            )
            s.add(realm)
            s.flush()
            return self._realm_to_dict(realm)

    def get_active_realm(self, realm_type: str = "main") -> Optional[dict]:
        """获取当前活跃境界"""
        with self.session_scope() as s:
            realm = s.query(Realm).filter(
                Realm.status == "active",
                Realm.realm_type == realm_type
            ).first()
            if not realm:
                return None
            return self._realm_to_dict(realm, include_skills=True, session=s)

    def complete_realm(self, realm_id: int) -> Optional[dict]:
        """完成境界"""
        with self.session_scope() as s:
            realm = s.query(Realm).filter(Realm.id == realm_id).first()
            if not realm:
                return None
            realm.status = "completed"
            realm.completed_at = datetime.now()
            s.flush()
            return self._realm_to_dict(realm)

    def create_skill(self, realm_id: int, name: str, description: str = None) -> dict:
        """创建技能（大任务）"""
        with self.session_scope() as s:
            skill = Skill(realm_id=realm_id, name=name, description=description)
            s.add(skill)
            s.flush()
            return self._skill_to_dict(skill)

    def create_sub_task(self, skill_id: int, name: str) -> dict:
        """创建子任务"""
        with self.session_scope() as s:
            sub = SubTask(skill_id=skill_id, name=name)
            s.add(sub)
            s.flush()
            return {"id": sub.id, "skill_id": sub.skill_id, "name": sub.name, "is_completed": False}

    def complete_sub_task(self, sub_task_id: int) -> dict:
        """完成子任务，自动检查大任务是否完成"""
        with self.session_scope() as s:
            sub = s.query(SubTask).filter(SubTask.id == sub_task_id).first()
            if not sub:
                raise ValueError("子任务不存在")
            sub.is_completed = True
            sub.completed_at = datetime.now()

            # 检查大任务下所有子任务是否完成
            skill = s.query(Skill).filter(Skill.id == sub.skill_id).first()
            all_subs = s.query(SubTask).filter(SubTask.skill_id == skill.id).all()
            completed_count = sum(1 for st in all_subs if st.is_completed)
            skill_auto_completed = completed_count == len(all_subs)
            if skill_auto_completed:
                skill.is_completed = True
                skill.completed_at = datetime.now()

            s.flush()
            return {
                "sub_task_id": sub.id,
                "skill_id": skill.id,
                "skill_completed": skill_auto_completed,
                "progress": completed_count / len(all_subs) if all_subs else 0,
            }

    # ============ 灵石系统 ============

    def add_transaction(self, type: str, amount: float, category: str,
                        description: str = None, transaction_date: date = None) -> dict:
        """添加收支记录"""
        with self.session_scope() as s:
            txn = Transaction(
                type=type,
                amount=amount,
                category=category,
                description=description,
                transaction_date=transaction_date or date.today(),
            )
            s.add(txn)
            s.flush()
            return {
                "id": txn.id, "type": txn.type, "amount": txn.amount,
                "category": txn.category, "description": txn.description,
                "transaction_date": str(txn.transaction_date),
            }

    def get_balance(self) -> dict:
        """获取灵石余额"""
        with self.session_scope() as s:
            income = s.query(func.sum(Transaction.amount)).filter(Transaction.type == "income").scalar() or 0
            expense = s.query(func.sum(Transaction.amount)).filter(Transaction.type == "expense").scalar() or 0
            return {"income": float(income), "expense": float(expense), "balance": float(income - expense)}

    def get_transactions(self, start_date: date = None, end_date: date = None,
                         type: str = None, category: str = None,
                         limit: int = 50) -> list[dict]:
        """查询收支记录"""
        with self.session_scope() as s:
            q = s.query(Transaction)
            if start_date:
                q = q.filter(Transaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(Transaction.transaction_date <= end_date)
            if type:
                q = q.filter(Transaction.type == type)
            if category:
                q = q.filter(Transaction.category == category)
            txns = q.order_by(Transaction.transaction_date.desc()).limit(limit).all()
            return [{
                "id": t.id, "type": t.type, "amount": float(t.amount),
                "category": t.category, "description": t.description,
                "transaction_date": str(t.transaction_date),
            } for t in txns]

    # ============ 负债 ============

    def create_debt(self, name: str, total_amount: float, monthly_payment: float,
                    interest_rate: float = 0) -> dict:
        """创建负债"""
        with self.session_scope() as s:
            debt = Debt(
                name=name, total_amount=total_amount,
                remaining_amount=total_amount, monthly_payment=monthly_payment,
                interest_rate=interest_rate,
            )
            s.add(debt)
            s.flush()
            return self._debt_to_dict(debt)

    def get_debts(self, active_only: bool = True) -> list[dict]:
        """获取负债列表"""
        with self.session_scope() as s:
            q = s.query(Debt)
            if active_only:
                q = q.filter(Debt.is_active == True)
            return [self._debt_to_dict(d) for d in q.all()]

    # ============ 预算 ============

    def set_budget(self, category: str, amount: float, month: str) -> dict:
        """设置预算"""
        with self.session_scope() as s:
            budget = s.query(Budget).filter(Budget.category == category, Budget.month == month).first()
            if budget:
                budget.amount = amount
            else:
                budget = Budget(category=category, amount=amount, month=month)
                s.add(budget)
            s.flush()
            return {"category": budget.category, "amount": float(budget.amount), "month": budget.month}

    def get_budgets(self, month: str) -> list[dict]:
        """获取月度预算"""
        with self.session_scope() as s:
            budgets = s.query(Budget).filter(Budget.month == month).all()
            return [{"category": b.category, "amount": float(b.amount), "month": b.month} for b in budgets]

    # ============ 统御系统 ============

    def create_person(self, name: str, relationship_type: str, **kwargs) -> dict:
        """创建人物档案"""
        with self.session_scope() as s:
            person = Person(name=name, relationship_type=relationship_type, **kwargs)
            s.add(person)
            s.flush()
            return self._person_to_dict(person)

    def get_people(self, active_only: bool = True) -> list[dict]:
        """获取人物列表"""
        with self.session_scope() as s:
            q = s.query(Person)
            if active_only:
                q = q.filter(Person.is_active == True)
            return [self._person_to_dict(p) for p in q.order_by(Person.name).all()]

    def get_person(self, person_id: int) -> Optional[dict]:
        """获取人物详情"""
        with self.session_scope() as s:
            person = s.query(Person).filter(Person.id == person_id).first()
            if not person:
                return None
            return self._person_to_dict(person, include_tags=True, include_events=True, session=s)

    def add_event(self, person_id: int, event_date: date, event_description: str, **kwargs) -> dict:
        """添加人际事件"""
        with self.session_scope() as s:
            event = RelationshipEvent(
                person_id=person_id, event_date=event_date,
                event_description=event_description, **kwargs
            )
            s.add(event)
            s.flush()
            return self._event_to_dict(event)

    def get_events(self, person_id: int, limit: int = 20) -> list[dict]:
        """获取人物事件列表"""
        with self.session_scope() as s:
            events = s.query(RelationshipEvent).filter(
                RelationshipEvent.person_id == person_id
            ).order_by(RelationshipEvent.event_date.desc()).limit(limit).all()
            return [self._event_to_dict(e) for e in events]

    # ============ AI 配置 ============

    def get_active_ai_config(self) -> Optional[dict]:
        """获取当前激活的 AI 配置"""
        with self.session_scope() as s:
            config = s.query(AIConfig).filter(AIConfig.is_active == True).first()
            if not config:
                return None
            return {
                "id": config.id, "provider": config.provider,
                "api_key": config.api_key, "api_base": config.api_base,
                "model": config.model, "proxy": config.proxy,
            }

    def save_ai_config(self, provider: str, api_key: str = None,
                       api_base: str = None, model: str = None,
                       proxy: str = None) -> dict:
        """保存 AI 配置"""
        with self.session_scope() as s:
            # 先取消所有激活
            s.query(AIConfig).update({AIConfig.is_active: False})
            config = AIConfig(
                provider=provider, api_key=api_key, api_base=api_base,
                model=model, proxy=proxy, is_active=True,
            )
            s.add(config)
            s.flush()
            return {"id": config.id, "provider": config.provider, "is_active": True}

    # ============ K线人生图 ============

    def get_daily_score(self, score_date: date) -> Optional[dict]:
        """获取某天的评分"""
        with self.session_scope() as s:
            score = s.query(DailyScore).filter(DailyScore.score_date == score_date).first()
            if not score:
                return None
            return self._daily_score_to_dict(score)

    def get_daily_scores(self, start_date: date, end_date: date) -> list[dict]:
        """获取日期范围内的评分"""
        with self.session_scope() as s:
            scores = s.query(DailyScore).filter(
                DailyScore.score_date >= start_date,
                DailyScore.score_date <= end_date,
            ).order_by(DailyScore.score_date).all()
            return [self._daily_score_to_dict(sc) for sc in scores]

    def upsert_daily_score(self, score_date: date, **kwargs) -> dict:
        """创建或更新每日评分"""
        with self.session_scope() as s:
            score = s.query(DailyScore).filter(DailyScore.score_date == score_date).first()
            if not score:
                score = DailyScore(score_date=score_date)
                s.add(score)
            for key, val in kwargs.items():
                if hasattr(score, key) and val is not None:
                    setattr(score, key, val)
            score.updated_at = datetime.now()
            s.flush()
            return self._daily_score_to_dict(score)

    def delete_daily_score(self, score_id: int) -> bool:
        """删除每日评分"""
        with self.session_scope() as s:
            score = s.query(DailyScore).filter(DailyScore.id == score_id).first()
            if not score:
                return False
            s.delete(score)
            return True

    @staticmethod
    def _daily_score_to_dict(score: DailyScore) -> dict:
        return {
            "id": score.id,
            "score_date": score.score_date,
            "morning_score": score.morning_score,
            "evening_score": score.evening_score,
            "high_score": score.high_score,
            "low_score": score.low_score,
            "notes": score.notes,
            "tags": score.tags,
            "created_at": score.created_at,
            "updated_at": score.updated_at,
        }

    # ============ 序列化辅助 ============

    @staticmethod
    def _task_to_dict(task: Task) -> dict:
        return {
            "id": task.id, "name": task.name, "task_type": task.task_type,
            "spirit_effect": task.spirit_effect, "blood_effect": task.blood_effect,
            "emoji": task.emoji, "submission_type": task.submission_type,
            "enable_streak": task.enable_streak, "sort_order": task.sort_order,
            "is_active": task.is_active,
        }

    @staticmethod
    def _record_to_dict(record: TaskRecord) -> dict:
        return {
            "id": record.id, "task_id": record.task_id, "task_name": record.task_name,
            "spirit_change": record.spirit_change, "blood_change": record.blood_change,
            "is_undo": record.is_undo, "is_makeup": record.is_makeup,
            "completed_at": record.completed_at, "notes": record.notes,
        }

    @staticmethod
    def _realm_to_dict(realm: Realm, include_skills: bool = False, session: Session = None) -> dict:
        d = {
            "id": realm.id, "name": realm.name, "description": realm.description,
            "realm_type": realm.realm_type, "completion_rate": realm.completion_rate,
            "reward_spirit": realm.reward_spirit, "status": realm.status,
            "order_index": realm.order_index,
            "started_at": realm.started_at, "completed_at": realm.completed_at,
        }
        if include_skills and session:
            skills = session.query(Skill).filter(Skill.realm_id == realm.id).order_by(Skill.order_index).all()
            d["skills"] = []
            for sk in skills:
                sk_dict = DatabaseManager._skill_to_dict(sk)
                subs = session.query(SubTask).filter(SubTask.skill_id == sk.id).order_by(SubTask.order_index).all()
                sk_dict["sub_tasks"] = [
                    {"id": st.id, "name": st.name, "is_completed": st.is_completed, "order_index": st.order_index}
                    for st in subs
                ]
                completed = sum(1 for st in subs if st.is_completed)
                sk_dict["progress"] = completed / len(subs) if subs else 0
                d["skills"].append(sk_dict)
        return d

    @staticmethod
    def _skill_to_dict(skill: Skill) -> dict:
        return {
            "id": skill.id, "realm_id": skill.realm_id, "name": skill.name,
            "description": skill.description, "order_index": skill.order_index,
            "is_completed": skill.is_completed,
        }

    @staticmethod
    def _debt_to_dict(debt: Debt) -> dict:
        return {
            "id": debt.id, "name": debt.name, "total_amount": float(debt.total_amount),
            "remaining_amount": float(debt.remaining_amount),
            "monthly_payment": float(debt.monthly_payment),
            "interest_rate": float(debt.interest_rate), "is_active": debt.is_active,
        }

    @staticmethod
    def _person_to_dict(person: Person, include_tags: bool = False,
                        include_events: bool = False, session: Session = None) -> dict:
        d = {
            "id": person.id, "name": person.name,
            "relationship_type": person.relationship_type,
            "met_date": str(person.met_date) if person.met_date else None,
            "birthday": str(person.birthday) if person.birthday else None,
            "notes": person.notes, "ai_report": person.ai_report,
            "avatar_emoji": person.avatar_emoji, "is_active": person.is_active,
        }
        if include_tags and session:
            tags = session.query(PersonalityTag).filter(PersonalityTag.person_id == person.id).all()
            d["personality_tags"] = [
                {"id": t.id, "category": t.category, "tag_name": t.tag_name, "tag_value": t.tag_value}
                for t in tags
            ]
        if include_events and session:
            events = session.query(RelationshipEvent).filter(
                RelationshipEvent.person_id == person.id
            ).order_by(RelationshipEvent.event_date.desc()).limit(10).all()
            d["recent_events"] = [DatabaseManager._event_to_dict(e) for e in events]
        return d

    @staticmethod
    def _event_to_dict(event: RelationshipEvent) -> dict:
        return {
            "id": event.id, "person_id": event.person_id,
            "event_date": str(event.event_date), "location": event.location,
            "event_description": event.event_description,
            "impression_tags": event.impression_tags,
            "their_emotion": event.their_emotion,
            "topics": event.topics, "key_info": event.key_info,
            "my_feeling": event.my_feeling, "next_action": event.next_action,
        }
