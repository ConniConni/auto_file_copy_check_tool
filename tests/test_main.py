"""Tests for main module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main import (
    apply_file_type_filter,
    create_indexed_file_list,
    parse_args,
    parse_selection_input,
)


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


class TestParseSelectionInput:
    """Test suite for parse_selection_input function."""

    def test_parse_single_number(self) -> None:
        """Test parsing single number."""
        result = parse_selection_input("5", 10)
        assert result == {5}

    def test_parse_multiple_numbers(self) -> None:
        """Test parsing multiple comma-separated numbers."""
        result = parse_selection_input("1,3,5", 10)
        assert result == {1, 3, 5}

    def test_parse_range(self) -> None:
        """Test parsing range specification."""
        result = parse_selection_input("3-7", 10)
        assert result == {3, 4, 5, 6, 7}

    def test_parse_mixed(self) -> None:
        """Test parsing mixed single numbers and ranges."""
        result = parse_selection_input("1,3-5,8,10-12", 15)
        assert result == {1, 3, 4, 5, 8, 10, 11, 12}

    def test_parse_with_spaces(self) -> None:
        """Test parsing with extra spaces."""
        result = parse_selection_input(" 1 , 3 - 5 , 8 ", 10)
        assert result == {1, 3, 4, 5, 8}

    def test_parse_out_of_range(self) -> None:
        """Test parsing with numbers out of range."""
        result = parse_selection_input("1,5,15,20", 10)
        assert result == {1, 5}

    def test_parse_invalid_input(self) -> None:
        """Test parsing with invalid input."""
        result = parse_selection_input("abc,def", 10)
        assert result == set()

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_selection_input("", 10)
        assert result == set()


class TestApplyFileTypeFilter:
    """Test suite for apply_file_type_filter function."""

    def test_filter_all(self) -> None:
        """Test filter with 'all' option."""
        all_files = {
            "documents": [Path("doc1.xlsx"), Path("doc2.xlsx")],
            "review_records": [Path("review1.xlsx")],
            "extra_files": [Path("extra1.pdf")],
        }

        result = apply_file_type_filter(all_files, "all")

        assert result == all_files

    def test_filter_documents(self) -> None:
        """Test filter with 'documents' option."""
        all_files = {
            "documents": [Path("doc1.xlsx"), Path("doc2.xlsx")],
            "review_records": [Path("review1.xlsx")],
            "extra_files": [Path("extra1.pdf")],
        }

        result = apply_file_type_filter(all_files, "documents")

        assert result["documents"] == all_files["documents"]
        assert result["extra_files"] == all_files["extra_files"]
        assert result["review_records"] == []

    def test_filter_reviews(self) -> None:
        """Test filter with 'reviews' option."""
        all_files = {
            "documents": [Path("doc1.xlsx"), Path("doc2.xlsx")],
            "review_records": [Path("review1.xlsx")],
            "extra_files": [Path("extra1.pdf")],
        }

        result = apply_file_type_filter(all_files, "reviews")

        assert result["documents"] == []
        assert result["extra_files"] == []
        assert result["review_records"] == all_files["review_records"]


class TestCreateIndexedFileList:
    """Test suite for create_indexed_file_list function."""

    def test_create_indexed_list(self) -> None:
        """Test creating indexed file list."""
        all_files = {
            "documents": [Path("doc1.xlsx"), Path("doc2.xlsx")],
            "review_records": [Path("review1.xlsx")],
            "extra_files": [Path("extra1.pdf")],
        }

        result = create_indexed_file_list(all_files)

        assert len(result) == 4
        assert result[0] == (1, "ドキュメント", Path("doc1.xlsx"))
        assert result[1] == (2, "ドキュメント", Path("doc2.xlsx"))
        assert result[2] == (3, "レビュー記録表", Path("review1.xlsx"))
        assert result[3] == (4, "例外ファイル", Path("extra1.pdf"))

    def test_create_indexed_list_empty(self) -> None:
        """Test creating indexed list with empty input."""
        all_files = {
            "documents": [],
            "review_records": [],
            "extra_files": [],
        }

        result = create_indexed_file_list(all_files)

        assert len(result) == 0
