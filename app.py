# app.py
from flask import Flask
import os

from config import Config
from db import init_db

# 라우트 블루프린트

from routes.capture import bp as capture_bp  # ← 새로 추가한 카메라 캡처

def create_app() -> Flask:
    # 저장 디렉터리 보장
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.IMG_DIR, exist_ok=True)
    os.makedirs(Config.ENC_DIR, exist_ok=True)

    app = Flask(__name__)
    app.config.from_object(Config)

    # DB 테이블 준비(DDL은 사전 적용, 여기서는 존재 확인/보정)
    init_db()

    # 블루프린트 등록    
    app.register_blueprint(capture_bp, url_prefix="/capture")  # POST /capture

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)