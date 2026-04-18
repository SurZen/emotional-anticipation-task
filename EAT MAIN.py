
# MaM_EAT_run.py
# Standalone PsychoPy runner script for the MaM Emotional Anticipation Task (EAT)
# Place this file in the PROJECT ROOT (same level as conditions/, stimuli/, data/)

from __future__ import annotations

import time, csv
from pathlib import Path
from dataclasses import dataclass
import threading
import numpy as np
try:
    import cv2
except Exception:
    cv2 = None

try:
    import mediapipe as mp
except Exception:
    mp = None
import os
from psychopy import visual, core, event, gui

# Automated pilot mode: set environment variable MAM_AUTOPILOT=1 to run non-interactively
AUTOPILOT = os.environ.get("MAM_AUTOPILOT", "0") == "1"

VALID_DECKS = [f"EAT_{i}" for i in range(1, 6)]

CUE_RGB = {
    "green": (0.0, 1.0, 0.0),
    "red": (1.0, 0.0, 0.0),
    "yellow": (1.0, 1.0, 0.0),
}

# fixed response window (seconds) for post-image prompt
RESPONSE_WINDOW = 2.0
DEFAULTS = {
    "participant_id": "P0001",
    "session_id": "S1",
    "deck_id": "EAT_1",
    "choose_deck_each_trial": False,
    "fullscreen": True,
}

OUT_COLS = [
    "participant_id","session_id","deck_id","trial_index","trial",
    "arrow_direction","cue_color","cue_meaning","resolved_valence",
    "image_path","image_category","image_valence",
    "fix_dur","arrow_dur","isi1_dur","cue_dur","anticip_dur","image_dur","iti_dur",
    "arrow_resp_key","arrow_resp_rt","arrow_correct",
    "event_code_arrow","event_code_cue","event_code_image",
    "ts_fix_on","ts_arrow_on","ts_cue_on","ts_anticip_on","ts_image_on","ts_trial_end",
]

# Compliance output fields (webcam-based, optional)
OUT_COLS += [
    "stim_compliance_pct",
    "stim_face_present_pct",
    "stim_mean_score",
    "stim_mean_yaw_proxy",
    "stim_mean_pitch_proxy",
]


@dataclass
class ComplianceState:
        timestamp: float = 0.0
        face_found: bool = False
        compliant: bool = False
        score: float = 0.0
        yaw_proxy: float = 0.0
        pitch_proxy: float = 0.0
        iris_lr: float = 0.5
        iris_ud: float = 0.5
        reason: str = "INIT"


