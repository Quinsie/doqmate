import uuid
import base64
import os
import mimetypes
from flask import request
from flask_restx import Resource, Namespace, fields
from database import get_db_connection

try:
    from services.queryService import progressQuery
    queryServiceAvailable = True
except ImportError as e:
    print(f"[WARN] queryService 모듈을 찾을 수 없습니다: {e}")
    progressQuery = None
    queryServiceAvailable = False

# ----------------------------------------------------------------------
# Namespace 정의
# ----------------------------------------------------------------------
ns_chats = Namespace('chats', description='챗봇 질의 및 시스템 응답', path='/api/chats')

# ----------------------------------------------------------------------
# DTO (Data Transfer Object) 정의
# ----------------------------------------------------------------------

# 1. 요청 모델 (Request)
message_item = ns_chats.model('MessageItem', {
    'role': fields.String(required=True, description='user 또는 admin', example='user'),
    'content': fields.String(required=True, description='사용자 쿼리', example='농가에서 발주처 그룹을 등록하는 방법이 뭐죠?'),
    'is_first': fields.Boolean(description='첫 질문 여부', default=False, example=True)
})

chat_input = ns_chats.model('ChatInput', {
    'chatbot_id': fields.String(required=True, description='챗봇 UUID'),
    'session_id': fields.String(description='클라이언트 로컬 생성 세션 ID'),
    'messages': fields.List(fields.Nested(message_item), required=True, description='대화 목록')
})

# 2. 응답 모델 (Response) - Supporting Chunks 구조화
chunk_meta = ns_chats.model('ChunkMeta', {
    'filename': fields.String(example='급식센터_매뉴얼.pdf'),
    'page': fields.Integer(example=37),
    'manual_id': fields.String(example='manual-001')
})

chunk_item = ns_chats.model('ChunkItem', {
    'chunk_id': fields.String(example='manual-001_p2_c1'),
    'score': fields.Float(example=0.87),
    'meta': fields.Nested(chunk_meta)
})

# 이미지 응답 모델
image_item = ns_chats.model('ImageItem', {
    'id': fields.String(description='이미지 ID', example='img-001'),
    'mime_type': fields.String(description='MIME 타입', example='image/png'),
    'img_data': fields.String(description='Base64 인코딩된 이미지 데이터'),
    'description': fields.String(description='이미지 설명', example='Page 3')
})

chat_response = ns_chats.model('ChatResponse', {
    'chatbot_name': fields.String(description='챗봇 이름', example='Chatbot-01'),
    'answer': fields.String(description='RAG 파이프라인 응답'),
    'images': fields.List(fields.Nested(image_item), description='관련 이미지 목록'),
    'supporting_chunks': fields.List(fields.Nested(chunk_item), description='참조 문서 청크'),
    'uncertainty': fields.String(description='불확실성 (low/high)', example='low'),
    'suggested_title': fields.String(description='추천 제목 (is_first=True일 때만)', example='발주처 그룹 등록 방법')
})

