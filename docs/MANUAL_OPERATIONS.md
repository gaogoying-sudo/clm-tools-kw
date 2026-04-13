# 待用户手动操作清单

> 本文档记录需要用户手动处理的配置和操作，AI 无法代劳。
> 更新日期：2026-04-13 03:00

---

## 🔐 敏感信息配置

以下信息需要用户手动填写，**不要提交到 Git**：

### 1. 生产环境配置 `.env.prod`

**位置：** 云服务器 `/opt/clm-review-tool/.env.prod`

**必须配置项：**

```bash
# MySQL 密码（使用强密码生成器）
MYSQL_ROOT_PASSWORD=<替换为强密码>
MYSQL_PASSWORD=<替换为强密码>

# 管理后台访问令牌
ADMIN_TOKEN=<替换为随机字符串，建议 32 位以上>

# 公司后台数据库连接（待确认）
SOURCE_DB_HOST=<公司数据库主机 IP 或域名>
SOURCE_DB_USER=<公司数据库用户名>
SOURCE_DB_PASSWORD=<公司数据库密码>
```

**可选配置项：**

```bash
# 飞书生产环境（确认无误后开启）
FEISHU_DRY_RUN=false       # 关闭演练模式
FEISHU_TEST_MODE=false     # 关闭测试群模式
```

---

## 📋 云服务器部署操作

### 前置条件确认

- [ ] 云服务器 SSH 密钥已配置
- [ ] Docker 和 Docker Compose 已安装
- [ ] 服务器防火墙规则已配置（开放 80/443/22 端口）
- [ ] 公司后台数据库连接信息已确认

### 部署步骤

**Step 1: SSH 登录云服务器**

```bash
ssh root@82.156.187.35
```

**Step 2: 检查环境**

```bash
# 检查 Docker
docker --version
docker compose version

# 检查磁盘空间
df -h /opt

# 检查端口占用
netstat -tlnp | grep -E '80|8001|3306'
```

**Step 3: 执行部署脚本**

```bash
cd /opt
# 如果还没有克隆代码
git clone git@github.com:gaogoying-sudo/clm-tools-kw.git clm-review-tool
cd clm-review-tool

# 执行部署脚本
chmod +x scripts/deploy-to-cloud.sh
./scripts/deploy-to-cloud.sh
```

**Step 4: 配置环境变量**

```bash
# 编辑配置文件
nano .env.prod

# 填写以下必填项：
# - MYSQL_ROOT_PASSWORD
# - MYSQL_PASSWORD
# - ADMIN_TOKEN
# - SOURCE_DB_HOST
# - SOURCE_DB_USER
# - SOURCE_DB_PASSWORD
```

**Step 5: 重启服务**

```bash
docker compose --env-file .env.prod up -d
```

**Step 6: 验证部署**

```bash
# 检查服务状态
docker compose ps

# 健康检查
curl http://localhost:8001/health
curl http://localhost:8081/

# 查看同步状态
curl http://localhost:8001/api/admin/sync/status
```

**Step 7: 初始化数据**

```bash
# 同步历史数据（近 30 天）
curl -X POST "http://localhost:8001/api/admin/sync/trigger/history?days=30" \
  -H "X-Admin-Token: <ADMIN_TOKEN>"

# 查看同步结果
curl http://localhost:8001/api/admin/sync/status \
  -H "X-Admin-Token: <ADMIN_TOKEN>"
```

---

## 🔍 验证清单

部署完成后，请逐项验证：

### 基础服务

- [ ] MySQL 容器运行正常
- [ ] Backend 容器运行正常
- [ ] Frontend 容器运行正常
- [ ] 所有容器健康检查通过

### API 测试

- [ ] `GET /health` 返回 `{"status":"ok"}`
- [ ] `GET /api/admin/sync/status` 返回正确统计
- [ ] `GET /api/admin/engineers` 返回工程师列表
- [ ] `GET /api/admin/dashboard` 返回仪表盘数据

### 前端测试

- [ ] 访问 `http://82.156.187.35:8081` 页面正常加载
- [ ] 登录页可以输入 ADMIN_TOKEN
- [ ] 数据看板页显示统计图表
- [ ] 数据检索页可以筛选查询
- [ ] 原始问答页显示数据列表

### 数据同步

- [ ] 源数据库连接成功（如果已配置）
- [ ] 历史数据同步完成
- [ ] 定时任务正常执行（18:30）

### 飞书推送（可选）

- [ ] 配置 FEISHU_DRY_RUN=false
- [ ] 测试消息发送
- [ ] 确认消息到达测试群

---

## 🛠️ 常用运维命令

### 查看服务状态

```bash
cd /opt/clm-review-tool
docker compose ps
```

### 查看日志

```bash
# 实时查看所有日志
docker compose logs -f

# 查看后端日志
docker compose logs -f backend

# 查看最近 100 行
docker compose logs --tail=100 backend
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart backend
```

### 更新代码

```bash
cd /opt/clm-review-tool
git pull
docker compose down
docker compose up -d
```

### 数据库备份

```bash
# 手动备份
./scripts/backup-db.sh

# 查看备份文件
ls -lh /opt/backups/clm-review-tool/
```

### 数据库恢复

```bash
# 从备份恢复
gunzip -c /opt/backups/clm-review-tool/db_20260413_020000.sql.tar.gz | \
  docker compose exec -T mysql mysql -u root -p$MYSQL_ROOT_PASSWORD clm_review
```

---

## 📞 问题反馈

如遇到问题，请提供以下信息：

1. **错误日志：** `docker compose logs backend | tail -100`
2. **服务状态：** `docker compose ps`
3. **配置文件：** `.env.prod`（隐藏敏感信息）
4. **复现步骤：** 详细描述操作步骤

---

## 📝 备注

- 所有密码请使用强密码生成器
- 定期更新服务器系统补丁：`apt update && apt upgrade -y`
- 定期检查磁盘空间：`df -h`
- 定期查看备份是否正常运行
