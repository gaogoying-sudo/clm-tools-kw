# CLM-Tools 口味工程师日总结系统

> 让一线口味工程师每天录菜结束后，通过问卷复盘当天工作，自动沉淀为可检索的经验知识库。

**项目代号：** clm-tools-kw  
**英文缩写：** CLM (Cooking Language Model / 口味工程师)  
**当前开发者：** 小强（整合原 CLM-Tools + DateUse + 小厨 三个团队）

---

## 快速开始

### 环境要求
- Docker + Docker Compose
- 或使用本地 Python 3.11+ + Node.js 18+

### Docker 一键启动
```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 启动所有服务
docker compose up -d

# 3. 等待 MySQL 就绪（约30秒）
docker compose logs -f mysql

# 4. 访问服务
# 前端: http://localhost:8081
# 后端 API: http://localhost:8001
# API 文档: http://localhost:8001/docs
# 管理后台: http://localhost:8081/#/admin
```

### 本地开发（不使用 Docker）

```bash
# === 后端 ===
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# === 前端（另一个终端） ===
cd frontend
npm install
npm run dev

# === MySQL（另一个终端，需已安装） ===
# 或使用 Docker 只跑 MySQL:
docker compose up -d mysql
```

---

## 项目结构

```
clm-tools-kw/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py       # 应用入口 + 定时任务
│   │   ├── models.py     # 数据库模型 (7张表)
│   │   ├── config.py     # 配置管理
│   │   ├── database.py   # 数据库连接
│   │   ├── sync_service.py   # 数据同步服务
│   │   ├── question_engine.py # 动态问题流引擎
│   │   ├── feishu.py     # 飞书消息发送
│   │   └── routers/      # API 路由
│   │       ├── sessions.py   # 会话管理
│   │       ├── answers.py    # 回答提交
│   │       └── admin.py      # 管理端
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # React 前端
│   ├── src/
│   │   ├── App.jsx       # 主应用（3个视图）
│   │   ├── api.js        # API 客户端
│   │   └── main.jsx      # 入口
│   ├── package.json
│   └── Dockerfile
├── data-sync/            # 数据同步模块（来自 DateUse）
│   ├── data_sync/
│   │   ├── engineers.py  # 工程师花名册 (36人)
│   │   ├── db.py         # 源数据库连接
│   │   ├── mapper.py     # 身份映射逻辑
│   │   └── config.py     # 配置
│   └── main.py
├── docker-compose.yml    # 本地开发编排
├── docs/                 # 项目文档
│   ├── DATA_HANDOVER_v1.md      # 数据交接文档
│   ├── ENGINEER_DB_DISCOVERY_v1.md  # 数据库发现
│   └── progress.md              # 进度追踪
└── PROJECT_ANALYSIS.md   # 详细分析与开发计划
```

---

## 核心功能

### 业务流程
1. **数据同步** — 从公司后台拉取当日录菜记录
2. **会话生成** — 按工程师聚合，检测信号，动态生成问题流
3. **飞书推送** — 发送问卷卡片给工程师
4. **填写提交** — 工程师在H5页面填写回答
5. **经验沉淀** — 自动分类入池（经验/失败/调优/客户反馈等）
6. **管理审核** — 管理端查看、审核、导出

### 数据库模型（7张表）
| 表名 | 用途 |
|------|------|
| engineers | 工程师信息 |
| sync_tasks | 当日录菜任务（含过程数据） |
| daily_sessions | 每日回传会话 |
| session_tasks | 会话-任务关联 |
| questions | 问题模板（支持触发/分支逻辑） |
| answers | 回答（三层存储） |
| experience_candidates | 经验候选（8种分类） |

---

## 当前阶段

- [x] 项目骨架搭建
- [ ] Docker 本地环境验证
- [ ] 数据同步打通（增强 mock 数据）
- [ ] 前后端完整闭环
- [ ] 前端 UI 升级（TailwindCSS）
- [ ] 管理后台增强
- [ ] 端到端测试

**详见：** [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md)

---

## 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 8081 | http://localhost:8081 |
| 后端 API | 8001 | http://localhost:8001 |
| MySQL | 3307 | localhost:3307 |

---

## 关键约束

1. 飞书默认 dry-run + test mode，不发送真实消息
2. 当前使用 mock 数据，源数据库接入待配置
3. 云服务器部署暂缓，专注本地开发

---

**最后更新：** 2026-04-12 00:50
