# Face Recognition Attendance System

A desktop application that uses real-time face recognition to automate attendance tracking in educational institutions and corporate settings. Built as a Final Year Project (FYP) for a Nigerian university context.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Tool Stack & Justification](#tool-stack--justification)
3. [System Requirements](#system-requirements)
4. [Installation & Setup](#installation--setup)
5. [Running the Application](#running-the-application)
6. [Usage Guide](#usage-guide)
7. [Project Structure](#project-structure)
8. [Database Schema](#database-schema)
9. [Core Algorithms](#core-algorithms)
10. [Default Credentials](#default-credentials)

---

## System Overview

The system replaces manual, paper-based attendance registers with a three-stage automated pipeline:

1. **Face Detection** — dlib's HOG-based frontal face detector (via `face_recognition`) locates faces in each webcam frame.
2. **Face Recognition** — A pre-trained ResNet model produces 128-dimensional face embeddings; Euclidean distance matching against enrolled encodings identifies individuals.
3. **Attendance Recording** — Confirmed identifications are written atomically to a SQLite database with a timestamp. Duplicate prevention (one record per user per session) is enforced at the database level with a `UNIQUE(user_id, session_id)` constraint.

Key capabilities:
- **User Enrolment**: Captures 40 face images per user, computes encodings, and stores them in the database.
- **Live Recognition Session**: Real-time face recognition from webcam feed with annotated bounding boxes.
- **Attendance Records**: Searchable and filterable records by session, course, date range, and name.
- **Report Generation**: Per-student attendance percentage with configurable Pass/Fail threshold.
- **CSV Export**: Reports and records can be exported to CSV.
- **Administrator Authentication**: Username/password login with SHA-256 hashed passwords.

---

## Tool Stack & Justification

### Python 3.9+
Python is the primary implementation language. Chosen for:
- **Ecosystem richness**: Direct access to `face_recognition`, `OpenCV`, and `Tkinter` without wrappers.
- **Rapid prototyping**: Allows iterative Agile development as specified in the project methodology (Chapter 3).
- **Academic precedent**: Most peer-reviewed attendance systems surveyed in the literature review (Adewale et al., 2019; Rajan et al., 2021) use Python.
- **Cross-platform**: Runs on Windows 10/11 and Ubuntu Linux 20.04+ without source changes (NFR5).

### OpenCV (`opencv-python`)
OpenCV handles all image and video I/O:
- `VideoCapture` reads frames from the webcam at 15–30 fps (FR1).
- BGR→RGB conversion, frame resizing (50% for processing speed), and bounding-box annotation.
- Chosen because it is the industry standard for real-time computer vision pipelines and is used in virtually every attendance system reviewed in the literature (Viola & Jones, 2004; Chintalapati & Raghunadh, 2013).

### face_recognition (built on dlib)
This library provides the entire recognition pipeline:
- **`face_locations(model='hog')`** — dlib's Histogram of Oriented Gradients (HOG) + SVM frontal face detector. Faster than Haar cascades on CPU and more accurate under varying conditions.
- **`face_encodings()`** — applies a pre-trained ResNet-based deep metric learning model to produce **128-dimensional** face embeddings (analogous to FaceNet by Schroff et al., 2015). The dlib model achieves **99.38% accuracy on the Labeled Faces in the Wild (LFW) benchmark** (King, 2009) — far exceeding the 95% minimum target (NFR2).
- **`compare_faces()` + `face_distance()`** — Euclidean distance matching with configurable tolerance (default 0.6).

Chosen over raw dlib or TensorFlow/PyTorch because:
- Single `pip install` deploys the complete pipeline (no GPU required).
- Runs on any machine with Intel Core i5 + 4 GB RAM (NFR1).
- Avoids the LBPH accuracy degradation under variable lighting documented by Adewale et al. (2019), which reached only 78% under uneven lighting.

### SQLite 3 (via Python's built-in `sqlite3`)
Chosen because:
- **Zero-configuration, serverless**: No separate database process — the entire database is a single `data/attendance.db` file.
- **Offline-first**: Operates entirely on a local area network without internet dependency, consistent with the infrastructure-aware design philosophy recommended by Oloyede & Hancke (2016) for sub-Saharan African contexts.
- **ACID-compliant**: All attendance writes use atomic transactions, preventing partial or corrupt records (NFR3).
- **Built-in**: Part of Python's standard library — zero extra driver dependencies.
- **Sufficient scale**: Supports up to 5,000 users and 500,000 records (NFR7). Indexes on `session_id`, `user_id`, and `course_code` ensure fast queries.

### Tkinter (Python standard library)
The GUI framework. Chosen because:
- **No additional dependency**: Ships with every CPython distribution on Windows and Linux.
- **Meets usability requirement**: All primary actions are accessible within 3 mouse clicks from the home screen (NFR4).
- **Thread-safe pattern**: Uses `after()` polling and `queue.Queue` for safe communication between background recognition/enrolment threads and the main UI thread.
- **Portable**: Same source runs on Windows and Linux without modification (NFR5).

### Pillow (`Pillow`)
Used solely to convert OpenCV BGR frames (`numpy.ndarray`) to `ImageTk.PhotoImage` objects for display in Tkinter `Label` widgets. No alternative exists for this bridging role within standard Tkinter.

---

## System Requirements

### Minimum Hardware
| Component | Minimum Specification                         |
|-----------|-----------------------------------------------|
| CPU       | Intel Core i5 (4th gen) or AMD Ryzen 5        |
| RAM       | 4 GB                                          |
| Storage   | 500 MB free (plus ~50 MB per 1,000 users)     |
| Camera    | USB webcam or built-in camera (640x480 min)   |
| Display   | 1280x800 or higher                            |

### Operating System
- Windows 10 / 11 (64-bit)
- Ubuntu Linux 20.04 LTS or later (64-bit)
- macOS 11+ (Big Sur) — supported but not the primary target platform

### Python Version
- Python 3.9, 3.10, or 3.11 recommended
- Python 3.12 requires a dlib wheel compatible with that version

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/hybridthegamer/face-recognition-attendance-system.git
cd face-recognition-attendance-system
```

### 2. Create and activate a virtual environment (recommended)

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install system build dependencies

**Ubuntu / Debian Linux:**
```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential libopenblas-dev liblapack-dev \
     libx11-dev libgtk-3-dev python3-tk
```

**Windows:**
Install [CMake](https://cmake.org/download/) and [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022) (select the "Desktop development with C++" workload) before running pip.

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Windows note**: If dlib fails to compile from source, download a pre-built wheel from the community:  
> Search for `dlib-XX.XX.XX-cpYY-cpYY-win_amd64.whl` matching your Python version on GitHub or PyPI alternatives, then install with `pip install <wheel-file>.whl`.

### 5. Verify installation

```bash
python -c "import face_recognition, cv2, tkinter; print('All dependencies OK')"
```

---

## Running the Application

```bash
python main.py
```

On first run, the application:
1. Creates the `data/` and `reports/` directories.
2. Initialises `data/attendance.db` with the five-table schema.
3. Creates a default administrator account (`admin` / `admin123`).
4. Displays the login window.

---

## Usage Guide

### Step 1 — Login
Enter username `admin` and password `admin123`. Click **LOGIN** or press **Enter**.

### Step 2 — Enrol Users (before any session)
Navigate to **Enrol User** in the left sidebar:

1. Fill in **Full Name**, **Matriculation / Staff ID**, **Department**, and **Programme**.
2. Click **Start Enrolment** — the webcam activates.
3. Look directly at the camera and stay still. The system automatically captures 40 images when exactly one face is detected in each frame.
4. A progress bar tracks the capture. After completion, encodings are computed and stored automatically.
5. A confirmation dialog confirms successful enrolment.

> Tip: Enrol each user under the same indoor lighting that will be used during sessions.

### Step 3 — Start an Attendance Session
Navigate to **Session** in the sidebar:

1. Enter **Course Code** (e.g. `CSC401`), **Course Title**, and **Lecturer Name**.
2. Click **▶ Start Session** — the webcam activates and live recognition begins.
3. Enrolled individuals who appear in front of the camera are automatically identified. Their name, ID, and timestamp are logged in the left panel.
4. Click **■ End Session** when the class ends. The session is closed in the database.

### Step 4 — View Attendance Records
Navigate to **Records**:
- Filter by Session ID, Course Code, Date range, or Name.
- Click **Search** to apply filters.
- Click **Export CSV** to download filtered results.

### Step 5 — Generate Attendance Report
Navigate to **Reports**:

1. Enter a **Course Code** or select from the dropdown.
2. Set the **Threshold %** (default: 75%).
3. Click **Generate Report**.
4. Students below the threshold are highlighted in red (attendance warning indicator).
5. Summary cards show total sessions, students tracked, pass count, and fail count.
6. Click **Export CSV** to save the full report.

### Step 6 — Manage Users
Navigate to **Users**:
- View all enrolled users in a searchable table.
- Select a row and click **Delete Selected** to remove a user and all associated data.

---

## Project Structure

```
Face-Recognition-Attendance-System/
│
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md
│
├── data/
│   └── attendance.db                # SQLite database (auto-created at runtime)
│
├── reports/                         # CSV exports (auto-created at runtime)
│
├── face_images/                     # Reserved for optional image archiving
│
└── src/
    ├── config.py                    # Global constants (paths, colours, fonts)
    │
    ├── database/
    │   └── db_manager.py            # DatabaseManager — all SQL operations
    │
    ├── recognition/
    │   ├── face_encoder.py          # FaceEncoder — detection, encoding, matching
    │   └── enrollment_manager.py    # EnrollmentManager — webcam capture + storage
    │
    ├── attendance/
    │   ├── attendance_controller.py # AttendanceController — live recognition loop
    │   ├── session_manager.py       # SessionManager — session lifecycle
    │   └── report_generator.py      # ReportGenerator — statistics + CSV export
    │
    └── gui/
        ├── app.py                   # FaceAttendanceApp — top-level controller
        ├── login_window.py          # Login dialog (modal Toplevel)
        ├── main_window.py           # Sidebar + content area shell
        ├── widgets.py               # Reusable themed Tkinter widgets
        └── frames/
            ├── home_frame.py        # Dashboard — statistics + quick actions
            ├── enrollment_frame.py  # User enrolment with live webcam preview
            ├── session_frame.py     # Live recognition session + attendance log
            ├── records_frame.py     # Attendance records viewer with filters
            ├── report_frame.py      # Report generation with Pass/Fail indicators
            └── users_frame.py       # User management (list + delete)
```

---

## Database Schema

Five tables as designed in the system analysis (Chapter 3, Section 3.7):

```sql
-- Registered individuals (students or staff)
Users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    institution_id TEXT    NOT NULL UNIQUE,
    department     TEXT    NOT NULL,
    programme      TEXT    NOT NULL,
    created_at     TEXT    NOT NULL
)

-- Serialised 128-d face embeddings (multiple per user for robustness)
FaceEncodings (
    encoding_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    encoding_blob BLOB    NOT NULL,
    created_at    TEXT    NOT NULL
)

-- Attendance sessions (course + date + lecturer)
Sessions (
    session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code   TEXT NOT NULL,
    course_title  TEXT NOT NULL,
    lecturer_name TEXT NOT NULL,
    date          TEXT NOT NULL,
    start_time    TEXT NOT NULL,
    end_time      TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1
)

-- One row per (student, session) pair — UNIQUE enforces no duplicate marking
AttendanceRecords (
    record_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES Users(user_id)    ON DELETE CASCADE,
    session_id INTEGER NOT NULL REFERENCES Sessions(session_id) ON DELETE CASCADE,
    timestamp  TEXT    NOT NULL,
    UNIQUE(user_id, session_id)
)

-- Administrator accounts (passwords stored as SHA-256 hashes)
Admins (
    admin_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
)
```

---

## Core Algorithms

### EnrolUser (Chapter 3, Section 3.8.1)
```
1. INSERT (name, institution_id, dept, prog) → Users → user_id
2. OPEN webcam VideoCapture
3. REPEAT until 40 valid single-face frames collected:
       frame ← read(); locs ← face_locations(rgb, model='hog')
       IF len(locs) == 1: append frame to image_list
4. CLOSE webcam
5. FOR EACH image:
       enc ← face_encodings(image)[0]
       blob ← pickle.dumps(enc)
       INSERT (user_id, blob) → FaceEncodings
6. COMMIT; reload in-memory encoding cache
```

### RunAttendanceSession (Chapter 3, Section 3.8.2)
```
1. Load all (user_id, encoding) pairs from FaceEncodings → memory
2. OPEN webcam; set is_active = TRUE
3. WHILE is_active:
       frame ← read(); small ← resize(frame, 0.5x); rgb ← BGR→RGB(small)
       locs ← face_locations(rgb, model='hog')
       encs ← face_encodings(rgb, locs)
       FOR EACH (loc, enc):
           matches   ← compare_faces(known_encs, enc, tolerance=0.6)
           distances ← face_distance(known_encs, enc)
           IF any(matches): identity ← known_users[argmin(distances)]
           ELSE:            identity ← "Unknown"
           IF identity != "Unknown" AND NOT already_marked(identity, session_id):
               INSERT AttendanceRecord; display notification
           annotate frame with bounding box + label
       display annotated frame
4. CLOSE webcam; UPDATE Sessions SET is_active=0, end_time=NOW
```

### GenerateReport (Chapter 3, Section 3.8.3)
```
1. total_sessions ← COUNT(*) FROM Sessions WHERE course_code
2. FOR EACH user with records for the course:
       attended ← COUNT(*) FROM AttendanceRecords WHERE user_id AND course
       percentage ← (attended / total_sessions) * 100
       status ← "PASS" IF percentage >= threshold ELSE "FAIL"
3. Sort descending by percentage
4. Render table in GUI; provide CSV export
```

---

## Default Credentials

| Username | Password  | Notes                              |
|----------|-----------|------------------------------------|
| `admin`  | `admin123`| Created automatically on first run |

Password is stored as a SHA-256 hash. Change it by logging in and navigating to the database or by modifying the Admins table directly:

```sql
UPDATE Admins
SET password_hash = hex(sha256('your-new-password'))
WHERE username = 'admin';
```

---

## References

- Adewale, O. S., Oke, A. O., & Afolabi, B. S. (2019). Development of a face recognition-based student attendance system for Nigerian universities. *IJACSA*, 10(7).
- King, D. E. (2009). Dlib-ml: A machine learning toolkit. *JMLR*, 10, 1755–1758.
- Oloyede, M. O., & Hancke, G. P. (2016). Unimodal and multimodal biometric sensing systems. *IEEE Access*, 4.
- Rajan, S., Kumar, S., Singh, P., & Sharma, R. (2021). Contactless face recognition attendance system during COVID-19. *IJIT*, 13(5).
- Schroff, F., Kalenichenko, D., & Philbin, J. (2015). FaceNet. *CVPR 2015*.
- Viola, P., & Jones, M. J. (2004). Robust real-time face detection. *IJCV*, 57(2).
