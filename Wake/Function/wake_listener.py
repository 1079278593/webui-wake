import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import sys
from message_sender import MessageSender
from voice_listener import create_listener

# 配置日志
def setup_logging():
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 设置日志文件名（使用当前时间）
    log_filename = f"logs/wake_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class WakeWordService:
    def __init__(self, listener_type="computer"):
        self.wake_word = "小明同学"
        self.dismiss_words = ["退下", "退下吧"]
        self.logger = setup_logging()
        self.is_active = False  # 是否处于活跃状态（是否发送消息）
        
        # 创建监听器和消息发送器
        self.listener = create_listener(listener_type, self.logger)
        self.sender = MessageSender(self.logger)
        
    def run(self):
        self.logger.info("启动语音监听服务")
        self.logger.info(f"当前唤醒词: {self.wake_word}")
        self.logger.info(f"当前停止词: {', '.join(self.dismiss_words)}")
        
        try:
            # 初始化监听器
            self.listener.initialize()
            
            while True:
                # 获取语音输入
                text = self.listener.listen()
                if not text:
                    continue
                
                # 如果是活跃状态，检查是否要停止
                if self.is_active:
                    if any(word in text for word in self.dismiss_words):
                        self.logger.info("检测到停止命令，回到等待唤醒状态")
                        self.is_active = False
                        continue
                    # 活跃状态下，直接发送识别到的内容
                    self.sender.send_message(text)
                # 如果不是活跃状态，检查是否是唤醒词
                elif self.wake_word in text:
                    self.logger.info("检测到唤醒词！进入活跃状态")
                    self.is_active = True
                    # 如果唤醒词后面还有内容，发送该内容
                    if len(text) > len(self.wake_word):
                        content = text.replace(self.wake_word, "").strip()
                        if content:
                            self.sender.send_message(content)
                            
        except KeyboardInterrupt:
            self.logger.info("程序被用户中断")
        except Exception as e:
            self.logger.error(f"程序异常退出: {str(e)}", exc_info=True)
        finally:
            self.listener.cleanup()

if __name__ == "__main__":
    try:
        # 从环境变量获取监听器类型
        listener_type = os.getenv('LISTENER_TYPE', 'computer')
        
        service = WakeWordService(listener_type)
        service.run()
    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.error(f"程序异常退出: {str(e)}", exc_info=True) 