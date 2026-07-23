import threading
import time

_lock = threading.Lock()
_frame = None
_walk_summary = None
_walk_active = False
_distances = {"left": None, "front": None, "right": None}
_warning = "-"
_location = {"lat": None, "lon": None, "ts": None}


def set_frame(jpeg_bytes):
    global _frame
    with _lock:
        _frame = jpeg_bytes


def get_frame():
    with _lock:
        return _frame


def set_distances(left, front, right):
    global _distances
    with _lock:
        _distances = {"left": left, "front": front, "right": right}


def get_distances():
    with _lock:
        return dict(_distances)


def set_warning(text):
    global _warning
    with _lock:
        _warning = text


def get_warning():
    with _lock:
        return _warning


def set_location(lat, lon):
    global _location
    with _lock:
        _location = {"lat": lat, "lon": lon, "ts": time.time()}


def get_location():
    with _lock:
        return dict(_location)


def set_walk_summary(text):
    global _walk_summary
    with _lock:
        _walk_summary = {"text": text, "created_at": time.time()}


def get_walk_summary():
    with _lock:
        return dict(_walk_summary) if _walk_summary else None


def clear_walk_summary():
    global _walk_summary
    with _lock:
        _walk_summary = None


def set_walk_active(is_active):
    global _walk_active
    with _lock:
        _walk_active = is_active


def get_walk_active():
    with _lock:
        return _walk_active
