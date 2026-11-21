"""Coordinate LocalREPL's process-wide stdout/cwd across recursive workers."""

import os
import sys
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import Any, Concatenate, ParamSpec, TypeVar

EXECUTION_LOCK = threading.RLock()
EXECUTION_STATE = threading.local()
P = ParamSpec("P")
T = TypeVar("T")


def serialized_execution(
    function: Callable[Concatenate[Any, P], T],
) -> Callable[Concatenate[Any, P], T]:
    """Own the whole cell before acquiring process-wide execution state."""

    @wraps(function)
    def call(owner: Any, *args: P.args, **kwargs: P.kwargs) -> T:
        with owner._execution_lock:
            return function(owner, *args, **kwargs)

    return call


@contextmanager
def local_execution() -> Iterator[None]:
    with EXECUTION_LOCK:
        if not hasattr(EXECUTION_STATE, "frames"):
            EXECUTION_STATE.frames = []
            EXECUTION_STATE.held = 0
        EXECUTION_STATE.frames.append((sys.stdout, sys.stderr, os.getcwd()))
        EXECUTION_STATE.held += 1
        try:
            yield
        finally:
            EXECUTION_STATE.held -= 1
            EXECUTION_STATE.frames.pop()


@contextmanager
def tool_execution() -> Iterator[None]:
    """Park stdout/cwd while a tool waits, allowing children to acquire execution."""
    held = getattr(EXECUTION_STATE, "held", 0)
    if not held:
        yield
        return
    current = (sys.stdout, sys.stderr, os.getcwd())
    ambient = EXECUTION_STATE.frames[0]
    sys.stdout, sys.stderr = ambient[:2]
    os.chdir(ambient[2])
    EXECUTION_STATE.held = 0
    for _ in range(held):
        EXECUTION_LOCK.release()
    try:
        yield
    finally:
        for _ in range(held):
            EXECUTION_LOCK.acquire()
        EXECUTION_STATE.held = held
        sys.stdout, sys.stderr = current[:2]
        os.chdir(current[2])


def releases_execution(function: Callable[P, T]) -> Callable[P, T]:
    @wraps(function)
    def call(*args: P.args, **kwargs: P.kwargs) -> T:
        with tool_execution():
            return function(*args, **kwargs)

    return call
