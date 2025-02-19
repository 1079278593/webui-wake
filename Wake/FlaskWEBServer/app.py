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
import speech_recognition as sr
from queue import Queue
import threading
import uuid

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
            # 发送请求给Ollama
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
                            logger.info(f"Ollama响应片段: {chunk}")
                            yield f"data: {json.dumps({'response': chunk})}\n\n"
                            
                logger.info("Ollama响应完成")
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

class DialogueManager:
    def __init__(self):
        self.active_dialogues = {}
        self.max_dialogues = 3
        self.lock = threading.Lock()

    def create_dialogue(self):
        with self.lock:
            # 清理已完成的对话
            self._cleanup_completed_dialogues()
            
            # 如果达到最大对话数，尝试重用已完成的对话
            if len(self.active_dialogues) >= self.max_dialogues:
                for dialogue_id, dialogue in self.active_dialogues.items():
                    if dialogue['status'] == 'completed':
                        return dialogue_id
                
                # 如果没有已完成的对话，返回None
                return None
            
            # 创建新对话
            dialogue_id = str(uuid.uuid4())
            self.active_dialogues[dialogue_id] = {
                'status': 'active',
                'controller': None,
                'response_queue': Queue()
            }
            return dialogue_id

    def _cleanup_completed_dialogues(self):
        completed = [did for did, d in self.active_dialogues.items() 
                    if d['status'] == 'completed']
        for did in completed:
            del self.active_dialogues[did]

    def get_dialogue(self, dialogue_id):
        return self.active_dialogues.get(dialogue_id)

    def set_dialogue_controller(self, dialogue_id, controller):
        if dialogue_id in self.active_dialogues:
            self.active_dialogues[dialogue_id]['controller'] = controller

    def complete_dialogue(self, dialogue_id):
        if dialogue_id in self.active_dialogues:
            self.active_dialogues[dialogue_id]['status'] = 'completed'

dialogue_manager = DialogueManager()

