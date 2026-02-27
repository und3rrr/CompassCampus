"""
SVG to PNG converter for floor plans
Converts all SVG files to PNG format for use in the app
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SVGToPNGConverter:
    """Конвертер SVG в PNG используя PyQt5"""

    SUPPORTED_FORMATS = ('.svg', '.SVG')
    OUTPUT_FORMAT = '.png'

    @staticmethod
    def convert_file(svg_path: str, output_path: str, width: int = 9757, height: int = 3408) -> bool:
        """
        Конвертировать один SVG файл в PNG используя PyQt5

        Args:
            svg_path: Путь к SVG файлу
            output_path: Путь для сохранения PNG
            width: Ширина вывода в пиксель
            height: Высота вывода в пиксель

        Returns:
            True если успешно, False если ошибка
        """
        try:
            from PyQt5.QtGui import QPixmap, QImage, QPainter
            from PyQt5.QtSvg import QSvgRenderer
            from PyQt5.QtCore import QSize
            
            if not os.path.exists(svg_path):
                logger.error(f"SVG file not found: {svg_path}")
                return False
            
            # Создаём рендеринг SVG
            renderer = QSvgRenderer(svg_path)
            
            # Создаём изображение нужного размера
            image = QImage(width, height, QImage.Format_ARGB32)
            image.fill(0xffffffff)  # Заполняем белым цветом
            
            # Рисуем SVG на изображение
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            
            # Сохраняем как PNG
            image.save(output_path, "PNG")
            
            logger.info(f"Converted: {svg_path} -> {output_path} ({width}x{height})")
            return True
            
        except Exception as e:
            logger.error(f"Error converting {svg_path}: {e}")
            return False

    @staticmethod
    def convert_folder(folder_path: str, output_folder: Optional[str] = None, width: int = 9757, height: int = 3408) -> dict:
        """
        Конвертировать все SVG файлы в папке

        Args:
            folder_path: Папка с SVG файлами
            output_folder: Папка для вывода (по умолчанию = input folder)
            width: Ширина вывода
            height: Высота вывода

        Returns:
            Словарь с результатами: {'success': [...], 'failed': [...]}
        """
        if output_folder is None:
            output_folder = folder_path
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        results = {'success': [], 'failed': []}
        
        try:
            for filename in os.listdir(folder_path):
                if not any(filename.lower().endswith(fmt) for fmt in SVGToPNGConverter.SUPPORTED_FORMATS):
                    continue
                
                svg_path = os.path.join(folder_path, filename)
                png_filename = os.path.splitext(filename)[0] + SVGToPNGConverter.OUTPUT_FORMAT
                output_path = os.path.join(output_folder, png_filename)
                
                if SVGToPNGConverter.convert_file(svg_path, output_path, width, height):
                    results['success'].append(filename)
                else:
                    results['failed'].append(filename)
        
        except Exception as e:
            logger.error(f"Error processing folder {folder_path}: {e}")
        
        logger.info(f"Conversion complete: {len(results['success'])} successful, {len(results['failed'])} failed")
        return results


if __name__ == '__main__':
    # Скрипт для конвертации напрямую
    import sys
    
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = os.path.join(os.path.dirname(__file__), '../assets/floor_plans')
    
    print(f"Converting SVG files in: {folder}")
    results = SVGToPNGConverter.convert_folder(folder, width=9757, height=3408)
    
    print(f"\nSuccessful: {results['success']}")
    print(f"Failed: {results['failed']}")

