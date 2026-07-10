import time
import functools
import logging

logger = logging.getLogger(__name__)

TRANSIENT_MARKERS = ("503", "UNAVAILABLE", "overloaded", "rate limit", "429")


def retry_on_transient_error(max_attempts: int = 3, base_delay: float = 2.0):
    """Retry a function with exponential backoff if the error looks transient
    (e.g. Gemini 503 UNAVAILABLE / overload). Non-transient errors raise immediately."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    is_transient = any(marker in str(e) for marker in TRANSIENT_MARKERS)
                    if not is_transient or attempt == max_attempts:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Transient error on attempt {attempt}/{max_attempts}, "
                        f"retrying in {delay:.0f}s: {e}"
                    )
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator