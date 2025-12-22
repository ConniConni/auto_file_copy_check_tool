"""File copier module for copying files between internal and external areas."""

import logging
import shutil
from pathlib import Path

from src.config_loader import Config, PhaseCode
from src.file_scanner import OperationMode

logger = logging.getLogger(__name__)


def _build_phase_path(
    base_path: Path, project_name: str, quarter: str, item_name: str, phase: PhaseCode
) -> Path:
    """Build phase directory path.

    Args:
        base_path: Base path (internal or external).
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name (empty string to skip this hierarchy level).
        phase: Phase code.

    Returns:
        Path: Constructed phase directory path.
    """
    phase_names = {
        PhaseCode.PHASE_030: "調査",
        PhaseCode.PHASE_040: "設計",
        PhaseCode.PHASE_050: "製造",
        PhaseCode.PHASE_060: "UD作成",
        PhaseCode.PHASE_070: "UD消化",
        PhaseCode.PHASE_080: "SD作成",
        PhaseCode.PHASE_090: "SD消化",
    }
    phase_name = phase_names[phase]
    phase_folder = f"{phase.value}.{phase_name}"

    # If item_name is empty, skip that hierarchy level
    if item_name.strip():
        return base_path / project_name / quarter / item_name / phase_folder
    else:
        return base_path / project_name / quarter / phase_folder


def copy_document(
    source_file: Path,
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
    mode: OperationMode,
) -> bool:
    """Copy document file.

    Args:
        source_file: Source file path.
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.
        mode: Operation mode (OUTGOING or INCOMING).

    Returns:
        bool: True if copy succeeded, False otherwise.
    """
    try:
        if mode == OperationMode.OUTGOING:
            # Internal -> External
            dest_base = config.base_path_external
        else:  # INCOMING
            # External -> Internal
            dest_base = config.base_path_internal

        dest_phase_dir = _build_phase_path(dest_base, project_name, quarter, item_name, phase)
        dest_phase_dir.mkdir(parents=True, exist_ok=True)

        dest_file = dest_phase_dir / source_file.name
        shutil.copy2(source_file, dest_file)

        logger.info(f"ドキュメントをコピーしました: {source_file.name} -> {dest_file}")
        return True

    except PermissionError:
        logger.error(f"ファイルが開かれているためコピーできません: {source_file}")
        return False
    except Exception as e:
        logger.error(f"ファイルコピーに失敗しました: {source_file}, エラー: {e}")
        return False


def copy_review_record_outgoing(
    source_file: Path,
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
) -> bool:
    """Copy review record file from internal to external (outgoing mode).

    Args:
        source_file: Source file path.
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.

    Returns:
        bool: True if copy succeeded, False otherwise.
    """
    try:
        dest_base = config.base_path_external
        dest_phase_dir = _build_phase_path(dest_base, project_name, quarter, item_name, phase)
        dest_artifacts_dir = dest_phase_dir / "成果物"
        dest_artifacts_dir.mkdir(parents=True, exist_ok=True)

        dest_file = dest_artifacts_dir / source_file.name
        shutil.copy2(source_file, dest_file)

        logger.info(f"レビュー記録表をコピーしました: {source_file.name} -> {dest_file}")
        return True

    except PermissionError:
        logger.error(f"ファイルが開かれているためコピーできません: {source_file}")
        return False
    except Exception as e:
        logger.error(f"ファイルコピーに失敗しました: {source_file}, エラー: {e}")
        return False


def find_matching_file_in_internal(
    file_name: str,
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
) -> Path | None:
    """Find matching file in internal area by searching recursively.

    Args:
        file_name: File name to search for.
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.

    Returns:
        Path | None: Found file path or None if not found.
    """
    internal_base = config.base_path_internal
    phase_dir = _build_phase_path(internal_base, project_name, quarter, item_name, phase)

    if not phase_dir.exists():
        return None

    # Search recursively in phase directory
    for found_file in phase_dir.rglob(file_name):
        if found_file.is_file():
            return found_file

    return None


def copy_review_record_incoming(
    source_file: Path,
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
) -> bool:
    """Copy review record file from external to internal (incoming mode).

    Args:
        source_file: Source file path.
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.

    Returns:
        bool: True if copy succeeded, False otherwise.
    """
    try:
        # Find matching file in internal area
        dest_file = find_matching_file_in_internal(
            file_name=source_file.name,
            config=config,
            project_name=project_name,
            quarter=quarter,
            item_name=item_name,
            phase=phase,
        )

        if dest_file is None:
            logger.warning(
                f"コピー先が見つかりません（スキップ）: {source_file.name}"
            )
            return False

        shutil.copy2(source_file, dest_file)
        logger.info(f"レビュー記録表をコピーしました: {source_file.name} -> {dest_file}")
        return True

    except PermissionError:
        logger.error(f"ファイルが開かれているためコピーできません: {source_file}")
        return False
    except Exception as e:
        logger.error(f"ファイルコピーに失敗しました: {source_file}, エラー: {e}")
        return False


def copy_extra_file(
    source_file: Path,
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
) -> bool:
    """Copy extra file from internal to external (outgoing mode only).

    Args:
        source_file: Source file path.
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.

    Returns:
        bool: True if copy succeeded, False otherwise.
    """
    try:
        dest_base = config.base_path_external
        dest_phase_dir = _build_phase_path(dest_base, project_name, quarter, item_name, phase)
        dest_artifacts_dir = dest_phase_dir / "成果物"
        dest_artifacts_dir.mkdir(parents=True, exist_ok=True)

        dest_file = dest_artifacts_dir / source_file.name
        shutil.copy2(source_file, dest_file)

        logger.info(f"例外ファイルをコピーしました: {source_file.name} -> {dest_file}")
        return True

    except PermissionError:
        logger.error(f"ファイルが開かれているためコピーできません: {source_file}")
        return False
    except Exception as e:
        logger.error(f"ファイルコピーに失敗しました: {source_file}, エラー: {e}")
        return False
