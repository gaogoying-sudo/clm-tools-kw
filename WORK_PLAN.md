# WORK_PLAN.md 小强开发计划

**创建：** 2026-04-12 00:50  
**状态：** Phase 0 完成，等待确认

---

## 当前进度

| Phase | 状态 | 完成时间 |
|-------|------|---------|
| Phase 0: 项目骨架搭建 | 已完成 | 2026-04-12 |
| Phase 1: Docker 本地环境验证 | 待确认 | - |
| Phase 2: 数据同步打通 | 待开始 | - |
| Phase 3: 后端完善 | 待开始 | - |
| Phase 4: 前端升级 | 待开始 | - |
| Phase 5: 完整闭环验证 | 待开始 | - |

---

## Phase 0 已完成内容

- [x] 从 CLM-Tools 复制后端代码 (backend/app/)
- [x] 从 CLM-Tools 复制前端代码 (frontend/src/)
- [x] 从 DateUse 复制数据同步代码 (data-sync/)
- [x] 复制关键文档到 docs/
- [x] 创建 docker-compose.yml (MySQL + Backend + Frontend)
- [x] 创建 .env.example + .env
- [x] 创建 .gitignore
- [x] 创建 README.md
- [x] 创建 PROJECT_ANALYSIS.md (完整分析)
- [x] Git 初始化并推送到远程仓库

---

## 下一步：Phase 1 (Docker 本地环境验证)

### 1.1 启动 Docker 环境
```bash
cd /Users/mac/Projects/clm-tools-kw
docker compose up -d
```

### 1.2 验证服务
```bash
# 检查 MySQL 是否就绪
docker compose logs mysql | tail -20

# 检查后端是否启动
curl http://localhost:8001/health

# 检查前端是否可访问
curl http://localhost:8081/ | head -5

# 查看 API 文档
open http://localhost:8001/docs
```

### 1.3 验证数据链路
```bash
# 同步今日数据（mock）
curl -X POST http://localhost:8001/api/sessions/sync-today

# 查看生成的会话
curl http://localhost:8001/api/sessions/today

# 查看工程师列表
curl http://localhost:8001/api/engineers
```

### 1.4 预期问题与解决
- **MySQL 连接失败：** 等待 healthcheck 通过再访问后端
- **后端启动失败：** 检查 requirements.txt 是否完整
- **前端空白页：** 检查 VITE_API_URL 环境变量

---

## Phase 2: 数据同步打通

### 2.1 增强 mock 数据
当前 sync_service.py 使用 mock 数据，需要：
- 增加更多工程师（36人花名册）
- 增加更多菜品和过程数据
- 模拟真实的功率轨迹、投料时序
- 让测试数据更贴近真实场景

### 2.2 整合 data-sync 模块
- 将 data-sync 的工程师映射逻辑整合到后端
- 创建独立的 data-sync API 端点
- 验证从 mock 源数据到 sync_tasks 的完整链路

### 2.3 源数据库接入准备
- 确认源数据库连接信息
- 测试只读连接
- 编写数据同步脚本

---

## Phase 3: 后端完善

### 3.1 API 补全
- [ ] 添加错误处理和日志
- [ ] 添加请求/响应验证
- [ ] 完善 admin 鉴权
- [ ] 添加分页支持

### 3.2 数据导出
- [ ] CSV 导出
- [ ] Excel 导出（可选）

### 3.3 性能优化
- [ ] 数据库查询优化
- [ ] 缓存策略

---

## Phase 4: 前端升级

### 4.1 TailwindCSS 迁移
- [ ] 安装 TailwindCSS
- [ ] 替换内联样式
- [ ] 响应式优化

### 4.2 组件化
- [ ] 拆分 App.jsx 为独立组件
- [ ] 创建共享 UI 组件库

### 4.3 管理后台增强
- [ ] 数据可视化图表
- [ ] 筛选和搜索
- [ ] 批量操作

---

## Phase 5: 完整闭环验证

- [ ] 端到端测试
- [ ] 多工程师并发
- [ ] 异常流程
- [ ] 性能测试

---

## 关键决策记录

| 日期 | 决策 | 理由 |
|------|------|------|
| 2026-04-12 | 保留 FastAPI + SQLAlchemy | 已有完整模型，迁移成本高 |
| 2026-04-12 | 前端升级到 TailwindCSS | 内联样式难以维护 |
| 2026-04-12 | 先用 mock 数据跑通全链路 | 源DB连接信息待确认 |
| 2026-04-12 | 飞书默认 dry-run | 用户要求不发真实消息 |
| 2026-04-12 | 暂缓云部署 | 用户要求专注本地开发 |

---

**下次恢复时执行：** Phase 1 - Docker 环境验证
