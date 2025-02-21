from flask import Blueprint, request, jsonify, Response
import json
from utils.logger import logger
from modules.dialogue_manager import dialogue_manager

# 创建蓝图
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    dialogue_id = data.get('dialogue_id')
    
    logger.info(f"收到聊天请求 - IP: {request.remote_addr}")
    logger.info(f"用户消息: {user_message}")
    
    # 如果没有对话ID，创建新对话
    if not dialogue_id:
        dialogue_id = dialogue_manager.create_dialogue()
        if dialogue_id is None:
            return jsonify({'error': '已达到最大对话数限制'}), 429
    
    def generate():
        try:
            for response in dialogue_manager.send_message_to_ollama(user_message, dialogue_id):
                if response.get('error'):
                    yield f"data: {json.dumps({'error': response['error']})}\n\n"
                    break
                elif response.get('status') == 'interrupted':
                    yield f"data: {json.dumps({'status': 'interrupted'})}\n\n"
                    break
                else:
                    yield f"data: {json.dumps(response)}\n\n"
        except Exception as e:
            logger.error(f"流处理错误: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            logger.info("响应流结束")
    
    return Response(generate(), mimetype='text/event-stream')

@chat_bp.route('/stop_dialogue/<dialogue_id>', methods=['POST'])
def stop_dialogue(dialogue_id):
    dialogue = dialogue_manager.get_dialogue(dialogue_id)
    if dialogue and dialogue['controller']:
        dialogue['controller'].abort()
        dialogue_manager.complete_dialogue(dialogue_id)
        return jsonify({'status': 'stopped'})
    return jsonify({'error': '对话不存在或已结束'}), 404 