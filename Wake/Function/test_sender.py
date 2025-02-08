import asyncio
import logging
from message_sender import MessageSender

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # 创建消息发送器
    sender = MessageSender(logger)
    
    try:
        # 发送测试消息
        logger.info("开始发送测试消息...")
        success = await sender.send_message("测试消息")
        
        if success:
            logger.info("消息发送成功!")
        else:
            logger.error("消息发送失败!")
            
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
    finally:
        # 清理资源
        await sender.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 