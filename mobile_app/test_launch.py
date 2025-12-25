#!/usr/bin/env python3
"""
Скрипт быстрого запуска и теста приложения
"""
import sys
import os

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == '__main__':
    print("🚀 Запуск CampusCompass Mobile Application...")
    print("=" * 50)
    main()
