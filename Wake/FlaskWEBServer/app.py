from flask import Flask, render_template, request, jsonify, Response, url_for
import requests
import json
import logging
import functools
import os
import sys
import socket
import time
from datetime import datetime

def find_available_port(start_port=49152, max_port=65535):
    """查找可用的端口"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except socket.error:
            continue
    raise RuntimeError("未找到可用端口")

# 配置日志
def setup_logging():
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 设置日志文件名（使用当前时间）
    log_filename = f"logs/flask_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志
logger = setup_logging()

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# 配置Flask应用
app.config.update(
    SEND_FILE_MAX_AGE_DEFAULT=0,  # 禁用静态文件缓存
    TEMPLATES_AUTO_RELOAD=True,    # 启用模板自动重载
)

# 禁用Flask-Debug的自动重载
app.jinja_env.auto_reload = False

# 添加调试路由
@app.route('/debug')
def debug():
    static_url = url_for('static', filename='style.css')
    template_path = os.path.join(app.template_folder, 'index.html')
    static_css_path = os.path.join(app.static_folder, 'style.css')
    static_js_path = os.path.join(app.static_folder, 'script.js')
    
    return {
        'static_folder': app.static_folder,
        'static_url': static_url,
        'static_folder_path': os.path.abspath(app.static_folder),
        'template_folder_path': os.path.abspath(app.template_folder),
        'exists': {
            'style.css': os.path.exists(static_css_path),
            'script.js': os.path.exists(static_js_path),
            'index.html': os.path.exists(template_path)
        },
        'file_permissions': {
            'style.css': oct(os.stat(static_css_path).st_mode)[-3:] if os.path.exists(static_css_path) else None,
            'script.js': oct(os.stat(static_js_path).st_mode)[-3:] if os.path.exists(static_js_path) else None,
            'index.html': oct(os.stat(template_path).st_mode)[-3:] if os.path.exists(template_path) else None
        }
    }

# 添加静态文件路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    logger.info(f"请求静态文件: {filename}")
    response = app.send_from_directory(app.static_folder, filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def stream_with_context(generator):
    try:
        yield from generator()
    except GeneratorExit:
        logger.info("客户端关闭了连接")
    except Exception as e:
        logger.error(f"流处理错误: {str(e)}")
    finally:
        logger.info("响应流结束")

@app.route('/')
def index():
    logger.info(f"收到主页访问请求 - IP: {request.remote_addr}")
    logger.info(f"User-Agent: {request.headers.get('User-Agent')}")
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    logger.info(f"收到聊天请求 - IP: {request.remote_addr}")
    logger.info(f"用户消息: {user_message}")
    
    def generate():
        try:
            # 准备发送给Ollama的请求
            ollama_data = {
                "model": "deepseek-r1:1.5b",
                "prompt": user_message,
                "stream": True
            }
            
            logger.info("正在发送请求到Ollama服务")
            response = requests.post(OLLAMA_API_URL, json=ollama_data, stream=True)
            logger.info(f"Ollama响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        chunk = json_response.get('response', '')
                        if chunk:
                            yield f"data: {json.dumps({'response': chunk})}\n\n"
                # 确保流正确结束
                yield "data: {\"done\": true}\n\n"
            else:
                logger.error(f"Ollama错误: {response.text}")
                yield f"data: {json.dumps({'error': 'Ollama服务响应失败'})}\n\n"
        except Exception as e:
            logger.error(f"发生异常: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            logger.info("聊天响应完成")
    
    return Response(stream_with_context(generate), mimetype='text/event-stream')

if __name__ == '__main__':
    # 确保目录存在
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 检查必要的静态文件
    required_files = {
        'static/style.css': '样式表',
        'static/script.js': 'JavaScript脚本',
        'templates/index.html': '主页模板'
    }
    
    missing_files = []
    for file_path, desc in required_files.items():
        if not os.path.exists(file_path):
            missing_files.append(f"{desc} ({file_path})")
    
    if missing_files:
        logger.error("缺少必要的文件:")
        for file in missing_files:
            logger.error(f"- {file}")
        sys.exit(1)
    
    logger.info("=== 服务启动 ===")
    logger.info(f"静态文件目录: {os.path.abspath('static')}")
    logger.info(f"模板文件目录: {os.path.abspath('templates')}")
    logger.info(f"日志文件目录: {os.path.abspath('logs')}")
    
    # 使用固定端口
    PORT = 8080
    
    try:
        logger.info(f"正在启动服务，端口: {PORT}")
        logger.info("可通过以下地址访问服务：")
        logger.info(f"- http://127.0.0.1:{PORT}")
        logger.info(f"- http://localhost:{PORT}")
        
        # 获取本机IP地址
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            logger.info(f"- http://{local_ip}:{PORT}")
        except Exception as e:
            logger.warning(f"获取本机IP地址失败: {str(e)}")
        
        # 启动Flask应用
        app.run(
            debug=True,
            host='0.0.0.0',
            port=PORT
        )
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        sys.exit(1) 