import logging
import pickle
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import os
import cv2
import imutils
import numpy as np
import tensorflow as tf
from imutils.video import VideoStream
from django.db import transaction
from main.src.anti_spoof_predict import AntiSpoofPredict
from main.src.generate_patches import CropImage
from main.src.utility import parse_model_name
from main import facenet
from main.align import detect_face
from main.models import Classroom, Attendance, StudentInfo, StudentClassDetails
import warnings

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Suppress noisy TF / sklearn warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

model_test = AntiSpoofPredict(0)
image_cropper = CropImage()
model_dir = "main/resources/anti_spoof_models"

# ---------------------------------------------------------------------------
# In-memory cache: "just recognized" students (before DB commit completes)
# Key: (classroom_id, student_id), Value: {timestamp, status, student_name}
# TTL: 10 seconds (sau đó sẽ có từ DB)
# ---------------------------------------------------------------------------
_PENDING_ATTENDANCE_CACHE = {}
_CACHE_LOCK = threading.Lock()


def add_pending_attendance(classroom_id, student_id, student_name, status):
    """Thêm vào cache ngay khi nhận diện xong, trước khi ghi DB."""
    with _CACHE_LOCK:
        key = (classroom_id, student_id)
        _PENDING_ATTENDANCE_CACHE[key] = {
            "timestamp": datetime.now(),
            "student_id": student_id,
            "student_name": student_name,
            "attendance_status": status,
        }
    logger.debug("[CACHE] Added pending attendance | classroom_id=%s | student_id=%s", classroom_id, student_id)


def get_pending_attendance_for_classroom(classroom_id):
    """Lấy danh sách pending từ cache (chưa expire)."""
    now = datetime.now()
    TTL_SECONDS = 10
    with _CACHE_LOCK:
        result = []
        expired_keys = []
        for key, val in _PENDING_ATTENDANCE_CACHE.items():
            cid, sid = key
            if cid != classroom_id:
                continue
            age = (now - val["timestamp"]).total_seconds()
            if age > TTL_SECONDS:
                expired_keys.append(key)
                continue
            result.append(val)
        # Dọn dẹp expired
        for k in expired_keys:
            del _PENDING_ATTENDANCE_CACHE[k]
    return result

# ---------------------------------------------------------------------------
# Mapping: pkl class_names (folder names used during training)
#          → actual id_student values stored in PostgreSQL.
#
# Root cause of StudentInfo.DoesNotExist errors:
#   Training folders were named "2","3","4","12" (no leading zero),
#   but DB stores student IDs as "02","03","04".
#   Add/update this dict whenever the model is retrained.
# ---------------------------------------------------------------------------
PKL_TO_DB_STUDENT_ID: dict[str, str] = {
    "2":  "02",
    "3":  "03",
    "4":  "04",
    "12": "12",   # no leading-zero counterpart in DB — keep as-is
}

# Minimum confidence to accept a recognition result
CONFIDENCE_THRESHOLD = 0.8

# How many consecutive stable frames required before triggering save
STABLE_FRAME_REQUIREMENT = 10

# How many minutes must pass before the same student can be saved again
DUPLICATE_WINDOW_MINUTES = 5


