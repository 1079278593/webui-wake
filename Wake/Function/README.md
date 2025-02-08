# Wake 语音唤醒服务

这是一个语音唤醒服务，用于监听特定唤醒词并发送消息。

## 功能特性

- 实时监听麦克风输入
- 识别中文唤醒词"小明同学"
- 支持多种消息发送方式（WebUI、控制台等）
- 模块化设计，易于扩展

## 安装要求

1. Python 3.8+
2. 系统麦克风
3. 网络连接（用于语音识别）
4. portaudio（用于音频处理）

## 首次安装步骤

1. 创建虚拟环境：
```bash
python3 -m venv fresh_env
```

2. 激活虚拟环境：
```bash
# 在 macOS/Linux 上：
source fresh_env/bin/activate
# 在 Windows 上：
.\fresh_env\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建 `.env` 文件并设置：
```
# WebUI 配置（如果使用 WebUI 发送器）
WEBUI_URL=http://localhost:3000

# 消息发送器配置
SENDER_TYPE=console  # 可选值: webui, console
```

## 消息发送器

系统支持多种消息发送方式：

1. **WebUI发送器** (SENDER_TYPE=webui)
   - 将消息发送到 Open WebUI
   - 需要 WebUI 服务正在运行
   - 需要配置 WEBUI_URL

2. **控制台发送器** (SENDER_TYPE=console)
   - 将消息打印到控制台
   - 用于测试和调试
   - 不需要额外配置

## 日常运行方式

每次运行前，需要先激活虚拟环境：
```bash
# 1. 激活虚拟环境
source fresh_env/bin/activate  # macOS/Linux
# 或
.\fresh_env\Scripts\activate   # Windows

# 2. 运行程序 (要用python3)
python3 wake_listener.py
（或者：python3 Function/wake_listener.py ）
```

## 为什么需要激活虚拟环境？

虚拟环境（Virtual Environment）是一个独立的 Python 运行环境，它有以下好处：
1. 隔离项目依赖，避免与系统其他 Python 项目的依赖冲突
2. 确保使用正确版本的包
3. 方便项目迁移和部署
4. 保持系统 Python 环境的清洁

如果不激活虚拟环境，程序可能因为找不到必要的依赖包而无法运行。

## 扩展消息发送器

要添加新的消息发送方式：

1. 在 `message_sender.py` 中创建新的发送器类
2. 继承 `MessageSender` 基类
3. 实现 `send_message` 方法
4. 在 `create_sender` 函数中注册新的发送器

## 注意事项

1. 确保系统麦克风正常工作
2. 需要网络连接以使用Google语音识别服务
3. 如果使用 WebUI 发送器，确保 WebUI 服务正在运行
4. 每次运行前记得激活虚拟环境 