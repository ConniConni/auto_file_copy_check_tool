#!/usr/bin/env python3
"""Debug script to test file copying."""

import logging
from pathlib import Path

from src.config_loader import load_config, PhaseCode
from src.file_scanner import OperationMode, scan_documents, scan_review_records
from src.file_copier import copy_document, copy_review_record_outgoing

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
days_ago = 7

print("\n" + "="*80)
print("ファイルコピーテスト - Outgoing（内部→外部）")
print("="*80 + "\n")

# Scan documents
docs = scan_documents(config, project_name, quarter, item_name, phase, mode, days_ago)
print(f"\n【ドキュメント】 スキャン結果: {len(docs)}件")

# Scan review records
reviews = scan_review_records(config, project_name, quarter, item_name, phase, mode, days_ago)
print(f"【レビュー記録】 スキャン結果: {len(reviews)}件\n")

success_count = 0
failure_count = 0

# Copy documents
print("\n--- ドキュメントコピー開始 ---")
for doc in docs:
    print(f"\nコピー中: {doc.name}")
    if copy_document(doc, config, project_name, quarter, item_name, phase, mode):
        success_count += 1
        print("  ✅ 成功")
    else:
        failure_count += 1
        print("  ❌ 失敗")

# Copy review records
print("\n--- レビュー記録コピー開始 ---")
for review in reviews:
    print(f"\nコピー中: {review.name}")
    if copy_review_record_outgoing(review, config, project_name, quarter, item_name, phase):
        success_count += 1
        print("  ✅ 成功")
    else:
        failure_count += 1
        print("  ❌ 失敗")

print("\n" + "="*80)
print(f"コピー結果: 成功={success_count}件 / 失敗={failure_count}件")
print("="*80 + "\n")

# Check external area
print("外部エリアのファイルを確認:")
external_phase_dir = config.base_path_external / project_name / quarter / item_name / "030.調査"
if external_phase_dir.exists():
    for file in external_phase_dir.rglob("*.xlsx"):
        print(f"  - {file.relative_to(config.base_path_external)}")
else:
    print("  ディレクトリが存在しません")
