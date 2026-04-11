"""
飞书机器人对接

第一版：实现真实飞书 API 调用，发送卡片消息给工程师
"""
import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Any
from .config import settings

logger = logging.getLogger(__name__)

# 飞书 API 端点
FEISHU_API = {
    "tenant_token": "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    "send_message": "https://open.feishu.cn/open-apis/im/v1/messages",
}


def build_task_summary_card(engineer_name: str, tasks: List[Dict]) -> Dict:
    """构造飞书交互卡片 - 任务摘要"""
    total = len(tasks)
    total_exec = sum(t.get("exec_count", 1) for t in tasks)
    failed = sum(1 for t in tasks if t.get("status") == "failed")

    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**{engineer_name}**，今天你完成了 **{total}** 道菜，共执行 **{total_exec}** 次"
                           + (f"，其中 **{failed}** 道失败" if failed > 0 else "，全部通过")
            }
        },
        {"tag": "hr"},
    ]

    for t in tasks:
        status_emoji = "❌" if t.get("status") == "failed" else "✅"
        type_label = {0: "小份", 2: "大份", 7: "定制版"}.get(t.get("recipe_type", 0), "")
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"{status_emoji} **{t['dish_name']}** · {type_label} · recipe#{t.get('recipe_id', '?')}\n"
                    f"执行{t.get('exec_count', 1)}次 · {t.get('cooking_time', 0)}秒 · {t.get('customer_name', '')}"
                )
            }
        })

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": "📋 请花2分钟回答以下追问，帮助回收今天的现场经验"
        }
    })

    # 添加按钮跳转到填写页
    elements.append({
        "tag": "action",
        "actions": [{
            "tag": "button",
            "text": {"tag": "plain_text", "content": "开始填写"},
            "type": "primary",
            "url": "{{fill_url}}"  # 填写页 URL 在发送时替换
        }]
    })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📋 录菜复盘助手 · 今日回传"},
            "template": "blue"
        },
        "elements": elements
    }

    return card


