import threading
import uuid
from queue import Queue
import requests
import json
from utils.logger import logger
from config.settings import DIALOGUE_CONFIG, OLLAMA_CONFIG

class DialogueManager:
    def __init__(self):
        self.active_dialogues = {}
        self.max_dialogues = DIALOGUE_CONFIG['MAX_DIALOGUES']
        self.lock = threading.Lock()
        self.current_request = None  # 当前正在进行的请求

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
                'request': None,
                'response_queue': Queue(),
                'messages': []  # 存储对话历史
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

    def set_current_request(self, request):
        with self.lock:
            if self.current_request:
                self.stop_current_request()
            self.current_request = request

    def stop_current_request(self):
        with self.lock:
            if self.current_request:
                try:
                    # 发送中断请求到 Ollama
                    requests.delete(OLLAMA_CONFIG['API_URL'])
                    logger.info("已发送中断请求到 Ollama")
                    yield {'status': 'interrupted'}
                except Exception as e:
                    logger.error(f"中断 Ollama 请求时出错: {str(e)}")
                self.current_request = None

    def send_message_to_ollama(self, message, dialogue_id=None):
        """发送消息到Ollama并返回响应生成器"""
        try:
            # 如果提供了对话ID，则更新对话历史
            if dialogue_id and dialogue_id in self.active_dialogues:
                dialogue = self.active_dialogues[dialogue_id]
                dialogue['messages'].append({"role": "user", "content": message})
                
                # 构建完整的对话历史
                full_context = ""
                for msg in dialogue['messages']:
                    if msg["role"] == "user":
                        full_context += f"User: {msg['content']}\n"
                    else:
                        full_context += f"Assistant: {msg['content']}\n"
                message = full_context

            # 发送请求给Ollama
            ollama_data = {
                "model": OLLAMA_CONFIG['DEFAULT_MODEL'],
                "prompt": message,
                "stream": True
            }
            
            logger.info("正在发送请求到Ollama服务")
            response = requests.post(OLLAMA_CONFIG['API_URL'], json=ollama_data, stream=True)
            self.set_current_request(response)
            
            if response.status_code == 200:
                accumulated_response = ""
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        chunk = json_response.get('response', '')
                        if chunk:
                            # 使用额外的属性来标识这是Ollama的响应
                            logger.info(chunk, extra={'is_ollama_response': True})
                            accumulated_response += chunk
                            yield {'response': chunk}
                
                # 如果有对话ID，保存助手的回复
                if dialogue_id and dialogue_id in self.active_dialogues:
                    self.active_dialogues[dialogue_id]['messages'].append({
                        "role": "assistant",
                        "content": accumulated_response
                    })
                            
                logger.info("", extra={'is_ollama_response': True, 'is_response_complete': True})
                yield {'done': True}
            else:
                error_msg = f"Ollama服务响应失败: {response.text}"
                logger.error(error_msg)
                yield {'error': error_msg}
        except Exception as e:
            error_msg = f"发生异常: {str(e)}"
            logger.error(error_msg)
            if str(e) == 'interrupted':
                yield {'status': 'interrupted'}
            else:
                yield {'error': error_msg}
        finally:
            self.set_current_request(None)

# 创建全局对话管理器实例
dialogue_manager = DialogueManager() 