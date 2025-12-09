import os
import shutil
import uuid
import datetime
import threading
from flask import request, current_app
from flask_restx import Resource, Namespace
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from database import get_db_connection

# 수정된 DTO import
from DTOs import manual_list_resp, manual_response, simple_response, manual_dto, make_response_model

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.documentService import processDocument, deleteDocument
    documentServiceAvailable = True  # import 성공 플래그
except ImportError as e:
    print(f"[WARN] documentService 모듈을 찾을 수 없습니다. (인덱싱 기능 비활성화): {e}")
    processDocument = None
    deleteDocument = None
    documentServiceAvailable = False

# Namespace 설정: /api/set/manuals
ns_manuals = Namespace('set-manuals', description='챗봇별 문서(매뉴얼) 관리', path='/api/set/manuals')

# 업로드 파서 (FormData)
upload_parser = ns_manuals.parser()
upload_parser.add_argument('file', type=FileStorage, location='files', required=True, help='PDF 파일')
upload_parser.add_argument('display_name', type=str, required=True, help='문서 표시 이름')
# chatbot_id는 쿼리 파라미터로 받음

@ns_manuals.route('')
class ManualCollection(Resource):
    
    # ------------------------------------------------------------------
    # 6-2. 문서 목록 조회
    # GET /api/set/manuals?chatbot_id={id}
    # ------------------------------------------------------------------
    @ns_manuals.doc(params={'chatbot_id': '챗봇 ID'})
    @ns_manuals.response(200, '성공', manual_list_resp)
    def get(self):
        """해당 챗봇에 연결된 문서 목록 확인"""
        chatbot_id = request.args.get('chatbot_id')
        
        if not chatbot_id:
             return {
                "success": False,
                "error": {"code": "MISSING_PARAM", "message": "chatbot_id parameter is required"}
            }, 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # DB에서는 document_id로 저장되어 있다고 가정하고 manual_id로 alias 처리
            cur.execute("""
                SELECT document_id, chatbot_id, display_name, original_filename, status, uploaded_at 
                FROM documents 
                WHERE chatbot_id = %s
                ORDER BY uploaded_at DESC
            """, (chatbot_id,))
            
            rows = cur.fetchall()
            manuals = []
            for r in rows:
                manuals.append({
                    "manual_id": str(r[0]),      # DB: document_id -> API: manual_id
                    "chatbot_id": str(r[1]),
                    "display_name": r[2],
                    "original_filename": r[3],
                    "status": r[4],
                    "created_at": str(r[5])      # DB: uploaded_at -> API: created_at
                })
            
            return {
                "success": True,
                "data": {"manuals": manuals}
            }, 200

        except Exception as e:
            return {
                "success": False,
                "error": {"code": "DB_ERROR", "message": str(e)}
            }, 500
        finally:
            cur.close()
            conn.close()

    # ------------------------------------------------------------------
    # 6-1. 문서 업로드
    # POST /api/set/manuals?chatbot_id={id} (FormData: file, display_name)
    # ------------------------------------------------------------------
    @ns_manuals.expect(upload_parser)
    @ns_manuals.doc(params={'chatbot_id': '챗봇 ID'})
    @ns_manuals.response(201, '업로드 성공', manual_response)
    def post(self):
        """PDF 문서 업로드 및 인덱싱 시작"""
        chatbot_id = request.args.get('chatbot_id')
        print("[1] This line is working.")
        
        if not chatbot_id:
            return {
                "success": False,
                "error": {"code": "MISSING_PARAM", "message": "chatbot_id parameter is required"}
            }, 400

        print("[2] This line is working.")

        args = upload_parser.parse_args()
        file = args['file']
        display_name = args['display_name']

        if not file:
            return {
                "success": False,
                "error": {"code": "NO_FILE", "message": "File is required"}
            }, 400
        
        print("[3] This line is working.")

        filename = secure_filename(file.filename)
        # [수정 포인트 1] 물리적 파일 저장 경로 (절대 경로 사용)
        # 예: /home/jiho/doqmate/data/PDF/{chatbot_id}/
        abs_save_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], chatbot_id)
        if not os.path.exists(abs_save_dir):
            try: os.makedirs(abs_save_dir)
            except: pass

        print("[4] This line is working.")
        
        # 파일 저장 (OS 상의 절대 경로)
        abs_file_path = os.path.join(abs_save_dir, filename)

        print("[5] This line is working.")
        
        # [수정 포인트 2] DB 저장용 경로 (상대 경로 문자열 생성)
        # 예: data/PDF/{chatbot_id}/{filename} (앞에 슬래시나 ../ 없음)
        db_file_path = os.path.join(current_app.config['UPLOAD_RELATIVE_PATH'], chatbot_id, filename)

        print("[6] This line is working.")
        
        try:
            file.save(abs_file_path)
        except Exception as e:
             return {
                "success": False,
                "error": {"code": "FILE_SAVE_ERROR", "message": str(e)}
            }, 500

        print("[7] This line is working.")

        # DB 저장
        new_id = str(uuid.uuid4())
        conn = get_db_connection()
        cur = conn.cursor()

        print("[8] This line is working.")
        
        try:
            # documents 테이블 사용 (status 초기값: pending)
            cur.execute("""
                INSERT INTO documents (document_id, chatbot_id, display_name, original_filename, storage_path, status, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
            """, (new_id, chatbot_id, display_name, filename, db_file_path))
            
            conn.commit()
            print("[9] This line is working.")
            
            # =========================================================
            # 실제 인덱싱 서비스 호출 (비동기 스레드)
            # =========================================================
            if documentServiceAvailable:
                def run_indexing_task(doc_id, path, bot_id, origin_fname):
                    t_conn = get_db_connection()
                    t_cur = t_conn.cursor()
                    print(f"[INFO] Indexing thread started for {doc_id}", flush=True)

                    try:
                        # (1) 상태 변경: pending -> indexing
                        t_cur.execute("UPDATE documents SET status='indexing' WHERE document_id=%s", (doc_id,))
                        t_conn.commit()

                        # (2) 서비스 호출: processDocument
                        processDocument(
                            chatbotId=bot_id,
                            documentId=doc_id,
                            pdfPath=path,
                            filename=origin_fname,
                            debug=True # 디버그 로그 필요 시 True
                        )
                        
                        # (3) 성공 시: indexing -> ready
                        t_cur.execute("UPDATE documents SET status='ready' WHERE document_id=%s", (doc_id,))
                        t_conn.commit()
                        print(f"[INFO] Indexing success for {doc_id}")

                    except Exception as e:
                        # (4) 실패 시: indexing -> failed
                        t_conn.rollback()
                        t_cur.execute("UPDATE documents SET status='failed' WHERE document_id=%s", (doc_id,))
                        t_conn.commit()
                        print(f"[ERROR] Indexing failed for {doc_id}: {e}")
                    
                    finally:
                        t_cur.close()
                        t_conn.close()

                # 비동기 실행 (사용자는 기다리지 않게 함)
                thread = threading.Thread(
                    target=run_indexing_task, 
                    args=(new_id, db_file_path, chatbot_id, filename)
                )
                thread.start()
            else:
                print("[WARN] documentService 미연결: 인덱싱 건너뜀")
            
            # 응답 데이터 구성
            created_data = {
                "manual_id": new_id,
                "chatbot_id": chatbot_id,
                "display_name": display_name,
                "original_filename": filename,
                "status": "pending",
                "created_at": str(datetime.datetime.now()) # 정확한 시간은 DB 리턴값을 쓰는게 좋으나 편의상 현재시간
            }

            return {
                "success": True,
                "data": created_data
            }, 201

        except Exception as e:
            conn.rollback()
            return {
                "success": False,
                "error": {"code": "DB_ERROR", "message": str(e)}
            }, 500
        finally:
            cur.close()
            conn.close()


