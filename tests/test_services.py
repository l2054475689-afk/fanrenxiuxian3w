"""
Service 层测试 — 验证业务逻辑
"""
import sys
import os
import pytest
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from services.spirit_service import SpiritService
from services.realm_service import RealmService
from services.lingshi_service import LingshiService
from services.tongyu_service import TongyuService
from services.panel_service import PanelService


@pytest.fixture
def db():
    manager = DatabaseManager(":memory:")
    manager.init_user_config(birth_year=1998)
    return manager


@pytest.fixture
def spirit(db):
    return SpiritService(db)


@pytest.fixture
def realm(db):
    return RealmService(db)


@pytest.fixture
def lingshi(db):
    return LingshiService(db)


@pytest.fixture
def tongyu(db):
    return TongyuService(db)


@pytest.fixture
def panel(db):
    return PanelService(db)


# ============ 心境系统 ============

class TestSpiritService:

    def test_create_positive_task(self, spirit):
        task = spirit.create_positive_task("早起", spirit_effect=1, emoji="🌅")
        assert task["name"] == "早起"
        assert task["spirit_effect"] == 1

    def test_create_positive_rejects_negative(self, spirit):
        with pytest.raises(ValueError):
            spirit.create_positive_task("坏任务", spirit_effect=-5)

    def test_create_demon_task_forces_negative(self, spirit):
        task = spirit.create_demon_task("刷手机", spirit_effect=3)
        assert task["spirit_effect"] == -3

    def test_complete_daily_task(self, spirit):
        task = spirit.create_positive_task("早起", spirit_effect=5)
        result = spirit.complete_daily_task(task["id"])
        assert result["success"] is True
        assert result["record"]["new_spirit"] == 5

    def test_daily_task_once_per_day(self, spirit):
        task = spirit.create_positive_task("早起", spirit_effect=5)
        spirit.complete_daily_task(task["id"])
        result = spirit.complete_daily_task(task["id"])
        assert result["success"] is False
        assert "已完成" in result["message"]

    def test_repeatable_task_multiple_times(self, spirit):
        task = spirit.create_positive_task("冥想", spirit_effect=2, submission_type="repeatable")
        r1 = spirit.complete_repeatable_task(task["id"])
        r2 = spirit.complete_repeatable_task(task["id"])
        assert r1["success"] is True
        assert r2["success"] is True
        assert r2["record"]["new_spirit"] == 4

    def test_record_demon(self, spirit):
        task = spirit.create_demon_task("刷手机", spirit_effect=3)
        result = spirit.record_demon(task["id"])
        assert result["success"] is True
        assert result["record"]["new_spirit"] == -3

    def test_undo_task(self, spirit):
        task = spirit.create_positive_task("早起", spirit_effect=5)
        result = spirit.complete_daily_task(task["id"])
        undo = spirit.undo_task(result["record"]["id"])
        assert undo["success"] is True
        status = spirit.get_spirit_status()
        assert status["value"] == 0

    def test_spirit_status(self, spirit):
        status = spirit.get_spirit_status()
        assert status is not None
        assert status["value"] == 0
        assert status["level_name"] == "心平气和"

    def test_today_summary(self, spirit):
        task = spirit.create_positive_task("早起", spirit_effect=5)
        spirit.complete_daily_task(task["id"])
        summary = spirit.get_today_summary()
        assert summary["positive_count"] == 1
        assert summary["total_spirit_change"] == 5

    def test_statistics(self, spirit):
        task = spirit.create_positive_task("早起", spirit_effect=5)
        spirit.complete_daily_task(task["id"])
        stats = spirit.get_statistics(days=7)
        assert stats["positive_total"] == 5
        assert stats["positive_count"] == 1

    def test_streak_tracking(self, spirit):
        task = spirit.create_positive_task("冥想", spirit_effect=1, enable_streak=True)
        result = spirit.complete_daily_task(task["id"])
        assert result["streak"] is not None
        assert result["streak"]["current_streak"] == 1


# ============ 境界系统 ============

