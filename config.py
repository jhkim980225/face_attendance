import os
from dotenv import load_dotenv

load_dotenv()  # .env 로드

print(os.getenv("MYSQL_HOST"))

class Config:
    # 파일 저장 경로(그대로 사용)
    BASE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(BASE_DIR, "face_data")
    IMG_DIR  = os.path.join(DATA_DIR, "images")
    ENC_DIR  = os.path.join(DATA_DIR, "encodings")

    # 인증 임계값(낮을수록 엄격)
    THRESHOLD = 0.45

    # Flask 서버
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = True

    # MariaDB (SQLAlchemy + PyMySQL)
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "face_user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "face_pwd_1234")
    MYSQL_DB = os.getenv("MYSQL_DB", "face_api")

    # 커넥션 풀
    MYSQL_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", "5"))
    MYSQL_MAX_OVERFLOW = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))

    @classmethod
    def sqlalchemy_url(cls) -> str:
        # utf8mb4 & 로캘 고정
        return (
            f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}"
            f"@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}"
            f"?charset=utf8mb4"
        )
