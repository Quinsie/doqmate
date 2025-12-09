import psycopg2
from flask_restx import Resource, Namespace
from database import get_db_connection
from DTOs import admin_list_response, simple_response, make_response_model, admin_dto
from routes_auth import to_kst_string

ns_admin = Namespace('admin', description='관리자 관리', path='/api/admin')

@ns_admin.route('')
class AdminList(Resource):
    @ns_admin.doc(description='GET /api/admin : 목록', security='apiKey')
    @ns_admin.response(200, '목록', admin_list_response)
    def get(self):
        """관리자 목록"""
        print("[ADMIN] 사용자 목록 조회")
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT admin_id, username, name, created_at, last_login_at FROM admins")
            rows = cur.fetchall()
            
            admins = [{
                "admin_id": str(r[0]),
                "username": r[1],
                "name": r[2],
                "created_at": to_kst_string(r[3]),
                "last_login_at": to_kst_string(r[4])
            } for r in rows]
            
            return {"success": True, "data": {"admins": admins}}, 200
        finally:
            cur.close(); conn.close()

@ns_admin.route('/<uuid:admin_id>')
class AdminDetail(Resource):
    @ns_admin.doc(description='GET /api/admin/{admin_id} : 상세', security='apiKey')
    @ns_admin.response(200, '상세', make_response_model('AdminDetail', admin_dto))
    def get(self, admin_id):
        # 관리자 상세
        conn = get_db_connection()
        cur = conn.cursor()

        print(f"[ADMIN] 관리자 상세 조회: {admin_id}")
        try:
            cur.execute("""
                SELECT admin_id, username, name, created_at, last_login_at 
                FROM admins 
                WHERE admin_id=%s
            """, (str(admin_id),))
            r = cur.fetchone()
            if not r:
                return {"success": False, "error": {"message": "Not found"}}, 404
            
            return {
                "success": True,
                "data": {
                    "admin_id": str(r[0]),
                    "username": r[1],
                    "name": r[2],
                    "created_at": to_kst_string(r[3]),
                    "last_login_at": to_kst_string(r[4])
                }
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
            # 1. 삭제하려는 관리자가 실제로 존재하는지 확인
            cur.execute("SELECT username FROM admins WHERE admin_id = %s", (str(admin_id),))
            row = cur.fetchone()
            
            if not row:
                return {"success": False, "error": {"message": "Admin not found"}}, 404
            
            target_username = str(row[0])

            # 2. 의존성 해결 (이 관리자가 만든 챗봇이나 처리한 내역에서 ID 제거)
            # -> 삭제가 막히지 않도록, 작성자를 NULL로 변경
            cur.execute("UPDATE chatbots SET created_by = NULL WHERE created_by = %s", (str(admin_id),))
            cur.execute("UPDATE signups SET processed_by = NULL WHERE processed_by = %s", (str(admin_id),))

            # 3. 관리자 테이블에서 삭제
            cur.execute("DELETE FROM admins WHERE admin_id = %s", (str(admin_id),))

            # 4. [핵심] 가입 신청 내역(signups)에서도 삭제 
            # -> 이걸 해야 아이디 중복 체크에서 '사용 가능'으로 뜸
            cur.execute("DELETE FROM signups WHERE username = %s", (target_username,))

            conn.commit() # 변동사항 확정
            
            print(f"[ADMIN] 관리자 추방 완료: {admin_id}")
            return {"success": True, "data": {"message": "Admin deleted successfully"}}, 200
            
        except psycopg2.IntegrityError:
            # (중요) 만약 이 관리자가 만든 챗봇이나 처리한 가입 내역이 남아있으면 DB가 삭제를 막습니다.
            conn.rollback()
            return {
                "success": False, 
                "error": {"message": "이 관리자가 생성한 챗봇이나 기록이 남아있어 삭제할 수 없습니다. 관련 데이터를 먼저 정리해주세요."}
            }, 409
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()