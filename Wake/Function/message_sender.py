import os
import logging
import websocket
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MessageSender:
    """发送消息到 WebUI"""
    
    def __init__(self, logger=None):
        self.webui_url = os.getenv('WEBUI_URL', 'http://localhost:3000')
        self.ws_url = os.getenv('WEBUI_WS_URL', 'ws://localhost:3000/ws/voice')
        self.logger = logger or logging.getLogger(__name__)
        self.ws = None
        
    def connect_websocket(self):
        """连接到 WebSocket 服务器"""
        try:
            self.ws = websocket.create_connection(self.ws_url)
            self.logger.info("WebSocket 连接成功")
            return True
        except Exception as e:
            self.logger.error(f"WebSocket 连接失败: {str(e)}")
            return False
    
    def send_message(self, text: str) -> bool:
        """
        发送消息到 WebUI
        :param text: 要发送的文本
        :return: 是否发送成功
        """
        try:
            if not self.ws:
                if not self.connect_websocket():
                    return False
            
            # 发送消息
            message = {
                "type": "voice_input",
                "text": text
            }
            self.ws.send(json.dumps(message))
            self.logger.info(f"消息发送成功：{text}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            if self.ws:
                self.ws.close()
                self.ws = None
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None 