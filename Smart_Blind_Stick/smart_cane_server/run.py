#!/usr/bin/env python3
"""
File chạy server Flask
Chạy: python run.py
"""

import sys
import os

# Thêm thư mục hiện tại vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 KHỞI ĐỘNG SERVER GẬY THÔNG MINH")
    print("=" * 60)
    print("📌 Lưu ý:")
    print("  • Server sẽ chạy tại: http://localhost:5000")
    print("  • Để dừng server: Nhấn Ctrl+C")
    print("  • Đảm bảo ESP32 cùng mạng WiFi với máy này")
    print("=" * 60)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n👋 Đang tắt server...")
        print("✅ Server đã dừng")