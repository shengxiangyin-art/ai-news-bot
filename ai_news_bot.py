#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻自动采集推送机器人 - GitHub Actions版
- 采集微信公众号文章
- 每天9:00推送到钉钉
- 支持：法律修音机、钛媒体、晚点LatePost
"""

import os
import requests
import json
import re
import time
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import urlencode

# 从环境变量读取配置
DINGTALK_TOKEN = os.environ.get('DINGTALK_TOKEN')

# 关键词配置
AI_KEYWORDS = [
    "AI", "人工智能", "大模型", "ChatGPT", "AIGC", "机器学习", "深度学习",
    "算法", "智能合约", "法律科技", "LegalTech", "自动化", "GPT", "LLM",
    "生成式AI", "多模态", "神经网络", "数据合规", "算法备案"
]

# 模拟新闻数据（实际部署后可接入RSS或爬虫）
MOCK_NEWS = [
    {
        "title": "AI法律科技发展趋势报告发布",
        "summary": "最新报告显示，AI在法律领域的应用正在快速增长，智能合约审核、法律文档自动生成成为热点...",
        "source": "法律修音机",
        "category": "法律科技",
        "icon": "⚖️",
        "link": "https://mp.weixin.qq.com"
    },
    {
        "title": "大模型技术在合同审查中的实践案例",
        "summary": "某头部律所引入大模型辅助合同审查，效率提升300%，准确率达到95%以上，成为行业标杆...",
        "source": "钛媒体",
        "category": "AI产业",
        "icon": "🤖",
        "link": "https://www.tmtpost.com"
    },
    {
        "title": "互联网大厂AI法务部门建设揭秘",
        "summary": "深度报道：阿里、腾讯、字节等公司的AI法务团队如何运作，技术+法律的复合型人才成为抢手资源...",
        "source": "晚点LatePost",
        "category": "深度阅读",
        "icon": "📰",
        "link": "https://mp.weixin.qq.com"
    }
]


class DingTalkPusher:
    """钉钉消息推送器"""
    
    def __init__(self, token, secret=None):
        self.token = token
        self.secret = secret
        self.base_url = "https://oapi.dingtalk.com/robot/send"
    
    def _generate_sign(self):
        """生成钉钉机器人签名"""
        if not self.secret:
            return {}
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return {"timestamp": timestamp, "sign": sign}
    
    def _get_webhook(self):
        """获取完整的webhook地址"""
        params = {"access_token": self.token}
        params.update(self._generate_sign())
        return f"{self.base_url}?{urlencode(params)}"
    
    def send_markdown(self, title, content):
        """发送Markdown格式消息"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            }
        }
        try:
            webhook = self._get_webhook()
            response = requests.post(
                webhook,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=10
            )
            result = response.json()
            if result.get("errcode") == 0:
                print(f"✅ 钉钉推送成功: {title}")
                return True
            else:
                print(f"❌ 钉钉推送失败: {result}")
                return False
        except Exception as e:
            print(f"❌ 钉钉推送异常: {e}")
            return False


def generate_daily_report():
    """生成每日推送报告"""
    today = datetime.now().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]
    
    # 按分类分组
    categorized = {}
    for article in MOCK_NEWS:
        cat = article["category"]
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(article)
    
    # 生成Markdown内容
    lines = [
        f"# 📰 AI早报 - {today} {weekday}",
        "",
        f"> 今日精选 **{len(MOCK_NEWS)}** 篇AI相关文章",
        "",
        "---",
        ""
    ]
    
    # 按分类输出
    category_order = ["法律科技", "AI产业", "深度阅读"]
    for cat in category_order:
        if cat in categorized:
            lines.append(f"## {categorized[cat][0]['icon']} {cat}")
            lines.append("")
            for i, article in enumerate(categorized[cat][:3], 1):
                lines.append(f"**{i}. [{article['title']}]({article['link']})**")
                lines.append(f"> {article['summary']}")
                lines.append(f"> *来源：{article['source']}*")
                lines.append("")
    
    # 添加今日要点
    lines.append("---")
    lines.append("")
    lines.append("## 💡 今日要点")
    lines.append("")
    lines.append("AI法律科技领域持续活跃，建议关注大模型在合同审查中的应用进展。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本消息由AI新闻机器人自动推送*")
    
    return "\n".join(lines)


def main():
    """主函数"""
    print("=" * 50)
    print("AI新闻机器人启动")
    print("=" * 50)
    
    if not DINGTALK_TOKEN:
        print("❌ 错误：未设置 DINGTALK_TOKEN 环境变量")
        print("请在GitHub Secrets中设置 DINGTALK_TOKEN")
        return
    
    print(f"✅ Token已配置: {DINGTALK_TOKEN[:10]}...")
    
    pusher = DingTalkPusher(DINGTALK_TOKEN)
    report = generate_daily_report()
    
    if report:
        success = pusher.send_markdown("AI早报", report)
        if success:
            print("✅ 每日推送任务完成")
        else:
            print("❌ 推送失败")
    else:
        print("⚠️ 今日无AI相关新闻")


if __name__ == "__main__":
    main()
