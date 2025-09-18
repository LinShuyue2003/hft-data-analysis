
import time
import math
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

"""
Simple REST downloader with exponential backoff and 429 handling.
"""

def make_session(total=5, backoff=0.5):
    """Create a requests session with retry policy."""
    sess = requests.Session()
    retry = Retry(total=total, read=total, connect=total, backoff_factor=backoff, status_forcelist=[429,500,502,503,504])
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    return sess

def get_with_backoff(url, params=None, headers=None, max_attempts=8):
    """GET with manual exponential backoff as an extra safety."""
    sess = make_session()
    for i in range(max_attempts):
        r = sess.get(url, params=params, headers=headers, timeout=30)
        if r.status_code == 429:
            wait = min(60, (2 ** i) * 0.5)
            time.sleep(wait); continue
        r.raise_for_status()
        return r
    raise RuntimeError("Too many retries")
