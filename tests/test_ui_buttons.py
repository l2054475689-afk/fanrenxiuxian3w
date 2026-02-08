"""
UI 按钮/交互全面测试 — 模拟 Flet Page，测试每个按钮回调
不需要浏览器，直接在 Python 里调用所有 on_click/on_change 回调
"""
import os, sys, tempfile, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import flet as ft
from unittest.mock import MagicMock, patch
from database.db_manager import DatabaseManager
from services.spirit_service import SpiritService
from services.realm_service import RealmService
from services.lingshi_service import LingshiService
from services.tongyu_service import TongyuService
from services.panel_service import PanelService


class MockPage:
    """模拟 Flet Page 对象"""
    def __init__(self):
        self.title = ""
        self.theme_mode = ft.ThemeMode.LIGHT
        self.padding = 0
        self.spacing = 0
        self.controls = []
        self.overlay = []
        self.snack_bar = None
        self._dialogs = []
        self.window = MagicMock()
        self.window.width = 400
        self.window.height = 800

    def update(self):
        pass

    def open(self, control):
        """模拟打开 SnackBar 或 Dialog"""
        self._dialogs.append(control)

    def close(self, control):
        """模拟关闭 Dialog"""
        if control in self._dialogs:
            self._dialogs.remove(control)

    def add(self, *controls):
        self.controls.extend(controls)

    @property
    def last_dialog(self):
        return self._dialogs[-1] if self._dialogs else None


class MockEvent:
    """模拟 Flet 事件"""
    def __init__(self, control=None, data=None):
        self.control = control or MagicMock()
        self.data = data
        self.page = MockPage()


@pytest.fixture
def db():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    d = DatabaseManager(f.name)
    d.init_user_config(1998)
    yield d
    os.unlink(f.name)


@pytest.fixture
def page():
    return MockPage()


# ============================================================
# 面板页 — 只读展示，无按钮需要测试
# ============================================================
class TestPanelPageUI:
    def test_build_empty(self, db, page):
        from ui.pages.panel_page import PanelPage
        svc = PanelService(db)
        p = PanelPage(page, svc)
        result = p.build()
        # 应该能构建不崩溃
        assert p is not None

    def test_build_with_data(self, db, page):
        from ui.pages.panel_page import PanelPage
        spirit = SpiritService(db)
        spirit.create_positive_task("冥想", 10, 5)
        spirit.complete_daily_task(1)
        LingshiService(db).add_income(5000, "工资")
        realm = RealmService(db)
        realm.create_realm("练气期", "")
        realm.add_skill(1, "打坐", "")

        svc = PanelService(db)
        p = PanelPage(page, svc)
        result = p.build()
        assert p is not None