class TestRealmService:

    def test_create_main_realm(self, realm):
        result = realm.create_realm("练气期", description="掌握基础")
        assert result["success"] is True
        assert result["realm"]["name"] == "练气期"

    def test_cannot_create_duplicate_active(self, realm):
        realm.create_realm("练气期")
        result = realm.create_realm("筑基期")
        assert result["success"] is False

    def test_create_dungeon(self, realm):
        realm.create_realm("练气期")
        result = realm.create_realm("突发副本", realm_type="dungeon")
        assert result["success"] is True

    def test_full_workflow(self, realm):
        """完整流程：创建境界→添加技能→添加子任务→完成→晋升"""
        r = realm.create_realm("练气期", reward_spirit=10)
        realm_id = r["realm"]["id"]

        sk = realm.add_skill(realm_id, "高等数学")
        skill_id = sk["skill"]["id"]

        s1 = realm.add_sub_task(skill_id, "函数定义")
        s2 = realm.add_sub_task(skill_id, "极限")

        # 完成子任务
        result = realm.complete_sub_task(s1["sub_task"]["id"])
        assert result["skill_progress"] == 0.5
        assert result["realm_ready_to_advance"] is False

        result = realm.complete_sub_task(s2["sub_task"]["id"])
        assert result["skill_completed"] is True
        assert result["realm_ready_to_advance"] is True

        # 晋升
        advance = realm.advance_realm(realm_id)
        assert advance["success"] is True
        assert "圆满" in advance["message"]

    def test_realm_progress(self, realm):
        r = realm.create_realm("练气期")
        realm_id = r["realm"]["id"]
        sk = realm.add_skill(realm_id, "数学")
        realm.add_sub_task(sk["skill"]["id"], "任务1")
        realm.add_sub_task(sk["skill"]["id"], "任务2")

        progress = realm.get_realm_progress(realm_id)
        assert progress["total_sub_tasks"] == 2
        assert progress["completed_sub_tasks"] == 0
        assert progress["overall_progress"] == 0

    def test_uncomplete_sub_task(self, realm):
        r = realm.create_realm("练气期")
        sk = realm.add_skill(r["realm"]["id"], "数学")
        s1 = realm.add_sub_task(sk["skill"]["id"], "任务1")
        realm.complete_sub_task(s1["sub_task"]["id"])
        result = realm.uncomplete_sub_task(s1["sub_task"]["id"])
        assert result["success"] is True

    def test_advance_fails_if_incomplete(self, realm):
        r = realm.create_realm("练气期")
        realm_id = r["realm"]["id"]
        sk = realm.add_skill(realm_id, "数学")
        realm.add_sub_task(sk["skill"]["id"], "任务1")
        result = realm.advance_realm(realm_id)
        assert result["success"] is False


# ============ 灵石系统 ============

class TestLingshiService:

    def test_add_income(self, lingshi):
        result = lingshi.add_income(10000, "工资", "月薪")
        assert result["success"] is True

    def test_add_expense(self, lingshi):
        result = lingshi.add_expense(50, "餐饮", "午饭")
        assert result["success"] is True

    def test_reject_zero_amount(self, lingshi):
        result = lingshi.add_income(0, "工资")
        assert result["success"] is False

    def test_balance(self, lingshi):
        lingshi.add_income(10000, "工资")
        lingshi.add_expense(3000, "居住")
        balance = lingshi.get_balance()
        assert balance["balance"] == 7000

    def test_budget_warning(self, lingshi):
        lingshi.set_budget("餐饮", 1000)
        # 花超预算
        for _ in range(11):
            lingshi.add_expense(100, "餐饮")
        result = lingshi.add_expense(100, "餐饮")
        assert "超支" in result["message"]

    def test_budget_status(self, lingshi):
        lingshi.set_budget("餐饮", 2000)
        lingshi.add_expense(500, "餐饮")
        status = lingshi.get_budget_status()
        assert len(status["categories"]) == 1
        assert status["categories"][0]["spent"] == 500

    def test_debt_and_repay(self, lingshi):
        lingshi.create_debt("房贷", 1_000_000, 5000)
        debts = lingshi.get_debts()
        assert len(debts) == 1

        result = lingshi.repay_debt(debts[0]["id"], 5000)
        assert result["remaining"] == 995000

    def test_monthly_summary(self, lingshi):
        lingshi.add_income(10000, "工资")
        lingshi.add_expense(500, "餐饮")
        lingshi.add_expense(3000, "居住")
        summary = lingshi.get_monthly_summary()
        assert summary["income_total"] == 10000
        assert summary["expense_total"] == 3500

    def test_goal_progress(self, lingshi):
        lingshi.add_income(100000, "工资")
        progress = lingshi.get_goal_progress()
        assert progress["current"] == 100000
        assert progress["next_milestone"] == 500_000

    def test_delete_transaction(self, lingshi):
        result = lingshi.add_income(1000, "工资")
        txn_id = result["transaction"]["id"]
        del_result = lingshi.delete_transaction(txn_id)
        assert del_result["success"] is True


