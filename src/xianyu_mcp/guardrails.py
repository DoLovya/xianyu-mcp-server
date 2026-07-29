from __future__ import annotations

import asyncio
import os
import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RequestGuardrailsConfig:
    read_min_interval: float
    read_jitter: float
    write_min_interval: float
    write_jitter: float
    backoff_base: float
    backoff_max: float
    cooldown_seconds: float

    @staticmethod
    def _get_float(key: str, default: float) -> float:
        raw = os.environ.get(key, "").strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    @classmethod
    def from_env(cls) -> RequestGuardrailsConfig:
        return cls(
            read_min_interval=cls._get_float("XIANYU_GUARD_READ_MIN_INTERVAL", 1.2),
            read_jitter=cls._get_float("XIANYU_GUARD_READ_JITTER", 0.8),
            write_min_interval=cls._get_float("XIANYU_GUARD_WRITE_MIN_INTERVAL", 20.0),
            write_jitter=cls._get_float("XIANYU_GUARD_WRITE_JITTER", 20.0),
            backoff_base=cls._get_float("XIANYU_GUARD_BACKOFF_BASE", 2.0),
            backoff_max=cls._get_float("XIANYU_GUARD_BACKOFF_MAX", 120.0),
            cooldown_seconds=cls._get_float("XIANYU_GUARD_COOLDOWN_SECONDS", 1800.0),
        )


