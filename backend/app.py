import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# 상위 디렉토리(doqmate)를 Python path에 추가하여 services 모듈 접근 가능
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request
from flask_cors import CORS
from config import Config
from extensions import api

# 라우트 모듈 불러오기
from routes_auth import ns_auth
from routes_signup import ns_signup
from routes_admin import ns_admin
from routes_chatbot import ns_chatbots_public, ns_chatbots_admin
from routes_document import ns_manuals
from routes_chat import ns_chats, ns_stats

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 로그 설정
log_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs', 'backend')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'api.log')
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Flask 앱 시작')

# 모든 요청/응답 로깅
@app.before_request
def log_request():
    app.logger.info(f'[REQUEST] {request.method} {request.path} - {request.remote_addr}')

@app.after_request
def log_response(response):
    app.logger.info(f'[RESPONSE] {request.method} {request.path} - {response.status_code}')
    return response

api.init_app(app)

# 네임스페이스 등록
api.add_namespace(ns_auth)
api.add_namespace(ns_signup)
api.add_namespace(ns_admin)
api.add_namespace(ns_chatbots_public)
api.add_namespace(ns_chatbots_admin)
api.add_namespace(ns_manuals)
api.add_namespace(ns_chats)
api.add_namespace(ns_stats)

if __name__ == '__main__':
    ssl_context = ('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', port=11201, debug=True, ssl_context=ssl_context)