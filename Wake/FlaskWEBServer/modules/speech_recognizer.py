import speech_recognition as sr
import threading
import time
from queue import Queue
from utils.logger import logger
from config.settings import SPEECH_CONFIG

class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.stop_listening = None
        self.callback = None
        self.mic = None
        self.buffer = []
        self.last_speech_time = None
        self.speech_timeout = SPEECH_CONFIG['SPEECH_TIMEOUT']
        self._lock = threading.Lock()
        self.event_queue = Queue()
        
        # 优化识别器默认参数
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = SPEECH_CONFIG['ENERGY_THRESHOLD']
        self.recognizer.pause_threshold = SPEECH_CONFIG['PAUSE_THRESHOLD']
        self.recognizer.phrase_threshold = SPEECH_CONFIG['PHRASE_THRESHOLD']
        self.recognizer.non_speaking_duration = SPEECH_CONFIG['NON_SPEAKING_DURATION']

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
                language=SPEECH_CONFIG['LANGUAGE'],
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

# 创建全局语音识别器实例
speech_recognizer = SpeechRecognizer() 