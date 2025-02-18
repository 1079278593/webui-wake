#!/bin/bash

echo "=== 检查 PyAudio 安装 ==="

# 激活虚拟环境
source fresh_env/bin/activate

# 检查是否已安装 PyAudio
if ! python -c "import pyaudio" &> /dev/null; then
    echo "PyAudio 未安装，开始安装..."
    
    # 在 macOS 上安装 portaudio
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! brew list portaudio &> /dev/null; then
            echo "安装 portaudio..."
            brew install portaudio
        fi
        
        # 安装 PyAudio
        echo "安装 PyAudio..."
        pip install --global-option="build_ext" \
                   --global-option="-I/opt/homebrew/include" \
                   --global-option="-L/opt/homebrew/lib" \
                   pyaudio
    else
        # 其他系统直接安装
        pip install pyaudio
    fi
else
    echo "PyAudio 已安装，跳过..."
fi

# 安装其他依赖
echo "安装其他依赖..."
pip install -r requirements.txt

echo "=== 安装完成 ==="

# 提示用户
echo "现在可以运行: ./fresh_env/bin/python app.py" 