class WebcamComplianceMonitor:
    def __init__(
        self,
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        max_fps: float = 30.0,
        yaw_thresh: float = 0.18,
        pitch_thresh: float = 0.18,
        iris_margin_lr: float = 0.20,
        iris_margin_ud: float = 0.25,
        min_score_for_compliance: float = 0.6,
        min_det_conf: float = 0.5,
        min_track_conf: float = 0.5,
    ):
        self.yaw_thresh = yaw_thresh
        self.pitch_thresh = pitch_thresh
        self.iris_margin_lr = iris_margin_lr
        self.iris_margin_ud = iris_margin_ud
        self.min_score_for_compliance = min_score_for_compliance

        self.frame_period = 1.0 / float(max_fps)

        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))

        # Prefer MediaPipe Tasks FaceLandmarker (if a model file exists), then
        # legacy mp.solutions.FaceMesh, otherwise fall back to OpenCV cascades.
        self._use_solutions = False
        self.face_mesh = None
        self.face_cascade = None
        self.eye_cascade = None
        # check for a downloaded Tasks model in experiment/models/
        try:
            model_candidates = [
                project_root() / "experiment" / "models" / "face_landmarker.task",
                project_root() / "experiment" / "models" / "face_landmarker.tflite",
            ]
            model_path = None
            for mpth in model_candidates:
                try:
                    if mpth.exists():
                        model_path = str(mpth)
                        break
                except Exception:
                    continue

            # Try MediaPipe Tasks API if available and model file present
            if model_path and mp is not None and getattr(mp, "tasks", None) is not None:
                try:
                    # dynamic import; wrap in broad try so failures fall back safely
                    from mediapipe.tasks.python import vision
                    from mediapipe.tasks.python.core import base_options

                    BaseOptions = base_options.BaseOptions
                    FaceLandmarker = vision.face_landmarker.FaceLandmarker
                    FaceLandmarkerOptions = vision.face_landmarker.FaceLandmarkerOptions

                    opts = FaceLandmarkerOptions(
                        base_options=BaseOptions(model_asset_path=model_path),
                        running_mode=vision.face_landmarker.RunningMode.LIVE_STREAM,
                        num_faces=1,
                    )
                    try:
                        # prefer the factory method if present
                        self.face_mesh = FaceLandmarker.create_from_options(opts)
                    except Exception:
                        # fallback to direct construction
                        self.face_mesh = FaceLandmarker(opts)

                    self._use_solutions = True
                except Exception:
                    # if Tasks API instantiation fails, fall through to legacy/OPEN_CV
                    self.face_mesh = None

            # If Tasks API not used, try legacy mp.solutions.face_mesh
            if not self._use_solutions:
                try:
                    _mp_face_mesh = getattr(mp, "solutions", None)
                    if _mp_face_mesh is not None and hasattr(_mp_face_mesh, "face_mesh"):
                        self._use_solutions = True
                        self._mp_face_mesh = mp.solutions.face_mesh
                        self.face_mesh = self._mp_face_mesh.FaceMesh(
                            static_image_mode=False,
                            max_num_faces=1,
                            refine_landmarks=True,
                            min_detection_confidence=float(min_det_conf),
                            min_tracking_confidence=float(min_track_conf),
                        )
                except Exception:
                    self._use_solutions = False

            # OpenCV Haar cascades fallback (coarse face+eye detection)
            if not self._use_solutions:
                try:
                    self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                    self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
                except Exception:
                    self.face_cascade = None
                    self.eye_cascade = None
        except Exception:
            # very defensive fallback
            try:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
            except Exception:
                self.face_cascade = None
                self.eye_cascade = None

        self._state = ComplianceState()
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        try:
            self.face_mesh.close()
        except Exception:
            pass
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass

    def get_state(self) -> ComplianceState:
        with self._lock:
            return ComplianceState(**self._state.__dict__)

    def _update_state(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                setattr(self._state, k, v)
            self._state.timestamp = time.time()

    @staticmethod
    def _lm_xy(lms, idx: int, w: int, h: int):
        lm = lms[idx]
        return np.array([lm.x * w, lm.y * h], dtype=np.float32)

    @staticmethod
    def _mean_lm(lms, indices, w: int, h: int):
        pts = [WebcamComplianceMonitor._lm_xy(lms, i, w, h) for i in indices]
        return np.mean(np.stack(pts, axis=0), axis=0)

    def _loop(self) -> None:
        last_time = 0.0
        while self._running:
            now = time.time()
            if now - last_time < self.frame_period:
                time.sleep(0.001)
                continue
            last_time = now

            ok, frame_bgr = self.cap.read()
            if not ok or frame_bgr is None:
                self._update_state(face_found=False, compliant=False, score=0.0, reason="NO_FRAME")
                continue

            h, w = frame_bgr.shape[:2]
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # If MediaPipe FaceMesh is available, use it for fine-grained landmarks
            if self._use_solutions and self.face_mesh is not None:
                results = self.face_mesh.process(frame_rgb)
                if not results.multi_face_landmarks:
                    self._update_state(face_found=False, compliant=False, score=0.0, reason="NO_FACE")
                    continue

                lms = results.multi_face_landmarks[0].landmark

                nose = self._lm_xy(lms, 1, w, h)
                l_cheek = self._lm_xy(lms, 234, w, h)
                r_cheek = self._lm_xy(lms, 454, w, h)
                forehead = self._lm_xy(lms, 10, w, h)
                chin = self._lm_xy(lms, 152, w, h)

                face_w = max(1.0, float(np.linalg.norm(r_cheek - l_cheek)))
                face_h = max(1.0, float(np.linalg.norm(chin - forehead)))

                cheek_mid = (l_cheek + r_cheek) / 2.0
                fc_mid = (forehead + chin) / 2.0

                yaw_proxy = float((nose[0] - cheek_mid[0]) / face_w)
                pitch_proxy = float((nose[1] - fc_mid[1]) / face_h)

                head_ok = (abs(yaw_proxy) <= self.yaw_thresh) and (abs(pitch_proxy) <= self.pitch_thresh)

                iris_left = self._mean_lm(lms, list(range(468, 473)), w, h)
                iris_right = self._mean_lm(lms, list(range(473, 478)), w, h)
                iris_center = (iris_left + iris_right) / 2.0

                l_outer = self._lm_xy(lms, 33, w, h)
                l_inner = self._lm_xy(lms, 133, w, h)
                r_outer = self._lm_xy(lms, 362, w, h)
                r_inner = self._lm_xy(lms, 263, w, h)
                l_up = self._lm_xy(lms, 159, w, h)
                l_dn = self._lm_xy(lms, 145, w, h)
                r_up = self._lm_xy(lms, 386, w, h)
                r_dn = self._lm_xy(lms, 374, w, h)

                eye_left_x = float(min(l_outer[0], l_inner[0]))
                eye_right_x = float(max(r_outer[0], r_inner[0]))
                eye_top_y = float(min(l_up[1], r_up[1]))
                eye_bot_y = float(max(l_dn[1], r_dn[1]))

                eye_w = max(1.0, eye_right_x - eye_left_x)
                eye_h = max(1.0, eye_bot_y - eye_top_y)

                iris_lr = float((iris_center[0] - eye_left_x) / eye_w)
                iris_ud = float((iris_center[1] - eye_top_y) / eye_h)

                eyes_ok = (
                    (self.iris_margin_lr <= iris_lr <= 1.0 - self.iris_margin_lr) and
                    (self.iris_margin_ud <= iris_ud <= 1.0 - self.iris_margin_ud)
                )

                score = (0.6 if head_ok else 0.0) + (0.4 if eyes_ok else 0.0)
                compliant = score >= self.min_score_for_compliance

                if not head_ok and not eyes_ok:
                    reason = "HEAD+EYES_AWAY"
                elif not head_ok:
                    reason = "HEAD_AWAY"
                elif not eyes_ok:
                    reason = "EYES_AWAY"
                else:
                    reason = "OK"

                self._update_state(
                    face_found=True,
                    compliant=compliant,
                    score=float(score),
                    yaw_proxy=yaw_proxy,
                    pitch_proxy=pitch_proxy,
                    iris_lr=iris_lr,
                    iris_ud=iris_ud,
                    reason=reason,
                )
                continue

            # Fallback: coarse OpenCV detection (face box + eyes)
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            if self.face_cascade is None:
                self._update_state(face_found=False, compliant=False, score=0.0, reason="NO_DETECTOR")
                continue

            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(faces) == 0:
                self._update_state(face_found=False, compliant=False, score=0.0, reason="NO_FACE")
                continue

            x, y, fw, fh = faces[0]
            face_center = np.array([x + fw / 2.0, y + fh / 2.0], dtype=np.float32)

            # approximate proxies relative to face size
            yaw_proxy = float((face_center[0] - (w / 2.0)) / max(1.0, fw))
            pitch_proxy = float((face_center[1] - (h / 2.0)) / max(1.0, fh))

            head_ok = (abs(yaw_proxy) <= self.yaw_thresh) and (abs(pitch_proxy) <= self.pitch_thresh)

            eyes_ok = False
            iris_lr = 0.5
            iris_ud = 0.5
            if self.eye_cascade is not None:
                roi_gray = gray[y : y + fh, x : x + fw]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5)
                if len(eyes) >= 2:
                    # compute approximate horizontal centering between eyes
                    eye_centers = [np.array([ex + ew / 2.0, ey + eh / 2.0]) for (ex, ey, ew, eh) in eyes[:2]]
                    ec = np.mean(np.stack(eye_centers, axis=0), axis=0)
                    # normalize within face bbox
                    iris_lr = float((ec[0]) / max(1.0, fw))
                    iris_ud = float((ec[1]) / max(1.0, fh))
                    # convert to 0..1 relative within eyes region
                    eyes_ok = (
                        (self.iris_margin_lr <= iris_lr <= 1.0 - self.iris_margin_lr) and
                        (self.iris_margin_ud <= iris_ud <= 1.0 - self.iris_margin_ud)
                    )

            score = (0.6 if head_ok else 0.0) + (0.4 if eyes_ok else 0.0)
            compliant = score >= self.min_score_for_compliance

            if not head_ok and not eyes_ok:
                reason = "HEAD+EYES_AWAY"
            elif not head_ok:
                reason = "HEAD_AWAY"
            elif not eyes_ok:
                reason = "EYES_AWAY"
            else:
                reason = "OK"

            self._update_state(
                face_found=True,
                compliant=compliant,
                score=float(score),
                yaw_proxy=yaw_proxy,
                pitch_proxy=pitch_proxy,
                iris_lr=iris_lr,
                iris_ud=iris_ud,
                reason=reason,
            )


