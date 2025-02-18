#!/bin/bash

echo "正在启动语音助手..."
echo "------------------------"

# 获取脚本所在目录的绝对路径
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本所在目录
cd "$DIR"
echo "切换到工作目录：$DIR"

# 清理函数
cleanup_processes() {
    # 清理 Flask 服务
    if pgrep -f "python.*app.py" > /dev/null; then
        echo "正在关闭 Flask 服务..."
        pkill -f "python.*app.py"
        sleep 1
        # 如果进程仍然存在，强制终止
        if pgrep -f "python.*app.py" > /dev/null; then
            echo "强制终止 Flask 服务..."
            pkill -9 -f "python.*app.py"
        fi
    fi

    # 清理 Ollama 进程
    if pgrep -x "ollama" > /dev/null; then
        echo "正在清理 Ollama 进程..."
        curl -s http://localhost:11434/api/generate -d '{"command":"stop"}' > /dev/null 2>&1
        pkill -x ollama
        sleep 2
        if pgrep -x "ollama" > /dev/null; then
            echo "强制终止 Ollama 进程..."
            pkill -9 -x ollama
            sleep 1
        fi
    fi

    # 等待所有进程完全终止
    sleep 2
}

# 执行清理
cleanup_processes

# 检查虚拟环境是否存在
if [ ! -f "./fresh_env/bin/python" ]; then
    echo "错误: 虚拟环境未找到"
    echo "请先运行 setup.sh 创建虚拟环境"
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

# 激活虚拟环境
echo "正在激活虚拟环境..."
source fresh_env/bin/activate

# 检查 PyAudio 是否正确安装
./fresh_env/bin/python -c "import pyaudio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: PyAudio 未正确安装"
    echo "请运行 setup.sh 安装所需依赖"
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

# 选择启动模式
echo "请选择启动模式："
echo "1) 仅启动Web服务器 (app.py)"
echo "2) 仅启动语音监听 (wake_listener.py)"
echo "3) 同时启动两个服务"
read -p "请输入选项 [1-3]: " choice

case $choice in
    1)
        echo "启动Web服务器..."
        ./fresh_env/bin/python app.py
        ;;
    2)
        echo "启动语音监听服务..."
        ./fresh_env/bin/python Function/wake_listener.py
        ;;
    3)
        echo "同时启动两个服务..."
        # 启动Web服务器并等待其就绪
        ./fresh_env/bin/python app.py > /tmp/flask.log 2>&1 &
        FLASK_PID=$!
        
        # 等待Flask服务器启动（最多等待10秒）
        for i in {1..10}; do
            if curl -s http://localhost:52718 > /dev/null; then
                echo "Web服务器已就绪"
                break
            fi
            if ! ps -p $FLASK_PID > /dev/null; then
                echo "Web服务器启动失败，请检查 /tmp/flask.log"
                exit 1
            fi
            echo "等待Web服务器就绪... ($i/10)"
            sleep 1
        done
        
        # 启动语音监听服务
        ./fresh_env/bin/python Function/wake_listener.py
        ;;
    *)
        echo "无效的选项！"
        exit 1
        ;;
esac

# 等待用户按任意键退出
echo "------------------------"
echo "程序已结束"
read -p "按任意键退出..." key 