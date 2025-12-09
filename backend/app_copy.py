import os
import uuid
import psycopg2
import jwt  # JWT 라이브러리 for the token 
import datetime # 유효기간 설정을 위한 시간 라이브러리
from flask import Flask, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields, Namespace
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# --- 1. 데이터베이스 접속 설정 ---
# (설치했던 PostgreSQL 비밀번호)
DB_CONFIG = {
    'dbname': 'chatbot_db',
    'user': 'chatbot_admin',
    'password': '1324', 
    'host': 'localhost',
    'port': '5432'
}

# 파일 업로드 저장소 설정
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    """DB 접속 객체를 반환하는 함수"""
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# --- Flask 앱 및 Api 객체 초기화 ---
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# JWT 암호화에 사용할 비밀키 
# 실제 서비스에선 환경변수(os.environ.get)로 빼는 것이 좋다는데 뭔소리일까...? 
# 나중에 공부 ㄱㄱ
app.config['SECRET_KEY'] = 'this-is-very-secret-key'

api = Api(app, version='1.0', title='Chatbot API',
    description='PostgreSQL & File Upload 연동 완료 & JWT Token 적용 완료'
)
# ======================================================================
#  [DTO / Models] 데이터 모델 정의 (Swagger 표시용)
# ======================================================================

# 1. 기본 객체 DTO
admin_dto = api.model('Admin', {
    'admin_id': fields.String(description='관리자 UUID'),
    'username': fields.String(description='아이디'),
    'name': fields.String(description='이름'),
    'created_at': fields.String(description='생성일')
})

chatbot_dto = api.model('Chatbot', {
    'chatbot_id': fields.String(description='챗봇 UUID'),
    'name': fields.String(description='챗봇 이름'),
    'description': fields.String(description='설명'),
    'is_public': fields.Boolean(description='공개 여부')
})

document_dto = api.model('Document', {
    'document_id': fields.String(description='문서 UUID'),
    'display_name': fields.String(description='표시 이름'),
    'original_filename': fields.String(description='원본 파일명'),
    'status': fields.String(description='상태 (pending/indexed)'),
    'uploaded_at': fields.String(description='업로드 시간')
})

signup_dto = api.model('Signup', {
    'signup_id': fields.String,
    'username': fields.String,
    'name': fields.String,
    'status': fields.String,
    'created_at': fields.String
})

# 2. 응답 껍데기 (Response Wrapper) DTO
# -> { success: true, data: {...}, error: null } 구조를 표현

def make_response_model(name, data_model):
    """성공 응답 모델을 동적으로 생성하는 헬퍼"""
    return api.model(f'{name}Response', {
        'success': fields.Boolean(default=True, description='성공 여부'),
        'data': fields.Nested(data_model, description='실제 데이터'),
        'error': fields.String(default=None, description='에러 메시지 (실패 시)')
    })

# 각 API별 응답 모델 생성
# (1) 로그인 응답: 토큰 + 관리자 정보
login_data_model = api.model('LoginData', {
    'token': fields.String(description='JWT 인증 토큰'),
    'admin': fields.Nested(admin_dto)
})
login_response = make_response_model('Login', login_data_model)

# (2) 목록 조회 응답들
admin_list_response = make_response_model('AdminList', api.model('AdminsData', {'admins': fields.List(fields.Nested(admin_dto))}))
chatbot_list_response = make_response_model('ChatbotList', api.model('ChatbotsData', {'chatbots': fields.List(fields.Nested(chatbot_dto))}))
document_list_response = make_response_model('DocumentList', api.model('DocsData', {'documents': fields.List(fields.Nested(document_dto))}))
signup_list_response = make_response_model('SignupList', api.model('SignupsData', {'signups': fields.List(fields.Nested(signup_dto))}))

# (3) 단순 메시지 응답
message_data = api.model('MessageData', {'message': fields.String})
simple_response = make_response_model('Simple', message_data)

