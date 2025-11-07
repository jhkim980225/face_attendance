# routes/capture.py
from flask import Blueprint, request, jsonify
from services.camera_service import (
    capture_and_enroll, CameraOpenError, FaceTimeoutError, MultiFaceError, NoFaceError, identify_user
)
import traceback

bp = Blueprint("capture", __name__)

def _get(name, default=None):
    data = request.get_json(silent=True) or {}
    return request.args.get(name) or request.form.get(name) or data.get(name, default)

def _get_int(name, default):
    v = _get(name, default)
    try: return int(v)
    except: return default

def _get_float(name, default):
    v = _get(name, default)
    try: return float(v)
    except: return default

@bp.route("/", methods=["POST"], strict_slashes=False)
def capture_and_enroll_route():
    print("<<< Received capture/enroll request")
    

    device_index = _get_int("device_index", 0)
    min_width    = _get_int("min_width", 320)
    timeout_sec  = _get_float("timeout_sec", 8.0)
    preview      = _get("preview", "0") in ("1", "true", "True")
    name         = _get("name", None)

    print(f"test {device_index}, {min_width}, {timeout_sec}, {preview}, {name}")

    try:        
        result = capture_and_enroll(device_index, timeout_sec, min_width, name=name, preview=preview)
        return jsonify({"ok": True, **result})
    except CameraOpenError as e:
        print(f"[CameraOpenError] {e}")
        return jsonify({"ok": False, "error": str(e), "code": "CAMERA_OPEN_ERROR"}), 503
    except (FaceTimeoutError, NoFaceError, MultiFaceError) as e:
        print(f"[FaceError] {e}")
        return jsonify({"ok": False, "error": str(e)}), 422
    except Exception as e:
        print("[Unhandled Exception]", e)
        print(traceback.format_exc())   # ★ 트레이스 찍기
        return jsonify({"ok": False, "error": "internal error"}), 500




@bp.route("/identify", methods=["POST"])
def identify_route():
    result = identify_user()
    return jsonify(result)