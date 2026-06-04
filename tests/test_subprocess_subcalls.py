"""Tests for subprocess-backed parallel rlm_query_batched.

These tests target the building blocks (global semaphore, subprocess worker)
without standing up a full RLM + LLM backend, since spawning subprocesses
that go through the real client machinery is expensive and fragile.
"""

import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import dill
import pytest

from rlm.environments import local_repl as lr

# ---------------------------------------------------------------------------
# Helpers run in subprocesses — must be top-level for spawn to pickle them.
# ---------------------------------------------------------------------------


_TEST_SEMAPHORE = None


def _install_test_semaphore(sem) -> None:
    """ProcessPoolExecutor initializer — semaphores can't cross spawn via submit()."""
    global _TEST_SEMAPHORE
    _TEST_SEMAPHORE = sem


def _slot_holder(hold_seconds: float) -> tuple[float, float]:
    """Acquire the test semaphore, sleep, release. Returns (start_ts, end_ts)."""
    _TEST_SEMAPHORE.acquire()
    try:
        start = time.monotonic()
        time.sleep(hold_seconds)
        return (start, time.monotonic())
    finally:
        _TEST_SEMAPHORE.release()


def _isolated_writer(out_dir: str, payload: str) -> tuple[str, str]:
    """chdir into out_dir, write a file by relative path via three different
    APIs (open, os.open, pathlib), and return (cwd_seen, file_we_wrote)."""
    import pathlib

    os.chdir(out_dir)
    cwd_seen = os.getcwd()

    # Plain open with a relative path
    with open("via_open.txt", "w") as f:
        f.write(payload)

    # os.open with a relative path
    fd = os.open("via_os_open.txt", os.O_CREAT | os.O_WRONLY)
    try:
        os.write(fd, payload.encode())
    finally:
        os.close(fd)

    # pathlib relative path
    pathlib.Path("via_pathlib.txt").write_text(payload)

    return (cwd_seen, payload)


# ---------------------------------------------------------------------------
# Global semaphore enforcement
# ---------------------------------------------------------------------------


class TestGlobalSubprocessSemaphore:
    def test_semaphore_caps_concurrent_workers(self):
        """With N=2 slots and 4 workers each holding for 0.5s, total wall
        time must be at least ~1s (two waves of two)."""
        ctx = mp.get_context("spawn")
        sem = ctx.BoundedSemaphore(2)

        with ProcessPoolExecutor(
            max_workers=4,
            mp_context=ctx,
            initializer=_install_test_semaphore,
            initargs=(sem,),
        ) as pool:
            t0 = time.monotonic()
            futures = [pool.submit(_slot_holder, 0.5) for _ in range(4)]
            intervals = [f.result() for f in as_completed(futures)]
            wall = time.monotonic() - t0

        # Two waves of two — ≥1s total. Use generous bound to stay non-flaky.
        assert wall >= 0.9, f"semaphore did not cap concurrency: wall={wall:.2f}s"

        # Sweep over (start, +1) and (end, -1) events to confirm the live
        # count of holders never exceeds 2.
        events = []
        for s, e in intervals:
            events.append((s, 1))
            events.append((e, -1))
        events.sort()
        live = 0
        peak = 0
        for _, delta in events:
            live += delta
            peak = max(peak, live)
        assert peak <= 2, f"more than 2 workers held the semaphore concurrently: peak={peak}"

    def test_set_max_subprocesses_replaces_global_semaphore(self):
        """set_max_subprocesses(n) installs a fresh semaphore of size n."""
        original = lr._global_subprocess_semaphore
        try:
            lr.set_max_subprocesses(3)
            sem = lr._get_subprocess_semaphore()
            # BoundedSemaphore exposes the value via _value (CPython detail);
            # just confirm three acquires don't block and a fourth would.
            assert sem.acquire(timeout=0.1)
            assert sem.acquire(timeout=0.1)
            assert sem.acquire(timeout=0.1)
            assert not sem.acquire(timeout=0.1)
            # Cleanup: release what we acquired.
            sem.release()
            sem.release()
            sem.release()
        finally:
            lr._global_subprocess_semaphore = original

    def test_get_subprocess_semaphore_lazily_creates(self):
        """First call to _get_subprocess_semaphore creates with default size."""
        original = lr._global_subprocess_semaphore
        try:
            lr._global_subprocess_semaphore = None
            sem = lr._get_subprocess_semaphore()
            assert sem is not None
            assert lr._global_subprocess_semaphore is sem
        finally:
            lr._global_subprocess_semaphore = original


# ---------------------------------------------------------------------------
# Cwd isolation across parallel subprocess workers
# ---------------------------------------------------------------------------


class TestSubprocessCwdIsolation:
    def test_parallel_workers_each_have_their_own_cwd(self, tmp_path):
        """Four subprocesses each chdir into their own dir and write files
        via open/os.open/pathlib. None of the writes should cross-contaminate.
        """
        dirs = []
        for i in range(4):
            d = tmp_path / f"worker_{i}"
            d.mkdir()
            dirs.append(str(d))

        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=4, mp_context=ctx) as pool:
            futures = {pool.submit(_isolated_writer, dirs[i], f"payload-{i}"): i for i in range(4)}
            for fut in as_completed(futures):
                i = futures[fut]
                cwd, payload = fut.result()
                assert cwd == dirs[i]
                assert payload == f"payload-{i}"

        # Verify each file landed in the correct dir
        for i in range(4):
            for fname in ("via_open.txt", "via_os_open.txt", "via_pathlib.txt"):
                p = os.path.join(dirs[i], fname)
                assert os.path.exists(p), f"missing {p}"
                with open(p) as f:
                    assert f.read() == f"payload-{i}", f"wrong contents in {p}"

        # Spot-check: no cross-leak. dir 0 should not have dir 1's content.
        with open(os.path.join(dirs[0], "via_open.txt")) as f:
            assert f.read() == "payload-0"

    def test_parent_cwd_unchanged(self, tmp_path):
        """Subprocesses' chdir doesn't affect the parent's cwd."""
        before = os.getcwd()
        d = tmp_path / "iso"
        d.mkdir()
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as pool:
            pool.submit(_isolated_writer, str(d), "x").result()
        assert os.getcwd() == before


# ---------------------------------------------------------------------------
# _subprocess_worker_entry — exercise the dill envelope and semaphore
# ---------------------------------------------------------------------------


def _no_op_dill_job(semaphore) -> bytes:
    """Pretend to be a worker_entry that just returns a marker."""
    semaphore.acquire()
    try:
        return dill.dumps("ok")
    finally:
        semaphore.release()


class TestDillEnvelope:
    def test_dill_serializes_lambda_in_job_payload(self):
        """A lambda inside a custom_tools-like dict survives dill round-trip
        but would fail under stdlib pickle. Proves dill actually buys us
        something for the subprocess path."""
        import pickle

        payload = {
            "kind": "rlm",
            "custom_sub_tools": {"square": lambda x: x * x},
        }
        # stdlib pickle should fail on the lambda
        with pytest.raises((pickle.PicklingError, AttributeError)):
            pickle.dumps(payload)

        # dill should handle it
        roundtrip = dill.loads(dill.dumps(payload))
        assert roundtrip["custom_sub_tools"]["square"](5) == 25