# 본격적으로 시작
# ----------------------------------------------------------------------
# 1. 'auth' Namespace: 인증 관련 (로그인, 내 정보) - [DB 연동 완료]
# ----------------------------------------------------------------------
ns_auth = Namespace('auth', description='인증 (로그인/내 정보)')
api.add_namespace(ns_auth, path='/api/auth')

login_input = api.model('LoginInput', {
    'username': fields.String(required=True, example='test_admin'),
    'password': fields.String(required=True, example='1234')
})

'''login_model = api.model('LoginInput', {
    'username': fields.String(required=True, description='관리자 아이디'),
    'password': fields.String(required=True, description='관리자 비밀번호')
})

password_change_model = api.model('PasswordChangeInput', {
    'current_password': fields.String(required=True, description='현재 비밀번호'),
    'new_password': fields.String(required=True, description='새 비밀번호'),
    'admin_id': fields.String(required=True, description='변경할 관리자 UUID') 
})'''

@ns_auth.route('/login')
class Login(Resource):
    @ns_auth.doc(description='POST /api/auth/login : DB에서 계정 확인 후 로그인')
    @ns_auth.expect(login_input)
    @ns_auth.response(200, '로그인 성공', login_response) # <-- Swagger에 응답 모델 등록!
    
    def post(self):
        """username/password 검증 (DB 연동)"""
        data = api.payload
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 1. DB에서 username으로 관리자 정보 조회
            # (비밀번호 해시값도 같이 가져옴)
            cur.execute("SELECT admin_id, password_hash, name, created_at FROM admins WHERE username = %s", (username,))
            admin = cur.fetchone() # 결과 한 줄 가져오기
            
            # 2. 계정이 없거나 비밀번호가 틀리면 실패
            if not admin:
                return {
                    "success": False,
                    "error": {"code": 404, "message": "존재하지 않는 사용자입니다."}
                    }, 404
            
            # admin[1]은 DB에 저장된 '암호화된 비밀번호'
            if not check_password_hash(admin[1], password):
                return {
                    "success": False,
                    "error": {"code": 401, "message": "비밀번호가 일치하지 않습니다."}
                    }, 401

            # 토큰 안에 담을 정보 (Payload)
            payload = {
                'admin_id': str(admin[0]),       # 누구인지 식별값
                'username': username,            # 이름
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) # 유효기간: 24시간
            }
            
            # 암호화 (Encoding)
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            # 3. 로그인 성공
            print(f"[AUTH] 로그인 성공 및 토큰 발급: {username}")
            
            # DTO 구조와 일치하는 데이터 반환
            return {
                "success": True,
                "data": {
                    "token": token, 
                    "admin": {
                        "admin_id": str(admin[0]),
                        "username": username,
                        "name": admin[2],
                        "created_at": str(admin[3])
                    }
                }
            }, 200
            
        except Exception as e: # 1. 만약 위(try)에서 무슨 에러라도 발생하면 여기로 와라! (e라는 이름으로 에러를 잡음)
            print(f"[Error] {e}") # 2. 서버 관리자(나)가 볼 수 있게 검은 터미널에 에러 내용을 찍어.
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

