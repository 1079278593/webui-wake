from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import os
import socket
import logging
import json
from datetime import datetime
import sys
import http.client
import urllib.parse
import shutil

# 获取模型名称
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'deepseek-r1:1.5b')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('server.log')   # 只保存到文件
    ]
)

# 创建控制台处理器，只输出 WARNING 及以上级别的日志
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)

def find_free_port(start_port, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise OSError(f"无法找到可用端口 (尝试范围: {start_port}-{start_port + max_attempts - 1})")

class LoggingRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        """重写日志方法，使用DEBUG级别记录请求"""
        logger.debug("%s - - [%s] %s",
            self.address_string(),
            self.log_date_time_string(),
            format%args)

class CORSRequestHandler(LoggingRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        logger.debug("收到 OPTIONS 请求")
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        logger.debug(f"收到 GET 请求: {self.path}")
        # 添加新的路由处理模型名称请求
        if self.path == '/model':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({'model': OLLAMA_MODEL})
            self.wfile.write(response.encode('utf-8'))
            return
        # 如果请求根路径，重定向到chat.html
        if self.path == '/':
            self.path = '/chat.html'
            logger.debug("根路径请求，重定向到 chat.html")
        # 处理图标请求
        elif self.path in ['/favicon.ico', '/apple-touch-icon.png', '/apple-touch-icon-precomposed.png']:
            logger.debug(f"处理图标请求: {self.path}")
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.end_headers()
            return
        elif self.path == '/chat.html':
            # 读取文件内容
            try:
                with open('chat.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                # 发送响应
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                return
            except Exception as e:
                logger.error(f"处理 chat.html 时出错: {e}")
                return SimpleHTTPRequestHandler.do_GET(self)
        return SimpleHTTPRequestHandler.do_GET(self)

    def proxy_ollama_request(self, data):
        """代理转发请求到Ollama服务器"""
        try:
            # 连接到本地Ollama服务器
            conn = http.client.HTTPConnection("localhost", 11434)
            headers = {'Content-Type': 'application/json'}
            
            # 发送请求
            conn.request("POST", "/api/generate", data, headers)
            
            # 获取响应
            response = conn.getresponse()
            
            # 设置响应头
            self.send_response(response.status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # 直接转发响应数据
            shutil.copyfileobj(response, self.wfile)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"代理请求失败: {e}")
            self.send_error(500, f"代理请求失败: {str(e)}")

    def do_POST(self):
        """处理POST请求并记录数据"""
        logger.debug(f"收到 POST 请求: {self.path}")
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # 处理Ollama API请求
        if self.path == '/api/generate':
            return self.proxy_ollama_request(post_data)
            
        try:
            # 尝试解析JSON数据
            json_data = json.loads(post_data.decode('utf-8'))
            
            # 处理日志请求
            if self.path == '/log':
                log_type = json_data.get('type', 'unknown')
                
                if log_type == 'start':
                    data = json_data['data']
                    print(f"\n{'='*50}")
                    print(f"开始新对话 [{data['timestamp']}]")
                    print(f"模型: {OLLAMA_MODEL}")  # 使用当前选择的模型
                    print(f"用户: {data['user_message']}")
                    print("助手: ", end='', flush=True)
                
                elif log_type == 'stream':
                    data = json_data['data']
                    print(data['content'], end='', flush=True)
                    
                elif log_type == 'end':
                    print(f"\n{'='*50}")
                
                elif log_type == 'interrupt':
                    data = json_data['data']
                    print(f"\n[用户中断] {data['message']} [{data['timestamp']}]")
                    print(f"{'='*50}")
                
                elif log_type == 'error':
                    print(f"\n错误 [{json_data.get('timestamp', datetime.now().isoformat())}]: "
                          f"{json_data.get('error', 'Unknown error')}")
            else:
                logger.debug(f"请求数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
                
        except json.JSONDecodeError:
            logger.debug(f"非JSON数据: {post_data.decode('utf-8')}")
        except Exception as e:
            logger.error(f"处理POST数据时出错: {str(e)}")

        # 继续正常的请求处理
        self.send_response(200)
        self.end_headers()

class TCPServerReusableAddr(socketserver.TCPServer):
    allow_reuse_address = True  # 允许端口重用

def get_local_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def run_server(port):
    """运行服务器"""
    try:
        local_ip = get_local_ip()
        with TCPServerReusableAddr(("0.0.0.0", port), CORSRequestHandler) as httpd:
            print(f"服务器运行在:")
            print(f"- 本地访问: http://localhost:{port}")
            print(f"- 局域网访问: http://{local_ip}:{port}")
            print(f"使用模型: {OLLAMA_MODEL}")
            print("按 Ctrl+C 停止服务器")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.server_close()  # 确保关闭服务器并释放端口
    except Exception as e:
        logger.error(f"服务器错误: {e}")

if __name__ == "__main__":
    DEFAULT_PORT = 8000
    try:
        # 尝试找到可用端口
        port = find_free_port(DEFAULT_PORT)
        logger.info(f"启动服务器...")
        run_server(port)
    except Exception as e:
        logger.error(f"错误: {e}") 