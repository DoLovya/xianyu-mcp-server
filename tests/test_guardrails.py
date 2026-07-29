from __future__ import annotations

import os
import time
import unittest
from unittest.mock import patch

from xianyu_mcp.guardrails import RequestGuardrails


class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += max(0.0, float(seconds))

    async def asleep(self, seconds: float) -> None:
        self.t += max(0.0, float(seconds))


class TestRequestGuardrails(unittest.TestCase):
    def test_read_min_interval(self) -> None:
        clock = _FakeClock()
        guard = RequestGuardrails()
        calls: list[float] = []

        def fn():
            calls.append(clock.now())
            return 1

        with patch.dict(
            os.environ,
            {
                "XIANYU_GUARD_READ_MIN_INTERVAL": "1",
                "XIANYU_GUARD_READ_JITTER": "0",
                "XIANYU_GUARD_BACKOFF_BASE": "0",
                "XIANYU_GUARD_BACKOFF_MAX": "0",
            },
        ), patch.object(RequestGuardrails, "_now", side_effect=clock.now), patch.object(
            time, "sleep", side_effect=clock.sleep
        ):
            guard.run_read(fn)
            guard.run_read(fn)

        self.assertEqual(len(calls), 2)
        self.assertGreaterEqual(calls[1] - calls[0], 1.0)

    def test_backoff_on_suspicious_error(self) -> None:
        clock = _FakeClock()
        guard = RequestGuardrails()
        calls: list[float] = []

        def fail():
            raise RuntimeError("FAIL_SYS_TEST")

        def ok():
            calls.append(clock.now())
            return 1

        with patch.dict(
            os.environ,
            {
                "XIANYU_GUARD_READ_MIN_INTERVAL": "0",
                "XIANYU_GUARD_READ_JITTER": "0",
                "XIANYU_GUARD_BACKOFF_BASE": "2",
                "XIANYU_GUARD_BACKOFF_MAX": "10",
            },
        ), patch.object(RequestGuardrails, "_now", side_effect=clock.now), patch.object(
            RequestGuardrails, "_rand", return_value=0.0
        ), patch.object(time, "sleep", side_effect=clock.sleep):
            with self.assertRaises(RuntimeError):
                guard.run_read(fail)
            guard.run_read(ok)

        self.assertEqual(len(calls), 1)
        self.assertGreaterEqual(calls[0], 2.0)

    def test_cooldown_on_strong_risk_error_blocks_write(self) -> None:
        clock = _FakeClock()
        guard = RequestGuardrails()
        called = {"ok": 0}

        def strong_fail():
            raise RuntimeError("FAIL_SYS_USER_VALIDATE")

        def ok():
            called["ok"] += 1
            return 1

        with patch.dict(
            os.environ,
            {
                "XIANYU_GUARD_WRITE_MIN_INTERVAL": "0",
                "XIANYU_GUARD_WRITE_JITTER": "0",
                "XIANYU_GUARD_COOLDOWN_SECONDS": "60",
            },
        ), patch.object(RequestGuardrails, "_now", side_effect=clock.now), patch.object(
            time, "sleep", side_effect=clock.sleep
        ):
            with self.assertRaises(RuntimeError):
                guard.run_write(strong_fail)
            with self.assertRaises(RuntimeError):
                guard.run_write(ok)

        self.assertEqual(called["ok"], 0)

    def test_write_steps_respect_interval(self) -> None:
        clock = _FakeClock()
        guard = RequestGuardrails()
        calls: list[float] = []

        def step1():
            calls.append(clock.now())
            return 1

        def step2():
            calls.append(clock.now())
            return 2

        def run(call):
            call(step1)
            call(step2)
            return 0

        with patch.dict(
            os.environ,
            {
                "XIANYU_GUARD_WRITE_MIN_INTERVAL": "10",
                "XIANYU_GUARD_WRITE_JITTER": "0",
                "XIANYU_GUARD_BACKOFF_BASE": "0",
                "XIANYU_GUARD_BACKOFF_MAX": "0",
                "XIANYU_GUARD_COOLDOWN_SECONDS": "0",
            },
        ), patch.object(RequestGuardrails, "_now", side_effect=clock.now), patch.object(
            RequestGuardrails, "_rand", return_value=0.0
        ), patch.object(time, "sleep", side_effect=clock.sleep):
            guard.run_write_steps(run)

        self.assertEqual(len(calls), 2)
        self.assertGreaterEqual(calls[1] - calls[0], 10.0)


if __name__ == "__main__":
    unittest.main()