def sample_compliance(monitor: WebcamComplianceMonitor, duration_s: float, poll_hz: float = 30.0):
    step = 1.0 / float(poll_hz)
    t0 = time.time()

    n = 0
    n_compliant = 0
    n_face = 0
    score_sum = 0.0
    yaw_sum = 0.0
    pitch_sum = 0.0

    while (time.time() - t0) < duration_s:
        st = monitor.get_state()
        n += 1
        if st.face_found:
            n_face += 1
        if st.compliant:
            n_compliant += 1
        score_sum += float(st.score)
        yaw_sum += float(st.yaw_proxy)
        pitch_sum += float(st.pitch_proxy)
        time.sleep(step)

    denom = max(1, n)
    return {
        "compliance_pct": n_compliant / denom,
        "face_present_pct": n_face / denom,
        "mean_score": score_sum / denom,
        "mean_yaw_proxy": yaw_sum / denom,
        "mean_pitch_proxy": pitch_sum / denom,
    }


def draw_compliance_indicator(win: visual.Window, st: ComplianceState, text_stim: visual.TextStim, dot_stim: visual.Circle):
    if not st.face_found:
        text_stim.text = "NO FACE"
        dot_stim.fillColor = "red"
        dot_stim.lineColor = "red"
    elif st.compliant:
        text_stim.text = f"OK  score={st.score:.2f}"
        dot_stim.fillColor = "green"
        dot_stim.lineColor = "green"
    else:
        text_stim.text = f"LOOK AWAY  ({st.reason})  score={st.score:.2f}"
        dot_stim.fillColor = "red"
        dot_stim.lineColor = "red"

    dot_stim.draw()
    text_stim.draw()

