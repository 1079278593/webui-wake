#!/bin/bash

# 获取脚本所在目录的绝对路径
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本所在目录
cd "$DIR"

# 检查并关闭已运行的服务
PIDS=($(pgrep -f "python3 server.py"))
if [ ${#PIDS[@]} -gt 0 ]; then
    echo "发现正在运行的服务数量: ${#PIDS[@]}，正在关闭..."
    pkill -f "python3 server.py"
    sleep 1
fi

# 清理可能存在的 Ollama 未完成请求
if pgrep -x "ollama" > /dev/null; then
    echo "正在清理 Ollama 进程..."
    curl -s http://localhost:11434/api/generate -d '{"command":"stop"}' > /dev/null 2>&1
    pkill -x ollama
    sleep 2
    if pgrep -x "ollama" > /dev/null; then
        echo "正在强制终止 Ollama 进程..."
        pkill -9 -x ollama
        sleep 1
    fi
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    echo "请安装 Python3 后再试"
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

# 检查 Ollama 是否安装
if ! command -v ollama &> /dev/null; then
    echo "错误: 未找到 Ollama"
    echo "请先安装 Ollama: curl -fsSL https://ollama.com/install.sh | sh"
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

# 启动 Ollama 服务
if ! pgrep -x "ollama" > /dev/null; then
    echo "正在启动 Ollama 服务..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# 检查 Ollama 是否运行
if ! curl -s http://localhost:11434/api/tags >/dev/null; then
    echo "错误: Ollama 服务未运行"
    echo "请手动运行 'ollama serve' 启动服务"
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

# 获取可用模型列表
echo "正在获取可用模型列表..."
MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [model['name'] for model in data['models']]
    print('\n'.join(models))
except:
    print('获取模型列表失败')
")

# 显示可用模型
echo -e "\n可用模型列表:"
echo "$MODELS"
echo -e "\n默认模型: deepseek-r1:1.5b"

# 提示用户选择模型
echo -e "\n请选择要使用的模型 (直接回车使用默认模型):"
read MODEL

# 如果用户没有输入，使用默认模型
if [ -z "$MODEL" ]; then
    MODEL="deepseek-r1:1.5b"
fi

# 导出模型名称为环境变量
export OLLAMA_MODEL="$MODEL"

# 启动服务器
echo -e "\n使用模型: $MODEL"
echo "启动服务器..."
python3 server.py

# 如果服务器异常退出，等待用户按键
read -n 1 -s -r -p "按任意键退出..." 