class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.stop_listening = None
        self.callback = None
        self.mic = None
        self.buffer = []
        self.last_speech_time = None
        self.speech_timeout = 1.5
        self._lock = threading.Lock()
        self.event_queue = Queue()
        
        # 优化识别器默认参数
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 1000  # 降低阈值，提高灵敏度
        self.recognizer.pause_threshold = 0.3    # 缩短停顿判断时间
        self.recognizer.phrase_threshold = 0.3   # 降低短语阈值
        self.recognizer.non_speaking_duration = 0.3  # 非说话时间阈值

    def start_listening(self, callback):
        with self._lock:
            if self.is_listening:
                self.stop()
                time.sleep(0.5)
            
            # 重置状态
            self.is_listening = False
            self.stop_listening = None
            self.callback = None
            self.mic = None
            self.buffer = []
            self.last_speech_time = None
            
            try:
                # 获取可用的麦克风列表
                mics = sr.Microphone.list_microphone_names()
                logger.info(f"可用麦克风: {mics}")
                
                # 创建新的 Microphone 实例，使用默认设备
                self.mic = sr.Microphone()
                self.callback = callback
                
                # 配置识别器
                with self.mic as source:
                    logger.info("正在调整噪音...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    logger.info(f"能量阈值设置为: {self.recognizer.energy_threshold}")
                
                # 启动监听前确保设置正确
                self.is_listening = True
                
                # 使用新的 Microphone 实例启动监听
                self.stop_listening = self.recognizer.listen_in_background(
                    self.mic, 
                    self._audio_callback,
                    phrase_time_limit=10
                )
                
                logger.info("语音识别成功启动")
                return True
                
            except Exception as e:
                logger.error(f"启动语音识别失败: {str(e)}")
                self.stop()
                return False

    def _audio_callback(self, recognizer, audio):
        if not self.is_listening:
            return
            
        try:
            text = recognizer.recognize_google(
                audio, 
                language='zh-CN',
                show_all=False,
                with_confidence=True
            )
            
            current_time = time.time()
            
            if isinstance(text, tuple):
                text, confidence = text
                logger.info(f"识别到语音: {text} (置信度: {confidence})")
            else:
                logger.info(f"识别到语音: {text}")
            
            if text:
                self.buffer.append(text)
                self.last_speech_time = current_time
                
                # 检查是否需要发送
                if len(self.buffer) > 0 and self.is_listening:
                    if (current_time - self.last_speech_time) >= self.speech_timeout:
                        complete_text = "".join(self.buffer)
                        self.buffer = []
                        logger.info(f"发送完整语音内容: {complete_text}")
                        self.event_queue.put({
                            'text': complete_text,
                            'status': 'success'
                        })
                
        except sr.UnknownValueError:
            # 只在缓冲区有内容时处理
            if self.buffer and self.last_speech_time and self.is_listening and \
               (time.time() - self.last_speech_time) >= self.speech_timeout:
                complete_text = "".join(self.buffer)
                self.buffer = []
                if complete_text.strip():
                    logger.info(f"发送缓冲区内容: {complete_text}")
                    self.event_queue.put({
                        'text': complete_text,
                        'status': 'success'
                    })
                
        except sr.RequestError as e:
            logger.error(f"语音识别服务错误: {str(e)}")
            self.event_queue.put({
                'error': str(e),
                'status': 'error'
            })
            # 尝试重新启动识别
            if self.is_listening:
                logger.info("尝试重新启动语音识别...")
                self.stop()
                time.sleep(1)
                self.start_listening(self.callback)
        except Exception as e:
            logger.error(f"语音识别错误: {str(e)}")
            self.event_queue.put({
                'error': str(e),
                'status': 'error'
            })

    def stop(self):
        with self._lock:
            try:
                # 发送剩余的缓冲区内容
                if self.buffer and self.callback and self.is_listening:
                    complete_text = "".join(self.buffer)
                    if complete_text.strip():  # 只在有实际内容时发送
                        logger.info(f"停止前发送最后的内容: {complete_text}")
                        self.callback(complete_text)
                
                # 停止监听
                if self.stop_listening:
                    self.stop_listening(True)
                    time.sleep(0.2)
                
                # 重置所有状态
                self.is_listening = False
                self.stop_listening = None
                self.callback = None
                self.mic = None
                self.buffer = []
                self.last_speech_time = None
                
                logger.info("语音识别已停止")
                
            except Exception as e:
                logger.error(f"停止语音识别时出错: {str(e)}")

speech_recognizer = SpeechRecognizer()

@app.route('/start_voice', methods=['POST'])
def start_voice():
    try:
        dialogue_id = dialogue_manager.create_dialogue()
        if dialogue_id is None:
            return jsonify({'error': '已达到最大对话数限制'}), 429
        
        def recognition_callback(text):
            try:
                if isinstance(text, dict):
                    if text.get('status') == 'success' and text.get('text', '').strip():
                        logger.info(f"返回语音识别文本: {text['text']}")
                        return text
                return None
            except Exception as e:
                logger.error(f"处理语音识别结果失败: {str(e)}")
                return None
        
        if speech_recognizer.start_listening(recognition_callback):
            return jsonify({
                'status': 'started',
                'dialogue_id': dialogue_id
            })
        return jsonify({'error': '启动语音识别失败'}), 500
        
    except Exception as e:
        logger.error(f"启动语音识别服务失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stop_voice', methods=['POST'])
def stop_voice():
    try:
        speech_recognizer.stop()
        return jsonify({'status': 'stopped'})
    except Exception as e:
        logger.error(f"停止语音识别时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stop_dialogue/<dialogue_id>', methods=['POST'])
def stop_dialogue(dialogue_id):
    dialogue = dialogue_manager.get_dialogue(dialogue_id)
    if dialogue and dialogue['controller']:
        dialogue['controller'].abort()
        dialogue_manager.complete_dialogue(dialogue_id)
        return jsonify({'status': 'stopped'})
    return jsonify({'error': '对话不存在或已结束'}), 404

@app.route('/voice_events')
def voice_events():
    def generate():
        try:
            while speech_recognizer.is_listening:
                try:
                    event = speech_recognizer.event_queue.get(timeout=5)  # 减少超时时间
                    if event:
                        logger.info(f"发送语音事件: {event}")
                        yield f"data: {json.dumps(event)}\n\n"
                except Exception as e:
                    if speech_recognizer.is_listening:
                        # 发送保持活动信号
                        yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                    else:
                        break
        except GeneratorExit:
            logger.info("客户端关闭了语音事件流")
            speech_recognizer.stop()  # 确保停止语音识别
        except Exception as e:
            logger.error(f"处理语音事件错误: {str(e)}")
            speech_recognizer.stop()
    
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