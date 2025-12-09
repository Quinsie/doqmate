import uuid
import os
import shutil
import sys
import jwt
from flask import request, current_app
from flask_restx import Resource, Namespace, fields
from database import get_db_connection
from DTOs import (
    chatbot_list_response, chatbot_response, simple_response,
    chatbot_dto, chatbot_list_item_dto
)

# documentService import (Chroma 삭제용)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from services.documentService import deleteDocument
    deleteDocumentAvailable = True
except ImportError as e:
    print(f"[WARN] deleteDocument 함수를 찾을 수 없습니다: {e}")
    deleteDocument = None
    deleteDocumentAvailable = False

# ----------------------------------------------------------------------
# Namespace 정의
# ----------------------------------------------------------------------
# 1. 공용(비로그인) 영역 (기존 유지)
ns_chatbots_public = Namespace('chatbots', description='챗봇 목록 조회 (공용)', path='/api/chatbots')

# 2. 관리자용 설정 영역 (이번 수정 대상)
ns_chatbots_admin = Namespace('set-chatbots', description='챗봇 설정 (관리자용)', path='/api/set/chatbots')

# 관리자용 입력 모델 (POST/PATCH 공용)
chatbot_input = ns_chatbots_admin.model('ChatbotInput', {
    'name': fields.String(required=True, description='챗봇 이름 (필수)'), 
    'is_public': fields.Boolean(required=True, default=True, description='공개 여부 (필수)'),
    'description': fields.String(required=False, description='챗봇 설명 (선택)'), 
    'tag': fields.String(required=False, description='챗봇 태그 (선택)')          
    # admin_id는 토큰에서 가져오거나 해야 하지만, 명세서 요청 예시에 없으므로 제외하거나 내부적으로 처리
})

# 수정용 (PATCH): 모든 값이 선택사항 (부분 수정 지원)
chatbot_patch_input = ns_chatbots_admin.model('ChatbotPatchInput', {
    'name': fields.String(required=False, description='변경할 이름'), 
    'is_public': fields.Boolean(required=False, description='변경할 공개 여부'),
    'description': fields.String(required=False, description='변경할 설명'),
    'tag': fields.String(required=False, description='변경할 태그')
})

# ======================================================================
# 1. 공용 API (기존 로직 유지하되 DTO만 맞춤)
# ======================================================================
@ns_chatbots_public.route('')
class PublicChatbotList(Resource):
    @ns_chatbots_public.doc(description='GET /api/chatbots : 공개 챗봇 목록')
    # 공용 목록에는 manual_count가 필수는 아니지만, 구조 통일을 위해 같은 DTO 사용 가능
    # 여기서는 간단히 기본 정보만 리턴하는 것으로 유지
    def get(self):
        # 로그인 여부 확인
        is_logged_in = False
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1] if " " in auth_header else auth_header
                jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                is_logged_in = True
            except Exception:
                is_logged_in = False


        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if is_logged_in:
                query = "SELECT chatbot_id, name, description, is_public, created_at, tag FROM chatbots"
            else:
                query = "SELECT chatbot_id, name, description, is_public, created_at, tag FROM chatbots WHERE is_public = TRUE"

            cur.execute(query)
            rows = cur.fetchall()
            
            bots = [{
                "chatbot_id": str(r[0]), 
                "name": r[1], 
                "description": r[2], 
                "is_public": r[3],
                "created_at": str(r[4]),
                "tag": r[5],
                "manual_count": 0 # 공용에서는 굳이 count 안 보여줘도 되면 0 처리
            } for r in rows]
            
            return {"success": True, "data": {"chatbots": bots}}, 200
        finally:
            cur.close()
            conn.close()


