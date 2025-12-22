"""Tests for file_copier module."""

from pathlib import Path
import shutil
import pytest

from src.config_loader import Config, PhaseCode
from src.file_scanner import OperationMode
from src.file_copier import (
    copy_document,
    copy_review_record_outgoing,
    copy_review_record_incoming,
    copy_extra_file,
    find_matching_file_in_internal,
)


class TestCopyDocument:
    """Test suite for document copying."""

    def test_copy_document_outgoing_new_file(self, tmp_path: Path) -> None:
        """Test copying document from internal to external (new file).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup source
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        phase_dir.mkdir(parents=True)
        source_file = phase_dir / "調査検討書_案件A.xlsx"
        source_file.write_text("test content")

        # Setup destination
        external_base = tmp_path / "external"
        dest_phase_dir = external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        dest_phase_dir.mkdir(parents=True)

        config = Config(
            base_path_internal=internal_base,
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        success = copy_document(
            source_file=source_file,
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.OUTGOING,
        )

        assert success is True
        dest_file = dest_phase_dir / "調査検討書_案件A.xlsx"
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"

    def test_copy_document_incoming_overwrite(self, tmp_path: Path) -> None:
        """Test copying document from external to internal (overwrite).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup destination (internal)
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        phase_dir.mkdir(parents=True)
        dest_file = phase_dir / "調査検討書_案件A.xlsx"
        dest_file.write_text("old content")

        # Setup source (external)
        external_base = tmp_path / "external"
        source_phase_dir = external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        source_phase_dir.mkdir(parents=True)
        source_file = source_phase_dir / "調査検討書_案件A.xlsx"
        source_file.write_text("new content")

        config = Config(
            base_path_internal=internal_base,
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        success = copy_document(
            source_file=source_file,
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.INCOMING,
        )

        assert success is True
        assert dest_file.read_text() == "new content"

    def test_copy_document_with_empty_item_name(self, tmp_path: Path) -> None:
        """Test copying document when item_name is empty (no item hierarchy).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup source (no item_name hierarchy)
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "030.調査"
        phase_dir.mkdir(parents=True)
        source_file = phase_dir / "調査検討書_案件A.xlsx"
        source_file.write_text("test content")

        # Setup destination
        external_base = tmp_path / "external"

        config = Config(
            base_path_internal=internal_base,
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        success = copy_document(
            source_file=source_file,
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="",  # Empty item_name
            phase=PhaseCode.PHASE_030,
            mode=OperationMode.OUTGOING,
        )

        assert success is True
        dest_phase_dir = external_base / "案件A" / "2025_4Q" / "030.調査"
        dest_file = dest_phase_dir / "調査検討書_案件A.xlsx"
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"


class TestCopyReviewRecordOutgoing:
    """Test suite for copying review records in outgoing mode."""

    def test_copy_review_record_outgoing(self, tmp_path: Path) -> None:
        """Test copying review record from internal to external.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup source
        internal_base = tmp_path / "internal"
        artifacts_dir = (
            internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物" / "外部レビュー"
        )
        artifacts_dir.mkdir(parents=True)
        source_file = artifacts_dir / "レビュー記録表(社外)_1回目.xlsx"
        source_file.write_text("review content")

        # Setup destination
        external_base = tmp_path / "external"
        dest_artifacts_dir = external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物"
        dest_artifacts_dir.mkdir(parents=True)

        config = Config(
            base_path_internal=internal_base,
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        success = copy_review_record_outgoing(
            source_file=source_file,
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
        )

        assert success is True
        dest_file = dest_artifacts_dir / "レビュー記録表(社外)_1回目.xlsx"
        assert dest_file.exists()
        assert dest_file.read_text() == "review content"


class TestCopyReviewRecordIncoming:
    """Test suite for copying review records in incoming mode."""

    def test_copy_review_record_incoming_found(self, tmp_path: Path) -> None:
        """Test copying review record from external to internal (found).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup destination (internal) with existing file
        internal_base = tmp_path / "internal"
        internal_artifacts = (
            internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物" / "外部レビュー" / "20251219"
        )
        internal_artifacts.mkdir(parents=True)
        dest_file = internal_artifacts / "レビュー記録表(社外)_1回目.xlsx"
        dest_file.write_text("old review")

        # Setup source (external)
        external_base = tmp_path / "external"
        source_artifacts = external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物"
        source_artifacts.mkdir(parents=True)
        source_file = source_artifacts / "レビュー記録表(社外)_1回目.xlsx"
        source_file.write_text("new review")

        config = Config(
            base_path_internal=internal_base,
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        success = copy_review_record_incoming(
            source_file=source_file,
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
        )

        assert success is True
        assert dest_file.read_text() == "new review"

    def test_copy_review_record_incoming_not_found(self, tmp_path: Path) -> None:
        """Test copying review record when destination not found (skip).

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup source (external) only
        external_base = tmp_path / "external"
        source_artifacts = external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物"
        source_artifacts.mkdir(parents=True)
        source_file = source_artifacts / "レビュー記録表(社外)_1回目.xlsx"
        source_file.write_text("new review")

        # Internal base exists but no matching file
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        phase_dir.mkdir(parents=True)

        config = Config(
            base_path_internal=internal_base,
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        success = copy_review_record_incoming(
            source_file=source_file,
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
        )

        # Should return False as no matching file found
        assert success is False


class TestCopyExtraFile:
    """Test suite for copying extra files."""

    def test_copy_extra_file(self, tmp_path: Path) -> None:
        """Test copying extra file from internal to external.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        # Setup source
        internal_base = tmp_path / "internal"
        artifacts_dir = (
            internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物" / "外部レビュー"
        )
        artifacts_dir.mkdir(parents=True)
        source_file = artifacts_dir / "補足資料.pdf"
        source_file.write_text("pdf content")

        # Setup destination
        external_base = tmp_path / "external"
        dest_artifacts_dir = external_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査" / "成果物"
        dest_artifacts_dir.mkdir(parents=True)

        config = Config(
            base_path_internal=internal_base,
            base_path_external=external_base,
            document_patterns={},
            extra_files=[],
        )

        success = copy_extra_file(
            source_file=source_file,
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
        )

        assert success is True
        dest_file = dest_artifacts_dir / "補足資料.pdf"
        assert dest_file.exists()
        assert dest_file.read_text() == "pdf content"


class TestFindMatchingFileInInternal:
    """Test suite for finding matching files in internal area."""

    def test_find_matching_file_found(self, tmp_path: Path) -> None:
        """Test finding matching file in internal area.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        artifacts_dir = phase_dir / "成果物" / "外部レビュー" / "20251219"
        artifacts_dir.mkdir(parents=True)

        target_file = artifacts_dir / "レビュー記録表(社外)_1回目.xlsx"
        target_file.touch()

        config = Config(
            base_path_internal=internal_base,
            base_path_external=tmp_path / "external",
            document_patterns={},
            extra_files=[],
        )

        found_file = find_matching_file_in_internal(
            file_name="レビュー記録表(社外)_1回目.xlsx",
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
        )

        assert found_file is not None
        assert found_file.name == "レビュー記録表(社外)_1回目.xlsx"

    def test_find_matching_file_not_found(self, tmp_path: Path) -> None:
        """Test when matching file is not found in internal area.

        Args:
            tmp_path: Temporary directory path provided by pytest.
        """
        internal_base = tmp_path / "internal"
        phase_dir = internal_base / "案件A" / "2025_4Q" / "アイテムX" / "030.調査"
        phase_dir.mkdir(parents=True)

        config = Config(
            base_path_internal=internal_base,
            base_path_external=tmp_path / "external",
            document_patterns={},
            extra_files=[],
        )

        found_file = find_matching_file_in_internal(
            file_name="レビュー記録表(社外)_1回目.xlsx",
            config=config,
            project_name="案件A",
            quarter="2025_4Q",
            item_name="アイテムX",
            phase=PhaseCode.PHASE_030,
        )

        assert found_file is None
