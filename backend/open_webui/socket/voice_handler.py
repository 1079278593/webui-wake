import logging
import sys
from typing import Optional

from open_webui.env import (
    GLOBAL_LOG_LEVEL,
    SRC_LOG_LEVELS,
)

# 设置日志
logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("SOCKET", logging.INFO))

class VoiceHandler:
    """处理语音相关的 WebSocket 事件"""
    
    def __init__(self, sio):
        self.sio = sio
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置事件处理器"""
        @self.sio.on("voice-input")
        async def handle_voice_input(sid: str, data: dict):
            await self._handle_voice_input(sid, data)
    
    async def _handle_voice_input(self, sid: str, data: dict):
        """
        处理语音输入事件
        :param sid: Socket ID
        :param data: 事件数据
        """
        try:
            text = data.get("text", "").strip()
            if not text:
                return
            
            # 发送到对应客户端的输入框
            await self.sio.emit(
                "chat-input",
                {"text": text},
                room=sid
            )
            log.debug(f"语音输入已处理: {text[:50]}...")
            
        except Exception as e:
            log.error(f"处理语音输入时出错: {str(e)}") 