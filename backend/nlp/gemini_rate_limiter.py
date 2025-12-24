from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

# Global semaphore: allow only one Gemini API call at a time.
# This is process-wide (per Uvicorn worker).
_GEMINI_SEMAPHORE = threading.Semaphore(1)


@contextmanager
def gemini_call_slot() -> Iterator[None]:
    """Serialize Gemini API calls.

    Any concurrent code attempting a Gemini call will block here until the
    current call finishes. This reduces rate-limit bursts.
    """
    _GEMINI_SEMAPHORE.acquire()
    try:
        yield
    finally:
        _GEMINI_SEMAPHORE.release()
