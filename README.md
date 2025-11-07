# Face Attendance System# Face Attendance (Flask + OpenCV)  

> Flask + OpenCV + face_recognition 기반 얼굴인식 출퇴근 관리 시스템출퇴근 얼굴인식 시스템 개발 기록



------



## 📋 목차## 📌 프로젝트 개요

1. [프로젝트 개요](#프로젝트-개요)OpenCV + Flask 기반으로 얼굴을 인식하여 출근/퇴근을 기록하는 시스템.  

2. [주요 기능](#주요-기능)웹브라우저(노트북/태블릿)에서 API 호출로 이용하며, 로컬 또는 사내 서버에서 운영 가능.

3. [기술 스택](#기술-스택)

4. [프로젝트 구조](#프로젝트-구조)---

5. [API 명세](#api-명세)

6. [데이터베이스 스키마](#데이터베이스-스키마)## ✅ Git 초기 설정 과정 정리

7. [설치 및 실행](#설치-및-실행)

8. [환경 변수 설정](#환경-변수-설정)### 1. Git 초기화

9. [개발 과정](#개발-과정)```bash

git init

---git add .

git commit -m "init"

## 📌 프로젝트 개요git branch -M main

git push -u origin main  -> 이후 git push
### 목적
OpenCV와 face_recognition 라이브러리를 활용한 **실시간 얼굴인식** 기반 출퇴근 관리 시스템입니다.  
웹 브라우저(노트북/태블릿)에서 API를 호출하여 카메라로 얼굴을 촬영하고, 자동으로 사용자를 인식하여 출퇴근을 기록합니다.

### 특징
- 🎥 **실시간 카메라 캡처**: OpenCV로 웹캠에서 얼굴 실시간 감지
- 🧠 **얼굴 인코딩**: face_recognition 라이브러리로 128차원 벡터 생성
- 👤 **사용자 식별**: 유클리드 거리 기반 얼굴 매칭 (임계값 0.45)
- 🖼️ **프리뷰 모드**: 실시간 얼굴 박스 표시 및 캡처 타이밍 제어
- 💾 **영구 저장**: MariaDB(MySQL) + 파일 시스템에 이미지/인코딩 저장
- 🔒 **단일 얼굴 정책**: 한 번에 한 명만 인식 (다중 얼굴 감지 시 거부)

---

## 🎯 주요 기능

### 1. 얼굴 등록 (Enrollment)
- **엔드포인트**: `POST /capture/`
- 카메라로 얼굴 촬영 → 인코딩 생성 → DB 및 파일 저장
- 프리뷰 모드 지원: 실시간 화면에서 'C' 키로 캡처

### 2. 얼굴 인식 (Identification)
- **엔드포인트**: `POST /capture/identify`
- 실시간 얼굴 촬영 → 등록된 모든 사용자와 비교 → 가장 가까운 매칭 반환
- 임계값(tolerance=0.45) 이하일 때만 인증 성공

### 3. 데이터 관리
- 이미지 파일: `face_data/images/` (JPG 형식)
- 인코딩 파일: `face_data/encodings/` (NumPy .npy 형식)
- DB 메타데이터: `face_captures` 테이블에 경로 및 타임스탬프 저장

---

## 🛠️ 기술 스택

### Backend
- **Python 3.13** (C:\Users\JHKIM\AppData\Local\Programs\Python\Python313\python.exe)
- **Flask 3.1.2**: 웹 프레임워크
- **OpenCV 4.12.0.88**: 카메라 제어 및 이미지 처리
- **face_recognition**: dlib 기반 얼굴 인식 라이브러리
- **NumPy 2.2.6**: 수치 연산 및 인코딩 저장

### Database
- **MariaDB/MySQL**: 사용자 및 캡처 데이터 저장
- **SQLAlchemy 2.0.43**: ORM 및 커넥션 풀 관리
- **PyMySQL 1.1.2**: MySQL 드라이버

### Environment
- **python-dotenv 1.1.1**: 환경 변수 관리 (.env 파일)
- **Windows**: 기본 개발 환경

---

## 📁 프로젝트 구조

```
face_attendance/
├── app.py                    # Flask 앱 진입점 (서버 실행)
├── config.py                 # 전역 설정 (DB, 경로, 임계값)
├── db.py                     # DB 연결 및 쿼리 함수
├── .env                      # 환경 변수 (MySQL 접속 정보)
├── .gitignore                # Git 제외 파일
│
├── routes/
│   ├── capture.py            # API 라우트 (/capture/, /capture/identify)
│   └── __pycache__/
│
├── services/
│   ├── camera_service.py     # 카메라 제어 및 캡처 로직
│   ├── face_service.py       # 얼굴 감지/인코딩/저장 로직
│   └── __pycache__/
│
├── face_data/
│   ├── images/               # 촬영한 얼굴 이미지 (JPG)
│   └── encodings/            # 얼굴 인코딩 벡터 (NPY)
│       ├── 1761704793_2dea4b9c-7c6d-4be0-879c-19e6851d64bf.npy
│       ├── 1761711814_2fdbec40-3c31-46b6-95ac-a1b15952e0ee.npy
│       └── ... (30+ files)
│
├── data/                     # (현재 비어있음)
├── faces/                    # (현재 비어있음)
├── utils/                    # (현재 비어있음)
├── __pycache__/
└── README.md                 # 본 문서
```

---

## 🔌 API 명세

### 1. 얼굴 등록 (Enrollment)

**Endpoint**: `POST /capture/`

**Request Parameters** (JSON/Form/Query 모두 지원):
```json
{
  "device_index": 0,          // 카메라 장치 번호 (기본값: 0)
  "min_width": 320,           // 최소 프레임 너비 (기본값: 320)
  "timeout_sec": 8.0,         // 얼굴 감지 타임아웃 (기본값: 8.0초)
  "preview": "1",             // 프리뷰 모드 (0/1, true/false)
  "name": "홍길동"            // 사용자 이름 (선택사항)
}
```

**Response (성공)**:
```json
{
  "ok": true,
  "status": "success",
  "capture_id": "342f8c0a-aad6-438f-adae-f8e296024fff",
  "faces_in_frame": 1
}
```

**Response (실패)**:
```json
{
  "ok": false,
  "error": "no face detected within 8.0 sec",
  "code": "FACE_TIMEOUT_ERROR"
}
```

**Error Codes**:
- `CAMERA_OPEN_ERROR` (503): 카메라를 열 수 없음
- `FACE_TIMEOUT_ERROR` (422): 타임아웃 내 얼굴 미감지
- `NO_FACE_ERROR` (422): 얼굴 없음
- `MULTI_FACE_ERROR` (422): 여러 얼굴 감지 (단일 얼굴만 허용)

### 2. 얼굴 인식 (Identification)

**Endpoint**: `POST /capture/identify`

**Request Parameters**: (1번 API와 동일)

**Response (매칭 성공)**:
```json
{
  "status": "success",
  "user": "홍길동",
  "distance": 0.387
}
```

**Response (미등록 사용자)**:
```json
{
  "status": "unknown",
  "distance": 0.672
}
```

**Response (얼굴 미감지)**:
```json
{
  "status": "fail",
  "reason": "no_face_or_multiple"
}
```

---

## 🗄️ 데이터베이스 스키마

### 테이블: `users`
```sql
CREATE TABLE users (
  user_id    VARCHAR(128) NOT NULL,
  created_at BIGINT NOT NULL,
  PRIMARY KEY (user_id),
  KEY idx_users_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 테이블: `samples`
```sql
CREATE TABLE samples (
  sample_id     VARCHAR(64) NOT NULL,
  user_id       VARCHAR(128) NOT NULL,
  image_path    VARCHAR(512) NOT NULL,
  encoding_path VARCHAR(512) NOT NULL,
  created_at    BIGINT NOT NULL,
  PRIMARY KEY (sample_id),
  KEY idx_samples_user_id (user_id),
  KEY idx_samples_created_at (created_at),
  CONSTRAINT fk_samples_user FOREIGN KEY (user_id)
    REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 테이블: `face_captures` (현재 사용 중)
```sql
-- db.py의 insert_capture() 함수에서 사용
-- 컬럼: capture_id, name, image_path, encoding_path, captured_at
```

**주의**: 코드에는 `face_captures` 테이블을 사용하지만, DDL은 `users`/`samples` 구조로 정의되어 있습니다.  
실제 운영 시 테이블 스키마 통일이 필요합니다.

---

## 🚀 설치 및 실행

### 1. 사전 요구사항
- Python 3.13
- MariaDB/MySQL 서버
- 웹캠 (USB 카메라 또는 내장 카메라)

### 2. 프로젝트 클론
```bash
git clone <repository-url>
cd face_attendance
```

### 3. 가상환경 생성 및 활성화
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

### 4. 패키지 설치
```bash
pip install Flask==3.1.2
pip install opencv-python==4.12.0.88
pip install numpy==2.2.6
pip install SQLAlchemy==2.0.43
pip install PyMySQL==1.1.2
pip install python-dotenv==1.1.1
pip install face-recognition  # dlib 포함 (설치 시간 소요)
```

**주의**: `face-recognition` 설치 시 C++ 컴파일러가 필요합니다.  
Windows의 경우 Visual Studio Build Tools 또는 미리 빌드된 wheel 파일을 사용하세요.

### 5. 데이터베이스 설정
```sql
CREATE DATABASE face_api DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'face_user'@'%' IDENTIFIED BY 'face_pwd_1234';
GRANT ALL PRIVILEGES ON face_api.* TO 'face_user'@'%';
FLUSH PRIVILEGES;
```

### 6. 환경 변수 설정 (.env 파일)
```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=face_user
MYSQL_PASSWORD=face_pwd_1234
MYSQL_DB=face_api
MYSQL_POOL_SIZE=5
MYSQL_MAX_OVERFLOW=10
```

### 7. 서버 실행
```bash
python app.py
```

서버가 `http://0.0.0.0:8000`에서 실행됩니다.

---

## ⚙️ 환경 변수 설정

### config.py 주요 설정값

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATA_DIR` | `face_data/` | 데이터 저장 루트 디렉토리 |
| `IMG_DIR` | `face_data/images/` | 이미지 저장 경로 |
| `ENC_DIR` | `face_data/encodings/` | 인코딩 저장 경로 |
| `THRESHOLD` | `0.45` | 얼굴 매칭 임계값 (낮을수록 엄격) |
| `HOST` | `0.0.0.0` | Flask 서버 호스트 |
| `PORT` | `8000` | Flask 서버 포트 |
| `DEBUG` | `True` | 디버그 모드 |

---

## 🔧 핵심 모듈 설명

### 1. camera_service.py
**역할**: 카메라 제어 및 얼굴 캡처

**주요 함수**:
- `_open_camera(device_index)`: 카메라 장치 열기 (CAP_ANY → MSMF → DSHOW 순서로 시도)
- `_find_single_face_frame(cap, timeout, min_width)`: 단일 얼굴 프레임 감지 (타임아웃 내)
- `capture_and_enroll(...)`: 얼굴 촬영 → 등록 플로우
- `identify_user(...)`: 얼굴 촬영 → 기존 사용자 식별

**프리뷰 모드**:
- OpenCV 윈도우에서 실시간 얼굴 박스 표시
- 'C' 키: 캡처 실행
- 'ESC' 키: 취소

**예외 처리**:
- `CameraOpenError`: 카메라 열기 실패
- `FaceTimeoutError`: 타임아웃 내 얼굴 미감지
- `MultiFaceError`: 여러 얼굴 감지
- `NoFaceError`: 얼굴 없음

### 2. face_service.py
**역할**: 얼굴 인코딩 및 저장

**주요 함수**:
- `detect_and_encode_bgr(bgr_img)`: 얼굴 감지 + 128차원 인코딩 생성
  - HOG 모델 사용 (CNN보다 빠르지만 정확도 낮음)
  - 반환: (얼굴 박스들, 인코딩들)
- `save_capture(bgr_img, enc, name)`: 이미지/인코딩 파일 저장 + DB 기록
  - 파일명 형식: `{name}_{serial_num}.jpg`, `{timestamp}_{uuid}.npy`
- `load_all_encodings()`: 모든 인코딩 파일 로드 (캐싱 용도)

### 3. db.py
**역할**: 데이터베이스 연결 및 쿼리

**커넥션 풀 설정**:
- SQLAlchemy Engine (QueuePool)
- `pool_size=5`, `max_overflow=10`
- `pool_pre_ping=True`: 끊긴 연결 자동 복구
- `pool_recycle=1800`: 30분마다 재생성

**주요 함수**:
- `init_db()`: 테이블 생성 (IF NOT EXISTS)
- `ensure_user(user_id)`: 사용자 존재 보장
- `insert_capture(...)`: 캡처 데이터 삽입
- `list_all_encoding_paths()`: 모든 인코딩 경로 조회
- `get_all_registered_users()`: 등록된 사용자 목록 (name, encoding_path)
- `delete_user_all(user_id)`: 사용자 및 샘플 삭제

---

## 🧪 테스트 방법

### 1. API 테스트 (curl 예시)

**얼굴 등록**:
```bash
curl -X POST http://localhost:8000/capture/ \
  -H "Content-Type: application/json" \
  -d '{"name": "홍길동", "preview": "1"}'
```

**얼굴 인식**:
```bash
curl -X POST http://localhost:8000/capture/identify \
  -H "Content-Type: application/json" \
  -d '{"timeout_sec": 5.0}'
```

### 2. 프리뷰 모드 테스트
1. `preview=1` 옵션으로 API 호출
2. OpenCV 윈도우에서 얼굴 박스 확인
3. 'C' 키를 눌러 캡처
4. 자동으로 이미지/인코딩 저장

### 3. 데이터 확인
```bash
# 저장된 이미지 확인
ls face_data/images/

# 인코딩 파일 확인
ls face_data/encodings/

# DB 확인
mysql -u face_user -p face_api
SELECT * FROM face_captures;
```

---

## 🐛 알려진 이슈

### 1. face_recognition 패키지 미설치
**증상**: `ModuleNotFoundError: No module named 'face_recognition'`  
**원인**: pip list에는 없지만 코드에서 import 시도  
**해결**: `pip install face-recognition` (dlib 의존성 주의)

### 2. 카메라 열기 실패
**증상**: `CameraOpenError: cannot open camera index 0`  
**원인**: 카메라가 다른 앱에서 사용 중이거나 드라이버 문제  
**해결**:
- 다른 카메라 앱 종료 (Zoom, Teams 등)
- `device_index=1` 시도 (외장 USB 카메라)
- 카메라 드라이버 재설치

### 3. DB 테이블 불일치
**증상**: `table 'face_captures' doesn't exist`  
**원인**: DDL은 `users`/`samples` 구조, 코드는 `face_captures` 사용  
**해결**: 테이블 스키마 통일 필요 (아래 참고)

**임시 해결 SQL**:
```sql
CREATE TABLE face_captures (
  capture_id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128),
  image_path VARCHAR(512) NOT NULL,
  encoding_path VARCHAR(512),
  captured_at BIGINT NOT NULL,
  KEY idx_captured_at (captured_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 📝 개발 과정 및 기록

### Git 초기 설정
```bash
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin <repository-url>
git push -u origin main
```

### 프로젝트 히스토리
- **2025.01**: 프로젝트 초기 구조 설계
- 얼굴 인코딩 파일 30+ 개 생성 (face_data/encodings/)
- Flask API 서버 구현 (capture, identify 엔드포인트)
- OpenCV 카메라 제어 로직 구현 (프리뷰 모드 포함)
- MariaDB 연동 및 SQLAlchemy 커넥션 풀 설정

### 개선 예정 사항
- [ ] face_recognition 패키지 정상 설치 및 테스트
- [ ] DB 테이블 스키마 통일 (`face_captures` vs `users`/`samples`)
- [ ] CNN 모델 옵션 추가 (더 정확한 얼굴 감지)
- [ ] 출퇴근 기록 테이블 추가 (`attendance` 테이블)
- [ ] 관리자 웹 UI 구현 (사용자 목록, 출퇴근 기록 조회)
- [ ] Docker 컨테이너화
- [ ] 단위 테스트 및 CI/CD 파이프라인 구축

---

## 📚 참고 자료

- [face_recognition 공식 문서](https://github.com/ageitgey/face_recognition)
- [OpenCV Python 튜토리얼](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)

---

## 📄 라이선스
MIT License

---

## 👥 기여자
- 개발자: JHKIM
- 개발 환경: Windows + Python 3.13

---

**마지막 업데이트**: 2025년 11월 8일
