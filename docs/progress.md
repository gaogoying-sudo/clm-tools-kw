# CLM-Tools 进度日志

## 2026-04-12

**00:55** [小强] Phase 0 完成 —— 项目骨架搭建
- 从 CLM-Tools 复制后端 (FastAPI, 17文件) + 前端 (React, 6文件)
- 从 DateUse 复制 data-sync (7文件)
- 复制关键文档到 docs/
- 创建 docker-compose.yml (MySQL + Backend + Frontend)
- 创建 .env / .gitignore / README.md
- 编写 PROJECT_ANALYSIS.md (完整项目分析)
- 编写 WORK_PLAN.md (详细开发计划)
- Git 本地 commit (2359168)

**01:05** [小强] 治理制度建设 v1
- 编写 GOVERNANCE.md (三层治理：Memory → docs/ → graphify)
- 创建 TASK_BOARD.md (任务看板)
- 创建 RESOURCE.md (资源登记)
- 创建 decisions/001-tech-stack.md (首个 ADR)
- 更新 progress.md 格式

**01:15** [小强] 治理制度 v2.0 落地（五层架构）
- 融合 MemPalace + Obsidian + graphify 到治理架构
- 创建 mempalace.yaml (6 rooms: ai_recipe_roadmap/frontend/backend/documentation/deployment/general)
- 创建 Obsidian Vault: ~/Documents/CLM-Obsidian/ + 项目概览笔记
- 创建 AGENTS.md (包含 MemPalace + graphify + Obsidian 规则)
- 安装 graphify (v0.4.2, Python 3.12 venv)
- 生成初始图谱: 182 nodes, 332 edges, 25 communities
- Memory 已更新
- Git commit (683d032)

**下一步：**
1. 确认治理制度方案（等用户确认）
2. T02: Docker 本地环境验证
3. T03: 安装 graphify 并生成初始图谱
4. T04: 增强 mock 数据
5. T10: GitHub push 认证修复

**阻塞项：**
- GitHub push 超时（SSH key 或 token 认证问题，需配置）
- 公司源数据库连接信息待确认

**01:10** [小强] T02 Docker 本地环境验证 完成
- 启动 Docker Desktop，docker compose up -d
- 停掉旧容器 clm-review-tool-db-1 和 clm-review-tool-backend-1（端口冲突）
- 修复 config.py: MYSQL_HOST 默认值 localhost → mysql
- 修复 config.py: DATABASE_URL 优先读取完整环境变量
- 三个服务全部运行：MySQL(3307) + Backend(8001) + Frontend(8081)
- API 验证通过：健康检查、同步今日数据、会话创建、问题流生成
- Mock 数据质量验证：3道菜、完整功率轨迹/投料时序、异常场景触发题

**用户明确要求记录：**
- 飞书不要发任何消息（DRY_RUN + TEST_MODE 默认开启）
- 云服务器部署暂缓，专注本地开发
- 技术栈用最新的、最好用的、最适合的
- 关键信息记录到工程目录防遗忘
- 管理后台不要手机端，要桌面级看板
- 原始问答数据必须保留（三层：raw/transcribed/structured）
- 数据检索优先查本地缓存，当天数据标记"进行中"
- 治理工具（todo/task_board/progress/memory/adr/graphify）必须及时使用
