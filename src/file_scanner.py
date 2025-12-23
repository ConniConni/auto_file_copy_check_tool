"""File scanner module for discovering target files."""

import logging
from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path

from src.config_loader import Config, PhaseCode

logger = logging.getLogger(__name__)


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
    result = file_mtime >= cutoff_time
    logger.debug(
        f"ファイル時刻チェック: {file_path.name} | "
        f"更新日時={file_mtime.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"カットオフ={cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"結果={'OK' if result else 'NG (期間外)'}"
    )
    return result


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
        result = base_path / project_name / quarter / item_name / phase_folder
    else:
        result = base_path / project_name / quarter / phase_folder

    logger.debug(
        f"パス構築: base={base_path} | "
        f"案件={project_name} | Q={quarter} | "
        f"アイテム={'(なし)' if not item_name.strip() else item_name} | "
        f"工程={phase_folder} → {result}"
    )
    return result


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
    logger.debug(f"[ドキュメントスキャン開始] 工程={phase.value} モード={mode}")

    if mode == OperationMode.OUTGOING:
        base_path = config.base_path_internal
    else:  # INCOMING
        base_path = config.base_path_external

    phase_dir = _build_phase_path(base_path, project_name, quarter, item_name, phase)

    if not phase_dir.exists():
        logger.debug(f"工程ディレクトリが存在しません: {phase_dir}")
        return []

    patterns = config.document_patterns.get(phase, [])
    if not patterns:
        logger.debug(f"工程 {phase.value} にドキュメントパターンが設定されていません")
        return []

    logger.debug(f"検索パターン: {patterns}")

    found_files: list[Path] = []
    for pattern in patterns:
        # Search for files matching the pattern
        search_pattern = f"{pattern}_*.xlsx"
        logger.debug(f"パターンで検索中: {search_pattern} in {phase_dir}")
        matching_files = list(phase_dir.glob(search_pattern))
        logger.debug(f"パターン '{pattern}' で {len(matching_files)} 件のファイルが見つかりました")
        for file_path in matching_files:
            if file_path.is_file() and should_include_file(file_path, days_ago):
                found_files.append(file_path)
                logger.debug(f"ドキュメント追加: {file_path.name}")

    logger.debug(f"[ドキュメントスキャン完了] 合計 {len(found_files)} 件")
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
    logger.debug(f"[レビュー記録スキャン開始] 工程={phase.value} モード={mode}")

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

    logger.debug(f"レビュー記録検索ディレクトリ: {artifacts_dir}")

    if not artifacts_dir.exists():
        logger.debug(f"成果物ディレクトリが存在しません: {artifacts_dir}")
        return []

    # Search for review records (recursively to handle date folders)
    pattern = "レビュー記録表(社外)*.xlsx"
    logger.debug(f"レビュー記録パターンで再帰検索: {pattern}")
    found_files: list[Path] = []

    for file_path in artifacts_dir.rglob(pattern):
        logger.debug(f"レビュー記録候補: {file_path}")
        if file_path.is_file() and should_include_file(file_path, days_ago):
            found_files.append(file_path)
            logger.debug(f"レビュー記録追加: {file_path.name}")

    logger.debug(f"[レビュー記録スキャン完了] 合計 {len(found_files)} 件")
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
    logger.debug(f"[例外ファイルスキャン開始] 工程={phase.value} モード={mode}")

    if not config.extra_files:
        logger.debug("config.iniに例外ファイルが設定されていません")
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
        logger.debug("Incomingモードでは例外ファイルはスキップします")
        return []

    logger.debug(f"例外ファイル検索ディレクトリ: {search_dir}")

    if not search_dir.exists():
        logger.debug(f"検索ディレクトリが存在しません: {search_dir}")
        return []

    logger.debug(f"例外ファイルリスト: {config.extra_files}")
    found_files: list[Path] = []
    for file_name in config.extra_files:
        logger.debug(f"例外ファイル '{file_name}' を検索中...")
        # Search recursively for exact file name match
        for file_path in search_dir.rglob(file_name):
            logger.debug(f"例外ファイル候補: {file_path}")
            if file_path.is_file() and should_include_file(file_path, days_ago):
                found_files.append(file_path)
                logger.debug(f"例外ファイル追加: {file_path.name}")

    logger.debug(f"[例外ファイルスキャン完了] 合計 {len(found_files)} 件")
    return found_files
