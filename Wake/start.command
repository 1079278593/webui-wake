#!/bin/bash

echo "正在启动语音助手..."
echo "------------------------"

# 切换到指定目录
cd /Users/imvt/Desktop/GitHub/OpenAI/OpenWebUI/webui-wake/Wake
echo "cd /Users/imvt/Desktop/GitHub/OpenAI/OpenWebUI/webui-wake/Wake"

# 激活虚拟环境
echo "正在初始化环境...(source fresh_env/bin/activate)"
source fresh_env/bin/activate

# 运行程序
echo "启动完成！开始运行..."
echo "------------------------"
python3 Function/wake_listener.py

# 等待用户按任意键退出
echo "------------------------"
echo "程序已结束"
read -p "按任意键退出..." key 