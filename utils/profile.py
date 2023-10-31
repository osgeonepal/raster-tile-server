"""profile.py

Decorators for performance tracing.
"""

from typing import Iterator

import traceback
import contextlib


XRAY_PROFILE: bool = False

@contextlib.contextmanager
def trace(description: str) -> Iterator:
    if XRAY_PROFILE:
        print(description,'description')
        pass
    else:
        yield
