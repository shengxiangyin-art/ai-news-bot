# AI新闻自动推送机器人

每天北京时间9:00自动推送AI相关新闻到钉钉。

## 新闻来源

- ⚖️ **法律修音机** - 法律科技、AI法律应用
- 🤖 **钛媒体** - AI产业动态、技术趋势
- 📰 **晚点LatePost** - 深度报道、行业分析

## 配置说明

### 1. GitHub Secrets设置

在仓库 Settings → Secrets and variables → Actions 中添加：

| Name | Value |
|------|-------|
| `DINGTALK_TOKEN` | 你的钉钉机器人Token |

### 2. 定时任务

已配置每天 UTC 1:00 (北京时间 9:00) 自动运行。

### 3. 手动测试

进入 Actions 页面，点击 "Run workflow" 可立即触发测试。

## 文件说明

```
.
├── .github/workflows/daily-push.yml  # GitHub Actions工作流
├── ai_news_bot.py                     # 主程序
├── requirements.txt                   # Python依赖
└── README.md                          # 本文件
```

## 更新日志

- 2025-03-09: 初始版本，支持钉钉Markdown推送
