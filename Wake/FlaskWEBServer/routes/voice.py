from flask import Blueprint, request, jsonify, Response
import json
from utils.logger import logger
from modules.speech_recognizer import speech_recognizer
from modules.dialogue_manager import dialogue_manager

# 创建蓝图
voice_bp = Blueprint('voice', __name__)

@voice_bp.route('/start_voice', methods=['POST'])
def start_voice():
    try:
        dialogue_id = dialogue_manager.create_dialogue()
        if dialogue_id is None:
            return jsonify({'error': '已达到最大对话数限制'}), 429
        
        def recognition_callback(text):
            try:
                if isinstance(text, dict):
                    if text.get('status') == 'success' and text.get('text', '').strip():
                        logger.info(f"返回语音识别文本: {text['text']}")
                        return text
                return None
            except Exception as e:
                logger.error(f"处理语音识别结果失败: {str(e)}")
                return None
        
        if speech_recognizer.start_listening(recognition_callback):
            return jsonify({
                'status': 'started',
                'dialogue_id': dialogue_id
            })
        return jsonify({'error': '启动语音识别失败'}), 500
        
    except Exception as e:
        logger.error(f"启动语音识别服务失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@voice_bp.route('/stop_voice', methods=['POST'])
def stop_voice():
    try:
        speech_recognizer.stop()
        return jsonify({'status': 'stopped'})
    except Exception as e:
        logger.error(f"停止语音识别时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@voice_bp.route('/voice_events')
def voice_events():
    def generate():
        try:
            while speech_recognizer.is_listening:
                try:
                    event = speech_recognizer.event_queue.get(timeout=5)  # 减少超时时间
                    if event:
                        logger.info(f"发送语音事件: {event}")
                        yield f"data: {json.dumps(event)}\n\n"
                except Exception as e:
                    if speech_recognizer.is_listening:
                        # 发送保持活动信号
                        yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                    else:
                        break
        except GeneratorExit:
            logger.info("客户端关闭了语音事件流")
            speech_recognizer.stop()  # 确保停止语音识别
        except Exception as e:
            logger.error(f"处理语音事件错误: {str(e)}")
            speech_recognizer.stop()
    
    return Response(generate(), mimetype='text/event-stream') 