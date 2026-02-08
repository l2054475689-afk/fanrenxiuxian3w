"""
数据库管理器测试 — 验证所有 CRUD 操作
"""
import sys
import os
import pytest
from datetime import date, datetime, timedelta

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager


@pytest.fixture
def db():
    """每个测试用独立的内存数据库"""
    manager = DatabaseManager(":memory:")
    manager.init_user_config(birth_year=1998)
    return manager


class TestUserConfig:
    """用户配置测试"""

    def test_init_user_config(self, db):
        config = db.get_user_config()
        assert config is not None
        assert config["birth_year"] == 1998
        assert config["current_spirit"] == 0
        assert config["initial_blood"] > 0
        assert config["current_blood"] == config["initial_blood"]
        assert config["target_money"] == 5_000_000

    def test_init_blood_calculation(self, db):
        """血量 = (80 - 年龄) * 365 * 24 * 60"""
        config = db.get_user_config()
        age = datetime.now().year - 1998
        expected = (80 - age) * 365 * 24 * 60
        assert config["initial_blood"] == expected

    def test_update_spirit(self, db):
        new_val = db.update_spirit(50)
        assert new_val == 50
        config = db.get_user_config()
        assert config["current_spirit"] == 50

    def test_spirit_clamp_max(self, db):
        new_val = db.update_spirit(9999)
        assert new_val == 640  # SPIRIT_MAX

    def test_spirit_clamp_min(self, db):
        new_val = db.update_spirit(-9999)
        assert new_val == -200  # SPIRIT_MIN

    def test_update_blood(self, db):
        config = db.get_user_config()
        original = config["current_blood"]
        new_val = db.update_blood(-100)
        assert new_val == original - 100

    def test_blood_cannot_go_negative(self, db):
        new_val = db.update_blood(-999_999_999)
        assert new_val == 0


class TestTasks:
    """任务 CRUD 测试"""

    def test_create_positive_task(self, db):
        task = db.create_task("早起", "positive", spirit_effect=1, emoji="🌅")
        assert task["name"] == "早起"
        assert task["task_type"] == "positive"
        assert task["spirit_effect"] == 1
        assert task["emoji"] == "🌅"

    def test_create_demon_task(self, db):
        task = db.create_task("刷手机", "demon", spirit_effect=-3, submission_type="repeatable")
        assert task["task_type"] == "demon"
        assert task["spirit_effect"] == -3

    def test_get_tasks_by_type(self, db):
        db.create_task("早起", "positive", spirit_effect=1)
        db.create_task("冥想", "positive", spirit_effect=2)
        db.create_task("刷手机", "demon", spirit_effect=-3)

        positive = db.get_tasks_by_type("positive")
        demon = db.get_tasks_by_type("demon")
        assert len(positive) == 2
        assert len(demon) == 1

    def test_delete_task_soft(self, db):
        task = db.create_task("测试", "positive", spirit_effect=1)
        result = db.delete_task(task["id"])
        assert result is True
        # 软删除后不在列表中
        tasks = db.get_tasks_by_type("positive")
        assert len(tasks) == 0

    def test_reorder_tasks(self, db):
        t1 = db.create_task("A", "positive", spirit_effect=1)
        t2 = db.create_task("B", "positive", spirit_effect=1)
        t3 = db.create_task("C", "positive", spirit_effect=1)
        db.reorder_tasks([t3["id"], t1["id"], t2["id"]])
        tasks = db.get_tasks_by_type("positive")
        assert tasks[0]["name"] == "C"
        assert tasks[1]["name"] == "A"
        assert tasks[2]["name"] == "B"


class TestTaskRecords:
    """任务记录测试"""

    def test_complete_task(self, db):
        task = db.create_task("早起", "positive", spirit_effect=5, blood_effect=1)
        result = db.add_task_record(task["id"], "早起", 5, 1)
        assert result["spirit_change"] == 5
        assert result["new_spirit"] == 5

    def test_complete_demon_task(self, db):
        task = db.create_task("刷手机", "demon", spirit_effect=-3)
        result = db.add_task_record(task["id"], "刷手机", -3, 0)
        assert result["new_spirit"] == -3

    def test_undo_task_record(self, db):
        task = db.create_task("早起", "positive", spirit_effect=5, blood_effect=2)
        record = db.add_task_record(task["id"], "早起", 5, 2)
        undo = db.undo_task_record(record["id"])
        assert undo is not None
        assert undo["new_spirit"] == 0
        assert undo["reverted_spirit"] == 5

    def test_undo_only_today(self, db):
        """只能撤销当天的记录"""
        task = db.create_task("早起", "positive", spirit_effect=5)
        record = db.add_task_record(task["id"], "早起", 5, 0)
        # 当天可以撤销
        undo = db.undo_task_record(record["id"])
        assert undo is not None

    def test_is_task_completed_today(self, db):
        task = db.create_task("早起", "positive", spirit_effect=1)
        assert db.is_task_completed_today(task["id"]) is False
        db.add_task_record(task["id"], "早起", 1, 0)
        assert db.is_task_completed_today(task["id"]) is True

    def test_today_records(self, db):
        task = db.create_task("早起", "positive", spirit_effect=1)
        db.add_task_record(task["id"], "早起", 1, 0)
        records = db.get_today_records()
        assert len(records) == 1
        assert records[0]["task_name"] == "早起"


