# CLAUDE.md — 凡人修仙3w天 项目规则

## 项目概述
个人生命管理 App，修仙主题游戏化。Python + Flet 框架，打包 Android APK。

## 技术栈
- Python 3.10+
- Flet 0.21.0+
- SQLite + SQLAlchemy 2.0+
- cryptography (AES-256)

## 架构原则

### 分层架构
```
database/models.py    → ORM 模型定义（唯一真相源）
database/db_manager.py → 数据库 CRUD 操作
services/*.py         → 业务逻辑层
ui/pages/*.py         → UI 页面
ui/components/*.py    → 可复用 UI 组件
```

### 强制规则
1. **Service 层返回字典，不返回 ORM 对象** — 避免 DetachedInstanceError
2. **常量一处定义** — 心境等级、颜色等在 `services/constants.py` 定义，其他文件引用
3. **Session 用完即关** — 所有 DB 操作用 `with session:` 或 try/finally
4. **类型注解** — 所有函数签名必须有类型注解
5. **中文注释** — 注释和文档字符串用中文

### 数据模型核心参数
- 血量：实时倒计时，每5分钟扣5，单位=分钟
- 心境值：-200 到 +640，7个等级
- 境界：同时1个活跃境界 + 1个副本境界
- 灵石：1灵石 = 1人民币
- 统御：手动相处要点 + AI报告

### 心境等级定义（唯一标准）
| 范围 | 名称 |
|------|------|
| -200 ~ -80 | 心魔入体 |
| -80 ~ -20 | 烦躁不堪 |
| -20 ~ 0 | 心烦意乱 |
| 0 ~ 80 | 心平气和 |
| 80 ~ 160 | 清心寡欲 |
| 160 ~ 320 | 守静笃行 |
| 320 ~ 640 | 古井无波 |

## 测试规则
- 每个 service 必须有对应的 test 文件
- 测试用 pytest
- 先写测试，再写实现（TDD）
- 测试文件命名：`tests/test_{module}.py`

## 文件路径
- 跨平台路径用 `utils/path_helper.py`
- Android: `/data/data/com.fanrenxiuxian.app/files/`
- Desktop: `~/.fanrenxiuxian/`

## 编码规范
- 缩进：4空格
- 行宽：120字符
- import 顺序：标准库 → 第三方 → 本地
- 不用 `from xxx import *`