# ---------------------------------------------------------------------------
# Camera open helper (Windows-friendly)
# ---------------------------------------------------------------------------
def _open_camera():
    """
    Try to open an attached webcam robustly across Windows/OpenCV backends.
    Returns an opened cv2.VideoCapture or None.
    """
    # Allow overriding camera index from env without touching code.
    # Example: set CAMERA_INDEX=1 if the default camera isn't at 0.
    env_idx = os.getenv("CAMERA_INDEX")
    preferred_indices = []
    if env_idx is not None:
        try:
            preferred_indices.append(int(env_idx))
        except ValueError:
            logger.warning("[STREAM] Invalid CAMERA_INDEX=%s (must be int)", env_idx)
    preferred_indices += [0, 1, 2]

    # Prefer Windows backends that tend to work better with webcams.
    preferred_backends = []
    if hasattr(cv2, "CAP_DSHOW"):
        preferred_backends.append(cv2.CAP_DSHOW)
    if hasattr(cv2, "CAP_MSMF"):
        preferred_backends.append(cv2.CAP_MSMF)
    preferred_backends.append(None)  # OpenCV default fallback

    for idx in preferred_indices:
        for backend in preferred_backends:
            try:
                cap = cv2.VideoCapture(idx) if backend is None else cv2.VideoCapture(idx, backend)
                if cap is not None and cap.isOpened():
                    # Reduce latency; some drivers ignore these but harmless.
                    try:
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    except Exception:
                        pass
                    logger.info("[STREAM] Camera opened | index=%s | backend=%s", idx, backend)
                    return cap
            except Exception as exc:
                logger.debug("[STREAM] VideoCapture failed | index=%s | backend=%s | error=%s", idx, backend, exc)

    logger.error("[STREAM] Cannot open any camera | tried_indices=%s", preferred_indices)
    return None


# ---------------------------------------------------------------------------
# Progress bar helper
# ---------------------------------------------------------------------------
def draw_progress_bar(frame, progress, x, y, w, h):
    bar_width = 150
    bar_height = 20
    bar_x = x
    bar_y = y - 20
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (0, 0, 0), -1)
    filled_width = int(bar_width * progress)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), (0, 255, 0), -1)


def draw_save_overlay(frame, student_name):
    """Vẽ overlay 'Đã lưu' góc trên trái khi vừa ghi attendance."""
    cv2.putText(
        frame,
        f"Da luu: {student_name}",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 255, 0),
        3,
    )


