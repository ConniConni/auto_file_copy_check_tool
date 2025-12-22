"""Tests for file_scanner module."""

from datetime import datetime, timedelta
from pathlib import Path
import time
import pytest

from src.config_loader import Config, PhaseCode
from src.file_scanner import (
    OperationMode,
    scan_documents,
    scan_review_records,
    scan_extra_files,
    should_include_file,
)


class TestFileScannerUtils:
    """Test suite for file scanner utility functions."""

    def test_should_include_file_today(self, tmp_path: Path) -> None:
        """Test file inclusion with today filter.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        test_file = tmp_path / "test.txt"
        test_file.touch()

        assert should_include_file(test_file, days_ago=0) is True

    def test_should_include_file_old(self, tmp_path: Path) -> None:
        """Test file exclusion for old files.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        test_file = tmp_path / "old.txt"
        test_file.touch()

        # Set modification time to 10 days ago
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        test_file.touch()
        import os
        os.utime(test_file, (old_time, old_time))

        assert should_include_file(test_file, days_ago=1) is False

    def test_should_include_file_within_range(self, tmp_path: Path) -> None:
        """Test file inclusion within specified days range.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        test_file = tmp_path / "recent.txt"
        test_file.touch()

        # File just created should be included in 7-day range
        assert should_include_file(test_file, days_ago=7) is True


class TestScanDocuments:
    """Test suite for document scanning."""

    def test_scan_documents_outgoing(self, tmp_path: Path) -> None:
        """Test scanning documents in outgoing mode (internal -> external).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup directory structure
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        phase_dir.mkdir(parents=True)

        # Create test documents
        doc1 = phase_dir / "調査検討書_案件A_アイテムX.xlsx"
        doc1.touch()
        doc2 = phase_dir / "レビュー記録表_調査_社内_1回目.xlsx"  # Should be ignored
        doc2.touch()

        config = Config(
            base_path_internal=internal_base,
            base_path_external=tmp_path / "external",
            document_patterns={PhaseCode.PHASE_030: ["調査検討書"]},
            extra_files=[],
        )

        files = scan_documents(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.OUTGOING,
            days_ago=0,
        )

        assert len(files) == 1
        assert files[0].name == "調査検討書_案件A_アイテムX.xlsx"

    def test_scan_documents_incoming(self, tmp_path: Path) -> None:
        """Test scanning documents in incoming mode (external -> internal).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup directory structure
        external_base = tmp_path / "external"
        phase_dir = external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        phase_dir.mkdir(parents=True)

        # Create test documents
        doc1 = phase_dir / "調査検討書_案件A_アイテムX.xlsx"
        doc1.touch()

        config = Config(
            base_path_internal=tmp_path / "internal",
            base_path_external=external_base,
            document_patterns={PhaseCode.PHASE_030: ["調査検討書"]},
            extra_files=[],
        )

        files = scan_documents(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.INCOMING,
            days_ago=0,
        )

        assert len(files) == 1
        assert files[0].name == "調査検討書_案件A_アイテムX.xlsx"

    def test_scan_documents_multiple_patterns(self, tmp_path: Path) -> None:
        """Test scanning with multiple document patterns.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "アイテムX" / "090.SD消化"
        phase_dir.mkdir(parents=True)

        # Create test documents
        doc1 = phase_dir / "結合試験成績書_案件A.xlsx"
        doc1.touch()
        doc2 = phase_dir / "試験結果報告書_案件A.xlsx"
        doc2.touch()
        doc3 = phase_dir / "その他ドキュメント_案件A.xlsx"  # Should be ignored
        doc3.touch()

        config = Config(
            base_path_internal=internal_base,
            base_path_external=tmp_path / "external",
            document_patterns={PhaseCode.PHASE_090: ["結合試験成績書", "試験結果報告書"]},
            extra_files=[],
        )

        files = scan_documents(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_090,
            mode=OperationMode.OUTGOING,
            days_ago=0,
        )

        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "結合試験成績書_案件A.xlsx" in file_names
        assert "試験結果報告書_案件A.xlsx" in file_names

    def test_scan_documents_with_empty_item_name(self, tmp_path: Path) -> None:
        """Test scanning documents when item_name is empty (no item hierarchy).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup directory structure without item_name hierarchy
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "030.調査"
        phase_dir.mkdir(parents=True)

        # Create test documents
        doc1 = phase_dir / "調査検討書_案件A.xlsx"
        doc1.touch()

        config = Config(
            base_path_internal=internal_base,
            base_path_external=tmp_path / "external",
            document_patterns={PhaseCode.PHASE_030: ["調査検討書"]},
            extra_files=[],
        )

        files = scan_documents(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="",  # Empty item_name
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.OUTGOING,
            days_ago=0,
        )

        assert len(files) == 1
        assert files[0].name == "調査検討書_案件A.xlsx"


class TestScanReviewRecords:
    """Test suite for review record scanning."""

    def test_scan_review_records_outgoing(self, tmp_path: Path) -> None:
        """Test scanning review records in outgoing mode.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        internal_base = tmp_path / "internal"
        artifacts_dir = (
            internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物" / "外部レビュー"
        )
        artifacts_dir.mkdir(parents=True)

        # Create review records in date folder
        date_folder = artifacts_dir / "20251219"
        date_folder.mkdir()
        record1 = date_folder / "レビュー記録表(社外)_1回目_調査_案件A.xlsx"
        record1.touch()

        # Create another record without date folder
        record2 = artifacts_dir / "レビュー記録表(社外)_2回目_調査_案件A.xlsx"
        record2.touch()

        # Create internal review record (should be ignored)
        internal_record = artifacts_dir.parent / "内部レビュー" / "レビュー記録表_調査_社内_1回目.xlsx"
        internal_record.parent.mkdir(parents=True)
        internal_record.touch()

        config = Config(
            base_path_internal=internal_base,
            base_path_external=tmp_path / "external",
            document_patterns={},
            extra_files=[],
        )

        files = scan_review_records(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.OUTGOING,
            days_ago=0,
        )

        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "レビュー記録表(社外)_1回目_調査_案件A.xlsx" in file_names
        assert "レビュー記録表(社外)_2回目_調査_案件A.xlsx" in file_names

    def test_scan_review_records_incoming(self, tmp_path: Path) -> None:
        """Test scanning review records in incoming mode.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        external_base = tmp_path / "external"
        artifacts_dir = (
            external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物"
        )
        artifacts_dir.mkdir(parents=True)

        # Create review records
        record1 = artifacts_dir / "レビュー記録表(社外)_1回目_調査_案件A.xlsx"
        record1.touch()

        config = Config(
            base_path_internal=tmp_path / "internal",
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        files = scan_review_records(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.INCOMING,
            days_ago=0,
        )

        assert len(files) == 1
        assert files[0].name == "レビュー記録表(社外)_1回目_調査_案件A.xlsx"


class TestScanExtraFiles:
    """Test suite for extra files scanning."""

    def test_scan_extra_files_outgoing(self, tmp_path: Path) -> None:
        """Test scanning extra files in outgoing mode.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        internal_base = tmp_path / "internal"
        artifacts_dir = (
            internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物" / "外部レビュー"
        )
        artifacts_dir.mkdir(parents=True)

        # Create extra files
        extra1 = artifacts_dir / "補足資料.pdf"
        extra1.touch()
        extra2 = artifacts_dir / "説明書.docx"
        extra2.touch()
        extra3 = artifacts_dir / "不要ファイル.txt"  # Should be ignored
        extra3.touch()

        config = Config(
            base_path_internal=internal_base,
            base_path_external=tmp_path / "external",
            document_patterns={},
            extra_files=["補足資料.pdf", "説明書.docx"],
        )

        files = scan_extra_files(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.OUTGOING,
            days_ago=0,
        )

        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "補足資料.pdf" in file_names
        assert "説明書.docx" in file_names

    def test_scan_extra_files_empty_config(self, tmp_path: Path) -> None:
        """Test scanning when no extra files configured.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        config = Config(
            base_path_internal=tmp_path / "internal",
            base_path_external=tmp_path / "external",
            document_patterns={},
            extra_files=[],
        )

        files = scan_extra_files(
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.OUTGOING,
            days_ago=0,
        )

        assert len(files) == 0


class TestOperationMode:
    """Test suite for OperationMode enum."""

    def test_operation_mode_values(self) -> None:
        """Test OperationMode enum values."""
        assert OperationMode.OUTGOING.value == "OUTGOING"
        assert OperationMode.INCOMING.value == "INCOMING"
