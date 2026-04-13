# 数据同步配置指南

## 概述

CLM-REVIEW-TOOL 支持两种数据同步模式：

1. **Mock 模式**（默认）：生成模拟数据用于本地开发和测试
2. **真实数据源模式**：从公司后台 MySQL 数据库拉取真实数据

## Mock 模式（默认）

无需额外配置，直接启动即可：

```bash
cd /Users/mac/Projects/clm-tools-kw
docker compose up -d
```

系统会自动生成：
- 36 位工程师的近 30 天模拟数据
- 16 道菜的完整功率轨迹和投料时序
- 异常场景触发题

## 真实数据源模式

### 1. 配置环境变量

在 `.env` 文件中添加以下配置：

```bash
# === Source DB (公司后台数据库) ===
SOURCE_DB_HOST=your-db-host.example.com
SOURCE_DB_PORT=3306
SOURCE_DB_USER=your_username
SOURCE_DB_PASSWORD=your_password
SOURCE_DB_NAME=btyc
```

### 2. 数据库表结构要求

源数据库需要包含以下表：

- `btyc.ums_admin` - 管理员账户表
- `btyc.ums_role` - 角色表
- `btyc.ums_company` - 公司表
- `btyc.auth_user` - 认证用户表
- `btyc.auth_user_role_rel` - 用户角色关联表
- `btyc.auth_role` - 角色表
- `btyc.main_recipe` - 主菜谱表
- `btyc.recipe_detail` - 菜谱详情表

### 3. 工程师映射

系统会自动将工程师名字与源数据库中的账户进行匹配：
- 匹配字段：full_name, nickname, username, mobile, email
- 匹配策略：精确匹配 > 包含匹配（中文）> 包含匹配（拉丁字母）
- 输出：admin_id 或 account_id

### 4. 切换模式

设置 `SOURCE_DB_HOST` 后，系统自动切换到真实数据源模式。

要切换回 Mock 模式，清空 `SOURCE_DB_HOST` 即可：

```bash
SOURCE_DB_HOST=
```

## API 端点

### 查看同步状态

```bash
curl http://localhost:8001/api/admin/sync/status \
  -H "X-Admin-Token: your_admin_token"
```

### 手动触发当天同步

```bash
curl -X POST http://localhost:8001/api/admin/sync/trigger/today \
  -H "X-Admin-Token: your_admin_token"
```

强制重新同步（覆盖已有数据）：

```bash
curl -X POST "http://localhost:8001/api/admin/sync/trigger/today?force=true" \
  -H "X-Admin-Token: your_admin_token"
```

### 手动触发历史同步（仅 Mock 模式）

```bash
curl -X POST "http://localhost:8001/api/admin/sync/trigger/history?days=30" \
  -H "X-Admin-Token: your_admin_token"
```

### 查看源数据库配置状态

```bash
curl http://localhost:8001/api/admin/sync/config \
  -H "X-Admin-Token: your_admin_token"
```

## 定时同步

系统默认每天 `18:30`（Asia/Shanghai 时区）自动执行同步任务。

修改时间：

```bash
# .env
PUSH_TIME=18:30
PUSH_TIMEZONE=Asia/Shanghai
```

## 故障排查

### 源数据库连接失败

检查：
1. 网络连接是否正常
2. 数据库主机和端口是否正确
3. 用户名和密码是否正确
4. 防火墙是否允许连接

### 工程师匹配失败

检查：
1. 工程师名字是否与源数据库中的 full_name/nickname 匹配
2. 尝试使用别名（aliases）配置
3. 查看日志中的匹配详情

### 数据格式错误

检查：
1. cook_steps_json 是否为有效的 JSON 格式
2. power_profile 和 ingredient_sequence 是否为 JSON 数组
3. 日期格式是否为 ISO 8601（YYYY-MM-DD）

## 安全注意事项

1. **不要将 .env 文件提交到 Git** - 已添加到 .gitignore
2. **生产环境使用强密码** - 默认密码仅用于本地开发
3. **限制数据库权限** - 源数据库账户只需 READ ONLY 权限
4. **启用 FEISHU_DRY_RUN** - 测试期间保持开启，防止误发消息
