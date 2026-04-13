#!/bin/bash
# 云服务器部署脚本 - 检索页增强版
# 使用方法：scp 到服务器后执行

set -e

echo "🚀 开始部署 CLM-REVIEW-TOOL 增强版..."
echo "版本：e40fb1f"
echo ""

cd /opt/clm-review-tool

echo "📦 拉取最新代码..."
git pull
echo ""

echo "🔄 重启服务..."
docker compose restart
echo ""

echo "⏳ 等待服务就绪..."
sleep 10

echo "🏥 健康检查..."
if curl -s http://localhost:8001/health | grep -q 'ok'; then
    echo "✅ 后端健康检查通过"
else
    echo "❌ 后端健康检查失败"
    exit 1
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "🌐 访问地址："
echo "   前端：http://82.156.187.35:8081"
echo "   API 文档：http://82.156.187.35:8001/docs"
echo ""
echo "📋 验证步骤："
echo "   1. 访问前端页面"
echo "   2. 进入数据检索页"
echo "   3. 执行检索后切换到其他页面"
echo "   4. 返回检索页验证缓存"
echo "   5. 展开详情查看瀑布流展示"
echo ""
