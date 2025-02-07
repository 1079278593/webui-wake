import abc
import speech_recognition as sr
import logging
from datetime import datetime
import os

class VoiceListener(abc.ABC):
    """语音监听器的基类"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    @abc.abstractmethod
    def initialize(self):
        """初始化监听器"""
        pass
    
    @abc.abstractmethod
    def listen(self):
        """
        监听并返回识别的文本
        :return: 识别到的文本，如果识别失败返回None
        """
        pass
    
    @abc.abstractmethod
    def cleanup(self):
        """清理资源"""
        pass

class ComputerMicListener(VoiceListener):
    """使用电脑麦克风的监听器实现"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.recognizer = None
        self.microphone = None
    
    def initialize(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # 配置识别器参数
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # 初始调整环境噪音
        with self.microphone as source:
            self.logger.info("正在调整环境噪音...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.logger.info(f"环境噪音调整完成，能量阈值: {self.recognizer.energy_threshold}")
    
    def listen(self):
        try:
            with self.microphone as source:
                self.logger.info("等待语音输入...")
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
                self.logger.info("检测到语音输入，开始识别...")
                
                text = self.recognizer.recognize_google(audio, language='zh-CN')
                self.logger.info(f"识别结果: {text}")
                return text
                
        except sr.WaitTimeoutError:
            self.logger.warning("监听超时")
        except sr.UnknownValueError:
            self.logger.debug("无法识别语音内容")
        except sr.RequestError as e:
            self.logger.error(f"语音识别服务出错: {str(e)}")
        except Exception as e:
            self.logger.error(f"发生未知错误: {str(e)}", exc_info=True)
        
        return None
    
    def cleanup(self):
        # 目前不需要特别的清理操作
        pass

# 工厂函数
def create_listener(listener_type: str = "computer", logger=None) -> VoiceListener:
    """
    创建语音监听器的工厂函数
    :param listener_type: 监听器类型，可选值：'computer'（未来可以添加更多类型）
    :param logger: 日志记录器
    :return: 语音监听器实例
    """
    listeners = {
        "computer": ComputerMicListener,
    }
    
    listener_class = listeners.get(listener_type.lower())
    if not listener_class:
        raise ValueError(f"不支持的监听器类型: {listener_type}")
    
    return listener_class(logger=logger) 