# ============ 统御系统 ============

class TestTongyuService:

    def test_create_person(self, tongyu):
        result = tongyu.create_person("张三", "朋友", avatar_emoji="😎")
        assert result["success"] is True
        assert result["person"]["name"] == "张三"

    def test_reject_empty_name(self, tongyu):
        result = tongyu.create_person("", "朋友")
        assert result["success"] is False

    def test_update_person(self, tongyu):
        p = tongyu.create_person("张三", "朋友")
        result = tongyu.update_person(p["person"]["id"], notes="好人")
        assert result["success"] is True

    def test_delete_person(self, tongyu):
        p = tongyu.create_person("张三", "朋友")
        result = tongyu.delete_person(p["person"]["id"])
        assert result["success"] is True
        people = tongyu.get_people()
        assert len(people) == 0

    def test_personality_dimension(self, tongyu):
        p = tongyu.create_person("张三", "朋友")
        tongyu.set_personality_dimension(p["person"]["id"], "内向-外向", 75)
        detail = tongyu.get_person_detail(p["person"]["id"])
        tags = detail["personality_tags"]
        assert len(tags) == 1
        assert tags[0]["tag_value"] == 75

    def test_communication_style(self, tongyu):
        p = tongyu.create_person("张三", "朋友")
        tongyu.set_communication_style(p["person"]["id"], ["直接坦率", "话少沉默"])
        detail = tongyu.get_person_detail(p["person"]["id"])
        comm_tags = [t for t in detail["personality_tags"] if t["category"] == "communication"]
        assert len(comm_tags) == 2

    def test_add_event(self, tongyu):
        p = tongyu.create_person("张三", "朋友")
        result = tongyu.add_event(
            p["person"]["id"], date.today(), "一起吃饭",
            location="星巴克", impression_tags=["愉快", "深入"],
        )
        assert result["success"] is True

    def test_neglected_people(self, tongyu):
        tongyu.create_person("张三", "朋友")
        neglected = tongyu.get_neglected_people(days_threshold=0)
        assert len(neglected) == 1

    def test_relationship_stats(self, tongyu):
        tongyu.create_person("张三", "朋友")
        tongyu.create_person("李四", "同事")
        stats = tongyu.get_relationship_stats()
        assert stats["total_people"] == 2

    def test_interaction_template(self, tongyu):
        p = tongyu.create_person("张三", "朋友")
        tongyu.set_personality_dimension(p["person"]["id"], "内向-外向", 20)
        tongyu.add_event(p["person"]["id"], date.today(), "吃饭聊天")
        template = tongyu.generate_interaction_template(p["person"]["id"])
        assert "张三" in template
        assert "偏内向" in template


# ============ 面板系统 ============

class TestPanelService:

    def test_blood_status(self, panel):
        blood = panel.get_blood_status()
        assert blood is not None
        assert blood["remaining_minutes"] > 0
        assert blood["is_alive"] is True

    def test_dashboard(self, panel, db):
        # 添加一些数据
        spirit = SpiritService(db)
        task = spirit.create_positive_task("早起", spirit_effect=5)
        spirit.complete_daily_task(task["id"])

        dashboard = panel.get_dashboard()
        assert dashboard is not None
        assert dashboard["spirit"]["value"] == 5
        assert dashboard["today"]["positive_count"] == 1

    def test_weekly_trend(self, panel, db):
        spirit = SpiritService(db)
        task = spirit.create_positive_task("早起", spirit_effect=5)
        spirit.complete_daily_task(task["id"])

        trend = panel.get_weekly_trend()
        assert len(trend) == 7
        # 今天应该有数据
        assert trend[-1]["positive"] == 5
