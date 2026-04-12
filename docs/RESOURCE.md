# CLM-Tools 资源登记

> 敏感信息（密码、密钥）不进入 Git，仅存本地 + Memory

---

## 云服务器

| 项目 | 值 |
|------|-----|
| 服务商 | 腾讯云轻量 |
| IP | 82.156.187.35 |
| SSH 用户 | root |
| SSH 认证 | 本地有密钥 |
| 部署目录 | /opt/clm-review-tool/ |
| Compose 文件 | /opt/clm-review-tool/compose/docker-compose.prod.yml |
| 环境配置 | /opt/clm-review-tool/env/.env.prod |
| 启动脚本 | /opt/clm-review-tool/scripts/start.sh |
| 运行容器 | clm-mysql (MySQL 8.0) |
| 状态 | 已初始化，MySQL 运行中 |

---

## 本地开发

| 项目 | 值 |
|------|-----|
| 项目路径 | /Users/mac/Projects/clm-tools-kw/ |
| Git 远程 | git@github.com:gaogoying-sudo/clm-tools-kw.git |
| 分支 | main |
| 端口 - 前端 | 8081 |
| 端口 - 后端 | 8001 |
| 端口 - MySQL | 3307 |

---

## 飞书应用

| 项目 | 值 |
|------|-----|
| APP_ID | cli_a92b81d03838dbb3 |
| APP_SECRET | (见 .env.prod / Memory) |
| 测试群 chat_id | oc_c2eaef0dca9716e687620eec72bbcaa6 |
| 群主 ID | ou_40025e775477ba7ffce200c9d0bebe02 |
| 旧群 chat_id | oc_69142130bd9be78794c0840329a76c8c（有老板，不用） |
| DRY_RUN | true（默认开启） |
| TEST_MODE | true（默认开启） |

---

## 数据库

| 项目 | 值 |
|------|-----|
| 本地 MySQL | localhost:3307 (clm_review) |
| 云端 MySQL | 82.156.187.35:3306 |
| 公司源 DB | 待配置 (btyc 库) |
| 数据分层 | raw_* / core_* (DateUse) + biz_* / asset_* (CLM) |

---

## 相关项目

| 项目 | 路径 | 说明 |
|------|------|------|
| CLM Project (旧) | ~/Projects/CLM Project/ | 文档和交接包 |
| CLM-Tools (Cursor) | ~/software project/cursor/CLM-Tools/dailyReport/clm-review-tool/ | 原始业务代码 |
| DateUse (Codex) | ~/software project/DateUse/app/data-sync/ | 原始数据同步代码 |

---

## 环境变量模板

见项目根目录 `.env.example`，完整配置复制到 `.env`（不提交Git）。
