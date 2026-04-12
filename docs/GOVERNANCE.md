# CLM-Tools 项目治理制度 v1.0

**创建人：** 小强  
**日期：** 2026-04-12  
**状态：** 待确认

---

## 一、治理架构（三层结构）

```
┌─────────────────────────────────────────────────────┐
│  第一层：Memory 索引层（最小、最快、跨会话持久化）      │
│  - 项目昵称 + 路径 + 当前阶段 + 下一步                │
│  - 关键资源快速索引                                   │
│  - 角色区分（小厨 = CLM项目专属）                     │
└─────────────────────────────────────────────────────┘
                        ↓ 读取
┌─────────────────────────────────────────────────────┐
│  第二层：项目文档层（docs/ 目录，完整上下文）           │
│  - progress.md       每日进度追踪                    │
│  - TASK_BOARD.md     任务看板（Backlog/Doing/Done）  │
│  - RESOURCE.md       资源登记（服务器/DB/API/端口）   │
│  - decisions/        架构决策记录（ADR）              │
└─────────────────────────────────────────────────────┘
                        ↓ 查询
┌─────────────────────────────────────────────────────┐
│  第三层：代码图谱层（graphify，自动更新的代码知识）     │
│  - GRAPH_REPORT.md   架构全景、上帝节点、社区结构      │
│  - graph.json        完整依赖关系数据                 │
│  - graph.html        可视化图谱（可选查看）            │
│  - Git Hook自动更新  commit/checkout后自动重建        │
└─────────────────────────────────────────────────────┘
```

---

## 二、三层职责边界

| 层级 | 存什么 | 不存什么 | 更新频率 |
|------|--------|---------|---------|
| Memory | 项目身份、路径、阶段、下一步 | 详细需求、代码、长讨论 | 有变化时 |
| docs/ | 进度、任务看板、资源、决策 | 代码细节（graphify管） | 每天 |
| graphify | 代码结构、依赖、影响分析 | 业务逻辑讨论、进度 | 每次commit |

---

## 三、Graphify 使用规范

### 3.1 什么时候用 Graphify

| 场景 | 用 graphify 做什么 |
|------|-------------------|
| 新会话醒来 | 先看 GRAPH_REPORT.md，快速了解代码结构变化 |
| 改代码前 | 查依赖关系，知道会影响哪些文件 |
| 回答架构问题 | 用图谱代替逐文件读取 |
| 代码审查 | 检查变更是否破坏了依赖结构 |
| 新人交接 | 图谱就是最直观的代码地图 |

### 3.2 Graphify 配置要求

