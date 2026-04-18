"""
Minimal monitor-only pilot to verify camera + MediaPipe face mesh.
Run with the project's venv Python.
"""
import time
import numpy as np
import cv2
import mediapipe as mp

mpfm = mp.solutions.face_mesh
face_mesh = mpfm.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True,
                          min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError('Could not open camera (index 0)')

print('Starting monitor pilot: will run for 8 seconds and print states...')
start = time.time()
try:
    while time.time() - start < 8.0:
        ok, frame = cap.read()
        if not ok:
            print('No frame')
            time.sleep(0.1)
            continue
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)
        if not res.multi_face_landmarks:
            print('NO_FACE')
        else:
            lms = res.multi_face_landmarks[0].landmark
            def lm_xy(i):
                lm = lms[i]
                return np.array([lm.x * w, lm.y * h], dtype=np.float32)
            nose = lm_xy(1)
            l_cheek = lm_xy(234); r_cheek = lm_xy(454)
            forehead = lm_xy(10); chin = lm_xy(152)
            face_w = float(np.linalg.norm(r_cheek - l_cheek))
            face_h = float(np.linalg.norm(chin - forehead))
            cheek_mid = (l_cheek + r_cheek) / 2.0
            fc_mid = (forehead + chin) / 2.0
            yaw_proxy = (nose[0] - cheek_mid[0]) / max(1.0, face_w)
            pitch_proxy = (nose[1] - fc_mid[1]) / max(1.0, face_h)
            iris_left = np.mean([lm_xy(i) for i in range(468, 473)], axis=0)
            iris_right = np.mean([lm_xy(i) for i in range(473, 478)], axis=0)
            iris_center = (iris_left + iris_right) / 2.0
            l_outer = lm_xy(33); l_inner = lm_xy(133); r_outer = lm_xy(362); r_inner = lm_xy(263)
            l_up = lm_xy(159); l_dn = lm_xy(145); r_up = lm_xy(386); r_dn = lm_xy(374)
            eye_left_x = min(l_outer[0], l_inner[0]); eye_right_x = max(r_outer[0], r_inner[0])
            eye_top_y = min(l_up[1], r_up[1]); eye_bot_y = max(l_dn[1], r_dn[1])
            eye_w = max(1.0, eye_right_x - eye_left_x); eye_h = max(1.0, eye_bot_y - eye_top_y)
            iris_lr = (iris_center[0] - eye_left_x) / eye_w
            iris_ud = (iris_center[1] - eye_top_y) / eye_h
            print(f'FACE FOUND: yaw={yaw_proxy:.3f}, pitch={pitch_proxy:.3f}, iris_lr={iris_lr:.3f}, iris_ud={iris_ud:.3f}')
        time.sleep(0.25)
finally:
    cap.release()
    face_mesh.close()
    print('Pilot finished.')
