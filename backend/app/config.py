import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # MySQL
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "clm")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "clm123")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "clm_review")

    @property
    def DATABASE_URL(self):
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    # 飞书
    FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")
    FEISHU_BOT_WEBHOOK: str = os.getenv("FEISHU_BOT_WEBHOOK", "")
    
    # 推送安全配置
    FEISHU_DRY_RUN: bool = os.getenv("FEISHU_DRY_RUN", "true").lower() == "true"  # 默认开启 dry-run
    FEISHU_TEST_WHITELIST: str = os.getenv("FEISHU_TEST_WHITELIST", "")  # 逗号分隔的允许发送的 user_id
    
    # 测试群安全发送模式（公司环境专用）
    FEISHU_TEST_MODE: bool = os.getenv("FEISHU_TEST_MODE", "true").lower() == "true"  # 默认开启测试群模式
    FEISHU_TEST_CHAT_ID: str = os.getenv("FEISHU_TEST_CHAT_ID", "")  # 测试群 chat_id

    # 公司后台数据库
    SOURCE_DB_HOST: str = os.getenv("SOURCE_DB_HOST", "")
    SOURCE_DB_PORT: int = int(os.getenv("SOURCE_DB_PORT", "3306"))
    SOURCE_DB_USER: str = os.getenv("SOURCE_DB_USER", "")
    SOURCE_DB_PASSWORD: str = os.getenv("SOURCE_DB_PASSWORD", "")
    SOURCE_DB_NAME: str = os.getenv("SOURCE_DB_NAME", "")

    # 服务
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # 推送
    PUSH_TIME: str = os.getenv("PUSH_TIME", "18:30")
    PUSH_TIMEZONE: str = os.getenv("PUSH_TIMEZONE", "Asia/Shanghai")

    # 管理后台（可选）鉴权
    # - 为空：不启用鉴权（本地开发/演示）
    # - 非空：调用 /api/admin/* 需带 Header: X-Admin-Token: <token>
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")

    @property
    def use_mock_data(self):
        return not self.SOURCE_DB_HOST


settings = Settings()
