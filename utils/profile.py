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
        from aws_xray_sdk.core import xray_recorder

        try:
            subsegment = xray_recorder.begin_subsegment(description)
            yield subsegment
        except Exception as exc:
            stack = traceback.extract_stack()
            subsegment.add_exception(exc, stack)
            raise
        finally:
            xray_recorder.end_subsegment()
    else:
        yield
