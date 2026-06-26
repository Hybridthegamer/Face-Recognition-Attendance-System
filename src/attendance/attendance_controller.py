"""
Attendance Controller — implements RunAttendanceSession algorithm
(Chapter 3, Section 3.8.2)

ALGORITHM: RunAttendanceSession(session_id)
  1. Load all (user_id, encoding) pairs from FaceEncodings into memory
  2. Open webcam VideoCapture
  3. WHILE session is_active:
       a. frame ← read frame
       b. small_frame ← resize(frame, 0.5x)
       c. rgb_frame ← BGR→RGB(small_frame)
       d. face_locs ← face_locations(rgb_frame, model='hog')
       e. IF empty: CONTINUE
       f. face_encs ← face_encodings(rgb_frame, face_locs)
       g. FOR EACH face_enc:
            i.  matches ← compare_faces(known_encodings, face_enc, tolerance=0.6)
            ii. distances ← face_distance(known_encodings, face_enc)
           iii. IF match: identity ← known_users[argmin(distances)]
                ELSE:     identity ← 'Unknown'
            iv. IF identity != 'Unknown' AND NOT already_marked:
                    INSERT AttendanceRecord; show notification
            v.  annotate frame
       h. display frame
  4. CLOSE webcam; UPDATE session is_active=0
"""

import threading
import queue
import cv2
from datetime import datetime

from src.recognition.face_encoder import FaceEncoder
from src.config import FRAME_SCALE


class AttendanceController:
    def __init__(self, db_manager):
        self.db = db_manager
        self._encoder = FaceEncoder()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._session_id: int | None = None
        self._marked_this_session: set = set()

        # Queues for inter-thread communication
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)
        self.attendance_queue: queue.Queue = queue.Queue()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(self, session_id: int) -> tuple[bool, str]:
        if self._thread and self._thread.is_alive():
            return False, "A recognition session is already running."

        self._session_id = session_id
        self._marked_this_session = set()
        self._stop_event.clear()

        # Load face encodings from DB into memory
        self._encoder.load_encodings_from_db(self.db)
        if not self._encoder.is_populated:
            return False, "No enrolled users found. Please enrol users before starting a session."

        self._thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self._thread.start()
        return True, "Recognition session started."

    def stop_session(self):
        """Signal the recognition loop to stop and close the session in DB."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=4.0)
        if self._session_id is not None:
            self.db.close_session(self._session_id)
            self._session_id = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Background recognition loop
    # ------------------------------------------------------------------

    def _recognition_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self._stop_event.set()
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        frame_idx = 0
        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    continue

                frame_idx += 1
                # Run detection/recognition on every 3rd frame for performance
                if frame_idx % 3 == 0:
                    frame = self._process_frame(frame)

                # Non-blocking put; drop frame if GUI is behind
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass
        finally:
            cap.release()

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def _process_frame(self, frame):
        """
        Implements steps (b)–(g) of the recognition algorithm.
        Modifies frame in-place with annotation and returns it.
        """
        # Downscale for faster HOG detection + encoding
        small = cv2.resize(frame, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations, encodings = self._encoder.detect_and_encode(rgb_small)

        scale = int(1 / FRAME_SCALE)  # 2x when FRAME_SCALE=0.5

        for (top, right, bottom, left), enc in zip(locations, encodings):
            # Scale coordinates back to original frame size
            top, right, bottom, left = (
                top * scale, right * scale, bottom * scale, left * scale
            )

            identity = self._encoder.identify_face(enc)

            if identity:
                user_id = identity['user_id']
                label   = f"{identity['name']} | {identity['institution_id']}"
                color   = (0, 180, 0)

                # Duplicate prevention (step iv)
                if user_id not in self._marked_this_session:
                    if not self.db.is_attendance_marked(user_id, self._session_id):
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if self.db.mark_attendance(user_id, self._session_id, ts):
                            self._marked_this_session.add(user_id)
                            try:
                                self.attendance_queue.put_nowait({
                                    'name':           identity['name'],
                                    'institution_id': identity['institution_id'],
                                    'timestamp':      ts,
                                })
                            except queue.Full:
                                pass
            else:
                label = "Unknown"
                color = (0, 0, 200)

            # Annotate frame with bounding box and name label
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            label_y = bottom + 22 if bottom + 22 < frame.shape[0] else top - 8
            cv2.rectangle(frame, (left, bottom), (right, bottom + 26), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 4, bottom + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)

        return frame
