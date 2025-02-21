from flask import Flask
import os
import sys
from config.settings import FLASK_CONFIG, SERVER_CONFIG, DIRS
from utils.logger import logger
from routes.main import main_bp
from routes.chat import chat_bp
from routes.voice import voice_bp

def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(__name__,
                static_folder=DIRS['STATIC'],
                template_folder=DIRS['TEMPLATES'])
    
    # 配置Flask应用
    app.config.update(**FLASK_CONFIG)
    
    # 禁用Flask-Debug的自动重载
    app.jinja_env.auto_reload = False
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(voice_bp)
    
    return app

if __name__ == '__main__':
    # 创建应用实例
    app = create_app()
    
    # 只在主进程中打印启动信息
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        logger.info("=== 服务启动 ===")
        logger.info(f"静态文件目录: {DIRS['STATIC']}")
        logger.info(f"模板文件目录: {DIRS['TEMPLATES']}")
        logger.info(f"日志文件目录: {DIRS['LOGS']}")
    
    try:
        # 启动Flask应用
        app.run(
            debug=SERVER_CONFIG['DEBUG'],
            host=SERVER_CONFIG['HOST'],
            port=SERVER_CONFIG['PORT']
        )
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        sys.exit(1) 