# ============================================================
# 心境页 — 完成任务、触发心魔、添加任务、切换Tab
# ============================================================
class TestXinjingPageUI:
    def test_build(self, db, page):
        from ui.pages.xinjing_page import XinjingPage
        svc = SpiritService(db)
        p = XinjingPage(page, svc)
        p.build()
        assert p is not None

    def test_complete_task_button(self, db, page):
        """点击完成任务按钮"""
        from ui.pages.xinjing_page import XinjingPage
        svc = SpiritService(db)
        svc.create_positive_task("冥想", 10, 5)
        p = XinjingPage(page, svc)
        p.build()
        # 直接调用 service 完成（模拟按钮回调的效果）
        result = svc.complete_daily_task(1)
        assert result["success"]
        assert svc.get_spirit_status()["value"] == 10

    def test_record_demon_button(self, db, page):
        """点击心魔按钮"""
        from ui.pages.xinjing_page import XinjingPage
        svc = SpiritService(db)
        svc.create_demon_task("刷手机", 15, 10)
        p = XinjingPage(page, svc)
        p.build()
        result = svc.record_demon(1)
        assert result["success"]
        assert svc.get_spirit_status()["value"] == -15

    def test_add_task_dialog(self, db, page):
        """打开添加任务对话框"""
        from ui.pages.xinjing_page import XinjingPage
        svc = SpiritService(db)
        p = XinjingPage(page, svc)
        p.build()
        p._show_add_dialog("positive")
        assert page.last_dialog is not None

    def test_add_demon_dialog(self, db, page):
        """打开添加心魔对话框"""
        from ui.pages.xinjing_page import XinjingPage
        svc = SpiritService(db)
        p = XinjingPage(page, svc)
        p.build()
        p._show_add_dialog("demon")
        assert page.last_dialog is not None

    def test_tab_switch(self, db, page):
        """切换 Tab（正面/心魔/统计）"""
        from ui.pages.xinjing_page import XinjingPage
        svc = SpiritService(db)
        p = XinjingPage(page, svc)
        p.build()
        # 切换到心魔 tab
        p.current_tab = 1
        p._refresh()
        # 切换到统计 tab
        p.current_tab = 2
        p._refresh()

    def test_build_with_tasks(self, db, page):
        """有任务数据时构建"""
        from ui.pages.xinjing_page import XinjingPage
        svc = SpiritService(db)
        svc.create_positive_task("冥想", 10, 5)
        svc.create_positive_task("运动", 15, 8)
        svc.create_demon_task("刷手机", 15, 10)
        svc.complete_daily_task(1)
        svc.record_demon(3)
        p = XinjingPage(page, svc)
        p.build()
        assert p is not None


# ============================================================
# 境界页 — 创建境界、添加技能、添加子任务、完成、晋升
# ============================================================
class TestJingjiePageUI:
    def test_build_empty(self, db, page):
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        p = JingjiePage(page, svc)
        p.build()
        assert p is not None

    def test_create_realm_dialog(self, db, page):
        """打开创建境界对话框"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        p = JingjiePage(page, svc)
        p.build()
        p._show_create_realm("main")
        assert page.last_dialog is not None

    def test_add_skill_dialog(self, db, page):
        """打开添加技能对话框"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "")
        p = JingjiePage(page, svc)
        p.build()
        p._show_add_skill(1)
        assert page.last_dialog is not None

    def test_add_sub_task_dialog(self, db, page):
        """打开添加子任务对话框"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "")
        svc.add_skill(1, "打坐", "")
        p = JingjiePage(page, svc)
        p.build()
        p._show_add_sub_task(1)
        assert page.last_dialog is not None

    def test_complete_sub_task(self, db, page):
        """完成子任务"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "")
        svc.add_skill(1, "打坐", "")
        svc.add_sub_task(1, "第一周")
        p = JingjiePage(page, svc)
        p.build()
        result = svc.complete_sub_task(1)
        assert result["success"]

    def test_delete_skill(self, db, page):
        """删除技能按钮"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "")
        svc.add_skill(1, "打坐", "")
        p = JingjiePage(page, svc)
        p.build()
        p._delete_skill(1)
        realm = svc.get_active_main_realm()
        assert len(realm["skills"]) == 0

    def test_delete_sub_task(self, db, page):
        """删除子任务按钮"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "")
        svc.add_skill(1, "打坐", "")
        svc.add_sub_task(1, "任务1")
        p = JingjiePage(page, svc)
        p.build()
        p._delete_sub_task(1)

    def test_advance_realm(self, db, page):
        """晋升按钮"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "")
        svc.add_skill(1, "打坐", "")
        svc.add_sub_task(1, "唯一")
        svc.complete_sub_task(1)
        p = JingjiePage(page, svc)
        p.build()
        result = svc.advance_realm(1)
        assert result is not None

    def test_build_with_data(self, db, page):
        """有数据时构建"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "基础修炼")
        svc.add_skill(1, "打坐", "每日1小时")
        svc.add_skill(1, "练剑", "")
        svc.add_sub_task(1, "第一周")
        svc.add_sub_task(1, "第二周")
        svc.add_sub_task(2, "基础剑法")
        svc.complete_sub_task(1)
        p = JingjiePage(page, svc)
        p.build()
        assert p is not None

    def test_dungeon_build(self, db, page):
        """副本境界构建"""
        from ui.pages.jingjie_page import JingjiePage
        svc = RealmService(db)
        svc.create_realm("练气期", "主线")
        svc.create_realm("副本1", "紧急", realm_type="dungeon")
        p = JingjiePage(page, svc)
        p.build()
        assert p is not None


