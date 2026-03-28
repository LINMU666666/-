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
