"""Shared helpers for the security toolkit.

Small, dependency-light utilities: consistent console output, an
authorization prompt, and simple result reporting.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum


class Level(str, Enum):
    OK = "OK"
    INFO = "INFO"
    WARN = "WARN"
    FAIL = "FAIL"


_COLORS = {
    Level.OK: "\033[32m",
    Level.INFO: "\033[36m",
    Level.WARN: "\033[33m",
    Level.FAIL: "\033[31m",
}
_RESET = "\033[0m"


def _supports_color() -> bool:
    return sys.stdout.isatty()


def emit(level: Level, msg: str) -> None:
    """Print a single tagged line, colored when attached to a TTY."""
    tag = level.value
    if _supports_color():
        tag = f"{_COLORS[level]}{tag}{_RESET}"
    print(f"[{tag}] {msg}")


@dataclass
class Report:
    """Collects findings and computes a process exit code."""

    findings: list[tuple[Level, str]] = field(default_factory=list)

    def add(self, level: Level, msg: str) -> None:
        self.findings.append((level, msg))
        emit(level, msg)

    def ok(self, msg: str) -> None:
        self.add(Level.OK, msg)

    def info(self, msg: str) -> None:
        self.add(Level.INFO, msg)

    def warn(self, msg: str) -> None:
        self.add(Level.WARN, msg)

    def fail(self, msg: str) -> None:
        self.add(Level.FAIL, msg)

    @property
    def exit_code(self) -> int:
        if any(l is Level.FAIL for l, _ in self.findings):
            return 2
        if any(l is Level.WARN for l, _ in self.findings):
            return 1
        return 0

    def summary(self) -> None:
        counts = {lvl: 0 for lvl in Level}
        for lvl, _ in self.findings:
            counts[lvl] += 1
        emit(
            Level.INFO,
            "Summary: "
            f"{counts[Level.OK]} ok, {counts[Level.WARN]} warn, "
            f"{counts[Level.FAIL]} fail",
        )


def confirm_authorized(target: str) -> None:
    """Abort unless the operator confirms they are authorized to test target.

    Set env var TOOLKIT_ASSUME_AUTHORIZED=1 to skip in automated pipelines
    where authorization is already established out of band.
    """
    import os

    if os.environ.get("TOOLKIT_ASSUME_AUTHORIZED") == "1":
        return
    emit(Level.WARN, f"You are about to run against: {target}")
    ans = input("Confirm you are authorized to test this target [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        emit(Level.FAIL, "Authorization not confirmed. Aborting.")
        sys.exit(3)
