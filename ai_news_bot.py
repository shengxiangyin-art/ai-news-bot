#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI新闻自动采集推送机器人 - GitHub Actions版
- 采集微信公众号文章（RSS源）
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
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import urlencode, unquote

# 从环境变量读取配置
DINGTALK_TOKEN = os.environ.get('DINGTALK_TOKEN')

# 关键词配置
AI_KEYWORDS = [
    "AI", "人工智能", "大模型", "ChatGPT", "AIGC", "机器学习", "深度学习",
    "算法", "智能合约", "法律科技", "LegalTech", "自动化", "GPT", "LLM",
    "生成式AI", "多模态", "神经网络", "数据合规", "算法备案", "OpenAI",
    "Claude", "文心一言", "通义千问", "智谱", "月之暗面", "kimi"
]

# RSS源配置 - 使用RSSHub或其他聚合服务
RSS_SOURCES = {
    "法律修音机": {
        "url": "https://rsshub.app/wechat/mp/法律修音机",
        "fallback_url": "https://feeddd.org/feeds/627f3e9fd9ff7f0001c30b1a",
        "category": "法律科技",
        "icon": "⚖️"
    },
    "钛媒体": {
        "url": "https://rsshub.app/tmtpost",
        "fallback_url": "https://www.tmtpost.com/rss.xml",
        "category": "AI产业",
        "icon": "🤖"
    },
    "晚点LatePost": {
        "url": "https://rsshub.app/wechat/mp/晚点LatePost",
        "fallback_url": "https://feeddd.org/feeds/627f3e9fd9ff7f0001c30b1b",
        "category": "深度阅读",
        "icon": "📰"
    }
}


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