# ======================================================================
# 2. 관리자용 챗봇 관리 API (5-1 ~ 5-5)
# ======================================================================
@ns_chatbots_admin.route('')
class AdminChatbotCollection(Resource):
    
    # 5-1. 챗봇 목록 조회 (manual_count 포함)
    @ns_chatbots_admin.doc(description='GET /api/set/chatbots')
    @ns_chatbots_admin.response(200, '성공', chatbot_list_response)
    def get(self):
        """관리자용 전체 챗봇 목록 (문서 개수 포함)"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # LEFT JOIN으로 문서 개수(count) 함께 조회
            query = """
                SELECT c.chatbot_id, c.name, c.description, c.is_public, c.created_at, c.tag, COUNT(d.document_id)
                FROM chatbots c
                LEFT JOIN documents d ON c.chatbot_id = d.chatbot_id
                GROUP BY c.chatbot_id, c.tag  
                ORDER BY c.created_at DESC
            """
            cur.execute(query)
            rows = cur.fetchall()
            
            bots = []
            for r in rows:
                bots.append({
                    "chatbot_id": str(r[0]),
                    "name": r[1],
                    "description": r[2],
                    "is_public": r[3],
                    "created_at": str(r[4]),
                    "tag": r[5],    # DB에서 가져온 태그 값 매핑
                    "manual_count": r[5] # COUNT 결과
                })
            
            return {"success": True, "data": {"chatbots": bots}}, 200
        except Exception as e:
            return {"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

    # 5-2. 챗봇 생성
    @ns_chatbots_admin.doc(description='POST /api/set/chatbots')
    @ns_chatbots_admin.expect(chatbot_input)
    @ns_chatbots_admin.response(201, '생성 성공', chatbot_response)
    def post(self):
        """챗봇 생성"""
        
        # ---------------------------------------------------------
        # 1. 토큰 검사 및 admin_id 추출 (강제 검사)
        # ---------------------------------------------------------
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {
                "success": False, 
                "error": {"code": "UNAUTHORIZED", "message": "로그인 토큰(Header)이 필요합니다."}
            }, 401

        created_by = None
        try:
            # "Bearer <token>" 파싱
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            
            # 토큰 디코딩
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            created_by = payload.get('admin_id')
            
            if not created_by:
                raise Exception("토큰에 admin_id 정보가 없습니다.")
                
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": {"code": "TOKEN_EXPIRED", "message": "토큰이 만료되었습니다."}}, 401
        except jwt.InvalidTokenError:
            return {"success": False, "error": {"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."}}, 401
        except Exception as e:
            return {"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}, 401

        # ---------------------------------------------------------
        # 2. DB 저장 (이제 created_by는 무조건 값이 있음)
        # ---------------------------------------------------------
        data = request.json
        new_id = str(uuid.uuid4())

        name = data.get('name')
        description = data.get('description') # 값이 없으면 None (DB에는 NULL로 저장)
        tag = data.get('tag')                 # 값이 없으면 None (DB에는 NULL로 저장)
        is_public = data.get('is_public', True) # 값 없으면 기본값 True

        if not name:
             return {"success": False, "error": {"code": "MISSING_PARAM", "message": "name is required"}}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO chatbots (chatbot_id, name, description, is_public, created_by, tag, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING chatbot_id, name, description, is_public, tag, created_at
            """, (new_id, data['name'], data.get('description'), data.get('is_public', True), created_by, data.get('tag')))

            r = cur.fetchone()
            conn.commit()
            
            new_bot = {
                "chatbot_id": str(r[0]),
                "name": r[1],
                "description": r[2],
                "is_public": r[3],
                "tag": r[4],
                "created_at": str(r[5])
            }
            
            return {"success": True, "data": new_bot}, 201
            
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Chatbot create failed: {e}")
            return {"success": False, "error": {"code": "CREATE_ERROR", "message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()


@ns_chatbots_admin.route('/<uuid:chatbot_id>')
class AdminChatbotItem(Resource):
    
    # 5-3. 챗봇 상세 조회
    @ns_chatbots_admin.doc(description='GET /api/set/chatbots/{id}')
    @ns_chatbots_admin.response(200, '성공', chatbot_response)
    def get(self, chatbot_id):
        """챗봇 상세 조회"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT chatbot_id, name, description, is_public, tag, created_at 
                FROM chatbots 
                WHERE chatbot_id=%s
            """, (str(chatbot_id),))

            r = cur.fetchone()
            if not r: 
                return {"success": False, "error": {"code": "NOT_FOUND", "message": "Chatbot not found"}}, 404
            
            bot = {
                "chatbot_id": str(r[0]), 
                "name": r[1], 
                "description": r[2], 
                "is_public": r[3],
                "tag": r[4],
                "created_at": str(r[5])
            }
            return {"success": True, "data": bot}, 200
        finally:
            cur.close()
            conn.close()

    # 5-4. 챗봇 설정 수정
    @ns_chatbots_admin.doc(description='PATCH /api/set/chatbots/{id}')
    @ns_chatbots_admin.expect(chatbot_patch_input) # ★ 수정용 모델 적용
    @ns_chatbots_admin.response(200, '수정 성공', chatbot_response)
    def patch(self, chatbot_id):
        data = request.json
        if not data:
            return {"success": False, "error": {"message": "No data provided"}}, 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. 챗봇 존재 확인
            cur.execute("SELECT 1 FROM chatbots WHERE chatbot_id=%s", (str(chatbot_id),))
            if not cur.fetchone():
                return {"success": False, "error": {"code": "NOT_FOUND", "message": "Chatbot not found"}}, 404

            # 2. 동적 쿼리 생성 (Dynamic SQL Construction)
            # 요청에 포함된 키(key)만 골라서 UPDATE 문을 만듭니다.
            update_fields = []
            values = []

            # (주의: if 'key' in data 방식을 써야 None 값도 업데이트 가능하고, 키가 없을 때만 무시함)
            if 'name' in data:
                update_fields.append("name = %s")
                values.append(data['name'])
            
            if 'description' in data:
                update_fields.append("description = %s")
                values.append(data['description'])
            
            if 'is_public' in data:
                update_fields.append("is_public = %s")
                values.append(data['is_public'])
                
            if 'tag' in data:
                update_fields.append("tag = %s")
                values.append(data['tag'])

            # 수정할 내용이 없으면 바로 리턴
            if not update_fields:
                return {"success": False, "error": {"message": "No valid fields to update"}}, 400

            # 쿼리 조립
            query = f"""
                UPDATE chatbots 
                SET {', '.join(update_fields)} 
                WHERE chatbot_id = %s
                RETURNING chatbot_id, name, description, is_public, tag, created_at
            """
            values.append(str(chatbot_id)) # WHERE 절 파라미터 추가

            # 3. 실행
            cur.execute(query, tuple(values))
            r = cur.fetchone()
            conn.commit()
            
            updated_bot = {
                "chatbot_id": str(r[0]),
                "name": r[1],
                "description": r[2],
                "is_public": r[3],
                "tag": r[4],
                "created_at": str(r[5])
            }
            return {"success": True, "data": updated_bot}, 200
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"code": "UPDATE_ERROR", "message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

    # 5-5. 챗봇 삭제
    @ns_chatbots_admin.doc(description='DELETE /api/set/chatbots/{id}')
    @ns_chatbots_admin.response(200, '삭제 성공', simple_response)
    def delete(self, chatbot_id):
        """챗봇 삭제 (관련 문서 및 파일 포함)"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # 1. 연결된 문서들의 document_id, storage_path 조회
            cur.execute("SELECT document_id, storage_path FROM documents WHERE chatbot_id=%s", (str(chatbot_id),))
            documents = cur.fetchall()

            # 2. 각 문서의 PDF 파일, 이미지 폴더, Chroma 청크 삭제
            for doc in documents:
                doc_id = doc[0]
                storage_path = doc[1]

                # (1) PDF 파일 삭제
                if storage_path:
                    abs_path = os.path.join(project_root, storage_path)
                    if os.path.exists(abs_path):
                        try:
                            os.remove(abs_path)
                            print(f"[DELETE] PDF 삭제: {abs_path}")
                        except Exception as err:
                            print(f"[WARN] PDF delete error: {err}")

                # (2) 이미지 폴더 삭제 (data/pdf_images/{document_id})
                if doc_id:
                    image_folder = os.path.join(project_root, 'data', 'pdf_images', str(doc_id))
                    if os.path.exists(image_folder) and os.path.isdir(image_folder):
                        try:
                            shutil.rmtree(image_folder)
                            print(f"[DELETE] 이미지 폴더 삭제: {image_folder}")
                        except Exception as err:
                            print(f"[WARN] Image folder delete error: {err}")

                # (3) Chroma에서 해당 문서 청크 삭제
                if doc_id and deleteDocumentAvailable and deleteDocument:
                    try:
                        deleteDocument(chatbotId=str(chatbot_id), documentId=str(doc_id))
                        print(f"[DELETE] Chroma 청크 삭제: chatbot={chatbot_id}, doc={doc_id}")
                    except Exception as err:
                        print(f"[WARN] Chroma delete error: {err}")

            # 3. 챗봇 PDF 폴더 삭제 (data/PDF/{chatbot_id})
            pdf_folder = os.path.join(project_root, 'data', 'PDF', str(chatbot_id))
            if os.path.exists(pdf_folder) and os.path.isdir(pdf_folder):
                try:
                    shutil.rmtree(pdf_folder)
                    print(f"[DELETE] PDF 폴더 삭제: {pdf_folder}")
                except Exception as err:
                    print(f"[WARN] PDF folder delete error: {err}")

            # 4. DB 삭제
            # (1) 문서 데이터 삭제
            cur.execute("DELETE FROM documents WHERE chatbot_id=%s", (str(chatbot_id),))

            # (2) 채팅 로그 데이터 삭제
            cur.execute("DELETE FROM query_logs WHERE chatbot_id=%s", (str(chatbot_id),))

            # (3) 챗봇 본체 삭제
            cur.execute("DELETE FROM chatbots WHERE chatbot_id=%s", (str(chatbot_id),))

            conn.commit()
            return {"success": True, "data": {"message": "Successfully deleted"}}, 200

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": {"code": "DELETE_ERROR", "message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()