#!/usr/bin/env python3
"""Debug script to test file scanning."""

import logging
from pathlib import Path

from src.config_loader import load_config, PhaseCode
from src.file_scanner import OperationMode, scan_documents, scan_review_records

# Setup logging to DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
)

# Load test config
config_path = Path("config_test.ini")
config = load_config(config_path)

# Test parameters
project_name = "DeveloperSite対応"
quarter = "2025_4Q"
item_name = "ディベロッパサイト環境移行対応"
phase = PhaseCode.PHASE_030
mode = OperationMode.OUTGOING
days_ago = 7  # Use 7 days to ensure we catch the files

print("\n" + "="*80)
print("ドキュメントスキャンテスト")
print("="*80 + "\n")

docs = scan_documents(config, project_name, quarter, item_name, phase, mode, days_ago)
print(f"\n見つかったドキュメント: {len(docs)}件")
for doc in docs:
    print(f"  - {doc}")

print("\n" + "="*80)
print("レビュー記録スキャンテスト")
print("="*80 + "\n")

reviews = scan_review_records(config, project_name, quarter, item_name, phase, mode, days_ago)
print(f"\n見つかったレビュー記録: {len(reviews)}件")
for review in reviews:
    print(f"  - {review}")

print("\n" + "="*80)
print("期待される結果:")
print("  ドキュメント: 1件")
print("  レビュー記録: 2件（社外のみ）")
print("="*80 + "\n")
