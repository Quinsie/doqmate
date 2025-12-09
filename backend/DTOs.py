from flask_restx import fields
from extensions import api

# ======================================================================
#  [DTO / Models] 데이터 모델 정의 (Swagger 표시용)
# ======================================================================

# --- 1. 기본 객체 DTO ---
admin_dto = api.model('Admin', {
    'admin_id': fields.String(description='관리자 UUID'),
    'username': fields.String(description='아이디'),
    'name': fields.String(description='이름'),
    'created_at': fields.String(description='생성일'),
    'last_login_at': fields.String(description='마지막 로그인 시간')
})

chatbot_dto = api.model('Chatbot', {
    'chatbot_id': fields.String,
    'name': fields.String,
    'description': fields.String,
    'is_public': fields.Boolean,
    'tag': fields.String(description='챗봇 태그'), 
    'created_at': fields.String
})

chatbot_list_item_dto = api.model('ChatbotListItem', {
    'chatbot_id': fields.String,
    'name': fields.String,
    'description': fields.String,
    'is_public': fields.Boolean,
    'tag': fields.String(description='챗봇 태그'), 
    'created_at': fields.String,
    'manual_count': fields.Integer(description='연결된 매뉴얼 개수')
})

manual_dto = api.model('Manual', {
    'manual_id': fields.String(description='문서 ID'),
    'chatbot_id': fields.String(description='연결된 챗봇 ID'),
    'display_name': fields.String(description='화면 표시 이름'),
    'original_filename': fields.String(description='원본 파일명'),
    'status': fields.String(description='상태 (pending/indexing/ready/failed)'),
    'created_at': fields.String(description='생성일')
})

signup_dto = api.model('Signup', {
    'signup_id': fields.String,
    'username': fields.String,
    'name': fields.String,
    'status': fields.String,
    'created_at': fields.String
})

# 통계용 단위 객체 (리스트 내부에 들어갈 아이템)
stats_chatbot_item = api.model('ChatbotQueryCount', {
    'chatbot_id': fields.String(description='챗봇 UUID'),
    'chatbot_name': fields.String(description='챗봇 이름'),
    'queries': fields.Integer(description='질의 수')
})

stats_date_item = api.model('DateQueryCount', {
    'date': fields.String(description='날짜 (YYYY-MM-DD)'),
    'queries': fields.Integer(description='질의 수')
})
# --- 2. 응답 래퍼(Wrapper) DTO ---
# -> { success: true, data: {...}, error: null } 구조를 표현
def make_response_model(name, data_model):
    """ { success: true, data: { ... }, error: null } 형태 생성기 """
    return api.model(f'{name}Response', {
        'success': fields.Boolean(default=True),
        'data': fields.Nested(data_model, allow_null=True),
        'error': fields.Raw(default=None) # 에러 객체는 유연하게 처리
    })

# 각 API별 응답 모델
# (1) 로그인 응답: 토큰 + 관리자 정보
login_data_model = api.model('LoginData', {
    'token': fields.String,
    'admin': fields.Nested(admin_dto)
})
login_response = make_response_model('Login', login_data_model)

# (2) 단순 메시지 (성공/실패 메시지용)
message_data = api.model('MessageData', {'message': fields.String})
simple_response = make_response_model('Simple', message_data)

# (3) 관리자 목록
admin_list_response = make_response_model('AdminList', api.model('AdminsData', {
    'admins': fields.List(fields.Nested(admin_dto))
}))

# (4) 챗봇 관리
chatbot_list_response = make_response_model('ChatbotList', api.model('ChatbotsData', {
    'chatbots': fields.List(fields.Nested(chatbot_list_item_dto), description='챗봇 목록')
}))
chatbot_response = make_response_model('ChatbotDetail', chatbot_dto)

# (5) 문서(매뉴얼) 관리
manual_list_resp = make_response_model('ManualList', api.model('ManualsData', {
    'manuals': fields.List(fields.Nested(manual_dto))
}))
manual_response = make_response_model('Manual', manual_dto)

# (6) 가입 신청 관리 (★ 누락되었던 부분 추가)
signup_list_response = make_response_model('SignupList', api.model('SignupsData', {
    'signups': fields.List(fields.Nested(signup_dto))
}))

# ----------------------------------------------------------------------
# 통계(Stats) 관련 응답 모델
# ----------------------------------------------------------------------

# 전체 통계 (Overview)
stats_overview_data = api.model('OverviewStatsData', {
    'total_queries': fields.Integer(description='전체 누적 질의 수'),
    'unique_clients': fields.Integer(description='전체 유니크 사용자(세션) 수'),
    'by_chatbot': fields.List(fields.Nested(stats_chatbot_item), description='챗봇별 질의 통계 리스트'),
    'by_date': fields.List(fields.Nested(stats_date_item), description='날짜별 질의 통계 리스트')
})
stats_overview_response = make_response_model('StatsOverview', stats_overview_data)

# 챗봇별 상세 통계
stats_chatbot_detail_data = api.model('ChatbotStatsData', {
    'chatbot_id': fields.String(description='챗봇 UUID'),
    'chatbot_name': fields.String(description='챗봇 이름'),
    'total_queries': fields.Integer(description='해당 챗봇의 총 질의 수'),
    'unique_clients': fields.Integer(description='해당 챗봇의 유니크 사용자 수'),
    'by_date': fields.List(fields.Nested(stats_date_item), description='해당 챗봇의 날짜별 추이')
})
stats_chatbot_detail_response = make_response_model('StatsChatbot', stats_chatbot_detail_data)

# 날짜별 상세 통계
stats_date_detail_data = api.model('DateStatsData', {
    'date': fields.String(description='조회한 날짜 (YYYY-MM-DD)'),
    'total_queries': fields.Integer(description='해당 날짜의 총 질의 수'),
    'unique_clients': fields.Integer(description='해당 날짜의 유니크 사용자 수'),
    'by_chatbot': fields.List(fields.Nested(stats_chatbot_item), description='해당 날짜의 챗봇별 점유율')
})
stats_date_detail_response = make_response_model('StatsDate', stats_date_detail_data)

# ----------------------------------------------------------------------
# 비밀번호 재설정 응답 DTO
# ----------------------------------------------------------------------
reset_pw_data = api.model('ResetPwData', {
    'temp_password': fields.String(description='발급된 임시 비밀번호')
})
# 최종 응답 형태: { success: true, data: { temp_password: "..." }, error: null }
reset_pw_response = make_response_model('ResetPw', reset_pw_data)