# ---------------------------------------------------------------------------
# Attendance persistence
# ---------------------------------------------------------------------------
def insert_attendance(id_classroom, student_id):
    """
    Mark all enrolled students absent (status=1) if not yet recorded today,
    then mark the recognised student as present (2) or late (3).

    Returns a short status string for the caller to log.
    """
    ts = datetime.now()
    logger.info(
        "[ATTENDANCE] insert_attendance called | classroom_id=%s | student_id=%s | timestamp=%s",
        id_classroom, student_id, ts.strftime("%Y-%m-%d %H:%M:%S"),
    )

    classroom = Classroom.objects.get(pk=id_classroom)
    begin_time = classroom.begin_time

    # Determine late vs present (> 15 minutes = late)
    time_difference = (
        datetime.combine(ts.date(), ts.time()) - datetime.combine(ts.date(), begin_time)
    )
    attendance_status = 3 if time_difference.total_seconds() > 900 else 2

    # ------------------------------------------------------------------
    # BUG FIX: StudentInfo has no 'classroom' field.
    # Use StudentClassDetails as the join table instead.
    # ------------------------------------------------------------------
    enrolled_details = StudentClassDetails.objects.filter(id_classroom=classroom).select_related("id_student")
    logger.debug(
        "[ATTENDANCE] Seeding absent records | classroom_id=%s | enrolled_count=%d",
        id_classroom, enrolled_details.count(),
    )

    with transaction.atomic():
        for detail in enrolled_details:
            student = detail.id_student
            Attendance.objects.get_or_create(
                id_student=student,
                id_classroom=classroom,
                check_in_time__date=ts.date(),
                defaults={
                    "check_in_time": ts,
                    "attendance_status": 1,  # default: absent
                },
            )

    # ------------------------------------------------------------------
    # 5-minute duplicate guard: check DB for recent record
    # ------------------------------------------------------------------
    try:
        student_info = StudentInfo.objects.get(id_student=student_id)
    except StudentInfo.DoesNotExist:
        logger.error(
            "[ATTENDANCE] Student not found | student_id=%s | classroom_id=%s",
            student_id, id_classroom,
        )
        return "ERROR: student not found"

    cutoff = ts - timedelta(minutes=DUPLICATE_WINDOW_MINUTES)
    recent = Attendance.objects.filter(
        id_student=student_info,
        id_classroom=classroom,
        check_in_time__gte=cutoff,
        attendance_status__in=[2, 3],  # only count real check-ins, not defaults
    ).first()

    if recent:
        logger.info(
            "[ATTENDANCE] Duplicate within %d min — skipping | student_id=%s | classroom_id=%s | last_check_in=%s",
            DUPLICATE_WINDOW_MINUTES, student_id, id_classroom,
            recent.check_in_time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return f"DUPLICATE_SKIP: {student_id}"

    # ------------------------------------------------------------------
    # Persist the recognised student's attendance
    # ------------------------------------------------------------------
    logger.info(
        "[ATTENDANCE] Saving attendance | student_id=%s | classroom_id=%s | status=%d | timestamp=%s",
        student_id, id_classroom, attendance_status, ts.strftime("%Y-%m-%d %H:%M:%S"),
    )

    try:
        with transaction.atomic():
            attendance, created = Attendance.objects.get_or_create(
                id_student=student_info,
                id_classroom=classroom,
                check_in_time__date=ts.date(),
                defaults={
                    "check_in_time": ts,
                    "attendance_status": attendance_status,
                },
            )

            if not created:
                attendance.check_in_time = ts
                attendance.attendance_status = attendance_status
                attendance.save()

        action = "CREATED" if created else "UPDATED"
        logger.info(
            "[ATTENDANCE] DB commit OK | action=%s | student_id=%s | classroom_id=%s | status=%d",
            action, student_id, id_classroom, attendance_status,
        )
        return f"OK:{action}:{student_id}:status={attendance_status}"

    except Exception as exc:
        logger.exception(
            "[ATTENDANCE] DB write failed | student_id=%s | classroom_id=%s | error=%s",
            student_id, id_classroom, exc,
        )
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# MJPEG streaming generator — face recognition loop
# ---------------------------------------------------------------------------
def main(id_subject):
    INPUT_IMAGE_SIZE = 160
    CLASSIFIER_PATH = "main/Models/facemodel.pkl"
    FACENET_MODEL_PATH = "main/Models/20180402-114759.pb"

    logger.info("[STREAM] Starting face-recognition stream | classroom_id=%s", id_subject)

    with open(CLASSIFIER_PATH, "rb") as file:
        model, class_names = pickle.load(file)
    logger.info("[STREAM] Classifier loaded | classes=%d", len(class_names))

    facenet.load_model(FACENET_MODEL_PATH)
    graph = tf.compat.v1.get_default_graph()
    images_placeholder = graph.get_tensor_by_name("input:0")
    embeddings = graph.get_tensor_by_name("embeddings:0")
    phase_train_placeholder = graph.get_tensor_by_name("phase_train:0")

    logger.info("[STREAM] FaceNet model loaded")

    cap = _open_camera()
    if cap is None:
        logger.error("[STREAM] Cannot open camera | classroom_id=%s", id_subject)
        return

    global justscanned, pause_cnt
    justscanned = False
    pause_cnt = 0
    current_face_name = ""
    current_face_progress = 0

    # In-memory set of student IDs already saved this session
    recognized_names = []

    # Overlay "Đã lưu" sau khi ghi attendance thành công
    last_saved_student_name = ""
    save_display_frames_left = 0

    sess = tf.compat.v1.Session(graph=graph)
    consecutive_read_failures = 0
    MAX_CONSECUTIVE_READ_FAILURES = 30

    while cap is not None and cap.isOpened():
        isSuccess, frame = cap.read()
        if not isSuccess:
            consecutive_read_failures += 1
            if consecutive_read_failures % 10 == 0:
                logger.warning(
                    "[STREAM] Failed to read frame | classroom_id=%s | consecutive=%d",
                    id_subject, consecutive_read_failures
                )

            # If camera becomes busy/disconnected, try reopening.
            if consecutive_read_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                logger.error("[STREAM] Reopening camera after read failures | classroom_id=%s", id_subject)
                try:
                    cap.release()
                except Exception:
                    pass
                cap = _open_camera()
                consecutive_read_failures = 0
            continue

        consecutive_read_failures = 0

        image_bbox = model_test.get_bbox(frame)

        # ----------------------------------------------------------------
        # No face detected
        # ----------------------------------------------------------------
        if image_bbox is None:
            logger.debug("[STREAM] No face detected | classroom_id=%s | timestamp=%s",
                         id_subject, datetime.now().strftime("%H:%M:%S"))
            # Vẫn hiển thị overlay "Đã lưu" nếu còn frames
            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1

            ret, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            continue

        # ----------------------------------------------------------------
        # Face detected — run liveness check
        # ----------------------------------------------------------------
        frame_h, frame_w = frame.shape[:2]
        x = max(0, image_bbox[0])
        y = max(0, image_bbox[1] - 50)
        w = min(frame_w, image_bbox[0] + image_bbox[2])
        h = min(frame_h, image_bbox[1] + image_bbox[3])

        logger.debug("[STREAM] Face bbox detected | classroom_id=%s | bbox=[%d,%d,%d,%d]",
                     id_subject, x, y, w, h)

        prediction = np.zeros((1, 3))
        for model_name in os.listdir(model_dir):
            h_input, w_input, model_type, scale = parse_model_name(model_name)
            param = {
                "org_img": frame,
                "bbox": image_bbox,
                "scale": scale,
                "out_w": w_input,
                "out_h": h_input,
                "crop": True,
            }
            if scale is None:
                param["crop"] = False
            img = image_cropper.crop(**param)
            prediction += model_test.predict(img, os.path.join(model_dir, model_name))

        label = np.argmax(prediction)
        value = prediction[0][label] / 2

        if label != 1:
            # Liveness check failed — spoof detected
            logger.warning("[STREAM] Liveness FAILED (spoof) | classroom_id=%s | score=%.3f",
                           id_subject, value)
            result_text = "Gia mao !!!"
            color = (0, 255, 255)
            cv2.rectangle(frame, (image_bbox[0], image_bbox[1] - 50),
                          (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),
                          color, 2)
            cv2.putText(frame, result_text, (image_bbox[0], image_bbox[1]),
                        cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, color, thickness=1, lineType=2)

            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1

            ret, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            continue

        # ----------------------------------------------------------------
        # Liveness passed — run face recognition
        # ----------------------------------------------------------------
        logger.debug("[STREAM] Liveness OK | classroom_id=%s | liveness_score=%.3f", id_subject, value)

        cropped = frame[y:h, x:w, :]
        if cropped is None or cropped.size == 0:
            logger.warning("[STREAM] Cropped face region is empty | classroom_id=%s", id_subject)
            ret, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            continue

        scaled = cv2.resize(cropped, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE),
                            interpolation=cv2.INTER_CUBIC)
        scaled = cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)
        scaled = facenet.prewhiten(scaled)
        scaled_reshape = scaled.reshape(-1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE, 3)

        feed_dict = {images_placeholder: scaled_reshape, phase_train_placeholder: False}
        emb_array = sess.run(embeddings, feed_dict=feed_dict)

        predictions = model.predict_proba(emb_array)
        best_class_indices = np.argmax(predictions, axis=1)
        best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
        pkl_name = class_names[best_class_indices[0]]
        # Translate pkl folder name → real DB student ID
        best_name = PKL_TO_DB_STUDENT_ID.get(pkl_name, pkl_name)
        confidence = float(best_class_probabilities[0])

        logger.info(
            "[RECOGNITION] Result | classroom_id=%s | pkl_name=%s | db_student_id=%s | confidence=%.4f | threshold=%.2f | timestamp=%s",
            id_subject, pkl_name, best_name, confidence, CONFIDENCE_THRESHOLD,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        # ----------------------------------------------------------------
        # Confidence gate (>= 0.8)
        # ----------------------------------------------------------------
        if confidence < CONFIDENCE_THRESHOLD:
            current_face_name = "UNKNOWN"
            current_face_progress = 0
            justscanned = False
            logger.debug(
                "[RECOGNITION] Below threshold — marking UNKNOWN | student_id=%s | confidence=%.4f",
                best_name, confidence,
            )
            cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)
            cv2.putText(frame, "UNKNOWN", (x, h + 20), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                        1, (255, 255, 255), thickness=1, lineType=2)

            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1

            ret, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            continue

        # ----------------------------------------------------------------
        # Already saved this session
        # ----------------------------------------------------------------
        if best_name in recognized_names:
            message = f"{best_name} da diem danh."
            logger.debug("[RECOGNITION] Already recorded this session | student_id=%s", best_name)
            cv2.rectangle(frame, (x, y), (w, h), (0, 0, 255), 2)
            cv2.putText(frame, message, (x, y - 10), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                        1, (0, 0, 255), thickness=1, lineType=2)

            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1

            ret, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            continue

        # ----------------------------------------------------------------
        # Stable frame accumulation
        # ----------------------------------------------------------------
        if current_face_name != best_name:
            logger.debug("[RECOGNITION] Face changed: %s → %s | resetting progress",
                         current_face_name, best_name)
            current_face_name = best_name
            current_face_progress = 0
            justscanned = False
        elif not justscanned:
            current_face_progress += 1
            progress = current_face_progress / STABLE_FRAME_REQUIREMENT
            draw_progress_bar(frame, progress, x, y, w, h)
            logger.debug(
                "[RECOGNITION] Stable frame %d/%d | student_id=%s | confidence=%.4f",
                current_face_progress, STABLE_FRAME_REQUIREMENT, best_name, confidence,
            )

        cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)
        cv2.putText(frame, best_name, (x, h + 20), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    1, (255, 255, 255), thickness=1, lineType=2)
        cv2.putText(frame, str(round(confidence, 3)), (x, h + 37),
                    cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255), thickness=1, lineType=2)

        # ----------------------------------------------------------------
        # Trigger DB save after STABLE_FRAME_REQUIREMENT consecutive frames
        # ----------------------------------------------------------------
        if current_face_progress >= STABLE_FRAME_REQUIREMENT:
            justscanned = True
            recognized_names.append(best_name)
            logger.info(
                "[ATTENDANCE] Triggering save | classroom_id=%s | student_id=%s | confidence=%.4f | timestamp=%s",
                id_subject, best_name, confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            # Xác định status (đúng giờ / trễ) để thêm vào cache
            try:
                classroom_obj = Classroom.objects.get(pk=id_subject)
                begin_time = classroom_obj.begin_time
                now_ts = datetime.now()
                time_difference = (
                    datetime.combine(now_ts.date(), now_ts.time()) - datetime.combine(now_ts.date(), begin_time)
                )
                attendance_status = 3 if time_difference.total_seconds() > 900 else 2
            except Exception:
                attendance_status = 2  # Fallback

            # Lấy tên sinh viên từ DB để cache có đầy đủ info
            try:
                student_obj = StudentInfo.objects.get(pk=best_name)
                student_name = student_obj.student_name
            except Exception:
                student_name = best_name  # Fallback

            # ĐƯA VÀO CACHE NGAY (trước khi ghi DB) → UI thấy ngay lập tức
            add_pending_attendance(id_subject, best_name, student_name, attendance_status)
            logger.info("[ATTENDANCE] Added to pending cache | student_id=%s | status=%d", best_name, attendance_status)

            # Sau đó mới ghi DB (có thể chậm hơn do transaction)
            result = insert_attendance(id_subject, best_name)
            logger.info("[ATTENDANCE] insert_attendance returned: %s", result)

            # Hiển thị overlay "Đã lưu" trong 40 frames tiếp theo (~1-2s tùy FPS)
            last_saved_student_name = best_name
            save_display_frames_left = 40

        # Overlay "Đã lưu" nếu vừa save xong
        if save_display_frames_left > 0:
            draw_save_overlay(frame, last_saved_student_name)
            save_display_frames_left -= 1

        ret, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

    sess.close()
    cap.release()
    cv2.destroyAllWindows()
    logger.info("[STREAM] Stream ended | classroom_id=%s", id_subject)
