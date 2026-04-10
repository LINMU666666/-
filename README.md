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

## 🎨 图像换色脚本

生成同一图片的不同颜色版本，并循环验证输出：

```bash
python image_recolor.py --url https://github.com/user-attachments/assets/a0fd8357-be7a-4915-96da-a05d1570d7ac
# 可选：python image_recolor.py --input /absolute/path/to/image.png --variants 6 --output-dir recolor_outputs
```

---

## 📱 DingTalk 钉钉机器人集成

### 配置

1. **复制并填写环境变量文件**

   ```bash
   cp .env.example .env
   # 编辑 .env，填入真实的 Webhook 地址和签名密钥
   ```

   | 变量 | 说明 |
   |------|------|
   | `DINGTALK_WEBHOOK_URL` | **必填** — 钉钉自定义机器人 Webhook 地址（含 `access_token`） |
   | `DINGTALK_SECRET`      | 可选 — 加签密钥（在机器人安全设置中启用"加签"后获取） |
   | `DINGTALK_APP_SECRET`  | 可选 — 用于验证 DingTalk 回调请求的签名（接收消息服务器侧） |

   > ⚠️ **请勿将 `.env` 提交到版本控制！** 该文件已列入 `.gitignore`。

2. **或直接导出环境变量**

   ```bash
   export DINGTALK_WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
   export DINGTALK_SECRET="YOUR_SECRET"   # 可选
   ```

### 发送测试消息

```bash
python scripts/send_dingtalk_message.py
```

成功输出示例：

```
🚀 Testing DingTalk integration...

1️⃣  Sending text message…
   ✅ Text message sent successfully

2️⃣  Sending Markdown message…
   ✅ Markdown message sent successfully

✨ All tests completed successfully!
```

### 启动消息监听服务器（接收回调）

```bash
python dingtalk_server.py              # 默认监听 8080 端口
python dingtalk_server.py --port 9000  # 自定义端口
```

在钉钉开发者后台将机器人的"消息接收地址"设置为：

```
http://<your-server>:8080/dingtalk/callback
```

服务器收到消息后会自动通过 Webhook 发送回复。健康检查接口：

```
GET http://<your-server>:8080/health
```

### 在 SpeedAI 流程中自动推送通知

`speedai_client.py` 会在文档处理完成后自动调用 `_notify_dingtalk()`。  
只需在运行前设置好 `DINGTALK_WEBHOOK_URL` 即可，无需额外参数。

```bash
export DINGTALK_WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
python speedai_client.py --apikey YOUR_API_KEY --mode deai --type weipu
# 处理完成时钉钉群将收到通知
```

### 在代码中使用

```python
from dingtalk_bot import DingTalkBot

bot = DingTalkBot()  # 从环境变量 / .env 读取配置
bot.send_text("Hello from OpenClaw!")
bot.send_markdown("报告标题", "## 内容\n正文...")
```
