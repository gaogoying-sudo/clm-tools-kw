# CLM-REVIEW-TOOL 数据落库与接口对接交接包（Hermes 用）
**版本：** v1  
**更新时间：** 2026-04-10  
**适用范围：** 三团队协作（CLM-Tools / DateUse / 运维）在**不改现有架构**前提下，确保"工程师回传"数据**可对接、可理解、可回溯**并稳定落在云端 MySQL。

---

## 0. 一句话目标
把"工程师当天录菜 → 飞书触达 → 工程师填写回传 → 管理端审核沉淀"的所有关键业务数据，**策略性落库在同一台云服务器 MySQL**，并形成跨团队稳定的数据契约与验收口径。

---

## 1. 现有架构边界（不改）
### 1.1 三团队职责边界
- **DateUse**：只负责"公司源库 → 清洗/映射/结构化"，写入 MySQL 的 `raw_*` / `core_*`（或等价表）。**不写业务会话逻辑**。
- **CLM-Tools（本仓库 review-app + worker）**：只读 DateUse 的结构化结果，生成业务会话并回收答案，落 `biz_*`（或等价表）。飞书推送、定时任务、重试补偿由 worker/任务系统承接。
- **运维**：提供云端运行环境（Docker/Compose、域名/HTTPS、DB 备份、密钥管理、监控）。

### 1.2 "不改架构"的关键约束
- review-app **不直连公司源数据库**（只对接 DateUse 写入的 MySQL）。
- 回传数据必须**在云端 MySQL 可追溯**（不能只留在飞书/日志里）。
- worker 与页面服务资源隔离，避免 Web 容器跑批任务。

---

## 2. 云端落库策略（同一 MySQL、分层隔离）
### 2.1 推荐的库表分层（概念层）
> 现状仓库里已实现一套"简化 core+biz"的表（见 2.3），后续可保持现状或迁移命名；关键是边界一致。

- **raw_***：原始快照/日志（追溯用）— 由 DateUse 写入
- **core_***：结构化实体（工程师/客户/设备/菜谱/执行锚点）— 由 DateUse 写入
- **biz_***：业务会话（工程师日会话/问题流/提交回传/推送记录）— 由 review-app/worker 写入
- **asset_***：知识沉淀（经验候选/失败案例/客户偏好）— 由 review-app（或后续审核流程）写入

### 2.2 单实例 MySQL 的隔离方式（运维可选）
二选一即可（优先 schema 隔离）：
- **方案 A（推荐）**：同一 MySQL 实例，分 schema：`dateuse` / `clm`  
- **方案 B**：同一 schema，分表前缀：`raw_*/core_*` 与 `biz_*/asset_*`

### 2.3 本仓库当前"已实现的落库表"（可立即验收）
这些表已在 `backend/app/models.py`：
- **工程师**：`engineers`（含 `feishu_user_id`）
- **当日任务**：`sync_tasks`（含菜品、客户、设备、功率轨迹、投料时序、调整记录、执行次数等）
- **会话**：`daily_sessions`（含 `summary_snapshot`、`root_event_type`、`status`、`submitted_at` 等）
- **会话 - 任务关联**：`session_tasks`（含 `is_focus_task`）
- **题模板**：`questions`
- **回答**：`answers`（三层存储：`raw_input` / `transcribed_text` / `structured_result`）
- **经验候选**：`experience_candidates`（审核状态、摘要、池子分类等）

> 说明：该表结构已满足"可对接、可回溯"的最小要求；后续对接 DateUse 的 `core/raw` 只是把 `sync_tasks` 的数据来源从 mock/临时源，切换为 DateUse 的结构化产物。

---

## 3. 业务数据链路（从源数据到可回溯回传）
### 3.1 任务侧（当天录菜数据）
1) DateUse 从源库同步（或本仓库 `sync_service.py` mock）  
2) 写入/生成当日任务（当前实现写到 `sync_tasks`）  
3) 关键字段（必须保留，用于"过程视角"与复盘）：
- `task_date`, `engineer_id`
- `dish_name`, `recipe_id`, `recipe_version`, `recipe_type`
- `customer_name`, `device_id`
- **过程信息**：`exec_count`, `exec_time`, `power_trace`, `ingredients_timeline`, `modifications`, `has_abnormal`

### 3.2 会话侧（当天会话生成与问题流）
由 `backend/app/routers/sessions.py` 完成：
- `POST /api/sessions/sync-today`：
  - 同步任务
  - 按工程师聚合，做信号检测 `detect_signals()`
  - 创建 `daily_sessions` + `session_tasks`
  - 生成 `summary_snapshot`（快照）
- `GET /api/sessions/{session_id}`：
  - 返回任务 + 问题流（`select_flow_questions()`）+ 已提交的 answers
  - root_event_type 支持从入口题推断

### 3.3 回传侧（提交答案、分类入池、生成经验候选）
由 `backend/app/routers/answers.py` 完成：
- `POST /api/answers/{session_id}/submit`
  - 写入 `answers`（保留 raw_input / transcribed_text / structured_result 三层字段）
  - 更新 `daily_sessions`：`status=submitted`、`submitted_at`、`duration_seconds`、`root_event_type`
  - 用 `ROOT_EVENT_TO_POOL` 将会话分配到池（pool）
  - 将 `q_experience` 的文本写入 `experience_candidates`（`status=draft`），形成后续审核入口

