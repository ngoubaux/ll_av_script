"""
Time utilities
"""


def get_sec(time_str: str) -> int:
    """Convert time string (HH:MM:SS) to seconds"""
    h, m, s = time_str.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)
