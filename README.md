# SpeedAI 示例

运行准备：
1. 安装依赖：`pip install -r requirements.txt`
2. 将 `.docx` 放在仓库根目录（默认文件名 `文本.docx`），或用 `--file` 指定路径
3. 运行脚本：
   ```bash
   python speedai_client.py --apikey YOUR_API_KEY --mode deai --type weipu
   ```
   可选：订阅进度 `--subscribe-token YOUR_TOKEN`

脚本流程：WS 处理 docx → 下载结果 → 段落改写 → 降 AI。支持 `--help` 查看所有参数，兼容 PyCharm 直接运行。

---

# DingTalk 文献阅读机器人

`dingtalk_bot.py` 是一个 Flask Webhook 服务，接收钉钉机器人消息，解析文献命令，调用 SpeedAI 处理，并将结果回复到钉钉群/会话。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

| 变量 | 说明 | 是否必填 |
|------|------|----------|
| `DINGTALK_APP_SECRET` | 钉钉机器人应用密钥（用于验签） | 生产环境必填 |
| `SPEEDAI_API_KEY` | SpeedAI API Key | 选填（不填则返回提取式摘要） |
| `PORT` | 监听端口（默认 8080） | 选填 |

```bash
export DINGTALK_APP_SECRET="your_app_secret"
export SPEEDAI_API_KEY="your_speedai_key"
export PORT=8080
```

### 3. 启动服务

```bash
python dingtalk_bot.py
```

服务启动后，在公网可访问的地址（如通过 nginx 反代）注册 Webhook 回调 URL：

```
https://your-domain.com/dingtalk/callback
```

健康检查地址：`GET /health`

### 4. 在钉钉开放平台配置机器人

1. 打开 [钉钉开放平台](https://open.dingtalk.com/) → **企业内部应用** → **机器人**
2. 创建机器人，填写 **消息接收地址** 为上方 Webhook URL
3. 记录 **AppSecret**，填入 `DINGTALK_APP_SECRET`
4. 将机器人添加到目标群/会话

## 支持的命令

在群内 @机器人 后发送以下命令：

| 命令 | 示例 | 说明 |
|------|------|------|
| `总结 <文本>` | `总结 近年来深度学习…` | 生成文献摘要 |
| `降AI <文本>` | `降AI 本研究旨在探讨…` | 降低 AI 痕迹 |
| `改写 <文本>` | `改写 学生是航行者…` | 改写文献段落 |
| `帮助` / `help` | `帮助` | 显示使用说明 |

## 运行测试

```bash
python -m pytest test_dingtalk_bot.py -v
```

