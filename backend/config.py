import os

# 현재 파일(config.py)의 위치: .../doqmate/backend/config.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 프로젝트 루트: .../doqmate
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# 파일 업로드 저장소 설정
#UPLOAD_FOLDER = '../data/PDF'
#if not os.path.exists(UPLOAD_FOLDER):
#    os.makedirs(UPLOAD_FOLDER)

class Config:
    # --- 1. 데이터베이스 접속 설정 ---
    # (설치했던 PostgreSQL 비밀번호)
    DB_CONFIG = {
        'dbname': 'chatbot_db',
        'user': 'chatbot_admin',
        'password': '1324', 
        'host': 'localhost',
        'port': '5432'
    }
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask 설정
    # 1. DB 저장용 상대 경로 (예: data/PDF)
    UPLOAD_RELATIVE_PATH = os.path.join('data', 'PDF')

    # 2. 파일 실제 저장용 절대 경로 (OS 인식용)
    # 예: /home/jiho/doqmate/data/PDF
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, UPLOAD_RELATIVE_PATH)
    # JWT 암호화에 사용할 비밀키 
    # 실제 서비스에선 환경변수(os.environ.get)로 빼는 것이 좋다는데 뭔소리일까...? 
    # 일단 해봐 ㅎㅎ
    SECRET_KEY = 'this-is-very-secret-key' 

    # ★ 업로드 용량 제한 해제 (또는 500MB 등으로 설정)
    # 16 * 1024 * 1024 = 16MB (Flask 기본값은 제한 없음이지만 명시하는 게 좋음)
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB