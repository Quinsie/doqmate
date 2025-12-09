import uuid
import psycopg2
from flask import request
from flask_restx import Resource, Namespace, fields
from werkzeug.security import generate_password_hash
from database import get_db_connection
from DTOs import signup_list_response, simple_response, make_response_model, signup_dto

ns_signup = Namespace('signup', description='가입 신청 관리', path='/api/signup')
check_username_parser = ns_signup.parser()
check_username_parser.add_argument('username', type=str, required=True, location='args', help='중복 확인할 아이디')

signup_model = ns_signup.model('SignupInput', {
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
        data = request.json
        username = data['username'].strip().lower()
        password = data['password']
        name = data['name'].strip()

        new_id = str(uuid.uuid4())
        conn = get_db_connection(); 
        cur = conn.cursor()
        print(f"[SIGNUP] 가입 신청: {data['username']}")
        try:
            cur.execute("INSERT INTO signups (signup_id, username, password_hash, name) VALUES (%s, %s, %s, %s)",
                        (new_id, data['username'], generate_password_hash(data['password']), data['name']))
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
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

    # 2. 가입 대기 목록 조회 (GET)
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
    # 3. 아이디 중복 체크 (GET)
    # @ns_signup.doc(description="아이디 중복 확인", params={'username': '중복 확인할 아이디'})
    
    @ns_signup.doc(description="아이디 중복 확인 (대소문자 구분 없음)")
    @ns_signup.expect(check_username_parser)
    
    def get(self):
        """아이디 중복 체크 (Admins + Signups 테이블 모두 검사)"""
        args = check_username_parser.parse_args()
        username_input = args.get('username')
        if not username_input:
            return {"success": False, "error": {"message": "Username parameter required"}}, 400
        
        # [대소문자 처리]
        username = username_input.strip().lower()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # LOWER() 함수를 사용하여 DB에 대문자로 섞여 있는 데이터가 있더라도 잡아냄
            # admins 테이블: 이미 승인된 사용자 (사용 불가)
            # signups 테이블: pending 상태만 확인 (rejected는 재가입 가능)
            query = """
                SELECT 1 FROM admins WHERE LOWER(username) = %s
                UNION
                SELECT 1 FROM signups WHERE LOWER(username) = %s AND status = 'pending'
            """
            cur.execute(query, (username, username))
            
            is_taken = cur.fetchone() is not None

            return {
                "success": True,
                "data": {
                    "username": username,
                    "is_available": not is_taken,
                    "message": "이미 사용 중인 아이디입니다." if is_taken else "사용 가능한 아이디입니다."
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
    approve_parser = ns_signup.parser()
    approve_parser.add_argument('X-Admin-ID', location='headers')

    @ns_signup.doc(description="POST /api/signup/{signup_id}/approve : 승인", security='apiKey')
    @ns_signup.expect(approve_parser)
    @ns_signup.response(200, '승인 성공', simple_response)
    def post(self, signup_id):
        """가입 신청 승인"""
        print(f"[SIGNUP] 가입 승인: {signup_id}")
        # 헤더에서 승인 처리자 ID 가져오기 (없으면 NULL 처리됨)
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
        """가입 신청 반려"""
        print(f"[SIGNUP] 가입 반려: {signup_id}")
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE signups SET status='rejected', processed_at=NOW() WHERE signup_id=%s", (str(signup_id),))
            conn.commit()
            return {"success": True, "data": {"message": "Rejected"}}, 200
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()