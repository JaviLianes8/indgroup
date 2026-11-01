"""Handwritten contracts for input-free API and CLI diagnostics."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

import indgroup
from indgroup import (
    Grouping,
    format_number,
    number_symbols,
    parse_indian,
    parse_number,
    resolve_locale,
)

CALLS: list[Callable[[str], object]] = [
    parse_indian,
    lambda text: parse_indian("123." + text),
    lambda text: parse_number(text, "en"),
    lambda text: parse_number("123." + text, "en"),
    resolve_locale,
    number_symbols,
    lambda text: format_number(1, "en", grouping=cast(Grouping, text)),
]


@pytest.mark.parametrize("call", CALLS)
@pytest.mark.parametrize("canary", ["password=qa-canary-123", "private-canary", "\nprivate\x1b"])
def test_invalid_input_is_absent_from_api_errors(
    call: Callable[[str], object], canary: str
) -> None:
    with pytest.raises((ValueError, LookupError)) as raised:
        call(canary)
    message = str(raised.value)
    assert "canary" not in message and "private" not in message
    assert len(message) < 120 and "\n" not in message and "\x1b" not in message


def test_an_unknown_locale_is_absent_from_lookup_errors() -> None:
    with pytest.raises(LookupError) as raised:
        resolve_locale("zz-canary")
    assert "canary" not in str(raised.value)


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["-p"],
        ["-l", "password=qa-canary-123", "1"],
        ["-g", "password=qa-canary-123", "1"],
        ["--password=qa-canary-123"],
        ["-ppassword=qa-canary-123"],
        ["--parse=qa-canary-123"],
    ],
)
def test_cli_stderr_never_echoes_invalid_values_or_options(argv: list[str]) -> None:
    env = {**os.environ, "PYTHONPATH": str(Path(indgroup.__file__).resolve().parents[1])}
    done = subprocess.run(
        [sys.executable, "-m", "indgroup", *argv],
        input=b"password=qa-canary-123\n",
        capture_output=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert done.returncode == 2 and done.stdout == b""
    assert b"canary" not in done.stderr and b"password" not in done.stderr
    assert len(done.stderr) < 150 and done.stderr.count(b"\n") == 1
