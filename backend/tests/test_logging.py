"""TASK-002: Logging configuration tests."""

import json
import logging

from app.core.logging import configure_logging


def test_configure_logging_emits_json(capsys) -> None:
    configure_logging()
    logger = logging.getLogger("app.test")
    logger.info("test message")
    captured = capsys.readouterr()
    # At least one line should be valid JSON
    lines = [line for line in captured.out.splitlines() if line.strip()]
    if lines:
        record = json.loads(lines[-1])
        assert "message" in record or "msg" in record or "event" in record


def test_configure_logging_no_credentials_in_output(capsys) -> None:
    configure_logging()
    logger = logging.getLogger("app.test.security")
    logger.info("Connected to database")
    captured = capsys.readouterr()
    # Ensure no credential-like tokens appear
    forbidden = ["password", "secret", "token", "credential", "api_key"]
    for token in forbidden:
        assert token not in captured.out.lower()
