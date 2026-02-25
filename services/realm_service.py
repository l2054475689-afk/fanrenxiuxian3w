"""
境界系统 Service 层
职责：境界创建/进阶/副本/归档
"""
from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from services.constants import REALM_TYPE_MAIN, REALM_TYPE_DUNGEON


class RealmService:
    """境界系统服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    # === 境界管理 ===

    def create_realm(self, name: str, description: str = None,
                     completion_rate: int = 100, reward_spirit: int = 0,
                     realm_type: str = REALM_TYPE_MAIN) -> dict:
        """创建新境界"""
        # 主境界只能有一个活跃的，副本可以有多个
        if realm_type == REALM_TYPE_MAIN:
            existing = self.db.get_active_realm(realm_type)
            if existing:
                return {"success": False, "message": f"已有活跃主境界「{existing['name']}」，请先完成或归档"}

        realm = self.db.create_realm(
            name=name, realm_type=realm_type,
            description=description, completion_rate=completion_rate,
            reward_spirit=reward_spirit,
        )
        return {"success": True, "realm": realm, "message": f"境界「{name}」已创建"}

    def get_active_main_realm(self) -> Optional[dict]:
        """获取当前主境界（含技能树）"""
        return self.db.get_active_realm(REALM_TYPE_MAIN)

    def get_active_dungeon(self) -> Optional[dict]:
        """获取当前副本境界（兼容旧接口，返回第一个）"""
        return self.db.get_active_realm(REALM_TYPE_DUNGEON)

    def get_active_dungeons(self) -> list[dict]:
        """获取所有活跃副本"""
        with self.db.session_scope() as s:
            from database.models import Realm
            realms = s.query(Realm).filter(
                Realm.realm_type == REALM_TYPE_DUNGEON,
                Realm.status == "active",
            ).order_by(Realm.started_at.desc()).all()
            return [self.db._realm_to_dict(r) for r in realms]

    def get_completed_realms(self, realm_type: str = None) -> list[dict]:
        """获取已完成的境界列表，可按类型过滤"""
        with self.db.session_scope() as s:
            from database.models import Realm
            q = s.query(Realm).filter(Realm.status == "completed")
            if realm_type:
                q = q.filter(Realm.realm_type == realm_type)
            realms = q.order_by(Realm.completed_at.desc()).all()
            return [self.db._realm_to_dict(r) for r in realms]

    # === 技能/大任务管理 ===

    def add_skill(self, realm_id: int, name: str, description: str = None) -> dict:
        """添加技能（大任务）"""
        skill = self.db.create_skill(realm_id, name, description)
        return {"success": True, "skill": skill}

    def delete_skill(self, skill_id: int) -> dict:
        """删除技能"""
        with self.db.session_scope() as s:
            from database.models import Skill
            skill = s.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return {"success": False, "message": "技能不存在"}
            s.delete(skill)
        return {"success": True, "message": "已删除"}

    # === 子任务管理 ===

    def add_sub_task(self, skill_id: int, name: str) -> dict:
        """添加子任务"""
        sub = self.db.create_sub_task(skill_id, name)
        return {"success": True, "sub_task": sub}

    def complete_sub_task(self, sub_task_id: int) -> dict:
        """完成子任务，自动检查大任务和境界进度"""
        result = self.db.complete_sub_task(sub_task_id)

        # 如果大任务完成了，检查境界是否可以晋升
        realm_ready = False
        if result["skill_completed"]:
            realm_ready = self._check_realm_completion(result["skill_id"])

        return {
            "success": True,
            "sub_task_id": result["sub_task_id"],
            "skill_completed": result["skill_completed"],
            "skill_progress": result["progress"],
            "realm_ready_to_advance": realm_ready,
        }

    def uncomplete_sub_task(self, sub_task_id: int) -> dict:
        """取消完成子任务"""
        with self.db.session_scope() as s:
            from database.models import SubTask, Skill
            sub = s.query(SubTask).filter(SubTask.id == sub_task_id).first()
            if not sub:
                return {"success": False, "message": "子任务不存在"}
            sub.is_completed = False
            sub.completed_at = None
            # 同时取消大任务的完成状态
            skill = s.query(Skill).filter(Skill.id == sub.skill_id).first()
            if skill and skill.is_completed:
                skill.is_completed = False
                skill.completed_at = None
        return {"success": True, "message": "已取消完成"}

    def delete_sub_task(self, sub_task_id: int) -> dict:
        """删除子任务"""
        with self.db.session_scope() as s:
            from database.models import SubTask
            sub = s.query(SubTask).filter(SubTask.id == sub_task_id).first()
            if not sub:
                return {"success": False, "message": "子任务不存在"}
            s.delete(sub)
        return {"success": True, "message": "已删除"}

    def delete_realm(self, realm_id: int) -> dict:
        """删除境界（含所有技能和子任务）"""
        with self.db.session_scope() as s:
            from database.models import Realm, Skill, SubTask
            realm = s.query(Realm).filter(Realm.id == realm_id).first()
            if not realm:
                return {"success": False, "message": "境界不存在"}
            name = realm.name
            # 删除所有子任务和技能
            skills = s.query(Skill).filter(Skill.realm_id == realm_id).all()
            for sk in skills:
                s.query(SubTask).filter(SubTask.skill_id == sk.id).delete()
                s.delete(sk)
            s.delete(realm)
        return {"success": True, "message": f"已删除境界「{name}」"}

    # === 境界晋升 ===

    def advance_realm(self, realm_id: int) -> dict:
        """境界晋升"""
        with self.db.session_scope() as s:
            from database.models import Realm, Skill, SubTask
            realm = s.query(Realm).filter(Realm.id == realm_id).first()
            if not realm:
                return {"success": False, "message": "境界不存在"}
            if realm.status != "active":
                return {"success": False, "message": "境界非活跃状态"}

            # 计算完成度
            skills = s.query(Skill).filter(Skill.realm_id == realm_id).all()
            if not skills:
                return {"success": False, "message": "境界下没有技能"}

            total_progress = 0
            for sk in skills:
                subs = s.query(SubTask).filter(SubTask.skill_id == sk.id).all()
                if subs:
                    completed = sum(1 for st in subs if st.is_completed)
                    total_progress += completed / len(subs)
                else:
                    total_progress += 1.0 if sk.is_completed else 0

            avg_progress = total_progress / len(skills) * 100

            if avg_progress < realm.completion_rate:
                return {
                    "success": False,
                    "message": f"完成度 {avg_progress:.0f}%，需要 {realm.completion_rate}%",
                    "current_progress": avg_progress,
                }

            # 执行晋升/成就达成
            realm.status = "completed"
            realm.completed_at = datetime.now()

            # 发放奖励
            reward_msg = ""
            if realm.reward_spirit > 0:
                from services.constants import clamp_spirit
                from database.models import UserConfig
                config = s.query(UserConfig).first()
                if config:
                    config.current_spirit = clamp_spirit(config.current_spirit + realm.reward_spirit)
                    reward_msg = f"，心境+{realm.reward_spirit}"

            # 根据 realm_type 区分提示文案
            if realm.realm_type == REALM_TYPE_DUNGEON:
                message = f"🏆 成就达成！「{realm.name}」挑战完成{reward_msg}"
            else:
                message = f"🎉 恭喜晋升！「{realm.name}」圆满{reward_msg}"

            return {
                "success": True,
                "message": message,
                "realm_name": realm.name,
                "realm_type": realm.realm_type,
                "completion_time": str(realm.completed_at),
            }

    def get_realm_progress(self, realm_id: int) -> dict:
        """获取境界详细进度"""
        with self.db.session_scope() as s:
            from database.models import Realm, Skill, SubTask
            realm = s.query(Realm).filter(Realm.id == realm_id).first()
            if not realm:
                return {"error": "境界不存在"}

            skills = s.query(Skill).filter(Skill.realm_id == realm_id).order_by(Skill.order_index).all()
            skill_list = []
            total_subs = 0
            completed_subs = 0

            for sk in skills:
                subs = s.query(SubTask).filter(SubTask.skill_id == sk.id).order_by(SubTask.order_index).all()
                sub_completed = sum(1 for st in subs if st.is_completed)
                total_subs += len(subs)
                completed_subs += sub_completed

                skill_list.append({
                    "id": sk.id, "name": sk.name,
                    "is_completed": sk.is_completed,
                    "total": len(subs), "completed": sub_completed,
                    "progress": sub_completed / len(subs) if subs else 0,
                    "sub_tasks": [
                        {"id": st.id, "name": st.name, "is_completed": st.is_completed}
                        for st in subs
                    ],
                })

            return {
                "realm_name": realm.name,
                "realm_type": realm.realm_type,
                "status": realm.status,
                "completion_rate": realm.completion_rate,
                "total_skills": len(skills),
                "total_sub_tasks": total_subs,
                "completed_sub_tasks": completed_subs,
                "overall_progress": completed_subs / total_subs * 100 if total_subs > 0 else 0,
                "skills": skill_list,
            }

    # === 内部方法 ===

    def _check_realm_completion(self, skill_id: int) -> bool:
        """检查技能所属境界是否满足晋升条件"""
        with self.db.session_scope() as s:
            from database.models import Skill, SubTask, Realm
            skill = s.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return False
            realm = s.query(Realm).filter(Realm.id == skill.realm_id).first()
            if not realm or realm.status != "active":
                return False

            skills = s.query(Skill).filter(Skill.realm_id == realm.id).all()
            total_progress = 0
            for sk in skills:
                subs = s.query(SubTask).filter(SubTask.skill_id == sk.id).all()
                if subs:
                    completed = sum(1 for st in subs if st.is_completed)
                    total_progress += completed / len(subs)
                else:
                    total_progress += 1.0 if sk.is_completed else 0

            avg = total_progress / len(skills) * 100 if skills else 0
            return avg >= realm.completion_rate
