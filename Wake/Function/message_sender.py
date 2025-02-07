import os
import logging
import socketio
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MessageSender:
    """发送消息到 WebUI"""
    
    def __init__(self, logger=None):
        # 只保留一个基础URL配置
        self.base_url = os.getenv('WEBUI_URL', 'http://localhost:3000')
        self.logger = logger or logging.getLogger(__name__)
        self.sio = None
        
    def check_server(self):
        """检查服务器是否可用"""
        try:
            response = requests.get(self.base_url)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"服务器连接检查失败: {str(e)}")
            return False
        
    async def connect_websocket(self):
        """连接到 Socket.IO 服务器"""
        if self.sio and self.sio.connected:
            self.logger.info("Socket.IO 已连接")
            return True
            
        try:
            if not self.check_server():
                self.logger.error("服务器不可用")
                return False
                
            # 创建异步Socket.IO客户端
            self.sio = socketio.AsyncClient(
                ssl_verify=False,
                logger=self.logger,
                engineio_logger=self.logger,
                reconnection=True,
                reconnection_attempts=3,
                reconnection_delay=1,
                http_session=None,  # 使用默认的aiohttp session
                request_timeout=5,  # 减少请求超时时间
                handle_sigint=False  # 不处理SIGINT信号
            )
            
            # 添加事件处理
            @self.sio.event
            async def connect():
                self.logger.info("Socket.IO 连接成功")
                
            @self.sio.event
            async def connect_error(data):
                self.logger.error(f"Socket.IO 连接错误: {data}")
                
            @self.sio.event
            async def disconnect():
                self.logger.info("Socket.IO 断开连接")
                
            @self.sio.event
            async def chat_input(data):
                self.logger.info(f"收到聊天输入确认: {data}")
            
            # 使用异步方式连接
            self.logger.info("正在连接到 Socket.IO 服务器...")
            await self.sio.connect(
                url=self.base_url,
                transports=['polling'],  # 只使用polling模式
                socketio_path='socket.io',  # 使用默认路径
                wait_timeout=5,  # 减少等待超时时间
                headers={
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'User-Agent': 'python-socketio-client'
                }
            )
            
            # 等待连接确认
            if not self.sio.connected:
                self.logger.error("Socket.IO 连接失败")
                return False
                
            self.logger.info("Socket.IO 连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Socket.IO 连接失败: {str(e)}")
            if self.sio:
                try:
                    await self.sio.disconnect()
                except:
                    pass
                self.sio = None
            return False
    
    async def send_message(self, text: str) -> bool:
        """
        发送消息到 WebUI
        :param text: 要发送的文本
        :return: 是否发送成功
        """
        try:
            # 确保连接存在且有效
            if not self.sio or not self.sio.connected:
                self.logger.info("Socket.IO 未连接，尝试重新连接...")
                if not await self.connect_websocket():
                    self.logger.error("无法建立 Socket.IO 连接")
                    return False
            
            # 发送消息
            self.logger.info(f"正在发送消息: {text}")
            await self.sio.emit('voice-input', {'text': text})
            self.logger.info(f"消息发送成功：{text}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            if self.sio:
                try:
                    await self.sio.disconnect()
                except:
                    pass
                self.sio = None
            return False
    
    async def cleanup(self):
        """清理资源"""
        if self.sio:
            try:
                await self.sio.disconnect()
            except:
                pass
            self.sio = None 