### 3.4 管理侧（查看回收结果与模板、审核经验候选）
由 `backend/app/routers/admin.py` 提供：
- `GET /api/admin/sessions/{id}/answers`：返回 `summary_snapshot`、`root_event_type`、`pool`、`qa_list`
- `GET /api/admin/questions` / `PUT /api/admin/questions/{id}`：模板管理
- `GET /api/admin/candidates` / `PATCH /api/admin/candidates/{id}`：候选审核

> 管理端鉴权：当 `ADMIN_TOKEN` 设置时，所有 `/api/admin/*` 需要 `X-Admin-Token`（见 `backend/app/routers/admin.py` 与 `backend/app/config.py`）。

---

## 4. "可对接、可理解、可回溯"的落库标准（验收口径）
### 4.1 可对接（Contract）
- 能从 MySQL 中用 `session_id` 完整还原：
  - 当天任务列表（含过程字段）
  - 问题流（questions 模板版本 + 触发规则）
  - 工程师的所有回答（answers）
  - 分类结果（root_event_type + pool）
  - 审核沉淀（experience_candidates）

### 4.2 可理解（Readable）
- 字段含义明确（表/字段命名、枚举值），管理端能直接读出"今天发生了什么/为什么问这些/答了什么/落到哪个池"。
- 所有关键状态可在 DB 内查到（不依赖日志）。

### 4.3 可回溯（Traceable）
最少要能回答：
- **这条经验从哪天哪位工程师哪次会话来的？**（candidate → answer → session → engineer）
- **当时看到的任务摘要是什么？**（session.summary_snapshot）
- **当时任务过程数据是什么？**（sync_tasks 的 power_trace/ingredients/modifications/exec_count）
- **当时模板是什么？**（questions 表）

---

## 5. 飞书推送与安全封闭测试（云端必备）
### 5.1 当前实现位置
- 发送封装：`backend/app/feishu.py`
- 推送接口：`backend/app/routers/sessions.py`
  - `POST /api/sessions/{id}/push`（个人发送模式，受白名单/测试模式限制）
  - `POST /api/sessions/{id}/push-to-test-group`（测试群安全模式）

### 5.2 环境变量（运维统一下发；不要进 Git）
最小必填：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_BOT_WEBHOOK`（用于拼接前端可访问地址；建议为云端域名或公网 IP）

安全策略（强烈建议默认开启）：
- `FEISHU_TEST_MODE=true`
- `FEISHU_TEST_CHAT_ID=oc_...`
- `FEISHU_DRY_RUN=true`（先演练，确认无误后再置为 false）
- `FEISHU_TEST_WHITELIST=ou_...`（当关闭测试群模式、改个人白名单发送时使用）

> 目标：先确保只发测试群，且默认 dry-run，不可能误发到业务群/老板群。

---

## 6. 开发/演示辅助（避免验收卡死）
### 6.1 清空今日会话（仅本地 mock）
`POST /api/sessions/dev/reset-today`  
实现：`backend/app/routers/sessions.py`

安全边界：
- 仅 `DEBUG=true` 且 `use_mock_data=true`（即未配置 SOURCE_DB_*）可用；否则 403。

用途：
- 本地反复验收"未提交 → 填写 → 提交"闭环，不被"已提交"状态卡住。

---

## 7. 对 DateUse 的最小对接请求（Hermes 协调点）
> 目标：让"过程视角"真正落地（每次执行的进展/信息），并稳定映射工程师身份。

### 7.1 身份映射（P0）
需要明确工程师主键：建议以 `admin_id` 为主，并补充 `feishu_id/mobile` 用于交叉校验。

### 7.2 执行过程明细（P1，支撑"每次执行进展"）
当前系统支持 `exec_count` + 轨迹/投料/调整等聚合字段；若要做到"每一次执行都有一条记录"的时间线，需要 DateUse 同步：
- 每次执行的时间点/状态/关键参数差异（可落到 `raw_execution_*` 或 `core_execution_*`）
- 并提供与 `recipe_id/sn/company_id/uuid` 的可追溯关联键

---

## 8. 运维部署建议（最小可用）
### 8.1 云端服务形态
- `frontend`：对公网 80/443（或临时对公网端口）
- `backend`：可仅内网，由反代转发 `/api`
- `mysql`：仅内网，定期备份

### 8.2 必须具备的运维能力（P0）
- DB 备份（至少每日）
- 密钥管理（`.env` 不入库、不入 Git）
- 日志（容器日志可追溯）

---

## 9. 统一验收清单（Hermes 可直接用）
- [ ] DateUse 写入的结构化数据能在云端 MySQL 查到（raw/core 或等价）
- [ ] review-app 能基于结构化数据创建当日会话（biz）
- [ ] 飞书测试群模式 + dry-run 演练成功（不误发）
- [ ] 工程师点击卡片按钮能打开填写页并提交
- [ ] 提交结果在 DB 可回溯（session/answers/candidates）
- [ ] 管理端可查看与审核候选（并可追溯来源）
