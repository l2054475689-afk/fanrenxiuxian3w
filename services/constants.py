"""
凡人修仙3w天 — 常量定义（唯一真相源）
所有模块引用此文件，不要在其他地方重复定义
"""

# ============ 血量系统 ============
DEFAULT_LIFESPAN_YEARS = 80  # 默认寿命
BLOOD_TICK_MINUTES = 5       # 每次扣血间隔（分钟）
BLOOD_TICK_AMOUNT = 5        # 每次扣血量（分钟）

# ============ 心境系统 ============
SPIRIT_MIN = -200
SPIRIT_MAX = 640
SPIRIT_DEFAULT = 0

SPIRIT_LEVELS = [
    {"name": "心魔入体", "min": -200, "max": -80, "color": "#f44336", "desc": "极度负面状态"},
    {"name": "烦躁不堪", "min": -80, "max": -20, "color": "#ff5722", "desc": "严重负面状态"},
    {"name": "心烦意乱", "min": -20, "max": 0, "color": "#ff9800", "desc": "轻度负面状态"},
    {"name": "心平气和", "min": 0, "max": 80, "color": "#4CAF50", "desc": "正常状态"},
    {"name": "清心寡欲", "min": 80, "max": 160, "color": "#2196F3", "desc": "良好状态"},
    {"name": "守静笃行", "min": 160, "max": 320, "color": "#3F51B5", "desc": "优秀状态"},
    {"name": "古井无波", "min": 320, "max": 640, "color": "#9c27b0", "desc": "卓越状态"},
]

# ============ 灵石系统 ============
DEFAULT_TARGET_MONEY = 5_000_000  # 默认目标灵石（500万）

# 支出分类
EXPENSE_CATEGORIES = ["餐饮", "交通", "娱乐", "购物", "居住", "医疗", "教育", "其他"]

# 收入分类
INCOME_CATEGORIES = ["工资", "奖金", "投资", "兼职", "其他"]

# ============ 境界系统 ============
REALM_TYPE_MAIN = "main"       # 主境界
REALM_TYPE_DUNGEON = "dungeon"  # 副本境界

# 默认完成条件
DEFAULT_COMPLETION_RATE = 100  # 100% 全部完成

# ============ 统御系统 ============
RELATIONSHIP_TYPES = ["家人", "朋友", "同事", "导师", "同学", "其他"]

# 核心性格维度（滑块）
PERSONALITY_DIMENSIONS = [
    {"name": "内向-外向", "left": "内向", "right": "外向"},
    {"name": "理性-感性", "left": "理性", "right": "感性"},
    {"name": "严谨-随性", "left": "严谨", "right": "随性"},
    {"name": "乐观-悲观", "left": "乐观", "right": "悲观"},
]

# 沟通风格标签
COMMUNICATION_STYLES = [
    "直接坦率", "委婉含蓄", "主动沟通", "被动回应", "话多健谈", "话少沉默"
]

# 印象标签
IMPRESSION_TAGS = [
    "愉快", "尴尬", "紧张", "轻松", "深入", "表面", "冲突", "和谐", "收获", "无聊", "意外", "平常"
]

# 情绪标签
EMOTION_TAGS = [
    "开心", "沮丧", "焦虑", "兴奋", "平静", "烦躁", "疲惫", "充满活力"
]

# ============ UI 颜色 ============
class Colors:
    PRIMARY = "#667eea"
    PRIMARY_DARK = "#764ba2"
    LIFE_RED = "#ff6b6b"
    SPIRIT_BLUE = "#4facfe"
    MONEY_GOLD = "#f6d365"
    REALM_GREEN = "#a8edea"
    RELATION_PURPLE = "#d299c2"
    BG_LIGHT = "#f8f9fa"
    BG_DARK = "#0f0f1e"
    CARD_LIGHT = "#ffffff"
    CARD_DARK = "#1a1a2e"
    TEXT_PRIMARY = "#333333"
    TEXT_SECONDARY = "#666666"
    TEXT_HINT = "#999999"
    SUCCESS = "#4CAF50"
    WARNING = "#ff9800"
    ERROR = "#f44336"


def get_spirit_level(value: int) -> dict:
    """根据心境值获取当前等级信息"""
    for level in SPIRIT_LEVELS:
        if value >= level["min"] and value < level["max"]:
            return level
    # 边界处理
    if value >= SPIRIT_MAX:
        return SPIRIT_LEVELS[-1]
    return SPIRIT_LEVELS[0]


def get_spirit_progress(value: int) -> float:
    """获取当前等级内的进度 0.0~1.0"""
    level = get_spirit_level(value)
    range_size = level["max"] - level["min"]
    if range_size <= 0:
        return 1.0
    progress = (value - level["min"]) / range_size
    return max(0.0, min(1.0, progress))


def clamp_spirit(value: int) -> int:
    """限制心境值在有效范围内"""
    return max(SPIRIT_MIN, min(SPIRIT_MAX, value))