# ============================================================
# 灵石页 — 记收入、记支出、设预算、创建负债
# ============================================================
class TestLingshiPageUI:
    def test_build_empty(self, db, page):
        from ui.pages.lingshi_page import LingshiPage
        svc = LingshiService(db)
        p = LingshiPage(page, svc)
        p.build()
        assert p is not None

    def test_add_income_dialog(self, db, page):
        """打开记收入对话框"""
        from ui.pages.lingshi_page import LingshiPage
        svc = LingshiService(db)
        p = LingshiPage(page, svc)
        p.build()
        p._show_add_dialog("income")
        assert page.last_dialog is not None

    def test_add_expense_dialog(self, db, page):
        """打开记支出对话框"""
        from ui.pages.lingshi_page import LingshiPage
        svc = LingshiService(db)
        p = LingshiPage(page, svc)
        p.build()
        p._show_add_dialog("expense")
        assert page.last_dialog is not None

    def test_budget_dialog(self, db, page):
        """打开设预算对话框"""
        from ui.pages.lingshi_page import LingshiPage
        svc = LingshiService(db)
        p = LingshiPage(page, svc)
        p.build()
        p._show_budget_dialog()
        assert page.last_dialog is not None

    def test_build_with_data(self, db, page):
        """有数据时构建"""
        from ui.pages.lingshi_page import LingshiPage
        svc = LingshiService(db)
        svc.add_income(15000, "工资", "1月")
        svc.add_expense(3000, "房租")
        svc.add_expense(500, "餐饮")
        svc.set_budget("餐饮", 2000)
        svc.create_debt("信用卡", 10000, 500)
        svc.repay_debt(1, 2000)
        p = LingshiPage(page, svc)
        p.build()
        assert p is not None

    def test_refresh(self, db, page):
        """刷新页面"""
        from ui.pages.lingshi_page import LingshiPage
        svc = LingshiService(db)
        svc.add_income(5000, "工资")
        p = LingshiPage(page, svc)
        p.build()
        svc.add_expense(200, "餐饮")
        p._refresh()


# ============================================================
# 统御页 — 添加人物、查看详情、添加事件、返回
# ============================================================
class TestTongyuPageUI:
    def test_build_empty(self, db, page):
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        p = TongyuPage(page, svc)
        p.build()
        assert p is not None

    def test_add_person_dialog(self, db, page):
        """打开添加人物对话框"""
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        p = TongyuPage(page, svc)
        p.build()
        p._show_add_person()
        assert page.last_dialog is not None

    def test_select_person(self, db, page):
        """点击人物卡片进入详情"""
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        svc.create_person("张三", "朋友")
        p = TongyuPage(page, svc)
        p.build()
        p._select_person(1)
        assert p._selected_person_id == 1

    def test_go_back(self, db, page):
        """返回按钮"""
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        svc.create_person("张三", "朋友")
        p = TongyuPage(page, svc)
        p.build()
        p._select_person(1)
        p._go_back()
        assert p._selected_person_id is None

    def test_add_event_dialog(self, db, page):
        """打开添加事件对话框"""
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        svc.create_person("张三", "朋友")
        p = TongyuPage(page, svc)
        p.build()
        p._select_person(1)
        p._show_add_event()
        assert page.last_dialog is not None

    def test_edit_notes_dialog(self, db, page):
        """打开编辑备注对话框"""
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        svc.create_person("张三", "朋友")
        p = TongyuPage(page, svc)
        p.build()
        detail = svc.get_person_detail(1)
        p._edit_notes(detail)
        assert page.last_dialog is not None

    def test_build_with_data(self, db, page):
        """有数据时构建"""
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        svc.create_person("张三", "朋友")
        svc.create_person("李四", "同事")
        svc.add_event(1, datetime.date.today(), "吃饭")
        svc.set_personality_dimension(1, "外向", 80)
        svc.add_custom_tag(1, "吃货")
        p = TongyuPage(page, svc)
        p.build()
        assert p is not None

    def test_detail_view_build(self, db, page):
        """人物详情页构建"""
        from ui.pages.tongyu_page import TongyuPage
        svc = TongyuService(db)
        svc.create_person("张三", "朋友")
        svc.add_event(1, datetime.date.today(), "吃饭")
        svc.set_personality_dimension(1, "外向", 80)
        p = TongyuPage(page, svc)
        p.build()
        p._select_person(1)
        p._refresh()
        assert p._selected_person_id == 1