@ns_manuals.route('/<uuid:manual_id>')
class ManualItem(Resource):
    
    # ------------------------------------------------------------------
    # 6-3. 문서 삭제
    # DELETE /api/set/manuals/{manual_id}
    # ------------------------------------------------------------------
    @ns_manuals.response(200, '삭제 성공', simple_response)
    def delete(self, manual_id):
        """문서 삭제 (DB 메타 + 실제 파일 + 벡터 스토어 데이터)"""
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 1. 파일 경로 및 chatbot_id 조회
            cur.execute("SELECT chatbot_id, storage_path FROM documents WHERE document_id=%s", (str(manual_id),))
            row = cur.fetchone()

            if not row:
                return {
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": "Manual not found"}
                }, 404

            chatbot_id = row[0]
            db_file_path = row[1]

            # 2. 실제 파일 삭제
            # storage_path는 상대 경로 (예: data/PDF/챗봇ID/파일.pdf)
            # 프로젝트 루트 기준으로 절대 경로 생성
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            if db_file_path:
                abs_path = os.path.join(project_root, db_file_path)
                print(f"[DELETE] 파일 삭제 시도: {abs_path}")
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                        print(f"[DELETE] 파일 삭제 완료: {abs_path}")
                    except Exception as err:
                        print(f"[WARN] File delete error: {err}")
                    # 파일 삭제 실패해도 DB는 삭제 진행
                else:
                    print(f"[WARN] 파일이 존재하지 않음: {abs_path}")

            # 3. 이미지 폴더 삭제 (data/pdf_images/{document_id})
            image_folder = os.path.join(project_root, 'data', 'pdf_images', str(manual_id))
            if os.path.exists(image_folder) and os.path.isdir(image_folder):
                try:
                    shutil.rmtree(image_folder)
                    print(f"[DELETE] 이미지 폴더 삭제 완료: {image_folder}")
                except Exception as err:
                    print(f"[WARN] Image folder delete error: {err}")

            # 4. 벡터 DB(Chroma)에서 해당 문서의 청크 삭제
            if documentServiceAvailable and deleteDocument:
                try:
                    deleteDocument(chatbotId=str(chatbot_id), documentId=str(manual_id))
                    print(f"[DELETE] Chroma 청크 삭제 완료: chatbot={chatbot_id}, doc={manual_id}")
                except Exception as err:
                    print(f"[WARN] Chroma delete error: {err}")

            # 5. DB 레코드 삭제
            cur.execute("DELETE FROM documents WHERE document_id=%s", (str(manual_id),))

            conn.commit()
            
            return {
                "success": True,
                "data": {"message": "Successfully deleted"}
            }, 200

        except Exception as e:
            conn.rollback()
            return {
                "success": False,
                "error": {"code": "DELETE_ERROR", "message": str(e)}
            }, 500
        finally:
            cur.close()
            conn.close()