"""
统御系统 Service 层
职责：人物档案、事件记录、性格标签、相处模板、互动提醒
"""
import json
from datetime import date, datetime, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from services.constants import RELATIONSHIP_TYPES, PERSONALITY_DIMENSIONS, IMPRESSION_TAGS, EMOTION_TAGS


class TongyuService:
    """统御系统服务"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    # === 人物管理 ===

    def create_person(self, name: str, relationship_type: str,
                      birthday: date = None, personality: str = None,
                      avatar_emoji: str = "👤", notes: str = None) -> dict:
        """创建人物档案"""
        if not name.strip():
            return {"success": False, "message": "姓名不能为空"}

        person = self.db.create_person(
            name=name, relationship_type=relationship_type,
            birthday=birthday, personality=personality,
            avatar_emoji=avatar_emoji, notes=notes,
        )
        return {"success": True, "person": person, "message": f"已添加「{name}」"}

    def update_person(self, person_id: int, **kwargs) -> dict:
        """更新人物信息"""
        with self.db.session_scope() as s:
            from database.models import Person
            person = s.query(Person).filter(Person.id == person_id).first()
            if not person:
                return {"success": False, "message": "人物不存在"}
            for key, value in kwargs.items():
                if hasattr(person, key):
                    setattr(person, key, value)
            person.updated_at = datetime.now()
        return {"success": True, "message": "已更新"}

    def delete_person(self, person_id: int) -> dict:
        """删除人物（软删除）"""
        with self.db.session_scope() as s:
            from database.models import Person
            person = s.query(Person).filter(Person.id == person_id).first()
            if not person:
                return {"success": False, "message": "人物不存在"}
            person.is_active = False
        return {"success": True, "message": "已删除"}

    def get_people(self) -> list[dict]:
        """获取人物列表"""
        return self.db.get_people()

    def get_person_detail(self, person_id: int) -> Optional[dict]:
        """获取人物详情（含标签和事件）"""
        return self.db.get_person(person_id)

    # === 性格标签 ===

    def set_personality_dimension(self, person_id: int, dimension_name: str, value: int) -> dict:
        """设置性格维度（滑块值 0-100）"""
        with self.db.session_scope() as s:
            from database.models import PersonalityTag
            tag = s.query(PersonalityTag).filter(
                PersonalityTag.person_id == person_id,
                PersonalityTag.category == "dimension",
                PersonalityTag.tag_name == dimension_name,
            ).first()
            if tag:
                tag.tag_value = max(0, min(100, value))
            else:
                tag = PersonalityTag(
                    person_id=person_id, category="dimension",
                    tag_name=dimension_name, tag_value=max(0, min(100, value)),
                )
                s.add(tag)
        return {"success": True}

    def set_communication_style(self, person_id: int, styles: list[str]) -> dict:
        """设置沟通风格标签"""
        with self.db.session_scope() as s:
            from database.models import PersonalityTag
            # 清除旧的
            s.query(PersonalityTag).filter(
                PersonalityTag.person_id == person_id,
                PersonalityTag.category == "communication",
            ).delete()
            # 添加新的
            for style in styles:
                tag = PersonalityTag(
                    person_id=person_id, category="communication",
                    tag_name=style,
                )
                s.add(tag)
        return {"success": True}

    def add_custom_tag(self, person_id: int, tag_name: str) -> dict:
        """添加自定义标签"""
        with self.db.session_scope() as s:
            from database.models import PersonalityTag
            tag = PersonalityTag(
                person_id=person_id, category="custom",
                tag_name=tag_name,
            )
            s.add(tag)
        return {"success": True}

    def remove_custom_tag(self, person_id: int, tag_name: str) -> dict:
        """删除自定义标签"""
        with self.db.session_scope() as s:
            from database.models import PersonalityTag
            s.query(PersonalityTag).filter(
                PersonalityTag.person_id == person_id,
                PersonalityTag.category == "custom",
                PersonalityTag.tag_name == tag_name,
            ).delete()
        return {"success": True}

    # === 事件记录 ===

    def add_event(self, person_id: int, event_date: date, description: str,
                  location: str = None, impression_tags: list[str] = None,
                  their_emotion: list[str] = None, topics: list[str] = None,
                  key_info: str = None, my_feeling: str = None,
                  next_action: str = None, is_completed: bool = False) -> dict:
        """添加人际事件"""
        if not description.strip():
            return {"success": False, "message": "事件描述不能为空"}

        event = self.db.add_event(
            person_id=person_id, event_date=event_date,
            event_description=description, location=location,
            impression_tags=json.dumps(impression_tags or [], ensure_ascii=False),
            their_emotion=json.dumps(their_emotion or [], ensure_ascii=False),
            topics=json.dumps(topics or [], ensure_ascii=False),
            key_info=key_info, my_feeling=my_feeling,
            next_action=next_action, is_completed=is_completed,
        )
        return {"success": True, "event": event, "message": "事件已记录"}

    def delete_event(self, event_id: int) -> dict:
        """删除事件"""
        with self.db.session_scope() as s:
            from database.models import RelationshipEvent
            event = s.query(RelationshipEvent).filter(RelationshipEvent.id == event_id).first()
            if not event:
                return {"success": False, "message": "事件不存在"}
            s.delete(event)
        return {"success": True, "message": "已删除"}

    def toggle_event_completed(self, event_id: int) -> dict:
        """切换事件完成状态"""
        with self.db.session_scope() as s:
            from database.models import RelationshipEvent
            event = s.query(RelationshipEvent).filter(RelationshipEvent.id == event_id).first()
            if not event:
                return {"success": False, "message": "事件不存在"}
            event.is_completed = not event.is_completed
            s.flush()
            return {"success": True, "is_completed": event.is_completed}

    def get_events(self, person_id: int, limit: int = 20) -> list[dict]:
        """获取人物事件列表"""
        events = self.db.get_events(person_id, limit)
        # 解析 JSON 字段
        for e in events:
            for field in ["impression_tags", "their_emotion", "topics"]:
                if e.get(field) and isinstance(e[field], str):
                    try:
                        e[field] = json.loads(e[field])
                    except json.JSONDecodeError:
                        e[field] = []
        return events

    # === 互动提醒 ===

    def get_neglected_people(self, days_threshold: int = 30) -> list[dict]:
        """获取长期未联系的人"""
        threshold_date = date.today() - timedelta(days=days_threshold)
        people = self.db.get_people()
        neglected = []

        for p in people:
            events = self.db.get_events(p["id"], limit=1)
            if not events:
                # 从未互动
                neglected.append({
                    "person": p,
                    "last_contact": None,
                    "days_since": None,
                    "message": f"从未记录与「{p['name']}」的互动",
                })
            else:
                last_date_str = events[0]["event_date"]
                last_date = date.fromisoformat(last_date_str) if isinstance(last_date_str, str) else last_date_str
                if last_date < threshold_date:
                    days_since = (date.today() - last_date).days
                    neglected.append({
                        "person": p,
                        "last_contact": str(last_date),
                        "days_since": days_since,
                        "message": f"已 {days_since} 天未联系「{p['name']}」",
                    })

        return sorted(neglected, key=lambda x: x.get("days_since") or 9999, reverse=True)

    def get_upcoming_birthdays(self, days_ahead: int = 7) -> list[dict]:
        """获取即将到来的生日"""
        today = date.today()
        upcoming = []

        with self.db.session_scope() as s:
            from database.models import Person
            people = s.query(Person).filter(
                Person.is_active == True,
                Person.birthday != None,
            ).all()

            for p in people:
                bday_this_year = p.birthday.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                days_until = (bday_this_year - today).days
                if days_until <= days_ahead:
                    upcoming.append({
                        "name": p.name,
                        "birthday": str(p.birthday),
                        "days_until": days_until,
                        "relationship_type": p.relationship_type,
                        "avatar_emoji": p.avatar_emoji,
                    })

        return sorted(upcoming, key=lambda x: x["days_until"])

    # === 统计 ===

    def get_relationship_stats(self) -> dict:
        """获取人际关系统计"""
        people = self.db.get_people()
        by_type = {}
        for p in people:
            t = p["relationship_type"]
            by_type[t] = by_type.get(t, 0) + 1

        # 本月互动次数
        today = date.today()
        month_start = today.replace(day=1)
        total_events = 0
        active_people = set()

        for p in people:
            events = self.db.get_events(p["id"], limit=100)
            for e in events:
                event_date = date.fromisoformat(e["event_date"]) if isinstance(e["event_date"], str) else e["event_date"]
                if event_date >= month_start:
                    total_events += 1
                    active_people.add(p["id"])

        return {
            "total_people": len(people),
            "by_type": by_type,
            "monthly_interactions": total_events,
            "active_this_month": len(active_people),
            "neglected": len(self.get_neglected_people()),
        }

    def generate_interaction_template(self, person_id: int) -> Optional[str]:
        """生成相处模板文本（手动版，非AI）"""
        detail = self.db.get_person(person_id)
        if not detail:
            return None

        lines = [f"━━━ {detail['name']} 的相处模板 ━━━\n"]

        # 性格标签
        if detail.get("personality_tags"):
            lines.append("【性格特点】")
            for tag in detail["personality_tags"]:
                if tag["category"] == "dimension":
                    dim = next((d for d in PERSONALITY_DIMENSIONS if d["name"] == tag["tag_name"]), None)
                    if dim:
                        if tag["tag_value"] <= 35:
                            lines.append(f"• 偏{dim['left']}")
                        elif tag["tag_value"] >= 65:
                            lines.append(f"• 偏{dim['right']}")
                        else:
                            lines.append(f"• {dim['left']}和{dim['right']}之间")
                elif tag["category"] == "communication":
                    lines.append(f"• {tag['tag_name']}")
                elif tag["category"] == "custom":
                    lines.append(f"• #{tag['tag_name']}")
            lines.append("")

        # 相处要点
        if detail.get("notes"):
            lines.append("【相处要点】")
            lines.append(detail["notes"])
            lines.append("")

        # 最近互动
        if detail.get("recent_events"):
            lines.append(f"【最近互动】（共{len(detail['recent_events'])}条）")
            for e in detail["recent_events"][:3]:
                lines.append(f"• {e['event_date']} - {e['event_description']}")
            lines.append("")

        return "\n".join(lines)