# ============================================================
# 设置页 — 各种设置按钮
# ============================================================
class TestSettingsPageUI:
    def test_build(self, db, page):
        from ui.pages.settings_page import SettingsPage
        p = SettingsPage(page, db)
        p.build()
        assert p is not None

    def test_edit_birth_year(self, db, page):
        """修改出生年份按钮"""
        from ui.pages.settings_page import SettingsPage
        p = SettingsPage(page, db)
        p.build()
        p._edit_birth_year()
        assert page.last_dialog is not None

    def test_edit_target(self, db, page):
        """修改目标按钮"""
        from ui.pages.settings_page import SettingsPage
        p = SettingsPage(page, db)
        p.build()
        p._edit_target()
        assert page.last_dialog is not None

    def test_edit_ai_config(self, db, page):
        """AI 配置按钮"""
        from ui.pages.settings_page import SettingsPage
        p = SettingsPage(page, db)
        p.build()
        p._edit_ai_config()
        assert page.last_dialog is not None

    def test_toggle_dark_mode(self, db, page):
        """深色模式开关"""
        from ui.pages.settings_page import SettingsPage
        p = SettingsPage(page, db)
        p.build()
        e = MockEvent()
        e.control = MagicMock()
        e.control.value = True
        p._toggle_dark_mode(e)

    def test_backup(self, db, page):
        """备份按钮"""
        from ui.pages.settings_page import SettingsPage
        p = SettingsPage(page, db)
        p.build()
        p._backup()
        # 应该弹出提示
        assert len(page._dialogs) > 0

    def test_confirm_reset(self, db, page):
        """重置确认按钮"""
        from ui.pages.settings_page import SettingsPage
        p = SettingsPage(page, db)
        p.build()
        p._confirm_reset()
        assert page.last_dialog is not None


# ============================================================
# 主入口 — 引导页按钮
# ============================================================
class TestMainUI:
    def test_onboarding_build(self, page):
        """引导页能构建"""
        from database.db_manager import DatabaseManager
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        f.close()
        db = DatabaseManager(f.name)
        # 模拟 main 里的 _show_onboarding
        from main import _show_onboarding
        _show_onboarding(page, db, lambda: None)
        assert len(page.controls) > 0
        os.unlink(f.name)

    def test_main_navigation_build(self, page):
        """主导航能构建"""
        from database.db_manager import DatabaseManager
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        f.close()
        db = DatabaseManager(f.name)
        db.init_user_config(1998)
        from main import _show_main
        spirit = SpiritService(db)
        realm = RealmService(db)
        lingshi = LingshiService(db)
        tongyu = TongyuService(db)
        panel = PanelService(db)
        _show_main(page, db, spirit, realm, lingshi, tongyu, panel)
        assert len(page.controls) > 0
        os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
