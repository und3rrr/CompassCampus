"""
SVG to PNG converter for floor plans using PyQt5
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)


def convert_svg_to_png():
    """Convert all SVG files in assets/floor_plans to PNG"""
    
    # Импортируем PyQt5 после инициа QApplication
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QImage, QPainter
    from PyQt5.QtSvg import QSvgRenderer
    
    # Создаём QApplication (необходимо для рендеринга)
    app = QApplication(sys.argv)
    
    # Правильно разрешаем путь
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(script_dir, 'assets', 'floor_plans')
    folder_path = os.path.normpath(folder_path)
    
    print(f"Converting SVG files in: {folder_path}")
    
    success = []
    failed = []
    
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith('.svg'):
            continue
        
        svg_path = os.path.join(folder_path, filename)
        png_filename = os.path.splitext(filename)[0] + '.png'
        output_path = os.path.join(folder_path, png_filename)
        
        try:
            print(f"Converting: {filename}...", end=' ')
            
            # Создаём рендеринг SVG
            renderer = QSvgRenderer(svg_path)
            
            # Создаём изображение нужного размера (9757 x 3408 пиксель)
            image = QImage(9757, 3408, QImage.Format_ARGB32)
            image.fill(0xffffffff)  # Заполняем белым цветом
            
            # Рисуем SVG на изображение
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            
            # Сохраняем как PNG
            if image.save(output_path, "PNG"):
                print("OK")
                success.append(filename)
            else:
                print("FAILED (save)")
                failed.append(filename)
        
        except Exception as e:
            print(f"FAILED ({e})")
            failed.append(filename)
    
    print(f"\nSuccessful: {len(success)}/{len(success) + len(failed)}")
    for f in success:
        print(f"  ✓ {f}")
    
    if failed:
        print(f"\nFailed: {len(failed)}")
        for f in failed:
            print(f"  ✗ {f}")
    
    return len(failed) == 0


if __name__ == '__main__':
    success = convert_svg_to_png()
    sys.exit(0 if success else 1)
