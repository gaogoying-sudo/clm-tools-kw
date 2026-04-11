# CLM 录菜复盘助手 — 使用说明（试运行前操作路径）

本文档基于**现有真实 API**，说明如何完成：同步数据、查看会话、查看问题流、修改问题模板、验证变化。  
**不依赖任何 seed/sample 专用接口。**

---

## 一、地址与入口

| 入口 | 地址 |
|------|------|
| 管理后台（前端） | http://localhost:8081 或 http://your-server:8081 |
| API 文档（OpenAPI） | http://localhost:8001/docs 或 http://your-server:8001/docs |
| 工程师填写页 | http://localhost:8081/#/fill/{session_id} |

**Admin 相关入口**：管理后台顶部 Tab  
- **今日总览**：同步今日数据、查看工程师列表、展开会话详情  
- **历史记录**：按日期范围查看会话、导出 CSV  
- **经验候选**：查看/管理回收的经验  
- **问题管理**：查看、编辑问题模板  

---

## 二、真实验证链路（可执行流程）

### 步骤 1：同步今日数据

**前端**：  
管理后台 → 今日总览 → 选择今天日期 → 点击「同步今日数据」

**API**：
```bash
curl -X POST http://localhost:8001/api/sessions/sync-today
```

说明：会从 sync_service 拉取/生成当天录菜任务，为每个工程师创建会话。  
若 `SOURCE_DB_HOST` 未配置，则使用内置模拟数据（辣椒炒肉等）。

---

### 步骤 2：查看今天会话列表

**前端**：  
管理后台 → 今日总览 → 同步后列表中会显示各工程师及 session_id

**API**：
```bash
curl http://localhost:8001/api/sessions/today/list
```

返回示例：
```json
[
  {
    "session_id": 1,
    "engineer": {"id": 1, "name": "张明", ...},
    "status": "pending",
    "task_count": 3,
    "total_exec": 5,
    "failed_count": 0,
    "question_count": 6
  }
]
```

---

### 步骤 3：查看会话详情（含问题流）

**前端**：  
- 待提交会话：直接访问 `http://localhost:8081/#/fill/{session_id}` 查看填写页问题流  
- 已提交会话：管理后台 → 今日总览 / 历史记录 → 点击某工程师行 → 展开查看完整问答与分类

**API**：
```bash
curl "http://localhost:8001/api/sessions/1"
```

返回：`engineer`、`tasks`、`questions`（问题流）、`answers`（已提交的回答）、`root_event_type` 等。

---

### 步骤 4：提交测试答案（可选）

**前端**：  
访问 `http://localhost:8081/#/fill/{session_id}` → 按问题流填写 → 提交

**API**：
```bash
curl -X POST http://localhost:8001/api/answers/1/submit \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_key": "q_entry", "answer_type": "single", "answer_json": "今天整体比较顺，没什么特别的"},
      {"question_key": "q_factor", "answer_type": "multi", "answer_json": []},
      {"question_key": "q_anchor", "answer_type": "anchor", "answer_json": {"taskId": 1, "dishName": "辣椒炒肉", "reason": "常规过"}, "related_task_id": 1},
      {"question_key": "q_experience", "answer_type": "text", "answer_text": "今天比较顺"}
    ],
    "duration_seconds": 60
  }'
```

说明：`related_task_id` 与 `taskId` 需为 `SyncTask.id`（来自 `GET /sessions/{id}` 的 `tasks[].id`）。

---

### 步骤 5：查看后台分类结果

**前端**：  
管理后台 → 今日总览 / 历史记录 → 展开已提交会话 → 查看 qa_list 与分类

**API**：
```bash
curl http://localhost:8001/api/admin/sessions/1/answers
```

返回：`summary_snapshot`、`root_event_type`、`pool`（分类池）、`qa_list`（问答列表）。

---

## 三、问题模板管理

### 查看当前模板

**前端**：管理后台 → 问题管理 Tab

**API**：
```bash
curl http://localhost:8001/api/admin/questions
```

### 修改某条题目

**前端**：管理后台 → 问题管理 → 点击编辑 → 修改 title / subtitle / placeholder / options / display_order 等 → 保存

**API**：
```bash
# 例：修改 q_anchor 的 placeholder
curl -X PUT http://localhost:8001/api/admin/questions/3 \
  -H "Content-Type: application/json" \
  -d '{"placeholder": "为什么选这道菜？请简短说明"}'
```

可修改字段：`title`, `subtitle`, `placeholder`, `options`, `display_order`, `sort_order`, `is_active`, `node_type`, `related_event_type` 等（见 `QuestionUpdateRequest`）。

### 再次验证问题流变化

1. 修改模板后，无需重启服务。  
2. 重新打开 `GET /api/sessions/{session_id}` 或填写页 `#/fill/{session_id}`，问题流会从数据库实时加载，即可看到新文案。

---

## 四、API 速查

| 接口 | 方法 | 用途 |
|------|------|------|
| `/api/sessions/sync-today` | POST | 同步今日数据并创建会话 |
| `/api/sessions/today/list` | GET | 今日会话列表 |
| `/api/sessions/{session_id}` | GET | 会话详情（任务 + 问题流 + 回答） |
| `/api/answers/{session_id}/submit` | POST | 提交回答 |
| `/api/admin/dashboard` | GET | 仪表盘统计（可带 `target_date`） |
| `/api/admin/engineers` | GET | 工程师及当日状态（可带 `target_date`） |
| `/api/admin/sessions/{id}/answers` | GET | 会话完整问答及分类 |
| `/api/admin/questions` | GET | 所有问题模板 |
| `/api/admin/questions` | POST | 创建问题模板 |
| `/api/admin/questions/{id}` | PUT | 更新问题模板 |
| `/api/admin/questions/{id}` | DELETE | 删除/禁用问题模板 |
| `/api/admin/history` | GET | 按日期范围历史会话 |
| `/api/admin/export` | GET | 导出 CSV |

---

## 五、真实会话问题流样本（基于 sync 后的数据）

同步后，每个会话的 `questions` 来自 `question_engine.select_flow_questions`，典型顺序：

1. **q_entry**（入口题）：今天最值得说的一件事，更接近下面哪种情况？  
2. **q_factor**（分支题）：今天最关键的影响因素是什么？  
3. **q_anchor**（分支题）：今天最想说的是哪道菜？  
4. **q_experience**（分支题）：用一句话说清楚，你会怎么说？  
5. 若选「客户今天提了明显意见」→ 追加 **q_customer**  
6. 若有失败任务或高执行次数 → 追加 **q_fail**、**q_retry**（触发题）

分类池由入口题映射：  
- iterative_debugging → tuning_record  
- customer_feedback → customer_pref  
- key_adjustment / reusable_method → experience  
- abnormal_failure → failure_case  
- normal_day → daily_record  

---

## 六、剩余只需微调的内容

1. **文案**：在问题管理 Tab 或 `PUT /api/admin/questions/{id}` 修改 title、subtitle、placeholder。  
2. **选项**：修改 `options` 数组。  
3. **顺序**：修改 `display_order`、`sort_order`。  
4. **触发规则**：在 `question_engine.py` 中调整 `has_failed`、`has_high_exec` 等条件（需改代码）。  

---

## 七、首次使用前

1. 启动服务：`docker-compose up -d`  
2. 初始化数据库：`docker-compose exec backend python -m app.init_db`  
3. 同步今日数据：管理后台点击「同步今日数据」或调用 `POST /api/sessions/sync-today`
