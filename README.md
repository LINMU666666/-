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

---

# OpenClaw + 钉钉部署排查（常见报错）

下列步骤针对截图中常见的两类错误：`cat: command not found`、`openclaw: command not found`。

## 1) `cat: command not found`

1. 先确认系统是否缺少基础工具：
   ```bash
   command -v cat
   ```
2. 如果没有输出，说明系统裁剪过，请安装基础工具：
   ```bash
   sudo apt-get update && sudo apt-get install -y coreutils
   ```

> 若脚本来自 Windows 环境，建议先转换行尾：
> ```bash
> sudo apt-get install -y dos2unix
> dos2unix ~/openclaw-dingtalk-setup.sh
> ```

## 2) `openclaw: command not found`

`openclaw` 并不是系统自带命令。请在 OpenClaw 项目目录内通过 Node 启动：

```bash
cd ~/OpenClaw
pnpm install
pnpm run build
pnpm start
```

或直接运行：

```bash
node scripts/run-node.mjs
```

如果你必须使用 CLI 形式（例如 `openclaw status`），请确保：

```bash
export PATH="$PWD/node_modules/.bin:$PATH"
```

## 3) 钉钉机器人不回消息

1. 检查配置文件是否已写入真实值：
   ```bash
   cat ~/.openclaw/openclaw.json
   ```
   确保 `clientId / clientSecret / robotCode / corpId` 不是占位符。示例结构如下：
   ```json
   {
     "client": {
       "channels": {
         "dingtalk": {
           "enabled": true,
           "clientId": "YOUR_CLIENT_ID",
           "clientSecret": "YOUR_CLIENT_SECRET",
           "robotCode": "YOUR_ROBOT_CODE",
           "corpId": "YOUR_CORP_ID",
           "dmPolicy": "open",
           "groupPolicy": "open",
           "messageType": "markdown"
         }
       }
     }
   }
   ```
2. 修改配置后重启 OpenClaw。
3. 确保服务器对外可访问（推荐 HTTPS + 443），并放行防火墙端口。
4. 可先用健康检查验证服务已启动：
   ```bash
   # OpenClaw 常见端口为 3000，按你的配置调整
   curl http://localhost:3000/health

   # 若检查 DingTalk 机器人服务（本仓库 dingtalk_bot.py），默认端口为 8080
   curl http://localhost:8080/health
   ```

## 4) 收到 401 Invalid signature（签名验证失败）

钉钉机器人每条消息都会携带 `timestamp` 和 `sign` 请求头。常见失败原因：

| 原因 | 解决方法 |
|------|---------|
| `DINGTALK_APP_SECRET` 填错或未配置 | 核对开放平台机器人配置页面的 **AppSecret** |
| 服务器时钟偏差超过 60 分钟 | 执行 `sudo ntpdate -u pool.ntp.org` 同步时间 |
| 请求通过反向代理被剥离了请求头 | nginx 需 `proxy_pass_request_headers on;` 并透传 `timestamp` / `sign` 头 |
| 签名过期（重放攻击保护） | 消息时间戳超过 60 分钟会被拒绝，属正常行为 |

验证方式（手动模拟 DingTalk 请求）：

```bash
SECRET="your_app_secret"
TS=$(date +%s%3N)        # 毫秒时间戳
SIGN=$(printf "%s\n%s" "$TS" "$SECRET" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)
curl -X POST http://localhost:8080/dingtalk/callback \
  -H "Content-Type: application/json" \
  -H "timestamp: $TS" \
  -H "sign: $SIGN" \
  -d '{"msgtype":"text","text":{"content":"帮助"},"senderNick":"test","sessionWebhook":""}'
```

预期返回：`{"errcode": 0, "errmsg": "ok"}`