class TestStreak:
    """连续打卡测试"""

    def test_first_streak(self, db):
        task = db.create_task("冥想", "positive", spirit_effect=1, enable_streak=True)
        streak = db.update_streak(task["id"])
        assert streak["current_streak"] == 1
        assert streak["max_streak"] == 1

    def test_consecutive_streak(self, db):
        task = db.create_task("冥想", "positive", spirit_effect=1, enable_streak=True)
        db.update_streak(task["id"])
        streak = db.get_streak(task["id"])
        assert streak["current_streak"] == 1


class TestRealm:
    """境界系统测试"""

    def test_create_realm(self, db):
        realm = db.create_realm("练气期", description="掌握基础")
        assert realm["name"] == "练气期"
        assert realm["status"] == "active"
        assert realm["realm_type"] == "main"

    def test_create_dungeon_realm(self, db):
        realm = db.create_realm("突发副本", realm_type="dungeon")
        assert realm["realm_type"] == "dungeon"

    def test_get_active_realm(self, db):
        db.create_realm("练气期")
        active = db.get_active_realm()
        assert active is not None
        assert active["name"] == "练气期"

    def test_skill_and_subtask(self, db):
        realm = db.create_realm("练气期")
        skill = db.create_skill(realm["id"], "高等数学")
        sub1 = db.create_sub_task(skill["id"], "函数定义")
        sub2 = db.create_sub_task(skill["id"], "极限")

        # 完成子任务
        result = db.complete_sub_task(sub1["id"])
        assert result["progress"] == 0.5
        assert result["skill_completed"] is False

        result = db.complete_sub_task(sub2["id"])
        assert result["progress"] == 1.0
        assert result["skill_completed"] is True

    def test_realm_with_skills(self, db):
        realm = db.create_realm("练气期")
        db.create_skill(realm["id"], "数学")
        db.create_skill(realm["id"], "编程")
        active = db.get_active_realm()
        assert len(active["skills"]) == 2

    def test_complete_realm(self, db):
        realm = db.create_realm("练气期")
        result = db.complete_realm(realm["id"])
        assert result["status"] == "completed"
        assert result["completed_at"] is not None
        # 完成后不再是活跃境界
        active = db.get_active_realm()
        assert active is None


class TestLingshi:
    """灵石系统测试"""

    def test_add_income(self, db):
        txn = db.add_transaction("income", 10000, "工资", "月薪")
        assert txn["type"] == "income"
        assert txn["amount"] == 10000

    def test_add_expense(self, db):
        txn = db.add_transaction("expense", 50, "餐饮", "午饭")
        assert txn["type"] == "expense"
        assert txn["amount"] == 50

    def test_balance(self, db):
        db.add_transaction("income", 10000, "工资")
        db.add_transaction("expense", 3000, "居住")
        db.add_transaction("expense", 500, "餐饮")
        balance = db.get_balance()
        assert balance["income"] == 10000
        assert balance["expense"] == 3500
        assert balance["balance"] == 6500

    def test_get_transactions(self, db):
        db.add_transaction("income", 10000, "工资")
        db.add_transaction("expense", 50, "餐饮")
        txns = db.get_transactions()
        assert len(txns) == 2

    def test_budget(self, db):
        db.set_budget("餐饮", 2000, "2026-02")
        db.set_budget("交通", 500, "2026-02")
        budgets = db.get_budgets("2026-02")
        assert len(budgets) == 2

    def test_debt(self, db):
        debt = db.create_debt("房贷", 1_000_000, 5000, interest_rate=3.5)
        assert debt["total_amount"] == 1_000_000
        assert debt["remaining_amount"] == 1_000_000
        debts = db.get_debts()
        assert len(debts) == 1


class TestTongyu:
    """统御系统测试"""

    def test_create_person(self, db):
        person = db.create_person("张三", "朋友", avatar_emoji="😎")
        assert person["name"] == "张三"
        assert person["relationship_type"] == "朋友"
        assert person["avatar_emoji"] == "😎"

    def test_get_people(self, db):
        db.create_person("张三", "朋友")
        db.create_person("李四", "同事")
        people = db.get_people()
        assert len(people) == 2

    def test_add_event(self, db):
        person = db.create_person("张三", "朋友")
        event = db.add_event(
            person["id"], date.today(), "一起吃饭",
            location="星巴克", key_info="他想学Python"
        )
        assert event["event_description"] == "一起吃饭"
        assert event["location"] == "星巴克"

    def test_get_events(self, db):
        person = db.create_person("张三", "朋友")
        db.add_event(person["id"], date.today(), "事件1")
        db.add_event(person["id"], date.today(), "事件2")
        events = db.get_events(person["id"])
        assert len(events) == 2

    def test_person_detail_with_events(self, db):
        person = db.create_person("张三", "朋友")
        db.add_event(person["id"], date.today(), "吃饭")
        detail = db.get_person(person["id"])
        assert "recent_events" in detail
        assert len(detail["recent_events"]) == 1


class TestAIConfig:
    """AI 配置测试"""

    def test_save_and_get(self, db):
        db.save_ai_config("openai", api_key="sk-test", model="gpt-4")
        config = db.get_active_ai_config()
        assert config["provider"] == "openai"
        assert config["api_key"] == "sk-test"

    def test_switch_provider(self, db):
        db.save_ai_config("openai", api_key="sk-1")
        db.save_ai_config("qianwen", api_key="sk-2")
        config = db.get_active_ai_config()
        assert config["provider"] == "qianwen"
