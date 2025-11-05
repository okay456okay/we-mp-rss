# WeRSS - WeChat Official Account RSS Subscription Assistant

<img src="static/logo.svg" alt="We-MP-RSS Logo" width="200">

[![Python Version](https://img.shields.io/badge/python-3.13.1+-red.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

[中文](README.zh-CN.md) | [English](ReadMe.md)

---

## 📢 Update Notice

This repository is cloned from [https://github.com/rachelos/we-mp-rss](https://github.com/rachelos/we-mp-rss), with the following improvements based on the original functionality:

- ✅ **Fixed issues with some accounts not updating**: Optimized synchronization mechanism to improve update success rate
- ✅ **Added update error notifications**: Automatically sends notifications when synchronization fails to promptly identify issues
- ✅ **Multiple notification methods supported**: Supports WeChat Work group bots, DingTalk, Feishu, and other notification channels
- ✅ **Fixed critical bugs**: Resolved multiple critical issues affecting stability

---

## 📮 Contact

If you have any questions or suggestions, please contact us through the following methods:

- Create a [GitHub Issue](https://github.com/okay456okay/nof1.ai.monitor/issues)
- X (Twitter): [@okay456okay](https://x.com/okay456okay)
- WeChat Official Account: 远见拾贝
- Website: [远见拾贝 - 用远见洞察，赚确定性的钱](https://www.insightpearl.com/)

<img src="https://github.com/okay456okay/nof1.ai.monitor/raw/main/images/InSightPearl21_qrcode.jpg" alt="远见拾贝公众号二维码" width="150" height="150">

---

## Quick Start

```bash
docker run -d --name we-mp-rss -p 8001:8001 -v ./data:/app/data ghcr.io/rachelos/we-mp-rss:latest
```

Visit `http://<your-ip>:8001/` to get started

## Quick Upgrade

```bash
docker stop we-mp-rss
docker rm we-mp-rss
docker pull ghcr.io/rachelos/we-mp-rss:latest
# If you added other parameters, please modify accordingly
docker run -d --name we-mp-rss -p 8001:8001 -v ./data:/app/data ghcr.io/rachelos/we-mp-rss:latest
```

## Official Image

```bash
docker run -d --name we-mp-rss -p 8001:8001 -v ./data:/app/data rachelos/we-mp-rss:latest
```

## Proxy Mirror for Faster Access (Faster access in China)

```bash
docker run -d --name we-mp-rss -p 8001:8001 -v ./data:/app/data docker.1ms.run/rachelos/we-mp-rss:latest
```

## Special Thanks (In no particular order)

cyChaos, 子健MeLift, 晨阳, 童总, 胜宇, 军亮, 余光, 一路向北, 水煮土豆丝, 人可, 须臾, 澄明, 五梭

A tool for subscribing to and managing WeChat Official Account content, providing RSS subscription functionality.

## Features

- WeChat Official Account content scraping and parsing
- RSS feed generation
- User-friendly web management interface
- Scheduled automatic content updates
- Multiple database support (default SQLite, optional MySQL)
- Multiple scraping methods support
- Multiple RSS client support
- Authorization expiration reminders
- Custom notification channels
- Custom RSS title, description, and cover
- Custom RSS pagination size
- Export to md/docx/pdf/json formats
- API interface and WebHook support

## ❤️ Sponsorship

If you find We-MP-RSS helpful, feel free to buy me a beer!

<img src="docs/赞赏码.jpg" width="180" alt="Sponsor QR Code"/>

[Paypal](https://www.paypal.com/ncp/payment/PUA72WYLAV5KW)

## Screenshots

- **Login Interface**

<img src="docs/登录.png" alt="Login" width="80%"/>

- **Main Interface**

<img src="docs/主界面.png" alt="Main Interface" width="80%"/>

- **QR Code Authorization**

<img src="docs/扫码授权.png" alt="QR Code Authorization" width="80%"/>

- **Add Subscription**

<img src="docs/添加订阅.png" alt="Add Subscription" width="80%"/>

- **Client Application**

<img src="docs/folo.webp" alt="FOLO Client Application" width="80%"/>



## System Architecture

The project adopts a front-end and back-end separation architecture:

- Backend: Python + FastAPI
- Frontend: Vue 3 + Vite
- Database: SQLite (default)/MySQL

<img src="docs/架构原理.png" alt="Architecture Diagram" width="80%"/>

For more project principles, please refer to the [Project Documentation](https://deepwiki.com/rachelos/we-mp-rss/3.5-notification-system).

## Installation Guide

### Development

#### Environment Requirements

- Python>=3.13.1
- Node>=20.18.3

#### Backend Service

1. Clone the project

```bash
git clone https://github.com/rachelos/we-mp-rss.git
cd we-mp-rss
```

2. Install Python dependencies

```bash
pip install -r requirements.txt
```

3. Configure database

Copy and modify the configuration file:

```bash
cp config.example.yaml config.yaml
# Windows system use
copy config.example.yaml config.yaml
```

4. Start the service

```bash
python main.py -job True -init True
```

#### Frontend Development

1. Install frontend dependencies

```bash
cd we-mp-rss/web_ui
yarn install
```

2. Start frontend service

```bash
yarn dev
```

3. Access frontend page

```
http://localhost:3000
```

## Environment Variable Configuration

The following are the environment variable configurations supported in `config.yaml`:

| Environment Variable | Default Value | Description |
|----------|--------|------|
| `APP_NAME` | `we-mp-rss` | Application name |
| `SERVER_NAME` | `we-mp-rss` | Server name |
| `WEB_NAME` | `WeRSS微信公众号订阅助手` | Frontend display name |
| `SEND_CODE` | `True` | Whether to send authorization QR code notifications |
| `CODE_TITLE` | `WeRSS授权二维码` | QR code notification title |
| `ENABLE_JOB` | `True` | Whether to enable scheduled tasks |
| `AUTO_RELOAD` | `False` | Auto-restart service on code changes |
| `THREADS` | `2` | Maximum number of threads |
| `DB` | `sqlite:///data/db.db` | Database connection string |
| `DINGDING_WEBHOOK` | Empty | DingTalk notification webhook URL |
| `WECHAT_WEBHOOK` | Empty | WeChat Work group bot webhook URL (format: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx). The system automatically identifies the notification type based on the webhook URL |
| `FEISHU_WEBHOOK` | Empty | Feishu notification webhook URL |
| `CUSTOM_WEBHOOK` | Empty | Custom notification webhook URL |
| `SECRET_KEY` | `we-mp-rss` | Secret key |
| `USER_AGENT` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36/WeRss` | User agent |
| `SPAN_INTERVAL` | `10` | Scheduled task execution interval (seconds) |
| `SYNC_CACHE_HOURS` | `8` | Sync cache time (hours). If an account has articles within the specified time, skip sync. Set to 0 to disable cache |
| `WEBHOOK.CONTENT_FORMAT` | `html` | Article content sending format |
| `PORT` | `8001` | API service port |
| `DEBUG` | `False` | Debug mode |
| `MAX_PAGE` | `5` | Maximum scraping pages |
| `RSS_BASE_URL` | Empty | RSS domain address |
| `RSS_LOCAL` | `False` | Whether to use local RSS links |
| `RSS_TITLE` | Empty | RSS title |
| `RSS_DESCRIPTION` | Empty | RSS description |
| `RSS_COVER` | Empty | RSS cover |
| `RSS_FULL_CONTEXT` | `True` | Whether to display full text |
| `RSS_ADD_COVER` | `True` | Whether to add cover images |
| `RSS_CDATA` | `False` | Whether to enable CDATA |
| `RSS_PAGE_SIZE` | `30` | RSS pagination size |
| `TOKEN_EXPIRE_MINUTES` | `4320` | Login session validity duration (minutes) |
| `CACHE.DIR` | `./data/cache` | Cache directory |
| `ARTICLE.TRUE_DELETE` | `False` | Whether to truly delete articles |
| `GATHER.CONTENT` | `True` | Whether to collect content |
| `GATHER.MODEL` | `app` | Collection mode |
| `GATHER.CONTENT_AUTO_CHECK` | `False` | Whether to automatically check uncollected article content |
| `GATHER.CONTENT_AUTO_INTERVAL` | `59` | Time interval for automatically checking uncollected article content (minutes) |
| `GATHER.CONTENT_MODE` | `web` | Content correction mode |
| `SAFE_HIDE_CONFIG` | `db,secret,token,notice.wechat,notice.feishu,notice.dingding` | Configuration information to hide |
| `SAFE_LIC_KEY` | `RACHELOS` | Authorization encryption key |
| `LOG_FILE` | Empty | Log file path |
| `LOG_LEVEL` | `INFO` | Log level |
| `EXPORT_PDF` | `False` | Whether to enable PDF export functionality |