1. **AGENTS.md** 必须包含 graphify 规则（已有）
2. **Git Hooks** 必须安装 commit/checkout 自动重建
3. **graphify-out/** 必须被 .gitignore 排除（本地生成即可）

### 3.3 Graphify 安装与初始化

```bash
cd /Users/mac/Projects/clm-tools-kw
pipx install graphifyy
graphify-out/wiki/index.md  # 如果支持wiki导航
# 手动触发首次构建
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

---

## 四、每次会话的固定流程

### 会话开始（恢复工作）
```
1. 读取 Memory → 确认是哪个项目、当前阶段
2. 读取 docs/progress.md → 看上次做到哪了、有什么阻塞
3. 读取 docs/TASK_BOARD.md → 看当前任务优先级
4. （如有graphify）读取 graphify-out/GRAPH_REPORT.md → 了解代码结构
5. 开始工作
```

### 会话结束（收尾工作）
```
1. 更新 docs/progress.md → 记录做了什么、下一步、阻塞项
2. 更新 docs/TASK_BOARD.md → 移动任务状态
3. （如有关键变化）更新 Memory → 阶段/路径/下一步
4. Git commit → 触发 graphify 自动重建
```

---

## 五、任务看板格式（TASK_BOARD.md）

用简单看板，不引入外部系统：

```markdown
# CLM-Tools 任务看板

## Backlog（待开发）
| ID | 任务 | 优先级 | 依赖 | 预计耗时 |
|----|------|--------|------|---------|
| T02 | Docker环境验证 | P0 | - | 30min |
| T03 | 数据同步打通 | P0 | T02 | 2h |
| T04 | 前后端闭环 | P1 | T03 | 3h |

## Doing（进行中）
| ID | 任务 | 开始时间 | 备注 |
|----|------|---------|------|
| T01 | 项目骨架搭建 | 04-12 00:45 | 已完成，待确认 |

## Done（已完成）
| ID | 任务 | 完成时间 | Commit |
|----|------|---------|--------|
| T01 | 项目骨架搭建 | 04-12 00:55 | 2359168 |
```

---

## 六、进度日志格式（progress.md）

```markdown
# CLM-Tools 进度日志

## 2026-04-12
**00:55** [小强] Phase 0 完成
- 整合后端/前端/data-sync代码
- 创建 docker-compose.yml
- 编写 PROJECT_ANALYSIS.md + WORK_PLAN.md
- Git commit (2359168)

**下一步：**
- Docker 环境验证
- 数据同步打通

**阻塞项：**
- GitHub push 超时（需SSH key配置）
```

---

## 七、资源登记（RESOURCE.md）

所有外部资源统一登记，**敏感信息不进Git**：

```markdown
# CLM-Tools 资源登记

## 云服务器
- IP: 82.156.187.35
- SSH: root@82.156.187.35
- 部署目录: /opt/clm-review-tool/
- 状态: MySQL 8.0 运行中

## 本地开发
- 路径: /Users/mac/Projects/clm-tools-kw/
- Git: git@github.com:gaogoying-sudo/clm-tools-kw.git
- 端口: 前端8081 / 后端8001 / MySQL 3307

## 飞书
- APP_ID: cli_a92b81d03838dbb3
- APP_SECRET: (见.env.prod / Memory)
- 测试群 chat_id: oc_c2eaef0dca9716e687620eec72bbcaa6
- 安全策略: DRY_RUN=true, TEST_MODE=true

## 数据库
- 本地: localhost:3307 (clm_review)
- 云端: 82.156.187.35:3306 (MySQL 8.0)
- 公司源: 待配置 (btyc)
```

---

## 八、防遗忘机制

### 8.1 关键信息持久化（防丢失）
- Memory：最核心的身份/路径/阶段信息
- docs/RESOURCE.md：完整资源清单
- .env.example：环境变量模板
- PROJECT_ANALYSIS.md：项目全景分析

### 8.2 每次新会话自动读取清单
1. Memory（自动注入）
2. docs/progress.md（读取最近3次记录）
3. docs/TASK_BOARD.md（读取当前Doing项）
4. graphify-out/GRAPH_REPORT.md（如有变更）

### 8.3 角色确认
每次会话开始，如果上下文模糊，主动询问：
> "现在是哪个项目？CLM项目用「小厨/小强」称呼。"

---

## 九、决策记录（ADR）

```
docs/decisions/
├── 001-tech-stack.md         # 技术选型决策
├── 002-docker-setup.md       # Docker环境决策
├── 003-data-strategy.md      # 数据同步策略
└── ...
```

每个ADR格式：
```markdown
# 001. [决策标题]
**日期：** YYYY-MM-DD
**状态：** 已采纳 / 已废弃 / 修订中

## 背景
## 决策
## 理由
## 影响
```

---

## 十、总结：三层治理的价值

| 问题 | 传统方式 | 三层治理 |
|------|---------|---------|
| "上次做到哪了？" | 回忆或翻聊天记录 | 看 docs/progress.md |
| "下一步做什么？" | 凭记忆 | 看 TASK_BOARD.md |
| "代码结构是什么？" | 逐文件读 | 看 GRAPH_REPORT.md |
| "这个改动会影响什么？" | 凭经验猜 | 看 graphify 依赖关系 |
| "云服务器密码是什么？" | 翻聊天记录 | 看 RESOURCE.md |
| "新项目重启" | 全部重新了解 | Memory + docs/ + graphify 自动恢复 |

---

**最后更新：** 2026-04-12
