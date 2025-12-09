import jwt  # JWT 라이브러리 for the token
import datetime # 유효기간 설정을 위한 시간 라이브러리
from datetime import timezone, timedelta
import psycopg2
import random  
import string
from flask import request, current_app  # ★ app 대신 current_app 필수
from flask_restx import Resource, Namespace, fields
from werkzeug.security import generate_password_hash, check_password_hash

# 분리된 모듈들 import
from database import get_db_connection
from DTOs import login_response, admin_dto, make_response_model, simple_response
from DTOs import (
    login_response, admin_dto, make_response_model, simple_response, 
    reset_pw_response 
)
KST = timezone(timedelta(hours=9))

def to_kst_string(dt):
    """UTC datetime을 KST 문자열로 변환"""
    if dt is None:
        return None
    # naive datetime이면 UTC로 간주
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    kst_dt = dt.astimezone(KST)
    return kst_dt.strftime('%Y-%m-%d %H:%M:%S')

def mask_username(username):
    """아이디 마스킹 처리 (예: kimdoq123 -> kim***123)"""
    if not username: return ""
    if len(username) <= 3:
        return username[0] + "*" * (len(username) - 1)
    head = username[:3]
    tail = username[6:] if len(username) > 6 else "" 
    return f"{head}***{tail}"

