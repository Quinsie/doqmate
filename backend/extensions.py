from flask_restx import Api

# ---------------------------------------------------------
# Swagger UI에 'Authorize' 버튼을 만들기 위한 설정
# ---------------------------------------------------------
authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "JWT Token을 입력하세요. 예: Bearer eyJhb..."
    }
}

# 순환 참조 방지를 위해 Api 객체만 따로 생성
api = Api(
    version='1.0', 
    title='Chatbot API',
    description='PostgreSQL & File Upload & JWT Token 적용 API',
    authorizations=authorizations, # ★ 여기에 설정을 넣어줍니다.
    security='Bearer Auth'         # ★ 기본적으로 이 인증 방식을 쓴다고 알립니다.
)