class RequestGuardrails:
    def __init__(self) -> None:
        self._state_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._last_read_at = 0.0
        self._last_write_at = 0.0
        self._backoff_until = 0.0
        self._cooldown_until = 0.0
        self._suspicious_failures = 0

    @staticmethod
    def _now() -> float:
        return time.monotonic()

    @staticmethod
    def _rand(jitter: float) -> float:
        return random.random() * max(0.0, jitter)

    @staticmethod
    def _is_strong_risk_error(error: BaseException) -> bool:
        msg = str(error)
        return "FAIL_SYS_USER_VALIDATE" in msg

    @staticmethod
    def _is_suspicious_error(error: BaseException) -> bool:
        msg = str(error)
        if "FAIL_SYS_" in msg:
            return True
        if "XianyuRequestError" in msg:
            return True
        if "requests" in msg and "RequestException" in msg:
            return True
        return False

    def _require_not_in_cooldown(self, now: float) -> None:
        with self._state_lock:
            cooldown_until = self._cooldown_until
        if now < cooldown_until:
            remaining = max(0, int(cooldown_until - now))
            raise RuntimeError(f"风控冷却中，已暂停写操作，请稍后再试（remaining={remaining}s）")

    def _compute_delay(self, kind: str, now: float, cfg: RequestGuardrailsConfig) -> float:
        with self._state_lock:
            backoff_delay = max(0.0, self._backoff_until - now)
            if kind == "read":
                last = self._last_read_at
                min_interval = cfg.read_min_interval
                jitter = cfg.read_jitter
            else:
                last = self._last_write_at
                min_interval = cfg.write_min_interval
                jitter = cfg.write_jitter
        base_delay = max(0.0, (last + max(0.0, min_interval) + self._rand(jitter)) - now)
        return max(base_delay, backoff_delay)

    def _mark_call(self, kind: str, now: float) -> None:
        with self._state_lock:
            if kind == "read":
                self._last_read_at = now
            else:
                self._last_write_at = now

    def _on_success(self) -> None:
        with self._state_lock:
            self._suspicious_failures = 0
            self._backoff_until = 0.0

    def _on_error(self, error: BaseException, cfg: RequestGuardrailsConfig) -> None:
        now = self._now()
        if self._is_strong_risk_error(error):
            with self._state_lock:
                self._cooldown_until = max(self._cooldown_until, now + max(0.0, cfg.cooldown_seconds))
                self._suspicious_failures = 0
                self._backoff_until = 0.0
            return

        if not self._is_suspicious_error(error):
            return

        with self._state_lock:
            self._suspicious_failures += 1
            failures = self._suspicious_failures

        backoff = min(cfg.backoff_max, cfg.backoff_base * (2 ** max(0, failures - 1)))
        backoff = max(0.0, backoff) + self._rand(min(1.0, backoff))
        with self._state_lock:
            self._backoff_until = max(self._backoff_until, now + backoff)

    def run_read(self, fn: Callable[[], T]) -> T:
        cfg = RequestGuardrailsConfig.from_env()
        now = self._now()
        delay = self._compute_delay("read", now, cfg)
        if delay > 0:
            time.sleep(delay)
        self._mark_call("read", self._now())
        try:
            result = fn()
        except BaseException as exc:
            self._on_error(exc, cfg)
            raise
        self._on_success()
        return result

    def run_write(self, fn: Callable[[], T]) -> T:
        cfg = RequestGuardrailsConfig.from_env()
        with self._write_lock:
            now = self._now()
            self._require_not_in_cooldown(now)
            delay = self._compute_delay("write", now, cfg)
            if delay > 0:
                time.sleep(delay)
            self._mark_call("write", self._now())
            try:
                result = fn()
            except BaseException as exc:
                self._on_error(exc, cfg)
                raise
            self._on_success()
            return result

    def run_write_steps(self, fn: Callable[[Callable[[Callable[[], T]], T]], T]) -> T:
        cfg = RequestGuardrailsConfig.from_env()
        with self._write_lock:
            def call(step: Callable[[], T]) -> T:
                now = self._now()
                self._require_not_in_cooldown(now)
                delay = self._compute_delay("write", now, cfg)
                if delay > 0:
                    time.sleep(delay)
                self._mark_call("write", self._now())
                try:
                    result = step()
                except BaseException as exc:
                    self._on_error(exc, cfg)
                    raise
                self._on_success()
                return result

            return fn(call)

    async def run_read_async(self, fn: Callable[[], Any] | Callable[[], asyncio.Future]) -> Any:
        cfg = RequestGuardrailsConfig.from_env()
        now = self._now()
        delay = self._compute_delay("read", now, cfg)
        if delay > 0:
            await asyncio.sleep(delay)
        self._mark_call("read", self._now())
        try:
            result = fn()
            if asyncio.iscoroutine(result):
                result = await result
        except BaseException as exc:
            self._on_error(exc, cfg)
            raise
        self._on_success()
        return result

    async def run_write_async(self, fn: Callable[[], Any] | Callable[[], asyncio.Future]) -> Any:
        cfg = RequestGuardrailsConfig.from_env()
        await asyncio.to_thread(self._write_lock.acquire)
        try:
            now = self._now()
            self._require_not_in_cooldown(now)
            delay = self._compute_delay("write", now, cfg)
            if delay > 0:
                await asyncio.sleep(delay)
            self._mark_call("write", self._now())
            try:
                result = fn()
                if asyncio.iscoroutine(result):
                    result = await result
            except BaseException as exc:
                self._on_error(exc, cfg)
                raise
            self._on_success()
            return result
        finally:
            self._write_lock.release()

    async def run_write_steps_async(
        self,
        fn: Callable[[Callable[[Callable[[], Any] | Callable[[], asyncio.Future]], Any]], Any],
    ) -> Any:
        cfg = RequestGuardrailsConfig.from_env()
        await asyncio.to_thread(self._write_lock.acquire)
        try:
            async def call(step: Callable[[], Any] | Callable[[], asyncio.Future]) -> Any:
                now = self._now()
                self._require_not_in_cooldown(now)
                delay = self._compute_delay("write", now, cfg)
                if delay > 0:
                    await asyncio.sleep(delay)
                self._mark_call("write", self._now())
                try:
                    result = step()
                    if asyncio.iscoroutine(result):
                        result = await result
                except BaseException as exc:
                    self._on_error(exc, cfg)
                    raise
                self._on_success()
                return result

            result = fn(call)
            if asyncio.iscoroutine(result):
                return await result
            return result
        finally:
            self._write_lock.release()
