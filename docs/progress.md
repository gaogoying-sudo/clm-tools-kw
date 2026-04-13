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

**01:30** [小强] T102 前端重构完成
- 全新架构: React Router + 5个页面 + 侧边栏导航
- TailwindCSS v4 替代内联样式 (3001行新增, 1211行删除)
- 登录页 /login + 数据看板 /dashboard + 数据检索 /search
- 原始问答 /qa-records + 经验沉淀 /insights + 系统管理 /settings
- 修复 api.js ADMIN_TOKEN_STORAGE_KEY 损坏问题
- 角色权限路由: superadmin/admin/analyst
**01:45** [小强] T105-T108 全部完成 + GitHub push 阻塞
- 后端: 创建 search.py (多条件检索 API + 内存缓存层 + /qa-records)
- 前端: SearchPage 接 /api/admin/search (6条件筛选+分页+缓存命中提示)
- 前端: QARecordsPage 接 /api/admin/qa-records (三层数据+关键词搜索+CSV/JSON导出)
- 前端: InsightsPage 接 /api/admin/candidates (审核流程: 草稿→待审→已确认/无效)
- 前端: SettingsPage 接工程师花名册(36人)+问题模板(7个)+数据源配置(3个连接状态)
- 修复: api.js ADMIN_TOKEN_STORAGE_KEY 从 *** 修复
- Git commit: ef37f49
- GitHub push 阻塞: HTTPS 认证超时，需要 SSH key 配置或 token

**01:35** [小强] T101 数据增强完成
- 36 位工程师完整入库（基于 DateUse 发现的真实花名册）
- 近 30 天模拟数据生成：1327 条任务、394 个会话
- 提交率 86.5%（341/394）
- 菜谱库 16 道菜（辣椒炒肉/麻婆豆腐/水煮鱼/酸菜鱼等）
- 每道菜含完整功率轨迹 + 投料时序 + 异常场景
- 创建 seed_30day_data.py 可重复执行

- 启动 Docker Desktop，docker compose up -d
- 停掉旧容器 clm-review-tool-db-1 和 clm-review-tool-backend-1（端口冲突）
- 修复 config.py: MYSQL_HOST 默认值 localhost → mysql
- 修复 config.py: DATABASE_URL 优先读取完整环境变量
- 三个服务全部运行：MySQL(3307) + Backend(8001) + Frontend(8081)
- API 验证通过：健康检查、同步今日数据、会话创建、问题流生成
- Mock 数据质量验证：3 道菜、完整功率轨迹/投料时序、异常场景触发题

**02:00** [小强] T109 后端缓存层 API 完成 + T110 端到端验证通过
- 修复 search.py: timedelta import 位置错误
- 新增缓存统计 API: GET /api/admin/cache/stats（命中率、条目数、TTL）
- 新增缓存清除 API: POST /api/admin/cache/clear
- 缓存命中统计：hits/misses 计数器
- 验证结果：
  - ✅ 健康检查 API 正常
  - ✅ 数据检索 API 正常（125 条今日会话）
  - ✅ 缓存机制正常（历史数据缓存命中率 50%+）
  - ✅ 原始问答 API 正常（7 条记录）
  - ✅ 工程师花名册 API 正常（75 人）
  - ✅ 前端 5 页面全部正常（登录/看板/检索/问答/系统管理）
- Git commit pending

**用户明确要求记录：**
- 飞书不要发任何消息（DRY_RUN + TEST_MODE 默认开启）
- 云服务器部署暂缓，专注本地开发
- 技术栈用最新的、最好用的、最适合的
- 关键信息记录到工程目录防遗忘
- 管理后台不要手机端，要桌面级看板
- 原始问答数据必须保留（三层：raw/transcribed/structured）
- 数据检索优先查本地缓存，当天数据标记"进行中"
- 治理工具（todo/task_board/progress/memory/adr/graphify）必须及时使用