@dataclass
class TriggerConfig:
    enabled: bool = False

class TriggerSender:
    def __init__(self, cfg: TriggerConfig):
        self.cfg = cfg
    def send(self, code: int):
        return

def project_root() -> Path:
    return Path(__file__).resolve().parent

def conditions_file(deck_id: str) -> Path:
    p = project_root() / "conditions" / deck_id / f"trials_{deck_id}.csv"
    if not p.exists():
        raise FileNotFoundError(p)
    return p

def norm(s): return (s or "").strip().lower()

def arrow_correct(dirn, key):
    return int(key in ("left","right") and norm(dirn)==norm(key))

def run():
    exp = DEFAULTS.copy()
    dlg = gui.DlgFromDict(exp, title="MaM EAT Runner")
    if not dlg.OK:
        core.quit()

    win = visual.Window(fullscr=bool(exp["fullscreen"]), color=(0,0,0), units="height")

    fix = visual.TextStim(win, "+", height=0.08)
    arrow = visual.TextStim(win, "<", height=0.12)
    # make cue full-screen color
    cue = visual.Rect(win, width=2.0, height=2.0)
    img = visual.ImageStim(win, size=(0.9,0.9))
    prompt = visual.TextStim(win, "Which direction was the ARROW pointing?\nPress LEFT or RIGHT.", height=0.06)

    instr_body = visual.TextStim(
        win,
        "This task measures emotional anticipation and short-term memory for a briefly shown arrow.\n\n"
        "Trial flow (pay close attention):\n"
        "1) An ARROW (left or right) will appear briefly — remember its direction.\n"
        "2) The screen will change color to indicate the cue meaning:\n"
        "   - GREEN: predicts a positive image\n"
        "   - RED: predicts a negative image\n"
        "   - YELLOW: cue meaning is unknown (could be positive or negative)\n"
        "3) An image will appear briefly.\n"
        "4) After the image you will be prompted to indicate the ARROW direction.\n\n"
        "Do NOT respond when the arrow or color cue appears — wait for the prompt after the image.\n"
        "When prompted, press the LEFT or RIGHT arrow key corresponding to the ORIGINAL arrow direction.\n\n"
        "Try to respond as quickly and accurately as possible. If you are unsure, guess rather than skip.\n\n"
        "Press any key to continue.",
        height=0.04,
        pos=(0, 0.12),
        wrapWidth=1.6,
        alignText='left',
    )
    instr_note = visual.TextStim(win, "Practice: 2 trials (labeled). Experiment follows. Press any key to continue.", height=0.032, pos=(0, -0.46), wrapWidth=1.6)
    instr_body.draw(); instr_note.draw(); win.flip()
    if AUTOPILOT:
        core.wait(0.5)
    else:
        event.waitKeys()

    # --- Webcam compliance config ---
    ENABLE_COMPLIANCE = True  # set False to disable webcam monitoring
    CAMERA_INDEX = 0
    SHOW_COMPLIANCE_INDICATOR = True  # set True for pilot/testing

    # create a small status indicator (used only if SHOW_COMPLIANCE_INDICATOR=True)
    status_text = visual.TextStim(win, text="INIT", pos=(0, 0.45), height=0.03)
    status_dot = visual.Circle(win, radius=0.03, pos=(0, 0.38))

    # Start webcam monitor (optional)
    monitor = None
    if ENABLE_COMPLIANCE:
        monitor = WebcamComplianceMonitor(
            camera_index=CAMERA_INDEX,
            max_fps=30.0,
            yaw_thresh=0.18,
            pitch_thresh=0.18,
            iris_margin_lr=0.20,
            iris_margin_ud=0.25,
            min_score_for_compliance=0.6,
        )
        monitor.start()
        core.wait(0.5)  # brief warm-up so the first state isn't INIT

    outdir = project_root() / "data" / "raw"
    outdir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    outpath = outdir / f"EAT_{exp['participant_id']}_{exp['session_id']}_{ts}.csv"

    with outpath.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()

        deck_id = exp["deck_id"]
        cf = conditions_file(deck_id)
        with open(cf, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))

        # select up to two practice trials from other decks (images only)
        practice_rows = []
        for other in VALID_DECKS:
            if other == deck_id:
                continue
            try:
                ocf = project_root() / "conditions" / other / f"trials_{other}.csv"
                if not ocf.exists():
                    continue
                with open(ocf, encoding="utf-8-sig", newline="") as ofh:
                    orows = list(csv.DictReader(ofh))
                for r in orows:
                    pimg = (r.get("image_path") or "").strip()
                    if not pimg:
                        continue
                    ppath = project_root() / pimg
                    if ppath.exists():
                        practice_rows.append(r)
                        break
            except Exception:
                continue
            if len(practice_rows) >= 2:
                break

        # show pre-practice message and run practice trials (visual only, labeled)
        pre_practice = visual.TextStim(win, "Now you'll do 2 practice trials. Press any key to begin.", height=0.045, wrapWidth=1.6, pos=(0, 0.0))
        pre_practice.draw(); win.flip()
        if AUTOPILOT:
            core.wait(0.4)
        else:
            event.waitKeys()

        # run practice trials (visual only, labeled)
        for idx, prow in enumerate(practice_rows[:2], start=1):
            label = visual.TextStim(win, f"Practice {idx}", height=0.06, pos=(0, 0.45))
            # resolve practice image
            prow_img = (prow.get("image_path") or "").strip()
            p_has_image = False
            if prow_img:
                ppath = project_root() / prow_img
                if ppath.exists():
                    try:
                        img.image = str(ppath)
                        p_has_image = True
                    except Exception:
                        p_has_image = False

            # durations for practice (fall back to small defaults)
            def _getp(key, default=0.25):
                try:
                    return float(prow.get(key, default))
                except Exception:
                    return float(default)

            p_fix = _getp("fix_dur", 0.5)
            p_arrow = _getp("arrow_dur", 0.5)
            p_isi = _getp("isi1_dur", 2.)
            p_cue = _getp("cue_dur", 0.5)
            p_img = _getp("image_dur", 0.5)

            # display practice trial
            label.draw(); win.flip(); core.wait(0.8)
            fix.draw(); win.flip(); core.wait(p_fix)
            arrow_dir = norm(prow.get("arrow_direction","left"))
            arrow.text = "<" if arrow_dir=="left" else ">"
            arrow.draw(); win.flip(); core.wait(p_arrow)
            win.flip(); core.wait(p_isi)
            cue.fillColor = cue.lineColor = CUE_RGB.get(norm(prow.get("cue_color","yellow")), CUE_RGB["yellow"]) 
            cue.draw(); win.flip(); core.wait(p_cue)
            if p_has_image:
                img.draw(); win.flip(); core.wait(p_img)
            else:
                win.flip(); core.wait(p_img)
            # prompt and give fixed response window
            event.clearEvents()
            prompt.draw(); win.flip()
            if AUTOPILOT:
                core.wait(min(0.05, RESPONSE_WINDOW))
            else:
                event.waitKeys(maxWait=RESPONSE_WINDOW, keyList=["left","right"]) 

        # post-practice message
        post_practice = visual.TextStim(win, "Practice complete. The real task will begin. Press any key to continue.", height=0.045, wrapWidth=1.6, pos=(0, 0.0))
        post_practice.draw(); win.flip()
        if AUTOPILOT:
            core.wait(0.5)
        else:
            event.waitKeys()

        clock = core.Clock()
        ti = 0

        for row in rows:
            ti += 1
            if "escape" in event.getKeys(["escape"]):
                break

            arrow_dir = norm(row["arrow_direction"])
            arrow.text = "<" if arrow_dir=="left" else ">"
            cue.fillColor = cue.lineColor = CUE_RGB.get(norm(row["cue_color"]), CUE_RGB["yellow"])

            def getf(key, default=0.0):
                try:
                    return float(row.get(key, default))
                except Exception:
                    return float(default)

            fix_d = getf("fix_dur")
            arrow_d = getf("arrow_dur")
            isi_d = getf("isi1_dur")
            cue_d = getf("cue_dur")
            ant_d = getf("anticip_dur")
            img_d = getf("image_dur")
            iti_d = getf("iti_dur")

            # Resolve image path; allow blank/missing images
            raw_img = (row.get("image_path") or "").strip()
            has_image = False
            if raw_img and raw_img != "stimuli/pools/":
                img_path = project_root() / raw_img
                if img_path.exists():
                    try:
                        img.image = str(img_path)
                        has_image = True
                    except Exception:
                        print(f"Warning: could not load image {img_path}; will skip image display.")
                        has_image = False
                else:
                    print(f"Warning: image file not found: {img_path}; skipping image display.")
                    has_image = False

            fix.draw(); win.flip(); t_fix = clock.getTime(); core.wait(fix_d)

            event.clearEvents()
            # show arrow (no response collected yet)
            arrow.draw(); win.flip(); t_arr = clock.getTime()
            core.wait(arrow_d)

            win.flip(); core.wait(isi_d)

            # full-screen color cue
            cue.fillColor = cue.lineColor = CUE_RGB.get(norm(row.get("cue_color","yellow")), CUE_RGB["yellow"])
            cue.draw(); win.flip(); t_cue = clock.getTime(); core.wait(cue_d)
            # no separate anticipation period in this flow; set t_ant for logging
            t_ant = t_cue

            # show image and sample compliance while image is displayed
            t_img = clock.getTime()
            stim_compliance_pct = 0.0
            stim_face_present_pct = 0.0
            stim_mean_score = 0.0
            stim_mean_yaw_proxy = 0.0
            stim_mean_pitch_proxy = 0.0

            if has_image:
                # sampling accumulators
                n = 0
                n_compliant = 0
                n_face = 0
                score_sum = 0.0
                yaw_sum = 0.0
                pitch_sum = 0.0

                t0 = time.time()
                while (time.time() - t0) < img_d:
                    img.draw()
                    if SHOW_COMPLIANCE_INDICATOR and monitor is not None:
                        st = monitor.get_state()
                        draw_compliance_indicator(win, st, status_text, status_dot)
                    win.flip()

                    if monitor is not None:
                        st = monitor.get_state()
                        n += 1
                        if st.face_found:
                            n_face += 1
                        if st.compliant:
                            n_compliant += 1
                        score_sum += float(st.score)
                        yaw_sum += float(st.yaw_proxy)
                        pitch_sum += float(st.pitch_proxy)

                    core.wait(0.001)

                if monitor is not None and n > 0:
                    denom = max(1, n)
                    stim_compliance_pct = n_compliant / denom
                    stim_face_present_pct = n_face / denom
                    stim_mean_score = score_sum / denom
                    stim_mean_yaw_proxy = yaw_sum / denom
                    stim_mean_pitch_proxy = pitch_sum / denom
            else:
                core.wait(img_d)

            # after image, prompt participant for arrow direction
            event.clearEvents()
            prompt.draw(); win.flip()
            # start a dedicated response clock at prompt onset so RTs are prompt-relative
            response_clock = core.Clock()
            response_clock.reset()
            # use the fixed RESPONSE_WINDOW (seconds) defined at top of file
            if AUTOPILOT:
                core.wait(min(0.05, RESPONSE_WINDOW))
                # timestamp relative to the prompt onset
                resp = [("left", response_clock.getTime())]
            else:
                resp = event.waitKeys(maxWait=RESPONSE_WINDOW, keyList=["left","right"], timeStamped=response_clock)
            rkey, rrt = ("","")
            corr = 0
            if resp:
                rkey, rrt = resp[0]
                # rrt is already relative to arrow onset
                corr = arrow_correct(arrow_dir, rkey)

            win.flip(); core.wait(iti_d)
            t_end = clock.getTime()

            w.writerow({
                "participant_id": exp["participant_id"],
                "session_id": exp["session_id"],
                "deck_id": deck_id,
                "trial_index": ti,
                "trial": row.get("trial",""),
                "arrow_direction": arrow_dir,
                "cue_color": row.get("cue_color",""),
                "cue_meaning": row.get("cue_meaning",""),
                "resolved_valence": row.get("resolved_valence",""),
                "image_path": row.get("image_path",""),
                "image_category": row.get("image_category",""),
                "image_valence": row.get("image_valence",""),
                "fix_dur": fix_d,
                "arrow_dur": arrow_d,
                "isi1_dur": isi_d,
                "cue_dur": cue_d,
                "anticip_dur": ant_d,
                "image_dur": img_d,
                "iti_dur": iti_d,
                "arrow_resp_key": rkey,
                "arrow_resp_rt": rrt,
                "arrow_correct": corr,
                "event_code_arrow": row.get("event_code_arrow",""),
                "event_code_cue": row.get("event_code_cue",""),
                "event_code_image": row.get("event_code_image",""),
                "ts_fix_on": t_fix,
                "ts_arrow_on": t_arr,
                "ts_cue_on": t_cue,
                "ts_anticip_on": t_ant,
                "ts_image_on": t_img,
                "ts_trial_end": t_end,
                "stim_compliance_pct": stim_compliance_pct,
                "stim_face_present_pct": stim_face_present_pct,
                "stim_mean_score": stim_mean_score,
                "stim_mean_yaw_proxy": stim_mean_yaw_proxy,
                "stim_mean_pitch_proxy": stim_mean_pitch_proxy,
            })

    win.close()
    # Stop webcam monitor if running
    try:
        if monitor is not None:
            monitor.stop()
    except Exception:
        pass
    core.quit()

if __name__ == "__main__":
    run()
