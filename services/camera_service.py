import time
import cv2
from typing import Tuple, Dict, Optional
from services.face_service import detect_and_encode_bgr, save_capture
from db import list_user_encoding_paths, get_all_registered_users
import numpy as np

"""예외 정의 """
class CameraOpenError(Exception): ...
class FaceTimeoutError(Exception): ...
class MultiFaceError(Exception): ...
class NoFaceError(Exception): ...


def identify_user(device_index: int = 0, timeout_sec: float = 5.0, min_width: int = 320, tolerance: float = 0.45) -> dict:
    """
    실시간으로 얼굴 캡처 → 등록된 얼굴들과 비교 → 사용자 식별
    """
    print(f"[identify] open camera index={device_index}")
    cap = _open_camera(device_index)
    if cap is None or not cap.isOpened():
        raise Exception("카메라를 열 수 없습니다")

    try:
        _warmup(cap, 3)

        # 🔹 새 얼굴 캡처
        frame, enc_new, faces_found = _find_single_face_frame(cap, timeout_sec, min_width)
        if faces_found != 1:
            return {"status": "fail", "reason": "no_face_or_multiple"}

        # 🔹 DB에서 모든 등록된 사용자 인코딩 불러오기
        registered = get_all_registered_users()  # [(name, enc_path), ...]
        print(f"[identify] loaded {len(registered)} encodings")

        best_match = None
        best_dist = 999.0

        for name, enc_path in registered:
            try:
                enc_saved = np.load(enc_path)
            except Exception as e:
                print(f"[identify] skip {enc_path}: {e}")
                continue

            dist = np.linalg.norm(enc_new - enc_saved)
            if dist < best_dist:
                best_dist = dist
                best_match = name

        # 🔹 임계값 비교
        if best_match and best_dist < tolerance:
            print(f"[identify] ✅ matched: {best_match} (distance={best_dist:.3f})")
            return {"status": "success", "user": best_match, "distance": float(best_dist)}
        else:
            print(f"[identify] ❌ unknown face (min_dist={best_dist:.3f})")
            return {"status": "unknown", "distance": float(best_dist)}

    finally:
        cap.release()




"""카메라 실행 및 얼굴 캡처 관련 서비스 로직 """
def _open_camera(device_index: int) -> cv2.VideoCapture:
    
    # 1) CAP_ANY (자동) → 2) MSMF → 3) DSHOW
    for api, label in [(cv2.CAP_ANY, "ANY"), (cv2.CAP_MSMF, "MSMF"), (cv2.CAP_DSHOW, "DSHOW")]:
        try:
            cap = cv2.VideoCapture(device_index, api)
        except Exception:
            cap = cv2.VideoCapture(device_index)  # 안전 폴백
            label = "ANY*"

        if cap and cap.isOpened():
            # 첫 프레임을 짧게라도 확인(블록 방지용 타임아웃 포함)
            import time
            end = time.time() + 2.0
            ok = False
            while time.time() < end:
                ok, frame = cap.read()
                if ok and frame is not None:
                    print(f"[camera] opened: idx={device_index}, api={label}, shape={frame.shape}")
                    return cap
                time.sleep(0.05)
            cap.release()

    raise CameraOpenError(f"cannot open camera index {device_index} with ANY/MSMF/DSHOW")


"""카메라 워밍업 """
def _warmup(cap: cv2.VideoCapture, n: int = 3) -> None:
    for _ in range(n):
        cap.read()


"""프레임 크기 조정 (너비 기준) """
def _maybe_resize(frame, min_width: int):
    h, w = frame.shape[:2]
    if w > min_width:
        ratio = min_width / float(w)
        return cv2.resize(frame, (int(w * ratio), int(h * ratio)))
    return frame

"""단일 얼굴 프레임 탐색 """
def _find_single_face_frame(cap: cv2.VideoCapture, timeout_sec: float, min_width: int) -> Tuple:
    start = time.time()
    chosen = None
    faces_found = 0
    while time.time() - start < timeout_sec:
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        frame = _maybe_resize(frame, min_width)
        _, encs = detect_and_encode_bgr(frame)
        if len(encs) == 1:
            chosen = frame
            faces_found = 1
            break
        elif len(encs) > 1:
            # 정책상 단일 얼굴만 허용
            chosen = frame
            faces_found = len(encs)
            # 계속 기다릴지 즉시 실패로 볼지 선택 가능
            # 여기선 계속 기다리다가 결국 실패 처리
    if chosen is None:
        raise FaceTimeoutError(f"no face detected within {timeout_sec} sec")
    # 최종 단일 확인
    _, encs = detect_and_encode_bgr(chosen)
    if len(encs) == 0:
        raise NoFaceError("no face detected")
    if len(encs) > 1:
        raise MultiFaceError("multiple faces detected")
    return chosen, encs[0], faces_found

""" 카메라에서 얼굴 캡처 후 사용자 DB 저장 하는 서비스 로직"""
def capture_and_enroll(device_index: int = 0, timeout_sec: float = 8.0, min_width: int = 320, name: Optional[str] = None, preview: bool = False) -> Dict:
     
    print(f"[camera] open index={device_index}, timeout={timeout_sec}, min_width={min_width}, name={name}, preview={preview}")

    cap = None               # ← 사전 초기화
    frame = None
    enc = None
    faces_found = 0
    cancelled = False

    try:
        cap = _open_camera(device_index)

        if cap is None or not getattr(cap, "isOpened", lambda: False)():
            raise CameraOpenError(f"cannot open camera index {device_index}")
        
        _warmup(cap, 3)
        frame, enc, faces_found = _find_single_face_frame(cap, timeout_sec, min_width)

        # 프리뷰 모드
        if preview:
            deadline = time.time() + 20.0  # 20초간 표시            
            window_name = "Preview"

            # 캡처된 프레임 계속 표시하기
            while time.time() < deadline:
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue      

                # 실시간 얼굴 감지 및 박스 그리기      
                disp = frame.copy()
                boxes, encs = detect_and_encode_bgr(disp)

                # 얼굴 박스 그리기
                for (top, right, bottom, left) in boxes:
                    cv2.rectangle(disp, (left, top), (right, bottom), (0, 255, 0), 2)
                
                cv2.putText(disp, "Press C to CAPTURE, ESC to cancel",(10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                # 프리뷰 표시 (동영상처럼 갱신)
                cv2.imshow(window_name, disp)
                
                key = cv2.waitKey(1) & 0xFF            
                if key == 27:  # ESC
                    cv2.destroyWindow(window_name)
                    break
                if key == ord('c'): # c를 눌렀을 때 캡처
                    if len(encs) == 1:                        
                        enc = encs[0]
                        faces_found = 1
                        cv2.destroyWindow(window_name)
                        break
            cv2.destroyAllWindows()
    finally:
        try:
             if cap is not None and getattr(cap, "isOpened", lambda: False)():
                cap.release()
        except Exception:
            pass
    
    if cancelled or faces_found == 0 or enc is None:
        print("[capture_and_enroll] cancelled or no face detected → skip save")
        return {"status": "cancelled", "faces_in_frame": 0}

    # cap = _open_camera(device_index)
    capture_id = save_capture(frame, enc, name)
    return {"status": "success", "capture_id": capture_id, "faces_in_frame": faces_found}
