# 项目配置

## 问题修复：GitHub Copilot 聊天输入框文字重叠

### 问题描述

在 VS Code 中使用 GitHub Copilot 聊天功能时，输入框内出现中文字符重叠、看不清楚的问题（如下图所示）。

**原因**：VS Code 默认字体不包含中文字符的完整支持，导致在聊天输入框中中文字符渲染时发生重叠。

### 解决方案

本项目已添加 `.vscode/settings.json` 配置文件，包含以下修复：

1. **字体配置**：设置支持中文的字体族（Microsoft YaHei / PingFang SC / Noto Sans CJK SC）
2. **行高调整**：增加行高（1.6）避免字符垂直方向重叠
3. **聊天视图字体**：单独为 Copilot 聊天视图配置字体和行高
4. **编码设置**：确保 UTF-8 编码，正确处理中文字符

### 应用配置

打开本项目后，VS Code 会自动应用 `.vscode/settings.json` 中的配置。

如需手动应用，也可以将以下配置复制到 VS Code 全局用户设置（`Ctrl+Shift+P` → `打开用户设置(JSON)`）：

```json
{
  "editor.fontFamily": "'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', Consolas, 'Courier New', monospace",
  "editor.lineHeight": 1.6,
  "chat.editor.fontFamily": "'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', Consolas, 'Courier New', monospace",
  "chat.editor.lineHeight": 1.6
}
```

### 其他解决方案

如果上述配置不能解决问题，可以尝试：

1. **重启 VS Code**：`Ctrl+Shift+P` → `重新加载窗口`
2. **更新 GitHub Copilot 扩展**：确保使用最新版本
3. **禁用 GPU 加速**（临时）：使用命令行启动 VS Code 时添加参数 `code --disable-hardware-acceleration`
4. **检查字体安装**：确保系统已安装 Microsoft YaHei 或其他中文字体
