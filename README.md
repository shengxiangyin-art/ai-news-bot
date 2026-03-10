# AI新闻自动推送机器人

每天北京时间9:00自动推送AI相关新闻到钉钉。

## 新闻来源

- ⚖️ **法律修音机** - 法律科技、AI法律应用
- 🤖 **钛媒体** - AI产业动态、技术趋势  
- 📰 **晚点LatePost** - 深度报道、行业分析

## 技术方案

- **RSS采集**：RSSHub公共RSS源
- **定时任务**：GitHub Actions
- **消息推送**：钉钉机器人

## 配置

1. 在 GitHub Secrets 中设置 `DINGTALK_TOKEN`
2. 每天9:00自动运行

## 手动测试

进入 Actions 页面，点击 "Run workflow" 可立即测试。
