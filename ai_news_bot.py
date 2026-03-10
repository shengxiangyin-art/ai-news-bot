#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻自动采集推送机器人
- 采集RSS订阅
- 每天9:00推送到钉钉
"""

import os
import requests
import json
import re
import feedparser
from datetime import datetime

DINGTALK_TOKEN = os.environ.get('DINGTALK_TOKEN')

# RSS源配置
RSS_SOURCES = {
    "法律修音机": {
        "url": "https://rsshub.app/wechat/mp/法律修音机",
        "category": "法律科技",
        "icon": "⚖️"
    },
    "钛媒体": {
        "url": "https://rsshub.app/tmtpost",
        "category": "AI产业",
        "icon": "🤖"
    },
    "晚点LatePost": {
        "url": "https://rsshub.app/wechat/mp/晚点LatePost",
        "category": "深度阅读",
        "icon": "📰"
    }
}


class DingTalkPusher:
    def __init__(self, token):
        self.token = token
        self.webhook = f"https://oapi.dingtalk.com/robot/send?access_token={token}"
    
    def send_markdown(self, title, content):
        data = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content}
        }
        try:
            response = requests.post(
                self.webhook,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=10
            )
            result = response.json()
            if result.get("errcode") == 0:
                print(f"✅ 推送成功: {title}")
                return True
            else:
                print(f"❌ 推送失败: {result}")
                return False
        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False


def fetch_news(source_name, source_config):
    """获取RSS新闻"""
    articles = []
    try:
        print(f"正在获取: {source_name}")
        feed = feedparser.parse(source_config["url"])
        
        for entry in feed.entries[:3]:  # 取最近3篇
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            
            # 清理HTML标签
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary[:150] + "..." if len(summary) > 150 else summary
            
            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "source": source_name,
                "category": source_config["category"],
                "icon": source_config["icon"]
            })
        
        print(f"  ✓ 获取到 {len(articles)} 篇文章")
        return articles
        
    except Exception as e:
        print(f"  ✗ 获取失败: {e}")
        return []


def generate_report(articles):
    """生成推送报告"""
    if not articles:
        return None
    
    today = datetime.now().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]
    
    # 按分类分组
    categorized = {}
    for article in articles:
        cat = article["category"]
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(article)
    
    # 生成内容
    lines = [
        f"# 📰 AI早报 - {today} {weekday}",
        "",
        f"> 今日精选 **{len(articles)}** 篇文章",
        "",
        "---",
        ""
    ]
    
    # 按分类输出
    for cat in ["法律科技", "AI产业", "深度阅读"]:
        if cat in categorized:
            lines.append(f"## {categorized[cat][0]['icon']} {cat}")
            lines.append("")
            for i, article in enumerate(categorized[cat][:2], 1):
                lines.append(f"**{i}. [{article['title']}]({article['link']})**")
                lines.append(f"> {article['summary']}")
                lines.append(f"> *来源：{article['source']}*")
                lines.append("")
    
    lines.extend([
        "---",
        "",
        "*本消息由AI新闻机器人自动推送*"
    ])
    
    return "\n".join(lines)


def main():
    print("=" * 50)
    print("AI新闻机器人启动")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if not DINGTALK_TOKEN:
        print("❌ 错误: 未设置 DINGTALK_TOKEN")
        return
    
    # 采集所有来源
    all_articles = []
    for name, config in RSS_SOURCES.items():
        articles = fetch_news(name, config)
        all_articles.extend(articles)
    
    print(f"\n共采集 {len(all_articles)} 篇文章")
    
    # 生成并推送报告
    report = generate_report(all_articles)
    if report:
        pusher = DingTalkPusher(DINGTALK_TOKEN)
        success = pusher.send_markdown("AI早报", report)
        if success:
            print("✅ 任务完成")
        else:
            print("❌ 推送失败")
    else:
        print("⚠️ 无文章可推送")


if __name__ == "__main__":
    main()
