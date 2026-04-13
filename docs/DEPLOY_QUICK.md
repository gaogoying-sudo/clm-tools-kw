# 🚀 快速部署指南 - 检索页增强版

**更新时间:** 2026-04-13 04:00  
**版本:** e40fb1f  
**变更内容:**
- ✅ 检索页缓存保留（切换页面后结果不丢失）
- ✅ 增强详情展示（功率轨迹瀑布流 + 投料时序 + 烹饪步骤）

---

## 📋 部署步骤

### 方案 A: 自动部署（推荐）

```bash
# 1. SSH 登录云服务器
ssh root@82.156.187.35

# 2. 进入项目目录
cd /opt/clm-review-tool

# 3. 拉取最新代码
git pull

# 4. 重启服务
docker compose restart

# 5. 查看日志确认
docker compose logs -f backend
```

### 方案 B: 手动部署

```bash
# SSH 登录后执行：
cd /opt/clm-review-tool
git pull
docker compose down
docker compose up -d
```

---

## 🔍 验证部署

### 1. 检查服务状态
```bash
docker compose ps
```

### 2. 访问前端
打开浏览器访问：`http://82.156.187.35:8081`

### 3. 验证新功能

**测试检索页缓存：**
1. 进入"数据检索"页面
2. 设置筛选条件并点击"检索"
3. 切换到其他页面（如"数据看板"）
4. 返回"数据检索"页面
5. ✅ 查询结果应该仍然显示

**测试详情展示：**
1. 在检索结果中点击任意会话展开
2. ✅ 应该看到：
   - 功率轨迹瀑布流（蓝色柱状图）
   - 投料时序列表
   - 烹饪步骤列表
   - 备菜须知标签
   - 烹饪参数卡片

---

## 🐛 故障排查

### 问题 1: 检索页仍然丢失数据
**原因:** 浏览器缓存未刷新  
**解决:** 强制刷新页面（Ctrl+Shift+R 或 Cmd+Shift+R）

### 问题 2: 详情展示为空
**原因:** 数据库中缺少详细数据  
**解决:** 
```bash
# 查看后端日志
docker compose logs backend | grep -i error

# 重新同步数据
curl -X POST "http://localhost:8001/api/admin/sync/trigger/history?days=7" \
  -H "X-Admin-Token: YOUR_ADMIN_TOKEN"
```

### 问题 3: 功率轨迹不显示
**原因:** mock 数据中 power_trace 为空  
**解决:** 等待真实数据源接入，或重新生成 mock 数据

---

## 📊 本次更新详情

### 前端变更
- `frontend/src/pages/SearchPage.jsx`
  - 新增 localStorage 缓存机制（5 分钟有效期）
  - 新增功率轨迹瀑布流可视化
  - 新增投料时序、烹饪步骤、备菜须知展示
  - 新增烹饪参数卡片

### 后端变更
- `backend/app/models.py`
  - 新增 `cook_steps` JSON 字段
- `backend/app/routers/search.py`
  - 增强任务详情返回数据（包含功率轨迹、投料时序等）

### 数据库变更
- `sync_tasks` 表新增 `cook_steps` 列（JSON 类型）

---

## 🎯 访问地址

- **前端:** http://82.156.187.35:8081
- **后端 API:** http://82.156.187.35:8001
- **API 文档:** http://82.156.187.35:8001/docs

---

## ⏭️ 下一步

部署完成后：
1. 用户访问前端验证新功能
2. 测试检索页缓存功能
3. 测试详情展示瀑布流
4. 反馈问题或继续推进 Phase 3

---

**部署负责人:** 小强  
**预计耗时:** 5-10 分钟  
**回滚方案:** `git checkout 98d2a02 && docker compose restart`
