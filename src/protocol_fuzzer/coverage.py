"""Line-coverage instrumentation and safe execution of a target parser.

``execute`` runs a target on one input under ``sys.settrace``, records the set of
lines hit inside the target module (the coverage signal that guides the fuzzer),
and classifies the outcome. An expected :class:`ParseError` is a clean rejection;
any other escaping exception is a crash, tagged with the deepest target-module
frame so triage can bucket it.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from types import FrameType
from typing import Any

Edge = tuple[str, int]


@dataclass(frozen=True)
class Execution:
    edges: frozenset[Edge]
    crashed: bool
    exception_type: str | None
    message: str
    location: str | None


def execute(
    target: Callable[[bytes], Any],
    data: bytes,
    expected: tuple[type[Exception], ...],
) -> Execution:
    """Run ``target(data)`` under coverage and classify the outcome."""

    file_of_interest = target.__code__.co_filename
    hits: set[Edge] = set()

    def tracer(frame: FrameType, event: str, _arg: Any) -> Any:
        if event == "line" and frame.f_code.co_filename == file_of_interest:
            hits.add((frame.f_code.co_name, frame.f_lineno))
        return tracer

    crashed = False
    exception_type: str | None = None
    message = ""
    location: str | None = None

    # Preserve any outer trace function (e.g. coverage.py's) and restore it, so
    # instrumenting a target does not silently disable coverage of everything
    # else in the process.
    previous = sys.gettrace()
    sys.settrace(tracer)
    try:
        target(data)
    except expected:
        pass
    except Exception as exc:
        crashed = True
        exception_type = _qualified_name(type(exc))
        message = str(exc)[:200]
        location = _deepest_location(exc, file_of_interest) or exception_type
    finally:
        sys.settrace(previous)

    return Execution(
        edges=frozenset(hits),
        crashed=crashed,
        exception_type=exception_type,
        message=message,
        location=location,
    )


def _qualified_name(exc_type: type[BaseException]) -> str:
    if exc_type.__module__ in ("builtins", ""):
        return exc_type.__name__
    return f"{exc_type.__module__}.{exc_type.__name__}"


def _deepest_location(exc: BaseException, file_of_interest: str) -> str | None:
    location: str | None = None
    tb = exc.__traceback__
    while tb is not None:
        code = tb.tb_frame.f_code
        if code.co_filename == file_of_interest:
            location = f"{code.co_name}:{tb.tb_lineno}"
        tb = tb.tb_next
    return location
