import os, time, uuid
import numpy as np
import cv2
import face_recognition
from typing import List, Tuple, Dict
from config import Config
from db import insert_capture, list_all_encoding_paths
from typing import Optional

""" 얼굴 인코딩 추출 """
def detect_and_encode_bgr(bgr_img) -> Tuple[List[Tuple[int, int, int, int]], List[np.ndarray]]:
    """
    입력: BGR 이미지(OpenCV)
    출력: (얼굴 박스들, 얼굴 인코딩들)
    """
    rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model="hog")  # 'cnn' 더 정확하지만 느림
    encs  = face_recognition.face_encodings(rgb, boxes)
    return boxes, encs

""" 촬영 결과 저장 (이름은 옵션) """
def save_capture(bgr_img, enc: Optional[np.ndarray], name: Optional[str] = None) -> str:
    ts = int(time.time())
    capture_id = str(uuid.uuid4())

    existing_files = [f for f in os.listdir(Config.IMG_DIR) if f.startswith(name + "_")]
    serial_num = len(existing_files) + 1

    # 파일 저장
    img_name = f"{name}_{serial_num}.jpg"
    img_path = os.path.join(Config.IMG_DIR, img_name)
    cv2.imwrite(img_path, bgr_img)

    enc_path = None
    if enc is not None:
        enc_name = f"{ts}_{capture_id}.npy"
        enc_path = os.path.join(Config.ENC_DIR, enc_name)
        np.save(enc_path, enc)

    # DB 기록 (user_id 없음)
    insert_capture(capture_id, name, img_path, enc_path, ts)
    return capture_id


""" 모든 임베딩 로드 (인증/매칭용 캐시 구성 시 사용) """
def load_all_encodings() -> List[np.ndarray]:
    paths = list_all_encoding_paths()  # [".../xxx.npy", ...]
    out: List[np.ndarray] = []
    for p in paths:
        try:
            out.append(np.load(p))
        except Exception:
            # 손상/누락 파일은 건너뜀
            pass
    return out