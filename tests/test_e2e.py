"""
端到端集成测试 — 模拟完整用户流程
不依赖 UI 渲染，直接测试 Service + DB 的完整链路
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from database.db_manager import DatabaseManager
from services.spirit_service import SpiritService
from services.realm_service import RealmService
from services.lingshi_service import LingshiService
from services.tongyu_service import TongyuService
from services.panel_service import PanelService


def test_full_user_journey():
    """模拟一个用户从注册到日常使用的完整流程"""
    print("=" * 60)
    print("凡人修仙3w天 — 端到端集成测试")
    print("=" * 60)

    # 1. 初始化
    print("\n📦 1. 初始化应用...")
    db = DatabaseManager(":memory:")
    config = db.init_user_config(birth_year=1998, target_money=5_000_000)
    print(f"   出生年份: {config['birth_year']}")
    print(f"   初始血量: {config['initial_blood']:,} 分钟")
    print(f"   目标灵石: {config['target_money']:,}")
    assert config["initial_blood"] > 0
    assert config["target_money"] == 5_000_000
    print("   ✅ 初始化成功")

    # 初始化服务
    spirit = SpiritService(db)
    realm = RealmService(db)
    lingshi = LingshiService(db)
    tongyu = TongyuService(db)
    panel = PanelService(db)

    # 2. 心境系统
    print("\n🧘 2. 心境系统测试...")

    # 创建正面任务
    t1 = spirit.create_positive_task("早起", spirit_effect=3, blood_effect=1, emoji="🌅", enable_streak=True)
    t2 = spirit.create_positive_task("冥想", spirit_effect=5, emoji="🧘", submission_type="repeatable")
    t3 = spirit.create_positive_task("跑步", spirit_effect=2, blood_effect=2, emoji="🏃")
    print(f"   创建正面任务: {t1['name']}, {t2['name']}, {t3['name']}")

    # 创建心魔任务
    d1 = spirit.create_demon_task("刷手机", spirit_effect=3, emoji="📱")
    d2 = spirit.create_demon_task("熬夜", spirit_effect=5, blood_effect=3, emoji="🌙")
    print(f"   创建心魔任务: {d1['name']}(心境{d1['spirit_effect']}), {d2['name']}(心境{d2['spirit_effect']})")
    assert d1["spirit_effect"] == -3  # 强制负值
    assert d2["blood_effect"] == -3

    # 完成任务
    r1 = spirit.complete_daily_task(t1["id"])
    assert r1["success"]
    print(f"   完成「早起」: 心境={r1['record']['new_spirit']}")
    assert r1["record"]["new_spirit"] == 3

    # 连续打卡
    assert r1["streak"]["current_streak"] == 1
    print(f"   连续打卡: {r1['streak']['current_streak']}天")

    # 重复任务可多次
    r2a = spirit.complete_repeatable_task(t2["id"])
    r2b = spirit.complete_repeatable_task(t2["id"])
    print(f"   冥想x2: 心境={r2b['record']['new_spirit']}")
    assert r2b["record"]["new_spirit"] == 13  # 3+5+5

    # 每日任务不能重复
    r1_dup = spirit.complete_daily_task(t1["id"])
    assert not r1_dup["success"]
    print(f"   重复打卡被拒: {r1_dup['message']}")

    # 心魔
    rd1 = spirit.record_demon(d1["id"])
    assert rd1["success"]
    print(f"   心魔「刷手机」: 心境={rd1['record']['new_spirit']}")
    assert rd1["record"]["new_spirit"] == 10  # 13-3

    # 撤销
    undo = spirit.undo_task(r2b["record"]["id"])
    assert undo["success"]
    status = spirit.get_spirit_status()
    print(f"   撤销冥想: 心境={status['value']}, 等级={status['level_name']}")
    assert status["value"] == 5  # 10-5

    # 今日摘要
    summary = spirit.get_today_summary()
    print(f"   今日: 正面{summary['positive_count']}次, 心魔{summary['demon_count']}次, 净心境{summary['total_spirit_change']:+d}")
    print("   ✅ 心境系统正常")

    # 3. 境界系统
    print("\n⚔️ 3. 境界系统测试...")

    # 创建主境界
    r = realm.create_realm("练气期", description="掌握基础", reward_spirit=10)
    assert r["success"]
    realm_id = r["realm"]["id"]
    print(f"   创建境界: {r['realm']['name']}")

    # 不能创建第二个主境界
    r_dup = realm.create_realm("筑基期")
    assert not r_dup["success"]
    print(f"   重复创建被拒: {r_dup['message']}")

    # 创建副本
    dungeon = realm.create_realm("突发副本", realm_type="dungeon")
    assert dungeon["success"]
    print(f"   创建副本: {dungeon['realm']['name']}")

    # 添加技能和子任务
    sk1 = realm.add_skill(realm_id, "高等数学")
    sk2 = realm.add_skill(realm_id, "Python编程")
    print(f"   添加技能: {sk1['skill']['name']}, {sk2['skill']['name']}")

    st1 = realm.add_sub_task(sk1["skill"]["id"], "函数定义")
    st2 = realm.add_sub_task(sk1["skill"]["id"], "极限")
    st3 = realm.add_sub_task(sk1["skill"]["id"], "微积分")
    st4 = realm.add_sub_task(sk2["skill"]["id"], "基础语法")
    st5 = realm.add_sub_task(sk2["skill"]["id"], "NumPy")
    print(f"   添加子任务: 数学3个, 编程2个")

    # 完成子任务
    realm.complete_sub_task(st1["sub_task"]["id"])
    realm.complete_sub_task(st2["sub_task"]["id"])
    progress = realm.get_realm_progress(realm_id)
    print(f"   完成2/5: 进度={progress['overall_progress']:.0f}%")
    assert 30 < progress["overall_progress"] < 50

    # 全部完成
    realm.complete_sub_task(st3["sub_task"]["id"])
    realm.complete_sub_task(st4["sub_task"]["id"])
    result = realm.complete_sub_task(st5["sub_task"]["id"])
    assert result["realm_ready_to_advance"]
    print(f"   全部完成! 可以晋升")

    # 晋升
    advance = realm.advance_realm(realm_id)
    assert advance["success"]
    print(f"   晋升: {advance['message']}")

    # 检查奖励
    new_status = spirit.get_spirit_status()
    print(f"   晋升奖励: 心境={new_status['value']} (之前5+奖励10=15)")
    assert new_status["value"] == 15

    # 已完成列表
    completed = realm.get_completed_realms()
    assert len(completed) == 1
    print("   ✅ 境界系统正常")

    # 4. 灵石系统
    print("\n💰 4. 灵石系统测试...")

    lingshi.add_income(15000, "工资", "月薪")
    lingshi.add_income(2000, "奖金", "项目奖金")
    lingshi.add_expense(3000, "居住", "房租")
    lingshi.add_expense(500, "餐饮", "本周伙食")
    lingshi.add_expense(200, "交通", "地铁充值")
    print("   记录: 收入17000, 支出3700")

    balance = lingshi.get_balance()
    print(f"   余额: {balance['balance']:,.2f}")
    assert balance["balance"] == 13300

    # 预算
    lingshi.set_budget("餐饮", 2000)
    lingshi.set_budget("交通", 500)
    budget = lingshi.get_budget_status()
    print(f"   预算: 餐饮已用{budget['categories'][0]['spent']}/2000")

    # 负债
    lingshi.create_debt("房贷", 1_000_000, 5000, interest_rate=3.5)
    repay = lingshi.repay_debt(1, 5000)
    print(f"   房贷还款: 剩余{repay['remaining']:,.0f}")
    assert repay["remaining"] == 995000

    # 目标进度
    goal = lingshi.get_goal_progress()
    print(f"   目标进度: {goal['progress']:.2f}%, 下一里程碑{goal['next_milestone']:,}")

    # 月度汇总
    monthly = lingshi.get_monthly_summary()
    print(f"   月度: 收入{monthly['income_total']:,}, 支出{monthly['expense_total']:,}, 净{monthly['net']:,}")
    print("   ✅ 灵石系统正常")

    # 5. 统御系统
    print("\n👥 5. 统御系统测试...")

    p1 = tongyu.create_person("张三", "朋友", avatar_emoji="😎")
    p2 = tongyu.create_person("李四", "同事", avatar_emoji="👨‍💼")
    p3 = tongyu.create_person("王五", "家人", birthday=date(1995, 6, 15), avatar_emoji="👴")
    print(f"   添加人物: {p1['person']['name']}, {p2['person']['name']}, {p3['person']['name']}")

    # 性格标签
    tongyu.set_personality_dimension(p1["person"]["id"], "内向-外向", 30)
    tongyu.set_personality_dimension(p1["person"]["id"], "理性-感性", 70)
    tongyu.set_communication_style(p1["person"]["id"], ["直接坦率", "话少沉默"])
    tongyu.add_custom_tag(p1["person"]["id"], "技术控")
    print("   设置张三性格: 偏内向, 偏感性, 直接坦率, #技术控")

    # 事件
    tongyu.add_event(
        p1["person"]["id"], date.today(), "一起吃饭聊天",
        location="星巴克",
        impression_tags=["愉快", "深入"],
        their_emotion=["开心", "平静"],
        topics=["工作", "技术"],
        key_info="他想学Python，最近考虑换工作",
        my_feeling="聊得很投机",
        next_action="推荐Python资源",
    )
    print("   记录事件: 与张三在星巴克吃饭")

    # 相处模板
    tongyu.update_person(p1["person"]["id"], notes="不喜欢闲聊，适合直入主题。对技术话题很感兴趣。")
    template = tongyu.generate_interaction_template(p1["person"]["id"])
    assert "张三" in template
    assert "偏内向" in template
    print(f"   相处模板生成: {len(template)}字")

    # 统计
    stats = tongyu.get_relationship_stats()
    print(f"   统计: {stats['total_people']}人, 本月互动{stats['monthly_interactions']}次")

    # 未联系提醒
    neglected = tongyu.get_neglected_people(days_threshold=0)
    print(f"   需关注: {len(neglected)}人")
    print("   ✅ 统御系统正常")

    # 6. 面板
    print("\n📊 6. 面板仪表盘测试...")

    blood = panel.get_blood_status()
    print(f"   血量: {blood['remaining_days']:,}天 ({blood['remaining_years']}年)")
    assert blood["is_alive"]

    dashboard = panel.get_dashboard()
    print(f"   心境: {dashboard['spirit']['value']} ({dashboard['spirit']['level_name']})")
    print(f"   今日: {dashboard['today']['total_tasks']}个任务, 心境{dashboard['today']['spirit_change']:+d}")
    print(f"   灵石: {dashboard['lingshi']['balance']:,.2f}")

    trend = panel.get_weekly_trend()
    print(f"   7日趋势: {len(trend)}天数据")
    assert len(trend) == 7
    print("   ✅ 面板正常")

    # 7. 跨系统验证
    print("\n🔗 7. 跨系统数据一致性验证...")

    final_config = db.get_user_config()
    print(f"   DB心境值: {final_config['current_spirit']}")
    print(f"   Service心境值: {spirit.get_spirit_status()['value']}")
    assert final_config["current_spirit"] == spirit.get_spirit_status()["value"]

    print(f"   DB血量: {final_config['current_blood']:,}")
    # 血量应该有变化（早起+1血量）
    assert final_config["current_blood"] == config["initial_blood"] + 1  # 早起+1

    print("   ✅ 数据一致")

    print("\n" + "=" * 60)
    print("🎉 全部测试通过！凡人修仙3w天 核心功能验证完毕")
    print("=" * 60)
    print(f"\n📋 测试覆盖:")
    print(f"   • 用户初始化 + 血量计算")
    print(f"   • 心境: 正面任务/心魔/打卡/撤销/统计")
    print(f"   • 境界: 创建/技能树/子任务/晋升/奖励/副本")
    print(f"   • 灵石: 收支/预算/负债/还款/目标/月度汇总")
    print(f"   • 统御: 人物/性格标签/事件/相处模板/提醒")
    print(f"   • 面板: 血量倒计时/仪表盘/趋势图")
    print(f"   • 跨系统数据一致性")


if __name__ == "__main__":
    test_full_user_journey()
