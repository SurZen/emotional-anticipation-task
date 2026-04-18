import time, csv, os
from pathlib import Path
import numpy as np
try:
    import cv2
except Exception:
    cv2 = None
try:
    import mediapipe as mp
except Exception:
    mp = None

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / 'experiment' / 'models' / 'face_landmarker.task'

class SimpleMonitor:
    def __init__(self, camera_index=0, max_fps=30.0):
        self.cap = None
        if cv2 is None:
            raise RuntimeError('cv2 not available')
        self.cap = cv2.VideoCapture(camera_index)
        self.frame_period = 1.0 / float(max_fps)
        self._use_tasks = False
        self.face_mesh = None
        if MODEL.exists() and mp is not None and getattr(mp, 'tasks', None) is not None:
            try:
                from mediapipe.tasks.python import vision
                from mediapipe.tasks.python.core import base_options
                BaseOptions = base_options.BaseOptions
                FaceLandmarker = vision.face_landmarker.FaceLandmarker
                FaceLandmarkerOptions = vision.face_landmarker.FaceLandmarkerOptions
                opts = FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(MODEL)), running_mode=vision.face_landmarker.RunningMode.LIVE_STREAM, num_faces=1)
                try:
                    self.face_mesh = FaceLandmarker.create_from_options(opts)
                except Exception:
                    self.face_mesh = FaceLandmarker(opts)
                self._use_tasks = True
                print('Using MediaPipe Tasks model:', MODEL)
            except Exception as e:
                print('Tasks API present but failed to init:', e)
                self.face_mesh = None
        if not self._use_tasks:
            # try cascades
            try:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
                print('Using OpenCV Haar cascades')
            except Exception as e:
                print('No detector available', e)
                self.face_cascade = None
                self.eye_cascade = None

    def sample_seconds(self, seconds=5.0):
        t0 = time.time()
        n=0; n_face=0
        while time.time()-t0 < seconds:
            ok, frame = self.cap.read()
            if not ok or frame is None:
                time.sleep(0.01); continue
            n+=1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if hasattr(self, 'face_cascade') and self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
                if len(faces)>0:
                    n_face+=1
            time.sleep(self.frame_period)
        return {'frames': n, 'faces': n_face}

if __name__=='__main__':
    m = SimpleMonitor()
    stats = m.sample_seconds(5.0)
    outdir = ROOT / 'data' / 'raw'
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f'test_monitor_{int(time.time())}.csv'
    with outpath.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['frames','faces'])
        w.writeheader()
        w.writerow(stats)
    print('Wrote', outpath)
