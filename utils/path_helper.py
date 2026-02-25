"""
凡人修仙3w天 — 路径工具
跨平台路径管理
"""
import flet as ft
from pathlib import Path


def get_app_data_dir(page: ft.Page) -> Path:
    """获取应用数据目录"""
    if hasattr(page, 'platform') and page.platform == ft.PagePlatform.ANDROID:
        data_dir = Path("/data/data/com.fanrenxiuxian.app/files")
    elif hasattr(page, 'platform') and page.platform == ft.PagePlatform.IOS:
        data_dir = Path.home() / "Documents" / "fanrenxiuxian"
    else:
        data_dir = Path.home() / ".fanrenxiuxian"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_database_path(page: ft.Page) -> str:
    """获取数据库路径"""
    return str(get_app_data_dir(page) / "fanrenxiuxian.db")


def get_backup_dir(page: ft.Page) -> Path:
    """获取备份目录"""
    backup_dir = get_app_data_dir(page) / "backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir
