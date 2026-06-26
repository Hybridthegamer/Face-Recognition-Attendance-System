"""
Face Encoder — Recognition module (Chapter 3, Sections 3.6.3 and 3.8)

Wraps the face_recognition library (dlib ResNet-based model) to provide:
  - HOG-based face detection  (face_recognition.face_locations, model='hog')
  - 128-dimensional deep metric embedding  (face_recognition.face_encodings)
  - Euclidean distance matching  (compare_faces + face_distance)

The encoder maintains an in-memory cache of all enrolled encodings so that
the per-frame matching step (O(n) Euclidean comparisons) does not require
repeated database I/O during a live session.
"""

import pickle
import numpy as np
import face_recognition

from src.config import TOLERANCE


class FaceEncoder:
    def __init__(self, tolerance: float = TOLERANCE):
        self.tolerance = tolerance
        # In-memory cache — populated by load_encodings_from_db()
        self._known_encodings: list = []
        self._known_user_ids: list = []
        self._known_names: list = []
        self._known_institution_ids: list = []

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def load_encodings_from_db(self, db_manager):
        """Deserialise all face encodings from the database into memory."""
        rows = db_manager.get_all_encodings()
        self._known_encodings.clear()
        self._known_user_ids.clear()
        self._known_names.clear()
        self._known_institution_ids.clear()

        for row in rows:
            enc = pickle.loads(row['encoding_blob'])
            self._known_encodings.append(enc)
            self._known_user_ids.append(row['user_id'])
            self._known_names.append(row['name'])
            self._known_institution_ids.append(row['institution_id'])

    @property
    def is_populated(self) -> bool:
        return len(self._known_encodings) > 0

    # ------------------------------------------------------------------
    # Detection and encoding
    # ------------------------------------------------------------------

    def detect_and_encode(self, rgb_frame):
        """
        Runs the two-step detection + encoding pipeline on a single RGB frame.

        Step 1: face_recognition.face_locations(rgb, model='hog')
                Uses dlib's HOG + SVM frontal face detector.
        Step 2: face_recognition.face_encodings(rgb, locations)
                Applies a pre-trained ResNet to produce 128-d vectors.

        Returns:
            locations: list of (top, right, bottom, left) tuples
            encodings: list of 128-d numpy arrays, aligned with locations
        """
        locations = face_recognition.face_locations(rgb_frame, model="hog")
        if not locations:
            return [], []
        encodings = face_recognition.face_encodings(rgb_frame, locations)
        return locations, encodings

    # ------------------------------------------------------------------
    # Matching (Chapter 3, Section 3.8.2 — Identity Resolution step)
    # ------------------------------------------------------------------

    def identify_face(self, face_encoding) -> dict | None:
        """
        Implements steps (i)–(iii) of the recognition algorithm:
          i.  compute boolean matches via compare_faces (tolerance threshold)
          ii. compute Euclidean distances via face_distance
          iii.select the best (minimum distance) match

        Returns a dict with user_id, name, institution_id, distance;
        or None if no enrolled face matches within the tolerance.
        """
        if not self._known_encodings:
            return None

        matches = face_recognition.compare_faces(
            self._known_encodings, face_encoding, tolerance=self.tolerance
        )
        distances = face_recognition.face_distance(self._known_encodings, face_encoding)

        if not any(matches):
            return None

        best_idx = int(np.argmin(distances))
        if matches[best_idx]:
            return {
                'user_id':        self._known_user_ids[best_idx],
                'name':           self._known_names[best_idx],
                'institution_id': self._known_institution_ids[best_idx],
                'distance':       float(distances[best_idx]),
            }
        return None

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_encoding(encoding) -> bytes:
        return pickle.dumps(encoding)

    @staticmethod
    def deserialize_encoding(blob: bytes):
        return pickle.loads(blob)
