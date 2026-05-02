import logging
import threading
import os
from datetime import datetime, timedelta

import cv2
import numpy as np
from django.db import transaction
from main.src.generate_patches import CropImage
from main import facenet
from main.models import Classroom, Attendance, StudentInfo, StudentClassDetails
from main.model_registry import get_registry

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Shared image cropper (stateless utility — safe to reuse across streams)
image_cropper = CropImage()

# How many camera frames to skip between full inference cycles.
# 0 = process every frame; 2 = process every 3rd frame (recommended for CPU).
FRAME_SKIP = 2

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
# MJPEG streaming generator — optimised face recognition loop
# ---------------------------------------------------------------------------
def main(id_subject):
    """
    Yields MJPEG frames.  Key optimisations vs. the original:

    1. All AI models come from the process-level ModelRegistry singleton —
       no FaceNet reload, no repeated torch.load().
    2. Frame skipping (FRAME_SKIP): full inference runs on every
       (FRAME_SKIP + 1)-th frame; intermediate frames are yielded as-is with
       the last known annotations painted on.  Set FRAME_SKIP=0 to disable.
    3. DB write is dispatched to a daemon thread so it never blocks the stream.
    4. Absent-seeding (expensive N×get_or_create) is deferred to the background
       thread alongside insert_attendance, not blocking the hot loop.
    """
    INPUT_IMAGE_SIZE = 160

    logger.info("[STREAM] Starting face-recognition stream | classroom_id=%s", id_subject)

    # Obtain the shared model registry (loaded once; subsequent calls are instant)
    registry = get_registry()
    model = registry.classifier
    class_names = registry.class_names

    cap = _open_camera()
    if cap is None:
        logger.error("[STREAM] Cannot open camera | classroom_id=%s", id_subject)
        return

    # Per-stream state
    current_face_name = ""
    current_face_progress = 0
    justscanned = False
    recognized_names: list[str] = []
    last_saved_student_name = ""
    save_display_frames_left = 0

    # Frame skip counter — counts frames since last inference
    skip_counter = 0

    # Cache last bbox so skipped frames can still draw the box
    last_bbox: list[int] | None = None
    last_label_is_spoof = False

    consecutive_read_failures = 0
    MAX_CONSECUTIVE_READ_FAILURES = 30

    while cap is not None and cap.isOpened():
        isSuccess, frame = cap.read()
        if not isSuccess:
            consecutive_read_failures += 1
            if consecutive_read_failures % 10 == 0:
                logger.warning(
                    "[STREAM] Failed to read frame | classroom_id=%s | consecutive=%d",
                    id_subject, consecutive_read_failures,
                )
            if consecutive_read_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                logger.error("[STREAM] Reopening camera | classroom_id=%s", id_subject)
                try:
                    cap.release()
                except Exception:
                    pass
                cap = _open_camera()
                consecutive_read_failures = 0
            continue

        consecutive_read_failures = 0

        # ----------------------------------------------------------------
        # Frame-skip: only run expensive ML every (FRAME_SKIP+1) frames.
        # Skipped frames get the previous bbox drawn but skip detection.
        # ----------------------------------------------------------------
        skip_counter += 1
        run_inference = skip_counter > FRAME_SKIP
        if run_inference:
            skip_counter = 0

        if not run_inference:
            # Re-draw last known annotations cheaply
            if last_bbox is not None:
                color = (0, 255, 255) if last_label_is_spoof else (0, 255, 0)
                bx, by, bw, bh = last_bbox
                cv2.rectangle(frame, (bx, by - 10), (bx + bw, by + bh), color, 2)
            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            continue

        # ----------------------------------------------------------------
        # Full inference cycle
        # ----------------------------------------------------------------
        image_bbox = registry.get_bbox(frame)

        if image_bbox is None:
            last_bbox = None
            logger.debug(
                "[STREAM] No face detected | classroom_id=%s | ts=%s",
                id_subject, datetime.now().strftime("%H:%M:%S"),
            )
            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            continue

        last_bbox = image_bbox
        frame_h, frame_w = frame.shape[:2]

        # Bounds-safe crop coordinates for face recognition
        bx = max(0, image_bbox[0])
        by = max(0, image_bbox[1])
        bx2 = min(frame_w, image_bbox[0] + image_bbox[2])
        by2 = min(frame_h, image_bbox[1] + image_bbox[3])

        # ----------------------------------------------------------------
        # Liveness / anti-spoof check
        # ----------------------------------------------------------------
        prediction = registry.predict_antispoof(frame, image_bbox, image_cropper)
        label = int(np.argmax(prediction))
        value = float(prediction[0][label]) / len(registry.antispoof_models)
        last_label_is_spoof = label != 1

        if label != 1:
            logger.warning(
                "[STREAM] Liveness FAILED (spoof) | classroom_id=%s | score=%.3f",
                id_subject, value,
            )
            color = (0, 255, 255)
            cv2.rectangle(
                frame,
                (image_bbox[0], max(0, image_bbox[1] - 50)),
                (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),
                color, 2,
            )
            cv2.putText(
                frame, "Gia mao !!!", (image_bbox[0], image_bbox[1]),
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, color, thickness=1, lineType=2,
            )
            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            continue

        logger.debug(
            "[STREAM] Liveness OK | classroom_id=%s | score=%.3f", id_subject, value
        )

        # ----------------------------------------------------------------
        # Face recognition (FaceNet + sklearn)
        # ----------------------------------------------------------------
        cropped = frame[by:by2, bx:bx2, :]
        if cropped is None or cropped.size == 0:
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            continue

        scaled = cv2.resize(cropped, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE), interpolation=cv2.INTER_LINEAR)
        scaled = cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)
        scaled = facenet.prewhiten(scaled)
        scaled_reshape = scaled.reshape(-1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE, 3)

        emb_array = registry.get_embedding(scaled_reshape)

        probs = model.predict_proba(emb_array)
        best_idx = int(np.argmax(probs, axis=1)[0])
        confidence = float(probs[0, best_idx])
        pkl_name = class_names[best_idx]
        best_name = PKL_TO_DB_STUDENT_ID.get(pkl_name, pkl_name)

        logger.info(
            "[RECOGNITION] pkl=%s db=%s conf=%.4f threshold=%.2f | classroom=%s",
            pkl_name, best_name, confidence, CONFIDENCE_THRESHOLD, id_subject,
        )

        # ----------------------------------------------------------------
        # Confidence gate
        # ----------------------------------------------------------------
        if confidence < CONFIDENCE_THRESHOLD:
            current_face_name = "UNKNOWN"
            current_face_progress = 0
            justscanned = False
            cv2.rectangle(frame, (bx, by), (bx2, by2), (0, 200, 0), 2)
            cv2.putText(
                frame, "UNKNOWN", (bx, by2 + 20),
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255), 1, 2,
            )
            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            continue

        # ----------------------------------------------------------------
        # Already saved this session
        # ----------------------------------------------------------------
        if best_name in recognized_names:
            cv2.rectangle(frame, (bx, by), (bx2, by2), (0, 0, 255), 2)
            cv2.putText(
                frame, f"{best_name} da diem danh.", (bx, by - 10),
                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1, 2,
            )
            if save_display_frames_left > 0:
                draw_save_overlay(frame, last_saved_student_name)
                save_display_frames_left -= 1
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            continue

        # ----------------------------------------------------------------
        # Stable-frame accumulation
        # ----------------------------------------------------------------
        if current_face_name != best_name:
            current_face_name = best_name
            current_face_progress = 0
            justscanned = False
        elif not justscanned:
            current_face_progress += 1
            progress = current_face_progress / STABLE_FRAME_REQUIREMENT
            draw_progress_bar(frame, progress, bx, by, bx2, by2)

        cv2.rectangle(frame, (bx, by), (bx2, by2), (0, 255, 0), 2)
        cv2.putText(
            frame, best_name, (bx, by2 + 20),
            cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255), 1, 2,
        )
        cv2.putText(
            frame, f"{confidence:.3f}", (bx, by2 + 37),
            cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255), 1, 2,
        )

        # ----------------------------------------------------------------
        # Trigger DB save — dispatched to a background thread so the stream
        # generator is never blocked by the attendance transaction.
        # ----------------------------------------------------------------
        if current_face_progress >= STABLE_FRAME_REQUIREMENT and not justscanned:
            justscanned = True
            recognized_names.append(best_name)
            logger.info(
                "[ATTENDANCE] Triggering save | classroom=%s | student=%s | conf=%.4f",
                id_subject, best_name, confidence,
            )

            # Compute status before handing off (cheap; avoids race on datetime)
            now_ts = datetime.now()
            try:
                classroom_obj = Classroom.objects.get(pk=id_subject)
                diff = (
                    datetime.combine(now_ts.date(), now_ts.time())
                    - datetime.combine(now_ts.date(), classroom_obj.begin_time)
                )
                attendance_status = 3 if diff.total_seconds() > 900 else 2
            except Exception:
                attendance_status = 2

            try:
                student_name = StudentInfo.objects.get(pk=best_name).student_name
            except Exception:
                student_name = best_name

            # Update in-memory cache immediately so the UI shows it now
            add_pending_attendance(id_subject, best_name, student_name, attendance_status)

            # DB write runs in a daemon thread — stream is never stalled
            _student_id_snap = best_name
            _classroom_id_snap = id_subject
            t = threading.Thread(
                target=_save_attendance_bg,
                args=(_classroom_id_snap, _student_id_snap),
                daemon=True,
            )
            t.start()

            last_saved_student_name = best_name
            save_display_frames_left = 40

        if save_display_frames_left > 0:
            draw_save_overlay(frame, last_saved_student_name)
            save_display_frames_left -= 1

        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"

    cap.release()
    logger.info("[STREAM] Stream ended | classroom_id=%s", id_subject)


def _save_attendance_bg(classroom_id, student_id):
    """Run insert_attendance in a daemon thread; errors are logged, not raised."""
    try:
        result = insert_attendance(classroom_id, student_id)
        logger.info("[ATTENDANCE] Background save done: %s", result)
    except Exception as exc:
        logger.exception(
            "[ATTENDANCE] Background save failed | classroom=%s | student=%s | error=%s",
            classroom_id, student_id, exc,
        )
