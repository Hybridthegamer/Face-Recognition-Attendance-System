import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'attendance.db')
FACE_IMAGES_DIR = os.path.join(BASE_DIR, 'face_images')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

# Recognition settings (per Chapter 3 algorithm specifications)
TOLERANCE = 0.6          # Euclidean distance threshold for face matching
FRAME_SCALE = 0.5        # Downscale factor for faster processing
N_ENROLLMENT_IMAGES = 40 # Images captured per user during enrolment

# Attendance settings
DEFAULT_THRESHOLD_PCT = 75.0

# Window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 780
SIDEBAR_WIDTH = 230

COLORS = {
    'bg':             '#f0f4f8',
    'sidebar_bg':     '#1a2744',
    'sidebar_text':   '#c8d6f0',
    'sidebar_hover':  '#253461',
    'sidebar_active': '#3b82f6',
    'header_bg':      '#ffffff',
    'card_bg':        '#ffffff',
    'primary':        '#3b82f6',
    'primary_dark':   '#2563eb',
    'success':        '#10b981',
    'warning':        '#f59e0b',
    'danger':         '#ef4444',
    'text_primary':   '#1e293b',
    'text_secondary': '#64748b',
    'border':         '#e2e8f0',
    'table_header':   '#f8fafc',
    'table_alt':      '#f1f5f9',
}

FONTS = {
    'title':      ('Helvetica', 20, 'bold'),
    'heading':    ('Helvetica', 14, 'bold'),
    'subheading': ('Helvetica', 12, 'bold'),
    'body':       ('Helvetica', 11),
    'small':      ('Helvetica', 9),
    'button':     ('Helvetica', 11, 'bold'),
    'sidebar':    ('Helvetica', 11),
    'logo':       ('Helvetica', 12, 'bold'),
    'mono':       ('Courier', 10),
}