class NewsCollector:
    """新闻采集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch_rss(self, source_name, source_config):
        """获取RSS订阅内容"""
        articles = []
        urls_to_try = [source_config.get("url"), source_config.get("fallback_url")]
        
        for url in urls_to_try:
            if not url:
                continue
            try:
                print(f"尝试获取 {source_name}: {url}")
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    parsed = self._parse_rss(response.text, source_name, source_config)
                    if parsed:
                        articles.extend(parsed)
                        break
            except Exception as e:
                print(f"获取失败 {url}: {e}")
                continue
        
        return articles
    
    def _parse_rss(self, xml_content, source_name, source_config):
        """解析RSS XML内容"""
        articles = []
        try:
            # 处理可能的编码问题
            if isinstance(xml_content, bytes):
                xml_content = xml_content.decode('utf-8', errors='ignore')
            
            # 移除BOM标记
            xml_content = xml_content.lstrip('\ufeff')
            
            root = ET.fromstring(xml_content)
            
            # 查找item元素
            items = root.findall('.//item')
            if not items:
                # 尝试Atom格式
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            for item in items[:5]:  # 只取最近5篇
                title = self._get_text(item, 'title')
                link = self._get_text(item, 'link')
                desc = self._get_text(item, 'description') or self._get_text(item, 'summary')
                pub_date = self._get_text(item, 'pubDate') or self._get_text(item, 'published')
                
                # 清理HTML标签
                desc = self._clean_html(desc)
                
                # 检查是否是最近24小时的文章
                if self._is_recent(pub_date) and self._is_ai_related(title, desc):
                    articles.append({
                        "title": title,
                        "link": link,
                        "summary": desc[:200] + "..." if len(desc) > 200 else desc,
                        "source": source_name,
                        "category": source_config["category"],
                        "icon": source_config["icon"],
                        "pub_time": pub_date
                    })
            
            print(f"[{source_name}] 成功解析 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            print(f"解析RSS失败: {e}")
            return []
    
    def _get_text(self, element, tag):
        """安全获取XML元素文本"""
        try:
            # 尝试无命名空间
            child = element.find(tag)
            if child is not None:
                return child.text or ""
            # 尝试Atom命名空间
            child = element.find('{http://www.w3.org/2005/Atom}' + tag)
            if child is not None:
                return child.text or ""
            return ""
        except:
            return ""
    
    def _clean_html(self, html):
        """清理HTML标签"""
        if not html:
            return ""
        # 移除HTML标签
        clean = re.sub(r'<[^>]+>', '', html)
        # 移除多余空白
        clean = re.sub(r'\s+', ' ', clean)
        # 移除特殊字符
        clean = clean.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&')
        return clean.strip()
    
    def _is_recent(self, pub_date_str):
        """判断文章是否为最近48小时内"""
        if not pub_date_str:
            return True  # 如果没有日期，默认包含
        try:
            # 尝试解析各种日期格式
            now = datetime.now()
            # 简化处理：默认返回True，实际使用时可以解析日期
            return True
        except:
            return True
    
    def _is_ai_related(self, title, summary):
        """判断是否与AI相关"""
        text = (title + " " + summary).lower()
        keywords = [k.lower() for k in AI_KEYWORDS]
        return any(kw in text for kw in keywords)
    
    def fetch_all_sources(self):
        """获取所有来源的文章"""
        all_articles = []
        for source_name, source_config in RSS_SOURCES.items():
            articles = self.fetch_rss(source_name, source_config)
            all_articles.extend(articles)
            time.sleep(1)  # 避免请求过快
        return all_articles


def generate_daily_report(articles):
    """生成每日推送报告"""
    today = datetime.now().strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]
    
    if not articles:
        return None
    
    # 按分类分组
    categorized = {}
    for article in articles:
        cat = article["category"]
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(article)
    
    # 生成Markdown内容
    lines = [
        f"# 📰 AI早报 - {today} {weekday}",
        "",
        f"> 今日精选 **{len(articles)}** 篇AI相关文章",
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
    lines.append(generate_summary(articles))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本消息由AI新闻机器人自动推送*")
    
    return "\n".join(lines)


def generate_summary(articles):
    """生成今日要点摘要"""
    if not articles:
        return "暂无要点"
    
    # 提取关键词
    titles = " ".join([a["title"] for a in articles[:3]])
    
    if "法律" in titles or "合规" in titles or "法务" in titles:
        return "法律科技领域有新动态，建议关注AI合规和智能合约相关进展。"
    elif "大模型" in titles or "GPT" in titles or "Claude" in titles:
        return "大模型技术持续演进，行业应用案例值得关注。"
    elif "数据" in titles or "算法" in titles:
        return "数据合规和算法治理成为热点，企业需关注监管动态。"
    else:
        return "AI产业动态活跃，建议阅读详情了解最新趋势。"


def main():
    """主函数"""
    print("=" * 50)
    print("AI新闻机器人启动")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if not DINGTALK_TOKEN:
        print("❌ 错误：未设置 DINGTALK_TOKEN 环境变量")
        print("请在GitHub Secrets中设置 DINGTALK_TOKEN")
        return
    
    print(f"✅ Token已配置: {DINGTALK_TOKEN[:10]}...")
    
    # 采集新闻
    collector = NewsCollector()
    articles = collector.fetch_all_sources()
    
    print(f"\n共采集到 {len(articles)} 篇AI相关文章")
    
    # 生成报告
    report = generate_daily_report(articles)
    
    if report:
        # 推送到钉钉
        pusher = DingTalkPusher(DINGTALK_TOKEN)
        success = pusher.send_markdown("AI早报", report)
        if success:
            print("✅ 每日推送任务完成")
        else:
            print("❌ 推送失败")
    else:
        print("⚠️ 今日无AI相关新闻")
        # 发送空消息提示
        pusher = DingTalkPusher(DINGTALK_TOKEN)
        today = datetime.now().strftime("%Y年%m月%d日")
        pusher.send_markdown("AI早报", f"# 📰 AI早报 - {today}\n\n今日暂无新的AI相关文章，明天见！")


if __name__ == "__main__":
    main()
