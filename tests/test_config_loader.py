"""Tests for config_loader module."""

from pathlib import Path
from tempfile import TemporaryDirectory
import configparser
import pytest

from src.config_loader import Config, load_config, PhaseCode


class TestConfigLoader:
    """Test suite for configuration loader."""

    def test_load_config_success(self, tmp_path: Path) -> None:
        """Test successful config file loading.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config_content = """[Paths]
base_path_internal = /test/internal
base_path_external = /test/external

[Documents]
030 = 調査検討書
040 = 機能設計書
050 =
060 = 単体試験仕様書
070 = 単体試験成績書
080 = 結合試験仕様書
090 = 結合試験成績書,試験結果報告書

[ExtraFiles]
include_files = test.pdf,sample.docx
"""
        config_file = tmp_path / "test_config.ini"
        config_file.write_text(config_content, encoding="utf-8")

        config = load_config(config_file)

        assert config.base_path_internal == Path("/test/internal")
        assert config.base_path_external == Path("/test/external")
        assert config.document_patterns[PhaseCode.PHASE_030] == ["調査検討書"]
        assert config.document_patterns[PhaseCode.PHASE_040] == ["機能設計書"]
        assert config.document_patterns[PhaseCode.PHASE_050] == []
        assert config.document_patterns[PhaseCode.PHASE_090] == ["結合試験成績書", "試験結果報告書"]
        assert config.extra_files == ["test.pdf", "sample.docx"]

    def test_load_config_file_not_found(self, tmp_path: Path) -> None:
        """Test error handling when config file does not exist.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        non_existent_file = tmp_path / "non_existent.ini"

        with pytest.raises(FileNotFoundError):
            load_config(non_existent_file)

    def test_load_config_missing_section(self, tmp_path: Path) -> None:
        """Test error handling when required section is missing.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config_content = """[Paths]
base_path_internal = /test/internal
base_path_external = /test/external
"""
        config_file = tmp_path / "invalid_config.ini"
        config_file.write_text(config_content, encoding="utf-8")

        with pytest.raises(configparser.NoSectionError):
            load_config(config_file)

    def test_load_config_missing_key(self, tmp_path: Path) -> None:
        """Test error handling when required key is missing.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config_content = """[Paths]
base_path_internal = /test/internal

[Documents]
030 = 調査検討書

[ExtraFiles]
include_files =
"""
        config_file = tmp_path / "invalid_config.ini"
        config_file.write_text(config_content, encoding="utf-8")

        with pytest.raises(configparser.NoOptionError):
            load_config(config_file)

    def test_config_empty_extra_files(self, tmp_path: Path) -> None:
        """Test handling of empty extra files configuration.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config_content = """[Paths]
base_path_internal = /test/internal
base_path_external = /test/external

[Documents]
030 = 調査検討書
040 = 機能設計書
050 =
060 = 単体試験仕様書
070 = 単体試験成績書
080 = 結合試験仕様書
090 = 結合試験成績書

[ExtraFiles]
include_files =
"""
        config_file = tmp_path / "config.ini"
        config_file.write_text(config_content, encoding="utf-8")

        config = load_config(config_file)

        assert config.extra_files == []

    def test_phase_code_enum(self) -> None:
        """Test PhaseCode enum values."""
        assert PhaseCode.PHASE_030.value == "030"
        assert PhaseCode.PHASE_040.value == "040"
        assert PhaseCode.PHASE_050.value == "050"
        assert PhaseCode.PHASE_060.value == "060"
        assert PhaseCode.PHASE_070.value == "070"
        assert PhaseCode.PHASE_080.value == "080"
        assert PhaseCode.PHASE_090.value == "090"

    def test_load_config_with_project_info(self, tmp_path: Path) -> None:
        """Test loading config with project information.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config_content = """[Paths]
base_path_internal = /test/internal
base_path_external = /test/external

[Documents]
030 = 調査検討書
040 = 機能設計書
050 =
060 = 単体試験仕様書
070 = 単体試験成績書
080 = 結合試験仕様書
090 = 結合試験成績書

[ExtraFiles]
include_files =

[Project]
project_name = TestProject
quarter = 2025_4Q
item_name = TestItem
"""
        config_file = tmp_path / "config_with_project.ini"
        config_file.write_text(config_content, encoding="utf-8")

        config = load_config(config_file)

        assert config.project_name == "TestProject"
        assert config.quarter == "2025_4Q"
        assert config.item_name == "TestItem"

    def test_load_config_without_project_section(self, tmp_path: Path) -> None:
        """Test loading config without project section.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config_content = """[Paths]
base_path_internal = /test/internal
base_path_external = /test/external

[Documents]
030 = 調査検討書
040 = 機能設計書
050 =
060 = 単体試験仕様書
070 = 単体試験成績書
080 = 結合試験仕様書
090 = 結合試験成績書

[ExtraFiles]
include_files =
"""
        config_file = tmp_path / "config_no_project.ini"
        config_file.write_text(config_content, encoding="utf-8")

        config = load_config(config_file)

        assert config.project_name is None
        assert config.quarter is None
        assert config.item_name is None

    def test_load_config_with_empty_project_values(self, tmp_path: Path) -> None:
        """Test loading config with empty project values.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config_content = """[Paths]
base_path_internal = /test/internal
base_path_external = /test/external

[Documents]
030 = 調査検討書
040 = 機能設計書
050 =
060 = 単体試験仕様書
070 = 単体試験成績書
080 = 結合試験仕様書
090 = 結合試験成績書

[ExtraFiles]
include_files =

[Project]
project_name =
quarter =
item_name =
"""
        config_file = tmp_path / "config_empty_project.ini"
        config_file.write_text(config_content, encoding="utf-8")

        config = load_config(config_file)

        assert config.project_name is None
        assert config.quarter is None
        assert config.item_name is None
