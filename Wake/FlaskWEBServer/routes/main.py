from flask import Blueprint, render_template, send_from_directory, url_for, request
import os
from utils.logger import logger
from config.settings import DIRS

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    logger.info(f"收到主页访问请求 - IP: {request.remote_addr}")
    logger.info(f"User-Agent: {request.headers.get('User-Agent')}")
    return render_template('index.html')

@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    logger.info(f"请求静态文件: {filename}")
    response = send_from_directory(DIRS['STATIC'], filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@main_bp.route('/debug')
def debug():
    static_url = url_for('main.serve_static', filename='style.css')
    template_path = os.path.join(DIRS['TEMPLATES'], 'index.html')
    static_css_path = os.path.join(DIRS['STATIC'], 'style.css')
    static_js_path = os.path.join(DIRS['STATIC'], 'script.js')
    
    return {
        'static_folder': DIRS['STATIC'],
        'static_url': static_url,
        'static_folder_path': os.path.abspath(DIRS['STATIC']),
        'template_folder_path': os.path.abspath(DIRS['TEMPLATES']),
        'exists': {
            'style.css': os.path.exists(static_css_path),
            'script.js': os.path.exists(static_js_path),
            'index.html': os.path.exists(template_path)
        },
        'file_permissions': {
            'style.css': oct(os.stat(static_css_path).st_mode)[-3:] if os.path.exists(static_css_path) else None,
            'script.js': oct(os.stat(static_js_path).st_mode)[-3:] if os.path.exists(static_js_path) else None,
            'index.html': oct(os.stat(template_path).st_mode)[-3:] if os.path.exists(template_path) else None
        }
    } 