# ----------------------------------------------------------------------
# API 구현
# ----------------------------------------------------------------------
@ns_chats.route('')
class ChatQuery(Resource):
    @ns_chats.doc(description="POST /api/chats : 1-2. 챗봇 질의 및 시스템 응답")
    @ns_chats.expect(chat_input)
    @ns_chats.response(200, '성공', chat_response)
    def post(self):
        """챗봇 질의 응답 (RAG)"""
        try:
            data = request.json
            if not data:
                return {
                    "success": False,
                    "error": {"code": "BAD_REQUEST", "message": "요청 데이터가 없습니다."}
                }, 400

            chatbot_id = data.get('chatbot_id')
            session_id = data.get('session_id')
            messages = data.get('messages', [])

            if not messages:
                return {
                    "success": False,
                    "error": {"code": "BAD_REQUEST", "message": "메시지가 없습니다."}
                }, 400

            # 마지막 사용자 메시지 추출
            last_msg = messages[-1]
            user_query = last_msg.get('content')
            is_first = last_msg.get('is_first', False)

            # -----------------------------------------------------
            # 챗봇 이름 조회
            # -----------------------------------------------------
            chatbot_name = "알 수 없음"
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT name FROM chatbots WHERE chatbot_id = %s", (chatbot_id,))
                bot_row = cur.fetchone()
                if bot_row:
                    chatbot_name = bot_row[0]
            except Exception as e:
                print(f"[CHAT] 챗봇 이름 조회 실패: {e}")
            finally:
                cur.close()
                conn.close()

            print(f"[CHAT] 챗봇[{chatbot_name}] 질문: {user_query}")

            # -----------------------------------------------------
            # queryService.progressQuery 호출
            # -----------------------------------------------------
            answer_text = ""
            chunks_json = []
            images_json = []  # 이미지 목록
            uncertainty = "high"
            suggested_title = None

            if queryServiceAvailable:
                try:
                    # ★ 서비스 함수 호출
                    result = progressQuery(
                        chatbotId=chatbot_id,
                        question=user_query,
                        userGroup=None, # 필요시 토큰에서 추출하여 전달
                        topK=5,
                        debug=True # 디버그 모드 (운영시 False 권장)
                    )

                    # 1. 답변 추출
                    answer_text = result.answer

                    # 2. 불확실성 추출
                    uncertainty = result.retrieval_confidence
                    # (서비스에서는 retrieval_confidence를 줌. 필요하면 매핑)

                    # 3. 근거 청크 변환 (Pydantic 모델 -> JSON dict)
                    if result.supporting_chunks:
                        for c in result.supporting_chunks:
                            # meta에서 필요한 필드만 추출
                            meta_raw = c.meta if hasattr(c, 'meta') else {}
                            if isinstance(meta_raw, dict):
                                meta_clean = {
                                    "filename": meta_raw.get('filename', ''),
                                    "page": meta_raw.get('page'),
                                    "manual_id": meta_raw.get('manual_id') or meta_raw.get('document_id', '')
                                }
                            else:
                                meta_clean = {"filename": "", "page": None, "manual_id": ""}

                            chunks_json.append({
                                "chunk_id": c.chunk_id if hasattr(c, 'chunk_id') and c.chunk_id else meta_raw.get('document_id', ''),
                                "score": c.score if hasattr(c, 'score') else 0,
                                "meta": meta_clean
                            })

                    # 4. 이미지 추출 및 Base64 인코딩
                    if hasattr(result, 'images') and result.images:
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                        for idx, img in enumerate(result.images):
                            image_key = img.get('image_key') if isinstance(img, dict) else getattr(img, 'image_key', None)
                            page_num = img.get('page') if isinstance(img, dict) else getattr(img, 'page', '')

                            if not image_key:
                                continue

                            # 이미지 파일 경로 구성: data/pdf_images/{image_key}
                            image_path = os.path.join(project_root, 'data', 'pdf_images', image_key)
                            print(f"[CHAT] 이미지 경로 시도: {image_path}")

                            # Base64 인코딩
                            base64_data = ""
                            mime_type = "image/png"

                            if os.path.exists(image_path):
                                try:
                                    # MIME 타입 추론
                                    guessed_type, _ = mimetypes.guess_type(image_path)
                                    if guessed_type:
                                        mime_type = guessed_type

                                    # 파일 읽기 및 Base64 인코딩
                                    with open(image_path, 'rb') as img_file:
                                        base64_data = base64.b64encode(img_file.read()).decode('utf-8')
                                    print(f"[CHAT] 이미지 인코딩 성공: {image_path} ({len(base64_data)} bytes)")
                                except Exception as img_err:
                                    print(f"[CHAT] 이미지 인코딩 실패: {image_path} - {img_err}")
                            else:
                                print(f"[CHAT] 이미지 파일 없음: {image_path}")

                            # 응답 형식에 맞게 변환
                            images_json.append({
                                "id": f"img-{idx + 1:03d}",
                                "mime_type": mime_type,
                                "img_data": base64_data,
                                "description": f"Page {page_num}"
                            })

                    # 5. 제목 생성 (첫 질문일 경우)
                    # 서비스에서 제목을 주지 않는다면, 간단히 질문 내용을 요약하거나 그대로 사용
                    if is_first:
                        # TODO: 별도 LLM 요약 호출이 없다면 질문 앞부분 사용
                        suggested_title = user_query[:20]

                except Exception as e:
                    print(f"[ERROR] RAG Service Failed: {e}")
                    import traceback
                    traceback.print_exc()
                    # queryService 내부 로직(안전 응답 등)이 실패했을 때 최후의 보루
                    answer_text = "죄송합니다. 시스템 오류로 답변을 생성할 수 없습니다."
            else:
                # 서비스 미연결 시 (테스트용)
                answer_text = f"[TEST] 서비스 미연결. 질문: {user_query}"

            # -----------------------------------------------------
            # DB 로깅 (query_logs)
            # -----------------------------------------------------
            log_id = str(uuid.uuid4())
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                # query_logs 테이블에 insert (구조에 따라 수정 필요)
                cur.execute("""
                    INSERT INTO query_logs (log_id, chatbot_id, question, answer, session_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (log_id, chatbot_id, user_query, answer_text, session_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"[CHAT Log Error] {e}")
            finally:
                cur.close()
                conn.close()

            # -----------------------------------------------------
            # 최종 응답 생성
            # -----------------------------------------------------
            response_data = {
                "chatbot_name": chatbot_name,
                "answer": answer_text,
                "images": images_json,
                "supporting_chunks": chunks_json,
                "uncertainty": uncertainty
            }

            if suggested_title:
                response_data["suggested_title"] = suggested_title

            return {
                "success": True,
                "data": response_data
            }, 200

        except Exception as e:
            print(f"[CRITICAL ERROR] Chat API Failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": "서버 오류가 발생했습니다."}
            }, 500
        
# ----------------------------------------------------------------------
# 8. 'stats' Namespace: 통계 API 
# ----------------------------------------------------------------------
ns_stats = Namespace('stats', description='서비스 이용 통계', path='/api/stats')

@ns_stats.route('/overview')
class StatsOverview(Resource):
    @ns_stats.doc(description="전체 서비스 이용 현황 (총 쿼리수, 유저수, 챗봇별/날짜별 통계)")
    def get(self):
        """7-1. 전체 통계 조회"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. 전체 쿼리 수
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT session_id) FROM query_logs")
            row = cur.fetchone()
            total_queries = row[0]
            unique_clients = row[1]

            # 2. 챗봇별 통계 (JOIN으로 이름 가져오기)
            cur.execute("""
                SELECT q.chatbot_id, COALESCE(c.name, '삭제된 챗봇'), COUNT(q.log_id)
                FROM query_logs q
                LEFT JOIN chatbots c ON q.chatbot_id = c.chatbot_id
                GROUP BY q.chatbot_id, c.name
                ORDER BY COUNT(q.log_id) DESC
            """)
            by_chatbot = [
                {"chatbot_id": str(r[0]), "chatbot_name": r[1], "queries": r[2]}
                for r in cur.fetchall()
            ]

            # 4. 날짜별 쿼리 수 (최근 30일 기준 예시)
            # PostgreSQL의 to_char 함수를 사용해 날짜 포맷팅
            cur.execute("""
                SELECT to_char(created_at, 'YYYY-MM-DD') as d, COUNT(*) 
                FROM query_logs 
                GROUP BY d 
                ORDER BY d ASC
            """)
            by_date = [{"date": row[0], "queries": row[1]} for row in cur.fetchall()]

            return {
                "success": True,
                "data": {
                    "total_queries": total_queries,
                    "unique_clients": unique_clients,
                    "by_chatbot": by_chatbot,
                    "by_date": by_date
                }
            }, 200
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