@ns_auth.route('/me')
class Me(Resource):
    auth_parser = api.parser()
    auth_parser.add_argument('X-Test-Admin-ID', location='headers', required=True, help='테스트용 Admin UUID')

    @ns_auth.expect(auth_parser)
    @ns_auth.response(200, '내 정보 조회 성공', make_response_model('Me', admin_dto))

    def get(self):
        """현재 로그인 관리자 정보 조회 (DB 연동)"""
        # 주의: 원래는 토큰에서 ID를 꺼내야 하지만, 
        # 아직 JWT 구현 전이므로 헤더에서 ID를 직접 받아서 테스트합니다.
        admin_id = request.headers.get('X-Test-Admin-ID')

        if not admin_id:
            return {"success": False, "error": {"message": "Header X-Test-Admin-ID required"}}, 400
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT admin_id, username, name, created_at FROM admins WHERE admin_id = %s", (admin_id,))
            admin = cur.fetchone()
            
            if not admin:
                return {"success": False, "error": {"code": 404, "message": "사용자를 찾을 수 없습니다."}}, 404

            return {
                "success": True,
                "data": {
                    "admin_id": str(admin[0]),
                    "username": admin[1],
                    "name": admin[2],
                    "created_at": str(admin[3])
                }
            }, 200
        except Exception as e:
            return {"success": False, "error": {"code": 500, "message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

    pw_change_input = api.model('PwChangeInput', {
        'admin_id': fields.String(required=True),
        'current_password': fields.String(required=True),
        'new_password': fields.String(required=True)
    })

    @ns_auth.expect(pw_change_input)
    @ns_auth.response(200, '비밀번호 변경 성공', simple_response)
    
    def patch(self):
        """비밀번호 변경 (DB 연동)"""
        data = api.payload
        admin_id = data.get('admin_id') # 테스트를 위해 ID를 직접 받음
        current_pw = data.get('current_password')
        new_pw = data.get('new_password')
        
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 1. 현재 비밀번호 확인
            cur.execute("SELECT password_hash FROM admins WHERE admin_id = %s", (admin_id,))
            row = cur.fetchone()
            
            if not row:
                return {"success": False, "error": {"message": "User not found"}}, 404

            if not check_password_hash(row[0], current_pw):
                return {"success": False, "error": {"message": "현재 비밀번호가 틀렸습니다."}}, 401

            # 2. 새 비밀번호 암호화 및 DB 업데이트
            new_hash = generate_password_hash(new_pw)
            cur.execute("UPDATE admins SET password_hash = %s WHERE admin_id = %s", (new_hash, admin_id))
            conn.commit()

            print(f"[AUTH] 비밀번호 변경 완료: {admin_id}")
            return {"success": True, "data": {"message": "Password updated successfully"}}, 200

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()
# ----------------------------------------------------------------------
# 2. 'admin' Namespace: 관리자 관리
# ----------------------------------------------------------------------
ns_admin = Namespace('admin', description='관리자 계정 관리 (슈퍼어드민용)')
api.add_namespace(ns_admin, path='/api/admin')

@ns_admin.route('')
class AdminList(Resource):
    @ns_admin.doc(description='GET /api/admin : 목록', security='apiKey')
    @ns_admin.response(200, '목록 조회 성공', admin_list_response)
    def get(self):
        """관리자 목록"""
        print("[ADMIN] 사용자 목록 조회")
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT admin_id, username, name, created_at FROM admins")
            rows = cur.fetchall()
            admins = [{"admin_id": str(r[0]), "username": r[1], "name": r[2], "created_at": str(r[3])} for r in rows]
            return {"admins": admins}, 200
        finally:
            cur.close()
            conn.close()

@ns_admin.route('/<uuid:admin_id>')
class AdminDetail(Resource):
    @ns_admin.doc(description='GET /api/admin/{admin_id} : 상세', security='apiKey')
    @ns_admin.response(200, '상세 조회 성공', make_response_model('AdminDetail', admin_dto))
    def get(self, admin_id):
        """관리자 상세"""
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[ADMIN] 관리자 상세 조회: {admin_id}")
        try:
            cur.execute("SELECT admin_id, username, name, created_at FROM admins WHERE admin_id = %s", (str(admin_id),))
            r = cur.fetchone()
            if not r:
                return {"success": False, "error": {"message": "Not found"}}, 404
            
            return {
                "success": True, 
                "data": {"admin_id": str(r[0]), "username": r[1], "name": r[2], "created_at": str(r[3])}
            }, 200
        finally:
            cur.close()
            conn.close()
    @ns_admin.doc(description='DELETE /api/admin/{admin_id} : 추방', security='apiKey')
    @ns_admin.response(200, '삭제 성공', simple_response)
    def delete(self, admin_id):
        """관리자 추방"""
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[ADMIN] 관리자 삭제(추방): {admin_id}")
        try:
            cur.execute("DELETE FROM admins WHERE admin_id = %s", (str(admin_id),))
            conn.commit()
            return {"success": True, "data": {"message": "Deleted"}}, 200
        finally:
            cur.close()
            conn.close()
# ----------------------------------------------------------------------
# 3. 'chatbots_public' Namespace: 공개 챗봇 API
# ----------------------------------------------------------------------
ns_chatbots_public = Namespace('chatbots', description='공개 챗봇 조회 API')
api.add_namespace(ns_chatbots_public, path='/api/chatbots')

@ns_chatbots_public.route('')
class PublicChatbotList(Resource):
    @ns_chatbots_public.doc(description='GET /api/chatbots : 공개용 목록')
    @ns_chatbots_public.response(200, '성공', chatbot_list_response)
    def get(self):
        """공개용 챗봇 목록"""
        conn = get_db_connection()
        cur = conn.cursor()
        print("[CHATBOT] 공개 챗봇 목록 조회")
        try:
            cur.execute("SELECT chatbot_id, name, description FROM chatbots WHERE is_public = TRUE")
            rows = cur.fetchall()
            bots = [{"chatbot_id": str(r[0]), "name": r[1], "description": r[2], "is_public": r[3]} for r in rows]
            return {"success": True, "data": {"chatbots": bots}}, 200
        finally:
            cur.close()
            conn.close()
# ----------------------------------------------------------------------
# 4. 'chatbots_admin' Namespace: 챗봇 설정 API
# ----------------------------------------------------------------------
ns_chatbots_admin = Namespace('set-chatbots', description='챗봇 생성/설정 (관리자용)')
api.add_namespace(ns_chatbots_admin, path='/api/set/chatbots')

chatbot_input = api.model('ChatbotInput', {
    'name': fields.String(required=True, description='챗봇 이름'),
    'description': fields.String(description='챗봇 설명'),
    'is_public': fields.Boolean(default=True, description='공개 여부'),
    'admin_id': fields.String(required=True, description="생성자 ID (테스트용)")
})

@ns_chatbots_admin.route('')
class AdminChatbotList(Resource):
    @ns_chatbots_admin.doc(description='GET /api/set/chatbots : 관리자용 전체 목록', security='apiKey')
    @ns_chatbots_admin.response(200, '성공', chatbot_list_response)
    def get(self):
        """관리자용 전체 챗봇 목록"""
        conn = get_db_connection()
        cur = conn.cursor()
        print("[CHATBOT] 관리자용 전체 챗봇 목록 조회")
        try:
            cur.execute("SELECT chatbot_id, name, is_public, description FROM chatbots")
            rows = cur.fetchall()
            return {"success": True, "data": {"chatbots": bots}}, 200
        finally:
            cur.close()
            conn.close()

    @ns_chatbots_admin.doc(description='POST /api/set/chatbots : 생성', security='apiKey')
    @ns_chatbots_admin.expect(chatbot_input)
    @ns_chatbots_admin.response(201, '생성 성공', simple_response)
    def post(self):
        """챗봇 생성"""
        data = api.payload
        new_id = str(uuid.uuid4())  
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[CHATBOT] 신규 챗봇 생성: {data.get('name')}")
        try:
            cur.execute("""
                INSERT INTO chatbots (chatbot_id, name, description, is_public, created_by)
                VALUES (%s, %s, %s, %s, %s) RETURNING chatbot_id
            """, (new_id, data['name'], data.get('description'), data.get('is_public', True), data['admin_id']))
            conn.commit()
            return {"success": True, "data": {"chatbot_id": new_id}}, 201
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

@ns_chatbots_admin.route('/<uuid:chatbot_id>')
class AdminChatbotDetail(Resource):
    @ns_chatbots_admin.doc(description='GET /api/set/chatbots/{chatbot_id} : 설정 페이지 기본 정보', security='apiKey')
    @ns_chatbots_admin.response(200, '성공', make_response_model('ChatbotDetail', chatbot_dto))
    def get(self, chatbot_id):
        """챗봇 설정 상세 조회"""
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[CHATBOT] 챗봇 상세 조회: {chatbot_id}")
        try:
            cur.execute("SELECT chatbot_id, name, description, is_public FROM chatbots WHERE chatbot_id = %s", (str(chatbot_id),))
            r = cur.fetchone()
            if not r: return {"success": False, "error": {"message": "Not found"}}, 404
            
            return {
                "success": True, 
                "data": {"chatbot_id": str(r[0]), "name": r[1], "description": r[2], "is_public": r[3]}
            }, 200
        finally:
            cur.close()
            conn.close()

    @ns_chatbots_admin.doc(description='PATCH /api/set/chatbots/{chatbot_id} : 이름/설명/공개여부 수정', security='apiKey')
    @ns_chatbots_admin.expect(chatbot_input) # 생성 모델 재사용
    @ns_chatbots_admin.response(200, '수정 성공', simple_response)
    def patch(self, chatbot_id):
        """챗봇 설정 수정"""
        data = api.payload
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[CHATBOT] 챗봇 수정: {chatbot_id}, 변경 내용: {data}")
        try:
            cur.execute("""
                UPDATE chatbots SET name=%s, description=%s, is_public=%s 
                WHERE chatbot_id=%s
            """, (data['name'], data.get('description'), data.get('is_public'), str(chatbot_id)))
            conn.commit()
            return {"success": True, "data": {"message": "Updated"}}, 200
        finally:
            cur.close()
            conn.close()

    @ns_chatbots_admin.doc(description='DELETE /api/set/chatbots/{chatbot_id} : 삭제', security='apiKey')
    @ns_chatbots_admin.response(200, '삭제 성공', simple_response)
    def delete(self, chatbot_id):
        """챗봇 삭제"""
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[CHATBOT] 챗봇 삭제: {chatbot_id}")
        try:
            cur.execute("DELETE FROM chatbots WHERE chatbot_id=%s", (str(chatbot_id),))
            conn.commit()
            return {"success": True, "data": {"message": "Deleted"}}, 204
        finally:
            cur.close()
            conn.close()

# ----------------------------------------------------------------------
# 5. 'signup' Namespace: 가입 신청
# ----------------------------------------------------------------------
ns_signup = Namespace('signup', description='가입 신청 및 승인/반려')
api.add_namespace(ns_signup, path='/api/signup')

signup_model = api.model('SignupInput', {
    'username': fields.String(required=True),
    'password': fields.String(required=True),
    'name': fields.String(required=True)
})

@ns_signup.route('')
class SignupRequest(Resource):
    @ns_signup.doc(description="POST /api/signup : 신규 신청 insert")
    @ns_signup.expect(signup_model)
    @ns_signup.response(201, '신청 성공', simple_response)
    def post(self):
        """신규 가입 신청"""
        data = api.payload
        hashed_pw = generate_password_hash(data['password'])
        new_id = str(uuid.uuid4())
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[SIGNUP] 가입 신청: {data['username']}")
        try:
            cur.execute("INSERT INTO signups (signup_id, username, password_hash, name) VALUES (%s, %s, %s, %s)",
                        (new_id, data['username'], hashed_pw, data['name']))
            conn.commit()
            return {
                "success": True,
                "data": {
                    "message": "Signup requested successfully",
                    "signup_id": new_id
                }
            }, 201
        except psycopg2.IntegrityError:
            conn.rollback()
            return {
                "success": False,
                "error": {"code": 409, "message": "Username exists already."}
            }, 409
        finally:
            cur.close()
            conn.close()

    @ns_signup.doc(description="GET /api/signup : status='pending' 목록", security='apiKey')
    @ns_signup.response(200, '목록 조회 성공', signup_list_response)
    def get(self):
        """'pending' 상태 가입 신청 목록 조회"""
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[SIGNUP] 'pending' 상태 목록 조회")
        try:
            cur.execute("SELECT signup_id, username, name, created_at FROM signups WHERE status='pending'")
            rows = cur.fetchall()
            signups = [{"signup_id": str(r[0]), "username": r[1], "name": r[2], "created_at": str(r[3])} for r in rows]
            return {"success": True, "data": {"signups": signups}}, 200
        finally:
            cur.close()
            conn.close()

@ns_signup.route('/check-username')
class CheckUsername(Resource):
    @ns_signup.doc(params={'username': 'ID'})
    def get(self):
        """아이디 중복 체크 (Admins + Signups 테이블 모두 검사)"""
        username = request.args.get('username')
        if not username:
            return {"success": False, "error": {"message": "Username parameter required"}}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. Admins 테이블 확인
            cur.execute("SELECT 1 FROM admins WHERE username = %s", (username,))
            exists_in_admin = cur.fetchone()
            
            # 2. Signups (대기중인 신청) 테이블 확인
            cur.execute("SELECT 1 FROM signups WHERE username = %s", (username,))
            exists_in_signup = cur.fetchone()

            # 둘 중 한 곳이라도 있으면 사용 불가
            is_available = not (exists_in_admin or exists_in_signup)
            
            return {
                "success": True,
                "data": {
                    "username": username,
                    "is_available": is_available,
                    "message": "사용 가능한 아이디입니다." if is_available else "이미 사용 중인 아이디입니다."
                }
            }, 200
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

@ns_signup.route('/<uuid:signup_id>')
class SignupDetail(Resource):
    @ns_signup.doc(description="GET /api/signup/{signup_id} : 단건 조회", security='apiKey')
    @ns_signup.response(200, '상세 조회 성공', make_response_model('SignupDetail', signup_dto))
    def get(self, signup_id):
        """가입 신청 단건 조회"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                SELECT signup_id, username, name, status, created_at 
                FROM signups 
                WHERE signup_id = %s
            ''', (str(signup_id),))
            row = cur.fetchone()
            
            if not row:
                return {"success": False, "error": {"message": "Not found"}}, 404
                
            return {
                "success": True,
                "data": {
                    "signup_id": str(row[0]),
                    "username": row[1],
                    "name": row[2],
                    "status": row[3],
                    "created_at": str(row[4])
                }
            }, 200
        finally:
            cur.close()
            conn.close()
            
@ns_signup.route('/<uuid:signup_id>/approve')
class SignupApprove(Resource):
    approve_parser = api.parser()
    approve_parser.add_argument('X-Admin-ID', location='headers')

    @ns_signup.doc(description="POST /api/signup/{signup_id}/approve : 승인", security='apiKey')
    @ns_signup.expect(approve_parser)
    @ns_signup.response(200, '승인 성공', simple_response)
    def post(self, signup_id):
        """가입 신청 승인"""
        print(f"[SIGNUP] 가입 승인: {signup_id}")
        admin_id = request.headers.get('X-Admin-ID') # 누가 승인했는지 기록용 (테스트)
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. 신청 정보 가져오기
            cur.execute("SELECT username, password_hash, name FROM signups WHERE signup_id=%s AND status='pending'", (str(signup_id),))
            signup_data = cur.fetchone()
            if not signup_data:
                return {"success": False, "error": {"message": "Request not found or processed"}}, 404

            # 2. Admins 테이블로 이동 (새로운 UUID 부여)
            new_admin_id = str(uuid.uuid4())
            cur.execute("INSERT INTO admins (admin_id, username, password_hash, name) VALUES (%s, %s, %s, %s)",
                        (new_admin_id, signup_data[0], signup_data[1], signup_data[2]))
            
            # 3. Signups 상태 업데이트
            cur.execute("UPDATE signups SET status='approved', processed_at=NOW(), processed_by=%s WHERE signup_id=%s",
                        (admin_id, str(signup_id)))
            
            conn.commit() # 트랜잭션 확정
            return {"success": True, "data": {"message": "Approved", "new_admin_id": new_admin_id}}, 200
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

@ns_signup.route('/<uuid:signup_id>/reject')
class SignupReject(Resource):
    @ns_signup.doc(description="POST /api/signup/{signup_id}/reject : 반려", security='apiKey')
    @ns_signup.response(200, '반려 성공', simple_response)
    def post(self, signup_id):
        conn = get_db_connection()
        cur = conn.cursor()
        """가입 신청 반려"""
        print(f"[SIGNUP] 가입 반려: {signup_id}")
        try:
            cur.execute("UPDATE signups SET status='rejected', processed_at=NOW() WHERE signup_id=%s", (str(signup_id),))
            conn.commit()
            return {"success": True, "data": {"message": "Rejected"}}, 200
        finally:
            cur.close()
            conn.close()

# ----------------------------------------------------------------------
# 6. 'documents' Namespace: 문서 관리 (parser 사용)
# ----------------------------------------------------------------------
ns_documents = Namespace('set-documents', description='문서 업로드/관리')
api.add_namespace(ns_documents, path='/api/set/documents')

# 폼데이터(form-data)용 파일 업로드를 위한 전용 파서(Parser) 생성parser 정의
doc_upload_parser = api.parser()
doc_upload_parser.add_argument('chatbot_id', type=str, required=True, help='연결할 챗봇 ID')
doc_upload_parser.add_argument('display_name', type=str, required=True, help='문서 표시 이름')
doc_upload_parser.add_argument('file', type=FileStorage, location='files', required=True, help='업로드할 파일')

@ns_documents.route('')
class DocumentList(Resource):
    @ns_documents.doc(description="GET /api/set/documents?chatbot_id={chatbot_id} : 목록", security='apiKey', params={'chatbot_id': '챗봇 ID'})
    @ns_documents.response(200, '성공', document_list_response)
    def get(self):
        """챗봇별 문서 목록 조회"""
        chatbot_id = request.args.get('chatbot_id')
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"[DOC] 문서 목록 조회: chatbot_id={chatbot_id}")
        try:
            cur.execute("SELECT document_id, display_name, status FROM documents WHERE chatbot_id=%s", (chatbot_id,))
            rows = cur.fetchall()
            docs = [{"document_id": str(r[0]), "display_name": r[1], "original_filename": r[2], "status": r[3], "uploaded_at": str(r[4])} for r in rows]
            return {"success": True, "data": {"documents": docs}}, 200
        finally:
            cur.close()
            conn.close()

    @ns_documents.doc(description="POST /api/set/documents : 폼데이터: chatbot_id, file, display_name", security='apiKey')
    @ns_documents.expect(doc_upload_parser) # JSON이 아닌 폼데이터 parser 사용
    @ns_documents.response(201, '업로드 성공', simple_response)
    def post(self):
        """문서 업로드 및 DB 저장"""
        args = doc_parser.parse_args()
        file = args['file']
        chatbot_id = args['chatbot_id']
        display_name = args['display_name']
        
        if file:
            filename = secure_filename(file.filename)
            # 저장 경로: uploads/chatbot_id/filename
            save_dir = os.path.join(app.config['UPLOAD_FOLDER'], chatbot_id)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            file_path = os.path.join(save_dir, filename)
            file.save(file_path) # 디스크에 저장

            # DB에 저장
            new_id = str(uuid.uuid4())
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO documents (document_id, chatbot_id, display_name, original_filename, storage_path, status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                """, (new_id, chatbot_id, display_name, filename, file_path))
                conn.commit()
                return {"success": True, "data": {"message": "Uploaded", "document_id": new_id}}, 201
            except Exception as e:
                conn.rollback()
                return {"success": False, "error": {"message": str(e)}}, 500
            finally:
                cur.close()
                conn.close()
        return {"success": False, "error": {"message": "No file"}}, 400

@ns_documents.route('/<uuid:document_id>')
class DocumentDetail(Resource):
    
    # 1. 단건 조회 (GET) - DB에서 정보 가져오기
    @ns_documents.doc(description="GET /api/set/documents/{document_id} : 단건 조회", security='apiKey')
    @ns_documents.response(200, '상세 조회', make_response_model('DocDetail', document_dto))
    def get(self, document_id):
        """문서 단건 조회 (DB 연동)"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # DB에서 해당 ID의 문서 정보 조회
            cur.execute("""
                SELECT document_id, chatbot_id, display_name, original_filename, status, uploaded_at 
                FROM documents 
                WHERE document_id = %s
            """, (str(document_id),))
            
            row = cur.fetchone()
            
            if not row:
                return {"success": False, "error": {"message": "Not found"}}, 404

            # 조회된 데이터를 JSON으로 반환
            return {
                "success": True,
                "document_id": str(row[0]),
                "chatbot_id": str(row[1]),
                "display_name": row[2],
                "original_filename": row[3],
                "status": row[4],
                "uploaded_at": str(row[5])
            }, 200
            
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            cur.close()
            conn.close()

    # 2. 삭제 (DELETE) - 파일 삭제 및 DB 레코드 삭제
    @ns_documents.doc(description="DELETE /api/set/documents/{document_id} : 삭제", security='apiKey')
    @ns_documents.response(200, '삭제 성공', simple_response)
    def delete(self, document_id):
        """문서 삭제 (파일 + DB)"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. 파일 경로 먼저 조회 (실제 파일을 지워야 하니까)
            cur.execute("SELECT storage_path FROM documents WHERE document_id=%s", (str(document_id),))
            row = cur.fetchone()
            
            # 파일이 존재하면 디스크에서 삭제
            if row and row[0] and os.path.exists(row[0]):
                os.remove(row[0]) 
            
            # 2. DB에서 레코드 삭제
            cur.execute("DELETE FROM documents WHERE document_id=%s", (str(document_id),))
            conn.commit()
            
            return {"success": True, "data": {"message": "Deleted"}}, 200
            
        except Exception as e:
            conn.rollback()
            return {"error": str(e)}, 500
        finally:
            cur.close()
            conn.close()

# ----------------------------------------------------------------------
# 7. 'chats' Namespace: RAG/LLM 호출 (핵심 API)
# ----------------------------------------------------------------------
ns_chats = Namespace('chats', description='RAG/LLM 챗봇 응답 API')
api.add_namespace(ns_chats, path='/api/chats')

chat_model = api.model('ChatInput', {
    'question': fields.String(required=True),
    'chatbot_id': fields.String(required=True, description='UUID'),
    'session_id': fields.String(description='대화 세션 ID (선택 사항)')
})

@ns_chats.route('')
class ChatQuery(Resource):
    @ns_chats.doc(description="POST /api/chats : RAG 파이프라인 호출 및 query_logs에 1줄 insert")
    @ns_chats.expect(chat_model)
    def post(self):
        """챗봇 질문 및 응답 (RAG/LLM)"""
        data = api.payload
        question = data.get('question')
        chatbot_id = data.get('chatbot_id')
        print(f"[CHAT] 챗봇[{chatbot_id}] 질문: {question}")
        
        # (나중에 여기에 RAG 모델 연동)
        answer = f"AI 답변입니다: '{question}' (DB Logged)"
        
        # 로그 저장 (INSERT)
        log_id = str(uuid.uuid4())
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO query_logs (log_id, chatbot_id, question, answer, session_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (log_id, chatbot_id, question, answer, data.get('session_id')))
            conn.commit()
            return {"success": True, "data": {"answer": answer, "warning": "Log failed"}}, 200
        except Exception as e:
            conn.rollback()
            # 로그 저장 실패해도 답변은 나가야 함 (선택 사항)
            return {"answer": answer, "error": "Log save failed"}, 200 
        finally:
            cur.close()
            conn.close()

# ----------------------------------------------------------------------
# 앱 실행
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=11202, debug=True)