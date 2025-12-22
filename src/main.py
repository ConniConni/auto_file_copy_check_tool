"""Main CLI application for file copy tool."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.config_loader import Config, PhaseCode, load_config
from src.excel_checker import check_review_checklist, check_review_record
from src.file_copier import (
    copy_document,
    copy_extra_file,
    copy_review_record_incoming,
    copy_review_record_outgoing,
)
from src.file_scanner import (
    OperationMode,
    scan_documents,
    scan_extra_files,
    scan_review_records,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="ファイルコピーチェックツール - 内部/外部エリア間のファイル同期支援"
    )
    parser.add_argument(
        "-i",
        "--config",
        type=str,
        default="config.ini",
        help="設定ファイルのパス (デフォルト: config.ini)",
    )
    return parser.parse_args()


def setup_logging() -> None:
    """Setup logging configuration."""
    log_filename = f"file_copy_tool_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Set console handler to INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger().handlers[1] = console_handler


def get_user_input(config: Config) -> tuple[str, str, str, list[PhaseCode], OperationMode, int]:
    """Get user input for operation parameters.

    Args:
        config: Configuration object (may contain default values).

    Returns:
        tuple: (project_name, quarter, item_name, phases, mode, days_ago)
    """
    print("\n=== ファイルコピーチェックツール ===\n")

    # Get project information (use config defaults if available)
    if config.project_name:
        project_name = config.project_name
        print(f"案件名: {project_name} (config.iniから取得)")
    else:
        project_name = input("案件名を入力してください: ").strip()

    if config.quarter:
        quarter = config.quarter
        print(f"クォータ: {quarter} (config.iniから取得)")
    else:
        quarter = input("クォータを入力してください (例: 2025_4Q): ").strip()

    if config.item_name is not None:
        # Use config value (may be empty string)
        item_name = config.item_name
        display_item = item_name if item_name else "(なし)"
        print(f"アイテム名: {display_item} (config.iniから取得)")
    else:
        # Prompt user (allow empty input)
        item_name = input("アイテム名を入力してください (空欄可): ").strip()

    # Get phase selection
    print("\n工程を選択してください:")
    print("1. 030.調査")
    print("2. 040.設計")
    print("3. 050.製造")
    print("4. 060.UD作成")
    print("5. 070.UD消化")
    print("6. 080.SD作成")
    print("7. 090.SD消化")
    print("8. 全工程")

    phase_choice = input("選択 (1-8): ").strip()

    phase_mapping = {
        "1": [PhaseCode.PHASE_030],
        "2": [PhaseCode.PHASE_040],
        "3": [PhaseCode.PHASE_050],
        "4": [PhaseCode.PHASE_060],
        "5": [PhaseCode.PHASE_070],
        "6": [PhaseCode.PHASE_080],
        "7": [PhaseCode.PHASE_090],
        "8": list(PhaseCode),
    }

    phases = phase_mapping.get(phase_choice, list(PhaseCode))

    # Get operation mode
    print("\n動作モードを選択してください:")
    print("1. Outgoing (内部→外部: 提出)")
    print("2. Incoming (外部→内部: 取込)")

    mode_choice = input("選択 (1-2): ").strip()
    mode = OperationMode.OUTGOING if mode_choice == "1" else OperationMode.INCOMING

    # Get days filter
    days_input = input("\n期間フィルタ（N日前以降、0=今日のみ）: ").strip()
    try:
        days_ago = int(days_input)
    except ValueError:
        days_ago = 0

    return project_name, quarter, item_name, phases, mode, days_ago


def scan_all_files(
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    phases: list[PhaseCode],
    mode: OperationMode,
    days_ago: int,
) -> dict[str, list[Path]]:
    """Scan all target files.

    Args:
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        phases: List of phase codes to process.
        mode: Operation mode.
        days_ago: Number of days ago to filter files.

    Returns:
        dict: Dictionary of file categories and their file lists.
    """
    all_files: dict[str, list[Path]] = {
        "documents": [],
        "review_records": [],
        "extra_files": [],
    }

    for phase in phases:
        # Scan documents
        docs = scan_documents(config, project_name, quarter, item_name, phase, mode, days_ago)
        all_files["documents"].extend(docs)

        # Scan review records
        records = scan_review_records(
            config, project_name, quarter, item_name, phase, mode, days_ago
        )
        all_files["review_records"].extend(records)

        # Scan extra files (outgoing only)
        if mode == OperationMode.OUTGOING:
            extras = scan_extra_files(
                config, project_name, quarter, item_name, phase, mode, days_ago
            )
            all_files["extra_files"].extend(extras)

    return all_files


def display_dry_run(
    all_files: dict[str, list[Path]], mode: OperationMode, config: Config
) -> None:
    """Display dry run results.

    Args:
        all_files: Dictionary of file categories and their file lists.
        mode: Operation mode.
        config: Configuration object.
    """
    print("\n=== スキャン結果 ===\n")

    total_count = sum(len(files) for files in all_files.values())

    if total_count == 0:
        print("対象ファイルが見つかりませんでした。")
        return

    # Display documents
    if all_files["documents"]:
        print(f"【ドキュメント本体】 ({len(all_files['documents'])}件)")
        for file_path in all_files["documents"]:
            print(f"  - {file_path.name}")

            # Check Excel content if outgoing mode
            if mode == OperationMode.OUTGOING and file_path.suffix == ".xlsx":
                # For now, skip checking documents (only check review records/checklists)
                pass
        print()

    # Display review records
    if all_files["review_records"]:
        print(f"【レビュー記録表】 ({len(all_files['review_records'])}件)")
        for file_path in all_files["review_records"]:
            status = "OK"
            if mode == OperationMode.OUTGOING:
                result = check_review_record(file_path)
                if not result.is_ok:
                    status = f"NG ({', '.join(result.errors)})"

            print(f"  - {file_path.name} [{status}]")
        print()

    # Display extra files
    if all_files["extra_files"]:
        print(f"【例外ファイル】 ({len(all_files['extra_files'])}件)")
        for file_path in all_files["extra_files"]:
            print(f"  - {file_path.name}")
        print()

    print(f"合計: {total_count}件")


def execute_copy(
    all_files: dict[str, list[Path]],
    config: Config,
    project_name: str,
    quarter: str,
    item_name: str,
    mode: OperationMode,
) -> tuple[int, int]:
    """Execute file copying.

    Args:
        all_files: Dictionary of file categories and their file lists.
        config: Configuration object.
        project_name: Project name.
        quarter: Quarter (e.g., "2025_4Q").
        item_name: Item name.
        mode: Operation mode.

    Returns:
        tuple: (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0

    # Determine phase for each file (simplified: extract from path)
    def get_phase_from_path(file_path: Path) -> PhaseCode | None:
        for part in file_path.parts:
            for phase in PhaseCode:
                phase_name_map = {
                    PhaseCode.PHASE_030: "030.調査",
                    PhaseCode.PHASE_040: "040.設計",
                    PhaseCode.PHASE_050: "050.製造",
                    PhaseCode.PHASE_060: "060.UD作成",
                    PhaseCode.PHASE_070: "070.UD消化",
                    PhaseCode.PHASE_080: "080.SD作成",
                    PhaseCode.PHASE_090: "090.SD消化",
                }
                if part == phase_name_map[phase]:
                    return phase
        return None

    # Copy documents
    for file_path in all_files["documents"]:
        phase = get_phase_from_path(file_path)
        if phase is None:
            logging.error(f"工程を特定できません: {file_path}")
            failure_count += 1
            continue

        if copy_document(file_path, config, project_name, quarter, item_name, phase, mode):
            success_count += 1
        else:
            failure_count += 1

    # Copy review records
    for file_path in all_files["review_records"]:
        phase = get_phase_from_path(file_path)
        if phase is None:
            logging.error(f"工程を特定できません: {file_path}")
            failure_count += 1
            continue

        if mode == OperationMode.OUTGOING:
            if copy_review_record_outgoing(
                file_path, config, project_name, quarter, item_name, phase
            ):
                success_count += 1
            else:
                failure_count += 1
        else:  # INCOMING
            if copy_review_record_incoming(
                file_path, config, project_name, quarter, item_name, phase
            ):
                success_count += 1
            else:
                failure_count += 1

    # Copy extra files
    for file_path in all_files["extra_files"]:
        phase = get_phase_from_path(file_path)
        if phase is None:
            logging.error(f"工程を特定できません: {file_path}")
            failure_count += 1
            continue

        if copy_extra_file(file_path, config, project_name, quarter, item_name, phase):
            success_count += 1
        else:
            failure_count += 1

    return success_count, failure_count


def main() -> None:
    """Main entry point."""
    setup_logging()

    # Parse command line arguments
    args = parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logging.error(f"設定ファイルが見つかりません: {config_path}")
        sys.exit(1)

    try:
        config = load_config(config_path)
    except Exception as e:
        logging.error(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

    # Get user input
    project_name, quarter, item_name, phases, mode, days_ago = get_user_input(config)

    # Scan files
    logging.info("ファイルスキャンを開始します...")
    all_files = scan_all_files(config, project_name, quarter, item_name, phases, mode, days_ago)

    # Display dry run
    display_dry_run(all_files, mode, config)

    # Confirm execution
    total_count = sum(len(files) for files in all_files.values())
    if total_count == 0:
        return

    print()
    confirm = input("コピーを実行しますか？ (y/n): ").strip().lower()

    if confirm != "y":
        print("処理を中止しました。")
        return

    # Execute copy
    print("\nコピーを実行中...")
    success_count, failure_count = execute_copy(
        all_files, config, project_name, quarter, item_name, mode
    )

    # Display results
    print("\n=== 実行結果 ===")
    print(f"成功: {success_count}件")
    print(f"失敗: {failure_count}件")
    print(f"\nログファイル: {[h.baseFilename for h in logging.getLogger().handlers if hasattr(h, 'baseFilename')][0]}")


if __name__ == "__main__":
    main()
