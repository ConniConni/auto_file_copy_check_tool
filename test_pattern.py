#!/usr/bin/env python3
"""Test the new pattern matching."""

from pathlib import Path

# Test pattern matching
pattern_old = "レビュー記録表(社外)_*.xlsx"
pattern_new = "レビュー記録表(社外)*.xlsx"

test_files = [
    "レビュー記録表(社外)_1回目_調査_DeveloperSite対応.xlsx",  # アンダースコアあり
    "レビュー記録表(社外)1回目_調査_DeveloperSite対応.xlsx",   # アンダースコアなし
    "レビュー記録表(社外)調査.xlsx",                          # アンダースコアなし
    "レビュー記録表(社外).xlsx",                             # 記号なし
    "レビュー記録表(社外)_2回目.xlsx",                        # アンダースコアあり
]

print("パターンマッチングテスト\n")
print("=" * 80)
print(f"旧パターン: {pattern_old}")
print(f"新パターン: {pattern_new}")
print("=" * 80 + "\n")

print("テストファイル名:")
for filename in test_files:
    # Simulate glob matching
    match_old = Path(filename).match(pattern_old)
    match_new = Path(filename).match(pattern_new)

    status_old = "✅" if match_old else "❌"
    status_new = "✅" if match_new else "❌"

    print(f"{filename}")
    print(f"  旧: {status_old}  新: {status_new}")
    if not match_old and match_new:
        print(f"  → 新パターンで検出可能になりました！")
    print()

print("\n結論:")
print("新パターン「レビュー記録表(社外)*.xlsx」は:")
print("- アンダースコアありのファイル名も引き続きマッチ")
print("- アンダースコアなしのファイル名もマッチ")
print("- より柔軟なファイル名に対応可能")
