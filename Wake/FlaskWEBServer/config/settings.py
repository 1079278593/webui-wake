import os

# Flask配置
FLASK_CONFIG = {
    'SEND_FILE_MAX_AGE_DEFAULT': 0,  # 禁用静态文件缓存
    'TEMPLATES_AUTO_RELOAD': True,    # 启用模板自动重载
}

# 服务器配置
SERVER_CONFIG = {
    'PORT': 8080,
    'HOST': '0.0.0.0',
    'DEBUG': True
}

# Ollama配置
OLLAMA_CONFIG = {
    'API_URL': 'http://localhost:11434/api/generate',
    'DEFAULT_MODEL': 'deepseek-r1:1.5b'
}

# 语音识别配置
SPEECH_CONFIG = {
    'LANGUAGE': 'zh-CN',
    'ENERGY_THRESHOLD': 1000,
    'PAUSE_THRESHOLD': 0.3,
    'PHRASE_THRESHOLD': 0.3,
    'NON_SPEAKING_DURATION': 0.3,
    'SPEECH_TIMEOUT': 1.5
}

# 对话管理配置
DIALOGUE_CONFIG = {
    'MAX_DIALOGUES': 3
}

# 目录配置
DIRS = {
    'STATIC': 'static',
    'TEMPLATES': 'templates',
    'LOGS': 'logs'
}

# 确保目录存在
for dir_path in DIRS.values():
    os.makedirs(dir_path, exist_ok=True) 