@ns_stats.route('/chatbot/<string:chatbot_id>')
class StatsChatbot(Resource):
    @ns_stats.doc(description="특정 챗봇의 이용 통계")
    def get(self, chatbot_id):
        """7-2. 챗봇별 통계"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. 챗봇 이름 조회
            cur.execute("SELECT name FROM chatbots WHERE chatbot_id = %s", (chatbot_id,))
            bot_row = cur.fetchone()
            chatbot_name = bot_row[0] if bot_row else "알 수 없음"

            # 2. 총계
            cur.execute("""
                SELECT COUNT(*), COUNT(DISTINCT session_id) 
                FROM query_logs WHERE chatbot_id = %s
            """, (chatbot_id,))
            stat_row = cur.fetchone()

            # 2. 해당 챗봇 고유 유저
            cur.execute("SELECT COUNT(DISTINCT session_id) FROM query_logs WHERE chatbot_id = %s", (chatbot_id,))
            unique_clients = cur.fetchone()[0]

            # 3. 날짜별 추이
            cur.execute("""
                SELECT to_char(created_at, 'YYYY-MM-DD') as d, COUNT(*) 
                FROM query_logs 
                WHERE chatbot_id = %s
                GROUP BY d 
                ORDER BY d ASC
            """, (chatbot_id,))
            by_date = [{"date": r[0], "queries": r[1]} for r in cur.fetchall()]

            return {
                "success": True,
                "data": {
                    "chatbot_id": chatbot_id,
                    "chatbot_name": chatbot_name, # 프론트 요청사항 반영
                    "total_queries": stat_row[0],
                    "unique_clients": stat_row[1],
                    "by_date": by_date
                }
            }, 200
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()

@ns_stats.route('/date/<string:date_str>')
class StatsDate(Resource):
    @ns_stats.doc(description="특정 날짜(YYYY-MM-DD)의 통계")
    def get(self, date_str):
        """날짜별 상세 통계"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # 1. 해당 날짜 총계
            cur.execute("""
                SELECT COUNT(*), COUNT(DISTINCT session_id) 
                FROM query_logs 
                WHERE to_char(created_at, 'YYYY-MM-DD') = %s
            """, (date_str,))
            stat_row = cur.fetchone()

            # 2. 챗봇별 분포 (이름 포함)
            cur.execute("""
                SELECT q.chatbot_id, COALESCE(c.name, '삭제된 챗봇'), COUNT(q.log_id)
                FROM query_logs q
                LEFT JOIN chatbots c ON q.chatbot_id = c.chatbot_id
                WHERE to_char(q.created_at, 'YYYY-MM-DD') = %s
                GROUP BY q.chatbot_id, c.name
                ORDER BY COUNT(q.log_id) DESC
            """, (date_str,))
            by_chatbot = [
                {"chatbot_id": str(r[0]), "chatbot_name": r[1], "queries": r[2]} 
                for r in cur.fetchall()
            ]

            return {
                "success": True,
                "data": {
                    "date": date_str,            
                    "total_queries": stat_row[0],
                    "unique_clients": stat_row[1],
                    "by_chatbot": by_chatbot      
                }
            }, 200
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}, 500
        finally:
            cur.close()
            conn.close()