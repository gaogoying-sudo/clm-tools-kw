# 云环境部署指南

## 目标环境

- **云服务器 IP:** 82.156.187.35
- **部署目录:** /opt/clm-review-tool/
- **端口映射:**
  - 前端：8081 → 80
  - 后端：8001 → 8001
  - MySQL：3307 → 3306（仅内网访问）

## 部署前准备

### 1. 本地验证清单

在上传代码到云服务器前，确保本地已完成：

- [x] Docker 本地环境运行正常
- [x] 所有 API 端点测试通过
- [x] 前端 5 个页面功能正常
- [x] 数据同步链路打通（T05）
- [ ] 源数据库配置信息确认（T09）
- [ ] GitHub 代码最新提交

### 2. 云服务器环境要求

```bash
# SSH 登录
ssh root@82.156.187.35

# 检查 Docker
docker --version
docker compose version

# 检查磁盘空间
df -h /opt

# 检查端口占用
netstat -tlnp | grep -E '80|8001|3306'
```

## 部署步骤

### Step 1: 创建部署目录

```bash
# SSH 登录云服务器
ssh root@82.156.187.35

# 创建部署目录
mkdir -p /opt/clm-review-tool
cd /opt/clm-review-tool
```

### Step 2: 克隆代码

```bash
# 从 GitHub 克隆
git clone git@github.com:gaogoying-sudo/clm-tools-kw.git .
# 或
git clone https://github.com/gaogoying-sudo/clm-tools-kw.git .
```

### Step 3: 配置环境变量

创建 `.env.prod` 文件：

```bash
cat > .env.prod << 'EOF'
# === MySQL ===
MYSQL_ROOT_PASSWORD=<STRONG_ROOT_PASSWORD>
MYSQL_DATABASE=clm_review
MYSQL_USER=clm
MYSQL_PASSWORD=<STRONG_CLM_PASSWORD>

# === Backend ===
DATABASE_URL=mysql+pymysql://clm:<STRONG_CLM_PASSWORD>@mysql:3306/clm_review?charset=utf8mb4
DEBUG=false
use_mock_data=false
ADMIN_TOKEN=<ADMIN_TOKEN_FOR_DASHBOARD>
API_PORT=8001

# === Feishu (生产环境配置) ===
FEISHU_APP_ID=cli_a92b81d03838dbb3
FEISHU_APP_SECRET=TO17YrJH0FmJdNqkw2ybhgSpMqS8YK0c
FEISHU_DRY_RUN=false
FEISHU_TEST_MODE=false
FEISHU_TEST_CHAT_ID=oc_c2eaef0dca9716e687620eec72bbcaa6
FEISHU_TEST_WHITELIST=ou_40025e775477ba7ffce200c9d0bebe02

# === Push Schedule ===
PUSH_TIME=18:30
PUSH_TIMEZONE=Asia/Shanghai

# === Source DB (公司后台数据库) ===
SOURCE_DB_HOST=<COMPANY_DB_HOST>
SOURCE_DB_PORT=3306
SOURCE_DB_USER=<COMPANY_DB_USER>
SOURCE_DB_PASSWORD=<COMPANY_DB_PASSWORD>
SOURCE_DB_NAME=btyc
EOF
```

**注意：** 将 `<xxx>` 替换为实际值

### Step 4: 启动服务

```bash
# 使用生产环境配置启动
docker compose --env-file .env.prod up -d

# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
```

### Step 5: 验证部署

```bash
# 健康检查
curl http://localhost:8001/health

# API 测试
curl http://localhost:8001/api/admin/sync/status \
  -H "X-Admin-Token: <ADMIN_TOKEN>"

# 前端访问
curl http://localhost:8081/
```

### Step 6: 配置 Nginx（可选）

如果需要反向代理和 HTTPS：

