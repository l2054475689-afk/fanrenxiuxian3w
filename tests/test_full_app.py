"""
全面 App 功能测试 v3 — 基于实际 API 签名
75 tests covering all features
"""
import os, sys, tempfile, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from database.db_manager import DatabaseManager
from services.spirit_service import SpiritService
from services.realm_service import RealmService
from services.lingshi_service import LingshiService
from services.tongyu_service import TongyuService
from services.panel_service import PanelService
from services.constants import *

TODAY = datetime.date.today()

@pytest.fixture
def db():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    d = DatabaseManager(f.name)
    yield d
    os.unlink(f.name)

@pytest.fixture
def full_db(db):
    db.init_user_config(1998)
    return db


# ============================================================
# 1. 引导流程
# ============================================================
class TestOnboarding:
    def test_init_config(self, db):
        db.init_user_config(1998)
        c = db.get_user_config()
        assert c["birth_year"] == 1998

    def test_no_config(self, db):
        assert db.get_user_config() is None

    def test_duplicate_init(self, full_db):
        full_db.init_user_config(2000)
        assert full_db.get_user_config() is not None


# ============================================================
# 2. 面板
# ============================================================
class TestPanel:
    def test_dashboard_structure(self, full_db):
        d = PanelService(full_db).get_dashboard()
        assert "blood" in d
        assert "spirit" in d
        assert "today" in d
        assert "lingshi" in d
        assert "realm" in d

    def test_blood_status(self, full_db):
        b = PanelService(full_db).get_blood_status()
        assert b["remaining_minutes"] > 0

    def test_weekly_trend(self, full_db):
        t = PanelService(full_db).get_weekly_trend()
        assert len(t) == 7

    def test_dashboard_with_data(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("冥想", 10, 5)
        s.complete_daily_task(1)
        d = PanelService(full_db).get_dashboard()
        assert d["spirit"]["value"] >= 10


# ============================================================
# 3. 心境
# ============================================================
class TestXinjing:
    def test_create_positive(self, full_db):
        s = SpiritService(full_db)
        r = s.create_positive_task("冥想", 10, 5)
        assert r["id"] == 1
        assert len(s.get_positive_tasks()) == 1

    def test_complete_daily(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("冥想", 10, 5)
        r = s.complete_daily_task(1)
        assert r["success"]
        assert s.get_spirit_status()["value"] == 10

    def test_complete_repeatable(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("喝水", 2, 1)
        assert s.complete_repeatable_task(1)["success"]

    def test_create_demon(self, full_db):
        s = SpiritService(full_db)
        r = s.create_demon_task("刷手机", 15, 10)
        assert r["id"] == 1
        assert len(s.get_demon_tasks()) == 1

    def test_record_demon(self, full_db):
        s = SpiritService(full_db)
        s.create_demon_task("刷手机", 15, 10)
        assert s.record_demon(1)["success"]
        assert s.get_spirit_status()["value"] == -15

    def test_undo(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("冥想", 10, 5)
        s.complete_daily_task(1)
        assert s.undo_task(1)["success"]

    def test_delete(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("冥想", 10, 5)
        assert s.delete_task(1) == True
        assert len(s.get_positive_tasks()) == 0

    def test_spirit_status_fields(self, full_db):
        st = SpiritService(full_db).get_spirit_status()
        assert "value" in st
        assert "level_name" in st
        assert "level_color" in st

    def test_trend(self, full_db):
        assert isinstance(SpiritService(full_db).get_spirit_trend(), list)

    def test_statistics(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("冥想", 10, 5)
        s.complete_daily_task(1)
        assert s.get_statistics() is not None

    def test_today_summary(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("冥想", 10, 5)
        s.complete_daily_task(1)
        assert s.get_today_summary() is not None

    def test_level_names(self):
        assert get_spirit_level(0) is not None
        assert get_spirit_level(-200) is not None
        assert get_spirit_level(640) is not None

    def test_bounds_max(self, full_db):
        s = SpiritService(full_db)
        for i in range(50):
            s.create_positive_task(f"t{i}", 50, 1)
        for i in range(1, 51):
            s.complete_daily_task(i)
        assert s.get_spirit_status()["value"] <= SPIRIT_MAX

    def test_bounds_min(self, full_db):
        s = SpiritService(full_db)
        for i in range(30):
            s.create_demon_task(f"d{i}", 50, 5)
        for i in range(1, 31):
            s.record_demon(i)
        assert s.get_spirit_status()["value"] >= SPIRIT_MIN

    def test_multi_complete(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("A", 10, 5)
        s.create_positive_task("B", 15, 8)
        s.create_positive_task("C", 8, 3)
        s.complete_daily_task(1)
        s.complete_daily_task(2)
        s.complete_daily_task(3)
        assert s.get_spirit_status()["value"] == 33

    def test_reorder(self, full_db):
        s = SpiritService(full_db)
        s.create_positive_task("A", 10, 5)
        s.create_positive_task("B", 10, 5)
        s.reorder_tasks([2, 1])  # returns None, just shouldn't crash


# ============================================================
# 4. 境界
# ============================================================
class TestJingjie:
    def test_create(self, full_db):
        assert RealmService(full_db).create_realm("练气期", "")["success"]

    def test_add_skill(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        assert r.add_skill(1, "打坐", "")["success"]

    def test_add_sub_task(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        assert r.add_sub_task(1, "第一周")["success"]

    def test_complete_sub(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        r.add_sub_task(1, "第一周")
        assert r.complete_sub_task(1)["success"]

    def test_uncomplete_sub(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        r.add_sub_task(1, "第一周")
        r.complete_sub_task(1)
        assert r.uncomplete_sub_task(1)["success"]

    def test_progress(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        r.add_sub_task(1, "t1")
        r.add_sub_task(1, "t2")
        r.complete_sub_task(1)
        p = r.get_realm_progress(1)
        assert p["overall_progress"] == 50.0

    def test_advance(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        r.add_sub_task(1, "唯一")
        r.complete_sub_task(1)
        assert r.advance_realm(1) is not None

    def test_active_main(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        assert r.get_active_main_realm() is not None

    def test_dungeon(self, full_db):
        r = RealmService(full_db)
        d = r.get_active_dungeon()
        assert d is None or isinstance(d, dict)

    def test_multi_skills(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        r.add_skill(1, "练剑", "")
        r.add_skill(1, "炼丹", "")
        assert len(r.get_active_main_realm()["skills"]) == 3

    def test_delete_skill(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        assert r.delete_skill(1)["success"]

    def test_delete_sub(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "")
        r.add_skill(1, "打坐", "")
        r.add_sub_task(1, "t1")
        assert r.delete_sub_task(1)["success"]

    def test_completed_realms(self, full_db):
        assert isinstance(RealmService(full_db).get_completed_realms(), list)

    def test_dungeon_realm(self, full_db):
        r = RealmService(full_db)
        r.create_realm("练气期", "主线")
        result = r.create_realm("副本1", "紧急", realm_type="dungeon")
        assert result["success"]
        d = r.get_active_dungeon()
        assert d is not None


# ============================================================
# 5. 灵石
# ============================================================
class TestLingshi:
    def test_income(self, full_db):
        assert LingshiService(full_db).add_income(5000, "工资", "月薪")["success"]

    def test_expense(self, full_db):
        assert LingshiService(full_db).add_expense(200, "餐饮", "午餐")["success"]

    def test_balance(self, full_db):
        l = LingshiService(full_db)
        l.add_income(5000, "工资")
        l.add_expense(200, "餐饮")
        l.add_expense(300, "交通")
        assert l.get_balance()["balance"] == 4500

    def test_transactions(self, full_db):
        l = LingshiService(full_db)
        l.add_income(5000, "工资")
        l.add_expense(200, "餐饮")
        assert len(l.get_transactions()) == 2

    def test_today_txns(self, full_db):
        l = LingshiService(full_db)
        l.add_income(5000, "工资")
        assert len(l.get_today_transactions()) >= 1

    def test_delete_txn(self, full_db):
        l = LingshiService(full_db)
        l.add_income(5000, "工资")
        assert l.delete_transaction(1)["success"]

    def test_budget(self, full_db):
        l = LingshiService(full_db)
        assert l.set_budget("餐饮", 2000)["success"]

    def test_budget_status(self, full_db):
        l = LingshiService(full_db)
        l.set_budget("餐饮", 2000)
        l.add_expense(500, "餐饮")
        l.add_expense(800, "餐饮")
        assert l.get_budget_status() is not None

    def test_debt(self, full_db):
        l = LingshiService(full_db)
        assert l.create_debt("信用卡", 10000, 500)["success"]

    def test_repay(self, full_db):
        l = LingshiService(full_db)
        l.create_debt("信用卡", 10000, 500)
        assert l.repay_debt(1, 3000)["success"]

    def test_debts_list(self, full_db):
        l = LingshiService(full_db)
        l.create_debt("信用卡", 10000, 500)
        assert len(l.get_debts()) >= 1

    def test_debt_summary(self, full_db):
        l = LingshiService(full_db)
        l.create_debt("信用卡", 10000, 500)
        assert l.get_debt_summary() is not None

    def test_goal(self, full_db):
        l = LingshiService(full_db)
        l.add_income(100000, "奖金")
        assert l.get_goal_progress() is not None

    def test_monthly(self, full_db):
        l = LingshiService(full_db)
        l.add_income(5000, "工资")
        assert l.get_monthly_summary() is not None

    def test_recurring(self, full_db):
        l = LingshiService(full_db)
        assert l.create_recurring("income", 15000, "工资")["success"]

    def test_apply_recurring(self, full_db):
        l = LingshiService(full_db)
        l.create_recurring("income", 15000, "工资")
        assert l.apply_recurring_transactions() is not None

    def test_negative_balance(self, full_db):
        l = LingshiService(full_db)
        l.add_expense(1000, "餐饮")
        assert l.get_balance()["balance"] == -1000


# ============================================================
# 6. 统御
# ============================================================
class TestTongyu:
    def test_create(self, full_db):
        assert TongyuService(full_db).create_person("张三", "朋友")["success"]

    def test_list(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        t.create_person("李四", "同事")
        assert len(t.get_people()) == 2

    def test_detail(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.get_person_detail(1)["name"] == "张三"

    def test_update(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.update_person(1, name="张三丰")["success"]

    def test_delete(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.delete_person(1)["success"]

    def test_event(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.add_event(1, TODAY, "一起吃饭")["success"]

    def test_events_list(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        t.add_event(1, TODAY, "吃饭")
        t.add_event(1, TODAY, "看电影")
        assert len(t.get_events(1)) == 2

    def test_delete_event(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        t.add_event(1, TODAY, "吃饭")
        assert t.delete_event(1)["success"]

    def test_personality(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.set_personality_dimension(1, "外向", 80)["success"]

    def test_custom_tag(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.add_custom_tag(1, "吃货")["success"]

    def test_remove_tag(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        t.add_custom_tag(1, "吃货")
        assert t.remove_custom_tag(1, "吃货")["success"]

    def test_comm_style(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.set_communication_style(1, ["直接了当"])["success"]

    def test_template(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.generate_interaction_template(1) is not None

    def test_neglected(self, full_db):
        assert isinstance(TongyuService(full_db).get_neglected_people(), list)

    def test_stats(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        assert t.get_relationship_stats() is not None

    def test_birthdays(self, full_db):
        assert isinstance(TongyuService(full_db).get_upcoming_birthdays(), list)

    def test_delete_with_events(self, full_db):
        t = TongyuService(full_db)
        t.create_person("张三", "朋友")
        t.add_event(1, TODAY, "吃饭")
        assert t.delete_person(1)["success"]


# ============================================================
# 7. 设置
# ============================================================
class TestSettings:
    def test_config(self, full_db):
        c = full_db.get_user_config()
        assert "birth_year" in c


# ============================================================
# 8. UI 导入
# ============================================================
class TestUI:
    def test_pages(self):
        from ui.pages.panel_page import PanelPage
        from ui.pages.xinjing_page import XinjingPage
        from ui.pages.jingjie_page import JingjiePage
        from ui.pages.lingshi_page import LingshiPage
        from ui.pages.tongyu_page import TongyuPage
        from ui.pages.settings_page import SettingsPage

    def test_styles(self):
        from ui.styles import (
            card_container, gradient_card, section_title,
            ALIGN_CENTER, XiuxianColors, gradient_purple_gold,
            shadow_glow, styled_textfield, primary_button,
        )

    def test_main(self):
        import main


# ============================================================
# 9. 完整旅程
# ============================================================
class TestJourney:
    def test_full(self, db):
        db.init_user_config(1998)

        # 心境
        s = SpiritService(db)
        s.create_positive_task("冥想", 10, 5)
        s.create_positive_task("运动", 15, 8)
        s.create_demon_task("刷手机", 15, 10)
        s.complete_daily_task(1)
        s.complete_daily_task(2)
        s.record_demon(3)

        # 境界
        r = RealmService(db)
        r.create_realm("练气期", "基础修炼")
        r.add_skill(1, "打坐", "")
        r.add_sub_task(1, "第一周")
        r.add_sub_task(1, "第二周")
        r.complete_sub_task(1)

        # 灵石
        l = LingshiService(db)
        l.add_income(15000, "工资", "1月")
        l.add_expense(3000, "房租")
        l.add_expense(500, "餐饮")
        l.set_budget("餐饮", 2000)
        l.create_debt("信用卡", 5000, 500)
        l.repay_debt(1, 1000)

        # 统御
        t = TongyuService(db)
        t.create_person("张三", "朋友")
        t.add_event(1, TODAY, "一起吃饭")
        t.set_personality_dimension(1, "外向", 80)

        # 面板
        d = PanelService(db).get_dashboard()
        assert d is not None
        assert d["blood"]["remaining_days"] > 0
        assert d["spirit"]["value"] == 10  # 10+15-15
        assert l.get_balance()["balance"] == 11500
        assert r.get_realm_progress(1)["overall_progress"] == 50.0

        print(f"\n✅ 完整旅程通过！血量{d['blood']['remaining_days']}天 心境{d['spirit']['value']} 灵石{l.get_balance()['balance']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
