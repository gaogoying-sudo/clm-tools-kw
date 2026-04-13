#!/bin/bash
# CLM-REVIEW-TOOL 云服务器部署脚本
# 使用方法：./deploy-to-cloud.sh

set -e

# 配置
CLOUD_IP="82.156.187.35"
DEPLOY_DIR="/opt/clm-review-tool"
PROJECT_NAME="clm-review-tool"

echo "🚀 CLM-REVIEW-TOOL 云部署脚本"
echo "=============================="
echo "目标服务器：$CLOUD_IP"
echo "部署目录：$DEPLOY_DIR"
echo ""

# 检查 SSH 连接
echo "📡 检查 SSH 连接..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes root@$CLOUD_IP "echo OK" > /dev/null 2>&1; then
    echo "❌ SSH 连接失败，请检查："
    echo "   1. 服务器 IP 是否正确"
    echo "   2. SSH key 是否已配置"
    echo "   3. 防火墙是否允许 SSH 连接"
    exit 1
fi
echo "✅ SSH 连接正常"
echo ""

# 检查 Docker
echo "🐳 检查 Docker 环境..."
ssh root@$CLOUD_IP "docker --version && docker compose version" || {
    echo "❌ Docker 未安装，请先安装 Docker 和 Docker Compose"
    exit 1
}
echo "✅ Docker 环境正常"
echo ""

# 创建部署目录
echo "📁 创建部署目录..."
ssh root@$CLOUD_IP "mkdir -p $DEPLOY_DIR"
echo "✅ 部署目录已创建"
echo ""

# 上传代码
echo "📦 上传代码到云服务器..."
cd "$(dirname "$0")"
CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo "当前提交：$CURRENT_COMMIT"

# 创建临时 tar 包
TEMP_TAR=$(mktemp /tmp/clm-deploy-XXXXXX.tar.gz)
git archive --format=tar.gz --prefix=$PROJECT_NAME/ HEAD > $TEMP_TAR

# 上传
scp $TEMP_TAR root@$CLOUD_IP:/tmp/
rm $TEMP_TAR

# 解压
ssh root@$CLOUD_IP "cd $DEPLOY_DIR && tar -xzf /tmp/clm-deploy-*.tar.gz --strip-components=1 && rm /tmp/clm-deploy-*.tar.gz"
echo "✅ 代码已上传"
echo ""

# 检查环境配置
echo "⚙️  检查环境配置..."
if ssh root@$CLOUD_IP "test -f $DEPLOY_DIR/.env.prod"; then
    echo "⚠️  .env.prod 已存在，跳过创建"
else
    echo "📝 创建 .env.prod 配置文件..."
    ssh root@$CLOUD_IP "cp $DEPLOY_DIR/.env.prod.template $DEPLOY_DIR/.env.prod"
    echo "⚠️  请编辑 $DEPLOY_DIR/.env.prod 并填写以下配置："
    echo "   - MYSQL_ROOT_PASSWORD"
    echo "   - MYSQL_PASSWORD"
    echo "   - ADMIN_TOKEN"
    echo "   - SOURCE_DB_HOST, SOURCE_DB_USER, SOURCE_DB_PASSWORD"
    echo ""
    read -p "按回车继续部署（配置可稍后修改）..."
fi
echo ""

# 启动服务
echo "🚀 启动服务..."
ssh root@$CLOUD_IP "cd $DEPLOY_DIR && docker compose --env-file .env.prod up -d"
echo "✅ 服务已启动"
echo ""

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 10

# 健康检查
echo "🏥 健康检查..."
if ssh root@$CLOUD_IP "curl -s http://localhost:8001/health | grep -q 'ok'"; then
    echo "✅ 后端健康检查通过"
else
    echo "❌ 后端健康检查失败，请查看日志："
    echo "   ssh root@$CLOUD_IP 'docker compose logs backend'"
    exit 1
fi

if ssh root@$CLOUD_IP "curl -s http://localhost:8081/ | head -1 | grep -q '<!DOCTYPE'"; then
    echo "✅ 前端健康检查通过"
else
    echo "⚠️  前端健康检查未通过（可能是构建问题）"
fi
echo ""

# 显示服务状态
echo "📊 服务状态:"
ssh root@$CLOUD_IP "cd $DEPLOY_DIR && docker compose ps"
echo ""

# 显示访问信息
echo "🌐 访问信息:"
echo "   前端：http://$CLOUD_IP:8081"
echo "   后端 API: http://$CLOUD_IP:8001"
echo "   API 文档：http://$CLOUD_IP:8001/docs"
echo ""

# 完成
echo "✅ 部署完成！"
echo ""
echo "📝 后续步骤："
echo "   1. 编辑配置文件：ssh root@$CLOUD_IP 'nano $DEPLOY_DIR/.env.prod'"
echo "   2. 重启服务：ssh root@$CLOUD_IP 'cd $DEPLOY_DIR && docker compose restart'"
echo "   3. 查看日志：ssh root@$CLOUD_IP 'docker compose logs -f'"
echo "   4. 初始化数据：curl -X POST http://$CLOUD_IP:8001/api/admin/sync/trigger/history?days=30"
echo ""
echo "🔧 常用命令："
echo "   查看状态：ssh root@$CLOUD_IP 'cd $DEPLOY_DIR && docker compose ps'"
echo "   重启服务：ssh root@$CLOUD_IP 'cd $DEPLOY_DIR && docker compose restart'"
echo "   更新代码：ssh root@$CLOUD_IP 'cd $DEPLOY_DIR && git pull && docker compose up -d'"
echo "   查看日志：ssh root@$CLOUD_IP 'docker compose logs -f backend'"
echo ""
