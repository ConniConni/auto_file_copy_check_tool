"""Tests for main module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import parse_args


class TestParseArgs:
    """Test suite for command line argument parsing."""

    def test_parse_args_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test parse_args with default config path.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        # Mock sys.argv to simulate running without arguments
        monkeypatch.setattr(sys, "argv", ["main.py"])

        args = parse_args()

        assert args.config == "config.ini"

    def test_parse_args_with_short_option(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test parse_args with -i option.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        test_config_path = "./custom/path/to/config.ini"
        monkeypatch.setattr(sys, "argv", ["main.py", "-i", test_config_path])

        args = parse_args()

        assert args.config == test_config_path

    def test_parse_args_with_long_option(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test parse_args with --config option.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        test_config_path = "/absolute/path/to/config.ini"
        monkeypatch.setattr(sys, "argv", ["main.py", "--config", test_config_path])

        args = parse_args()

        assert args.config == test_config_path

    def test_parse_args_with_relative_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test parse_args with relative path.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        test_config_path = "../parent/config.ini"
        monkeypatch.setattr(sys, "argv", ["main.py", "-i", test_config_path])

        args = parse_args()

        assert args.config == test_config_path


class TestMainIntegration:
    """Test suite for main() integration tests."""

    def test_main_with_missing_config_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test main() exits when config file does not exist.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
            tmp_path: Temporary directory path provided by pytest.
        """
        non_existent_config = tmp_path / "non_existent.ini"
        monkeypatch.setattr(sys, "argv", ["main.py", "-i", str(non_existent_config)])

        with pytest.raises(SystemExit) as exc_info:
            from src.main import main

            main()

        assert exc_info.value.code == 1

    def test_main_with_invalid_config_content(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test main() exits when config file has invalid content.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
            tmp_path: Temporary directory path provided by pytest.
        """
        # Create invalid config file
        invalid_config = tmp_path / "invalid.ini"
        invalid_config.write_text("[InvalidSection]\ninvalid_key = invalid_value")

        monkeypatch.setattr(sys, "argv", ["main.py", "-i", str(invalid_config)])

        with pytest.raises(SystemExit) as exc_info:
            from src.main import main

            main()

        assert exc_info.value.code == 1