def get_tenant_access_token() -> str:
    """获取飞书 Tenant Access Token"""
    if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
        raise ValueError("飞书凭证未配置：FEISHU_APP_ID 或 FEISHU_APP_SECRET 为空")

    data = json.dumps({
        "app_id": settings.FEISHU_APP_ID,
        "app_secret": settings.FEISHU_APP_SECRET
    }).encode('utf-8')

    req = urllib.request.Request(
        FEISHU_API["tenant_token"],
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get("code") != 0:
                raise Exception(f"获取 Token 失败：{result.get('msg', 'Unknown error')}")
            token = result.get("tenant_access_token")
            logger.info(f"成功获取飞书 Token (expire: {result.get('expire', 7200)}s)")
            return token
    except urllib.error.HTTPError as e:
        raise Exception(f"飞书 API HTTP 错误：{e.code} {e.reason}")
    except Exception as e:
        raise Exception(f"获取飞书 Token 失败：{str(e)}")


def check_whitelist(user_id: str) -> tuple[bool, str]:
    """检查 user_id 是否在白名单中（个人发送模式）
    
    Returns:
        (allowed, reason): 是否允许发送，原因说明
    """
    if not settings.FEISHU_TEST_WHITELIST:
        return False, "未配置 FEISHU_TEST_WHITELIST，拒绝发送（安全保护）"
    
    whitelist = [x.strip() for x in settings.FEISHU_TEST_WHITELIST.split(",") if x.strip()]
    if not whitelist:
        return False, "白名单为空，拒绝发送（安全保护）"
    
    if user_id in whitelist:
        return True, "user_id 在白名单中"
    
    return False, f"user_id 不在白名单中 (白名单：{whitelist})"


def check_test_mode(target_id: str, target_type: str = "user") -> tuple[bool, str]:
    """检查是否符合测试群模式要求
    
    Args:
        target_id: 目标 ID（chat_id 或 user_id）
        target_type: 目标类型 ("chat" 或 "user")
    
    Returns:
        (allowed, reason): 是否允许发送，原因说明
    """
    if not settings.FEISHU_TEST_MODE:
        return True, "测试群模式已关闭"
    
    if not settings.FEISHU_TEST_CHAT_ID:
        return False, "测试群模式已开启，但未配置 FEISHU_TEST_CHAT_ID"
    
    if target_type == "chat" and target_id == settings.FEISHU_TEST_CHAT_ID:
        return True, f"chat_id 匹配测试群配置"
    
    if target_type == "user":
        return False, f"测试群模式已开启，禁止向个人 user_id 发送（目标：{target_id}）"
    
    return False, f"chat_id 不匹配测试群配置（期望：{settings.FEISHU_TEST_CHAT_ID}, 实际：{target_id}）"


async def send_feishu_card_to_chat(chat_id: str, card: Dict, fill_url: str, dry_run: bool = None) -> dict:
    """发送飞书卡片消息到群聊
    
    Args:
        chat_id: 群聊 chat_id
        card: 卡片内容
        fill_url: 填写页 URL 路径
        dry_run: 是否仅模拟（None 则使用配置中的 FEISHU_DRY_RUN）
    
    Returns:
        dict: {
            "success": bool,
            "dry_run": bool,
            "message": str,
            "payload": dict (仅 dry_run 时返回),
            "api_endpoint": str (仅 dry_run 时返回)
        }
    """
    is_dry_run = dry_run if dry_run is not None else settings.FEISHU_DRY_RUN
    
    # 测试群模式检查
    allowed, reason = check_test_mode(chat_id, target_type="chat")
    if not allowed:
        logger.warning(f"❌ 拒绝发送：{reason}")
        return {
            "success": False,
            "dry_run": is_dry_run,
            "message": f"安全保护：{reason}",
            "blocked": True
        }
    
    # 构造完整 URL（fill_url 已经是 /fill/4 格式，直接拼接 #）
    base_url = settings.FEISHU_BOT_WEBHOOK.replace("/webhook", "") if settings.FEISHU_BOT_WEBHOOK else "http://localhost:8080"
    full_fill_url = f"{base_url}#{fill_url}"
    
    # 替换卡片中的占位符
    card_json = json.dumps(card).replace("{{fill_url}}", full_fill_url)
    
    # 构造消息 payload（群聊使用 chat_id）
    msg_data = {
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": card_json
    }
    
    # Dry-run 模式：仅输出信息，不实际发送
    if is_dry_run:
        logger.info("=" * 60)
        logger.info("🔍 [DRY-RUN MODE] 飞书群聊消息发送模拟")
        logger.info("=" * 60)
        logger.info(f"📤 目标 chat_id: {chat_id}")
        logger.info(f"🔗 填写页 URL: {full_fill_url}")
        logger.info(f"📍 API 端点：{FEISHU_API['send_message']}?receive_id_type=chat_id")
        logger.info(f"📦 Payload:\n{json.dumps(msg_data, indent=2, ensure_ascii=False)}")
        logger.info("=" * 60)
        logger.info("⚠️  当前为 DRY-RUN 模式，未实际发送消息")
        logger.info("💡 设置 FEISHU_DRY_RUN=false 并确认测试群 chat_id 后发送真实消息")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "dry_run": True,
            "message": "DRY-RUN 模式：消息未实际发送，请检查日志中的 payload",
            "payload": msg_data,
            "api_endpoint": f"{FEISHU_API['send_message']}?receive_id_type=chat_id",
            "fill_url": full_fill_url,
            "target_type": "chat"
        }
    
    # 真实发送模式
    try:
        token = get_tenant_access_token()
        
        req = urllib.request.Request(
            f"{FEISHU_API['send_message']}?receive_id_type=chat_id",
            data=json.dumps(msg_data).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get("code") != 0:
                logger.error(f"❌ 发送飞书群消息失败：{result.get('msg', 'Unknown error')}")
                return {
                    "success": False,
                    "dry_run": False,
                    "message": f"发送失败：{result.get('msg', 'Unknown error')}"
                }
            
            logger.info(f"✅ 成功向群聊 {chat_id} 发送飞书卡片消息")
            return {
                "success": True,
                "dry_run": False,
                "message": f"消息已发送至群聊 {chat_id}"
            }
    
    except Exception as e:
        logger.error(f"❌ 发送飞书群消息异常：{str(e)}")
        return {
            "success": False,
            "dry_run": False,
            "message": f"发送异常：{str(e)}"
        }


async def send_feishu_card(user_id: str, card: Dict, fill_url: str, dry_run: bool = None) -> dict:
    """发送飞书卡片消息（个人）
    
    Args:
        user_id: 接收者的飞书 user_id
        card: 卡片内容
        fill_url: 填写页 URL 路径
        dry_run: 是否仅模拟（None 则使用配置中的 FEISHU_DRY_RUN）
    
    Returns:
        dict: {
            "success": bool,
            "dry_run": bool,
            "message": str,
            "payload": dict (仅 dry_run 时返回),
            "api_endpoint": str (仅 dry_run 时返回)
        }
    """
    is_dry_run = dry_run if dry_run is not None else settings.FEISHU_DRY_RUN
    
    # 测试群模式检查（优先）
    if settings.FEISHU_TEST_MODE:
        allowed, reason = check_test_mode(user_id, target_type="user")
        if not allowed:
            logger.warning(f"❌ 拒绝发送：{reason}")
            return {
                "success": False,
                "dry_run": is_dry_run,
                "message": f"安全保护：{reason}",
                "blocked": True
            }
    
    # 白名单检查（测试群模式关闭时使用）
    allowed, reason = check_whitelist(user_id)
    if not allowed:
        logger.warning(f"❌ 拒绝发送：{reason}")
        return {
            "success": False,
            "dry_run": is_dry_run,
            "message": f"安全保护：{reason}",
            "blocked": True
        }
    
    # 构造完整 URL（fill_url 已经是 /fill/4 格式，直接拼接 #）
    base_url = settings.FEISHU_BOT_WEBHOOK.replace("/webhook", "") if settings.FEISHU_BOT_WEBHOOK else "http://localhost:8080"
    full_fill_url = f"{base_url}#{fill_url}"
    
    # 替换卡片中的占位符
    card_json = json.dumps(card).replace("{{fill_url}}", full_fill_url)
    card_data = json.loads(card_json)
    
    # 构造消息 payload
    msg_data = {
        "receive_id": user_id,
        "msg_type": "interactive",
        "content": card_json
    }
    
    # Dry-run 模式：仅输出信息，不实际发送
    if is_dry_run:
        logger.info("=" * 60)
        logger.info("🔍 [DRY-RUN MODE] 飞书消息发送模拟")
        logger.info("=" * 60)
        logger.info(f"📤 目标 user_id: {user_id}")
        logger.info(f"🔗 填写页 URL: {full_fill_url}")
        logger.info(f"📍 API 端点：{FEISHU_API['send_message']}?receive_id_type=user_id")
        logger.info(f"📦 Payload:\n{json.dumps(msg_data, indent=2, ensure_ascii=False)}")
        logger.info("=" * 60)
        logger.info("⚠️  当前为 DRY-RUN 模式，未实际发送消息")
        logger.info("💡 设置 FEISHU_DRY_RUN=false 并配置 FEISHU_TEST_WHITELIST 后发送真实消息")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "dry_run": True,
            "message": "DRY-RUN 模式：消息未实际发送，请检查日志中的 payload",
            "payload": msg_data,
            "api_endpoint": f"{FEISHU_API['send_message']}?receive_id_type=user_id",
            "fill_url": full_fill_url
        }
    
    # 真实发送模式
    try:
        # Step 1: 获取 Token
        token = get_tenant_access_token()

        # Step 2: 发送消息
        req = urllib.request.Request(
            f"{FEISHU_API['send_message']}?receive_id_type=user_id",
            data=json.dumps(msg_data).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get("code") != 0:
                logger.error(f"❌ 发送飞书消息失败：{result.get('msg', 'Unknown error')}")
                return {
                    "success": False,
                    "dry_run": False,
                    "message": f"发送失败：{result.get('msg', 'Unknown error')}"
                }
            
            logger.info(f"✅ 成功向 {user_id} 发送飞书卡片消息")
            return {
                "success": True,
                "dry_run": False,
                "message": f"消息已发送至 {user_id}"
            }

    except Exception as e:
        logger.error(f"❌ 发送飞书消息异常：{str(e)}")
        return {
            "success": False,
            "dry_run": False,
            "message": f"发送异常：{str(e)}"
        }


async def send_reminder(user_id: str, session_id: int) -> bool:
    """发送催填提醒"""
    if not settings.FEISHU_APP_ID:
        logger.info(f"[MOCK] 向 {user_id} 发送催填提醒")
        return True

    # TODO: 实现催填消息
    return True