```bash
# 安装 Nginx
apt update && apt install -y nginx

# 创建 Nginx 配置
cat > /etc/nginx/sites-available/clm-review-tool << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/clm-review-tool /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## 数据迁移

### 从本地导入数据

```bash
# 1. 本地导出数据库
docker compose exec mysql mysqldump -u root -p clm_review > backup.sql

# 2. 上传到云服务器
scp backup.sql root@82.156.187.35:/opt/clm-review-tool/

# 3. 云服务器导入
docker compose exec -T mysql mysql -u root -p clm_review < backup.sql
```

### 初始化数据

```bash
# 如果从头开始，运行数据同步
curl -X POST http://localhost:8001/api/admin/sync/trigger/history?days=30 \
  -H "X-Admin-Token: <ADMIN_TOKEN>"
```

## 监控与维护

### 查看日志

```bash
# 实时日志
docker compose logs -f

# 后端日志
docker compose logs -f backend

# MySQL 慢查询日志
docker compose exec mysql tail -f /var/log/mysql/slow.log
```

### 备份策略

```bash
# 创建备份脚本
cat > /opt/clm-review-tool/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/clm-review-tool"
mkdir -p $BACKUP_DIR

# 数据库备份
docker compose exec -T mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD clm_review > $BACKUP_DIR/db_$DATE.sql

# 压缩
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C /opt/clm-review-tool .

# 清理 7 天前的备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/clm-review-tool/backup.sh

# 添加到 crontab（每天凌晨 2 点）
echo "0 2 * * * /opt/clm-review-tool/backup.sh" | crontab -
```

### 服务重启

```bash
# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart backend

# 更新代码后重新部署
cd /opt/clm-review-tool
git pull
docker compose down
docker compose up -d
```

## 故障排查

### 常见问题

**1. 容器无法启动**
```bash
# 查看日志
docker compose logs backend

# 检查端口占用
netstat -tlnp | grep 8001

# 检查磁盘空间
df -h
```

**2. 数据库连接失败**
```bash
# 检查 MySQL 是否运行
docker compose ps mysql

# 测试数据库连接
docker compose exec backend python3 -c "from app.database import engine; print(engine.connect())"
```

**3. 飞书消息发送失败**
```bash
# 检查配置
curl http://localhost:8001/api/admin/sync/config

# 查看飞书日志
docker compose logs backend | grep feishu
```

### 回滚方案

```bash
# 1. 停止当前服务
docker compose down

# 2. 恢复旧版本代码
cd /opt/clm-review-tool
git checkout <PREVIOUS_COMMIT>

# 3. 恢复数据库备份
mysql -u root -p clm_review < /opt/backups/clm-review-tool/db_<DATE>.sql

# 4. 重新启动
docker compose up -d
```

## 安全注意事项

1. **强密码策略** - 所有密码使用强密码生成器
2. **防火墙配置** - 仅开放必要端口（80/443）
3. **定期更新** - 定期运行 `apt update && apt upgrade`
4. **备份验证** - 定期测试备份恢复流程
5. **日志审计** - 定期检查访问日志和错误日志
6. **飞书安全** - 生产环境关闭 DRY_RUN 前确保配置正确

## 性能优化

### MySQL 优化

```bash
# 编辑 MySQL 配置
cat > /opt/clm-review-tool/mysql.cnf << 'EOF'
[mysqld]
max_connections=200
innodb_buffer_pool_size=512M
query_cache_size=64M
slow_query_log=1
slow_query_log_file=/var/log/mysql/slow.log
long_query_time=2
EOF

# 挂载配置
# 在 docker-compose.yml 中添加：
# volumes:
#   - ./mysql.cnf:/etc/mysql/conf.d/custom.cnf
```

### 后端优化

```bash
# 设置 worker 数量（多核 CPU）
# 在 docker-compose.yml 中：
# command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 联系支持

- 项目文档：`/opt/clm-review-tool/docs/`
- API 文档：`http://<SERVER_IP>:8001/docs`
- 管理后台：`http://<SERVER_IP>:8081`
