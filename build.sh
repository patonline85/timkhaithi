#!/usr/bin/env bash
# Dừng lại ngay khi có lỗi
set -o errexit

echo "--- Cài đặt các thư viện ---"
pip install -r requirements.txt

echo "--- Bắt đầu lập chỉ mục dữ liệu ---"
python indexer.py

echo "--- Build hoàn tất ---"