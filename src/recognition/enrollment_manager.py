"""
Enrollment Manager — implements EnrolUser algorithm (Chapter 3, Section 3.8.1)

ALGORITHM: EnrolUser(name, institution_id, department, programme)
  1. INSERT user record → user_id
  2. Open webcam VideoCapture
  3. REPEAT until 40 valid single-face frames collected:
       Capture frame → detect → if exactly one face → append to list
  4. CLOSE webcam
  5. FOR EACH image: compute encoding → serialise → INSERT into FaceEncodings
  6. COMMIT → load cache → RETURN success

The enrolment loop runs on a background thread.  Callers receive progress via
frame_callback(bgr_frame) and progress_callback(n, total, msg) and are notified
of completion via done_callback(success, message).
"""

import threading
import cv2
import face_recognition

from src.config import N_ENROLLMENT_IMAGES
from src.recognition.face_encoder import FaceEncoder


class EnrollmentManager:
    def __init__(self, db_manager, n_images: int = N_ENROLLMENT_IMAGES):
        self.db = db_manager
        self.n_images = n_images
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_enrollment(
        self,
        name: str,
        institution_id: str,
        department: str,
        programme: str,
        frame_callback=None,
        progress_callback=None,
        done_callback=None,
    ):
        """
        Launch enrolment on a daemon thread.

        frame_callback(bgr_frame)          — receives each annotated webcam frame
        progress_callback(n, total, msg)   — receives capture progress
        done_callback(success, message)    — called when enrolment completes or fails
        """
        if self._thread and self._thread.is_alive():
            if done_callback:
                done_callback(False, "Enrolment already in progress.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._enroll_loop,
            args=(name, institution_id, department, programme,
                  frame_callback, progress_callback, done_callback),
            daemon=True,
        )
        self._thread.start()

    def cancel(self):
        """Signal the background thread to stop."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _enroll_loop(
        self,
        name, institution_id, department, programme,
        frame_cb, progress_cb, done_cb,
    ):
        # Validate uniqueness before opening webcam
        if self.db.get_user_by_institution_id(institution_id):
            if done_cb:
                done_cb(False, f"A user with ID '{institution_id}' already exists.")
            return

        # --- Step 1: insert user record ---
        user_id = self.db.add_user(name, institution_id, department, programme)

        # --- Step 2–4: capture frames ---
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.db.delete_user(user_id)
            if done_cb:
                done_cb(False, "Could not open webcam. Check camera connection.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        captured_images = []

        try:
            while len(captured_images) < self.n_images and not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locs = face_recognition.face_locations(rgb, model="hog")

                display = frame.copy()
                n_done = len(captured_images)

                if len(locs) == 1:
                    top, right, bottom, left = locs[0]
                    # Green box when capturing
                    cv2.rectangle(display, (left, top), (right, bottom), (0, 200, 0), 2)
                    label = f"Capturing {n_done + 1}/{self.n_images}"
                    cv2.putText(display, label, (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 0), 2)
                    captured_images.append(rgb)
                    if progress_cb:
                        progress_cb(n_done + 1, self.n_images,
                                    f"Captured {n_done + 1}/{self.n_images} images")
                elif len(locs) == 0:
                    cv2.putText(display, "No face detected — look at camera",
                                (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 220), 2)
                else:
                    cv2.putText(display, "Multiple faces — ensure only ONE face is visible",
                                (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 220), 2)

                # Progress bar overlay
                bar_w = int((n_done / self.n_images) * frame.shape[1])
                cv2.rectangle(display, (0, frame.shape[0] - 8),
                              (bar_w, frame.shape[0]), (0, 200, 0), -1)

                if frame_cb:
                    frame_cb(display)
        finally:
            cap.release()

        if self._stop_event.is_set() or len(captured_images) < self.n_images:
            self.db.delete_user(user_id)
            if done_cb:
                done_cb(False, "Enrolment cancelled.")
            return

        # --- Step 5–6: compute and store encodings ---
        if progress_cb:
            progress_cb(0, len(captured_images), "Computing face encodings…")

        stored = 0
        for i, img in enumerate(captured_images):
            encs = face_recognition.face_encodings(img)
            if encs:
                blob = FaceEncoder.serialize_encoding(encs[0])
                self.db.add_face_encoding(user_id, blob)
                stored += 1
            if progress_cb:
                progress_cb(i + 1, len(captured_images),
                            f"Processing image {i + 1}/{len(captured_images)}")

        if stored == 0:
            self.db.delete_user(user_id)
            if done_cb:
                done_cb(False, "No valid face encodings could be computed. Please try again.")
            return

        if done_cb:
            done_cb(True, f"'{name}' enrolled successfully with {stored} face encodings.")
