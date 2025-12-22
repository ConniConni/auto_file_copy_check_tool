"""File scanner module for discovering target files."""

from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path

from src.config_loader import Config, PhaseCode


class OperationMode(StrEnum):
    """Enumeration of operation modes."""

    OUTGOING = "OUTGOING"  # Internal -> External (submission)
    INCOMING = "INCOMING"  # External -> Internal (intake)


def should_include_file(file_path: Path, days_ago: int) -> bool:
    """Check if file should be included based on modification time.

    Args:
        file_path: Path to the file to check.
        days_ago: Number of days ago from today (0 = today only).

    Returns:
        bool: True if file should be included, False otherwise.
    """
    cutoff_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=days_ago
    )
    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return file_mtime >= cutoff_time


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
    phase_folder = f"{phase.value}.{_get_phase_name(phase)}"

    # If item_name is empty, skip that hierarchy level
    if item_name.strip():
        return base_path / project_name / quarter / item_name / phase_folder
    else:
        return base_path / project_name / quarter / phase_folder


def _get_phase_name(phase: PhaseCode) -> str:
    """Get phase name in Japanese.

    Args:
        phase: Phase code.

    Returns:
        str: Phase name in Japanese.
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
    return phase_names[phase]


def scan_documents(
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
    mode: OperationMode,
    days_ago: int,
) -> list[Path]:
    """Scan document files.

    Args:
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.
        mode: Operation mode (OUTGOING or INCOMING).
        days_ago: Number of days ago to filter files.

    Returns:
        list[Path]: List of document file paths.
    """
    if mode == OperationMode.OUTGOING:
        base_path = config.base_path_internal
    else:  # INCOMING
        base_path = config.base_path_external

    phase_dir = _build_phase_path(base_path, project_name, quarter, item_name, phase)

    if not phase_dir.exists():
        return []

    patterns = config.document_patterns.get(phase, [])
    if not patterns:
        return []

    found_files: list[Path] = []
    for pattern in patterns:
        # Search for files matching the pattern
        matching_files = list(phase_dir.glob(f"{pattern}_*.xlsx"))
        for file_path in matching_files:
            if file_path.is_file() and should_include_file(file_path, days_ago):
                found_files.append(file_path)

    return found_files


def scan_review_records(
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
    mode: OperationMode,
    days_ago: int,
) -> list[Path]:
    """Scan review record files.

    Args:
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.
        mode: Operation mode (OUTGOING or INCOMING).
        days_ago: Number of days ago to filter files.

    Returns:
        list[Path]: List of review record file paths.
    """
    if mode == OperationMode.OUTGOING:
        base_path = config.base_path_internal
        # Search in 外部レビュー directory (recursively for date folders)
        artifacts_dir = (
            _build_phase_path(base_path, project_name, quarter, item_name, phase)
            / "成果物"
            / "外部レビュー"
        )
    else:  # INCOMING
        base_path = config.base_path_external
        # Search in 成果物 directory (no nested structure in external)
        artifacts_dir = (
            _build_phase_path(base_path, project_name, quarter, item_name, phase) / "成果物"
        )

    if not artifacts_dir.exists():
        return []

    # Search for review records (recursively to handle date folders)
    pattern = "レビュー記録表(社外)_*.xlsx"
    found_files: list[Path] = []

    for file_path in artifacts_dir.rglob(pattern):
        if file_path.is_file() and should_include_file(file_path, days_ago):
            found_files.append(file_path)

    return found_files


def scan_extra_files(
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phase: PhaseCode,
    mode: OperationMode,
    days_ago: int,
) -> list[Path]:
    """Scan extra files specified in configuration.

    Args:
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phase: Phase code.
        mode: Operation mode (OUTGOING or INCOMING).
        days_ago: Number of days ago to filter files.

    Returns:
        list[Path]: List of extra file paths.
    """
    if not config.extra_files:
        return []

    if mode == OperationMode.OUTGOING:
        base_path = config.base_path_internal
        # Search in 外部レビュー directory
        search_dir = (
            _build_phase_path(base_path, project_name, quarter, item_name, phase)
            / "成果物"
            / "外部レビュー"
        )
    else:  # INCOMING
        # Extra files are only for OUTGOING mode
        return []

    if not search_dir.exists():
        return []

    found_files: list[Path] = []
    for file_name in config.extra_files:
        # Search recursively for exact file name match
        for file_path in search_dir.rglob(file_name):
            if file_path.is_file() and should_include_file(file_path, days_ago):
                found_files.append(file_path)

    return found_files