def generate_temp_password(length=8):
    """임시 비밀번호 생성 (영문+숫자)"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


# ----------------------------------------------------------------------
# Namespace 정의
# ----------------------------------------------------------------------
ns_auth = Namespace('auth', description='인증 (로그인/내 정보)', path='/api/auth')

# 입력 모델 정의
login_input = ns_auth.model('LoginInput', {
    'username': fields.String(required=True, example='test_admin'),
    'password': fields.String(required=True, example='1234')
})

find_id_input = ns_auth.model('FindIdInput', {
    'name': fields.String(required=True, description='가입한 이름', example='김도큐')
})

reset_pw_input = ns_auth.model('ResetPwInput', {
    'username': fields.String(required=True, description='아이디', example='kimdoq123'),
    'name': fields.String(required=True, description='이름', example='김도큐')
})

pw_update_input = ns_auth.model('PwUpdateInput', {
    'current_password': fields.String(required=True, description='현재 비밀번호'),
    'new_password': fields.String(required=True, description='새 비밀번호')
})
# ----------------------------------------------------------------------
# Resource 클래스들
# ----------------------------------------------------------------------

@ns_auth.route('/login')
class Login(Resource):
    @ns_auth.doc(description='POST /api/auth/login : DB에서 계정 확인 후 로그인')
    @ns_auth.expect(login_input)
    @ns_auth.response(200, '로그인 성공', login_response)
    def post(self):
        """username/password 검증 (DB 연동)"""
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 1. DB에서 username으로 관리자 정보 조회
            # (비밀번호 해시값도 같이 가져옴)
            cur.execute("SELECT admin_id, password_hash, name, created_at FROM admins WHERE username = %s", (username,))
            admin = cur.fetchone()
            
            # 2. 계정이 없으면 404 에러 (기존 로직 복원)
            if not admin:
                return {
                    "success": False,
                    "error": {"code": 404, "message": "존재하지 않는 사용자입니다."}
                }, 404
            
            # 3. 비밀번호가 틀리면 401 에러 (기존 로직 복원)
            # admin[1]은 DB에 저장된 암호화된 비밀번호
            if not check_password_hash(admin[1], password):
                return {
                    "success": False,
                    "error": {"code": 401, "message": "비밀번호가 일치하지 않습니다."}
                }, 401

            # =========================================================
            # 로그인 성공 시 last_login_at DB 업데이트
            # =========================================================
            admin_id_str = str(admin[0])
            cur.execute("UPDATE admins SET last_login_at = NOW() WHERE admin_id = %s", (admin_id_str,))
            conn.commit() # DB에 반영하려면 commit 필수!

            # 4. 토큰 생성
            payload = {
                'admin_id': admin_id_str,
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }
            token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            print(f"[AUTH] 로그인 성공: {username}")
            
            # =========================================================
            # 응답 데이터에 last_login_at 포함
            # =========================================================
            return {
                "success": True,
                "data": {
                    "token": token,
                    "admin": {
                        "admin_id": admin_id_str,
                        "username": username,
                        "name": admin[2],
                        "created_at": to_kst_string(admin[3]),
                        # 현재 시간을 KST로 반환
                        "last_login_at": datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
            }, 200
        except Exception as e:
            conn.rollback() # 에러나면 롤백
            print(f"[Error] {e}")
            return {"success": False, "error": {"message": str(e)}}, 500
        
        finally:
            cur.close()
            conn.close()

@ns_auth.route('/me')
class Me(Resource):
    
    @ns_auth.doc(description="현재 로그인된 관리자 정보 조회", security='Bearer Auth')
    @ns_auth.response(200, '내 정보 조회 성공', make_response_model('Me', admin_dto))
    def get(self):
        """내 정보 조회 (JWT 토큰 기반)"""
        
        # 1. 헤더에서 토큰 가져오기
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {
                "success": False, 
                "error": {"code": "UNAUTHORIZED", "message": "로그인 토큰(Header)이 필요합니다."}
            }, 401

        admin_id = None
        try:
            # 2. 토큰 파싱 및 디코딩 ("Bearer <token>")
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            admin_id = payload.get('admin_id')
            
            if not admin_id:
                raise Exception("토큰에 admin_id 정보가 없습니다.")
                
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": {"code": "TOKEN_EXPIRED", "message": "토큰이 만료되었습니다."}}, 401
        except jwt.InvalidTokenError:
            return {"success": False, "error": {"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."}}, 401
        except Exception as e:
            return {"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}, 401

        # 3. 토큰에서 얻은 admin_id로 DB 조회
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT admin_id, username, name, created_at, last_login_at 
                FROM admins 
                WHERE admin_id = %s
            """, (admin_id,))
            admin = cur.fetchone()
            
            if not admin:
                return {"success": False, "error": {"code": 404, "message": "User not found"}}, 404

            return {
                "success": True,
                "data": {
                    "admin_id": str(admin[0]),
                    "username": admin[1],
                    "name": admin[2],
                    "created_at": to_kst_string(admin[3]),
                    "last_login_at": to_kst_string(admin[4])
                }
            }, 200
        except Exception as e:
            return {"success": False, "error": {"code": 500, "message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

@ns_auth.route('/me/password')
class ChangePassword(Resource):
    @ns_auth.doc(description="로그인된 사용자의 비밀번호 변경", security='Bearer Auth')
    @ns_auth.expect(pw_update_input) # admin_id 없는 모델 사용
    @ns_auth.response(200, '비밀번호 변경 성공', simple_response)
    def patch(self):
        """비밀번호 변경 (JWT 토큰 필수)"""
        
        # 1. 헤더에서 토큰 꺼내서 admin_id 찾기 (보안)
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {"success": False, "error": {"code": "UNAUTHORIZED", "message": "로그인 토큰이 필요합니다."}}, 401

        admin_id = None
        try:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            admin_id = payload.get('admin_id')
            
            if not admin_id:
                raise Exception("토큰 정보 오류")
        except Exception as e:
            return {"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}, 401

        # 2. 바디에서 비밀번호 정보 가져오기
        data = request.json
        req_admin_id = data.get('admin_id')
        current_pw = data.get('current_password')
        new_pw = data.get('new_password')

        if req_admin_id != admin_id:
            return {"success": False, "error": {"code": "FORBIDDEN", "message": "본인의 계정만 수정할 수 있습니다."}}, 403

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 3. 현재 비밀번호 검증
            cur.execute("SELECT password_hash FROM admins WHERE admin_id = %s", (admin_id,))
            row = cur.fetchone()
            
            if not row:
                return {"success": False, "error": {"message": "User not found"}}, 404

            if not check_password_hash(row[0], current_pw):
                return {"success": False, "error": {"message": "현재 비밀번호가 일치하지 않습니다."}}, 401

            # 4. 새 비밀번호 암호화 및 업데이트
            new_hash = generate_password_hash(new_pw)
            cur.execute("UPDATE admins SET password_hash = %s WHERE admin_id = %s", (new_hash, admin_id))
            conn.commit()

            return {"success": True, "data": {"message": "Password updated successfully"}}, 200

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

# ----------------------------------------------------------------------
# 아이디 찾기 (수정 버전)
# ----------------------------------------------------------------------
@ns_auth.route('/find-username')
class FindUsername(Resource):
    @ns_auth.doc(description="이름으로 아이디 찾기 (마스킹 처리, Admins + Signups 전체 검색)")
    @ns_auth.expect(find_id_input)
    def post(self):
        """아이디 찾기 (이름 일치 시 마스킹된 아이디 반환)"""
        data = request.json
        name = data.get('name')
        
        print(f"[AUTH] 아이디 찾기 요청: 이름={name}") # 디버깅 로그

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            candidates = []

            # 1. Admins 테이블 검색 (정식 관리자)
            cur.execute("SELECT username FROM admins WHERE name = %s", (name,))
            admin_rows = cur.fetchall()
            for row in admin_rows:
                candidates.append({
                    "username_masked": mask_username(row[0]),
                    "status": "active" # 구분하기 쉽게 상태 추가 (선택사항)
                })

            # 2. Signups 테이블 검색 (가입 대기자)
            cur.execute("SELECT username FROM signups WHERE name = %s", (name,))
            signup_rows = cur.fetchall()
            for row in signup_rows:
                candidates.append({
                    "username_masked": mask_username(row[0]),
                    "status": "pending" 
                })
            
            print(f"[AUTH] 검색 결과: {len(candidates)}건 발견") # 로그 확인용

            return {
                "success": True, 
                "data": {
                    "candidates": candidates
                }
            }, 200

        except Exception as e:
            print(f"[AUTH Error] {e}")
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

# ----------------------------------------------------------------------
# 비밀번호 재설정
# ----------------------------------------------------------------------
@ns_auth.route('/reset-password')
class ResetPassword(Resource):
    @ns_auth.doc(description="아이디+이름 일치 시 임시 비밀번호 발급 및 DB 업데이트")
    @ns_auth.expect(reset_pw_input)
    def post(self):
        """비밀번호 재설정 (임시 비밀번호 발급)"""
        data = request.json
        username = data.get('username')
        name = data.get('name')
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. 사용자 확인
            cur.execute("SELECT admin_id FROM admins WHERE username = %s AND name = %s", (username, name))
            user = cur.fetchone()
            
            if not user:
                return {"success": False, "error": {"message": "일치하는 사용자 정보를 찾을 수 없습니다."}}, 404
            
            admin_id = user[0]
            
            # 2. 임시 비밀번호 생성 및 해싱
            temp_password = generate_temp_password(8) # 8자리 랜덤 문자열
            hashed_pw = generate_password_hash(temp_password)
            
            # 3. DB 업데이트
            cur.execute("UPDATE admins SET password_hash = %s WHERE admin_id = %s", (hashed_pw, str(admin_id)))
            conn.commit()
            
            print(f"[AUTH] 임시 비밀번호 발급 완료: {username} -> {temp_password}")
            
            # 4. 응답 (화면에 보여주기 위해 평문 임시 비밀번호 전송)
            return {
                "success": True, 
                "data": {
                    "temp_password": temp_password
                }
            }, 200
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()