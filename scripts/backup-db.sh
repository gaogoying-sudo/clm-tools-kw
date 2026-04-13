#!/bin/bash
# CLM-REVIEW-TOOL 数据库备份脚本
# 使用方法：
# 1. 配置环境变量或使用默认值
# 2. 添加到 crontab: 0 2 * * * /opt/clm-review-tool/scripts/backup-db.sh

set -e

# 配置
DEPLOY_DIR="${DEPLOY_DIR:-/opt/clm-review-tool}"
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/clm-review-tool}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录
mkdir -p $BACKUP_DIR

log_info "开始备份 CLM-REVIEW-TOOL 数据库..."
log_info "备份目录：$BACKUP_DIR"
log_info "备份时间：$DATE"

# 检查 Docker 容器
if ! docker ps | grep -q clm-review-tool.*mysql; then
    log_error "MySQL 容器未运行"
    exit 1
fi

# 数据库备份
BACKUP_FILE="$BACKUP_DIR/db_$DATE.sql"
log_info "正在导出数据库..."

docker compose -f $DEPLOY_DIR/docker-compose.yml --env-file $DEPLOY_DIR/.env.prod exec -T mysql \
    mysqldump -u root -p$MYSQL_ROOT_PASSWORD \
    --single-transaction \
    --routines \
    --triggers \
    clm_review > $BACKUP_FILE

# 压缩备份
log_info "正在压缩备份文件..."
COMPRESSED_FILE="$BACKUP_DIR/db_$DATE.sql.tar.gz"
tar -czf $COMPRESSED_FILE -C $BACKUP_DIR db_$DATE.sql
rm $BACKUP_FILE

# 显示备份大小
BACKUP_SIZE=$(du -h $COMPRESSED_FILE | cut -f1)
log_info "备份完成：$COMPRESSED_FILE (大小：$BACKUP_SIZE)"

# 清理旧备份
log_info "清理 $RETENTION_DAYS 天前的旧备份..."
find $BACKUP_DIR -name "db_*.sql.tar.gz" -mtime +$RETENTION_DAYS -delete
REMAINING=$(ls -1 $BACKUP_DIR/db_*.sql.tar.gz 2>/dev/null | wc -l)
log_info "剩余备份数量：$REMAINING"

# 验证备份（可选）
# log_info "验证备份完整性..."
# tar -tzf $COMPRESSED_FILE > /dev/null || {
#     log_error "备份文件损坏"
#     exit 1
# }

log_info "✅ 备份成功完成"

# 可选：上传到远程存储（如 S3、OSS）
# log_info "上传备份到远程存储..."
# aws s3 cp $COMPRESSED_FILE s3://your-bucket/clm-backups/

exit 0
