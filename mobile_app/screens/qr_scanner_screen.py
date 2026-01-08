"""
QR сканер для навигации - экран для сканирования QR кодов
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from services.qr_service import QRCodeService
from services.api_client import get_api_client
import logging

logger = logging.getLogger(__name__)


class QRScannerScreen(Screen):
    """Экран для сканирования QR кодов"""

    def __init__(self, qr_service=None, **kwargs):
        super().__init__(**kwargs)
        self.qr_service = qr_service
        self.api_client = get_api_client()
        
        # Основной лейаут
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Заголовок
        title = Label(
            text='[b]QR Сканер[/b]\nНаведите на QR код',
            markup=True,
            size_hint_y=0.15,
            font_size='18sp'
        )
        main_layout.add_widget(title)

        # Попытка использовать камеру (может не работать на всех системах)
        try:
            self.camera = Camera(play=True, size_hint_y=0.7)
            main_layout.add_widget(self.camera)
            self.camera_available = True
        except Exception as e:
            logger.warning(f"Camera not available: {e}")
            # Fallback на ввод текста если камера недоступна
            fallback_label = Label(
                text='Камера недоступна.\nВведите QR код вручную:',
                size_hint_y=0.3,
                markup=True
            )
            main_layout.add_widget(fallback_label)
            
            from kivy.uix.textinput import TextInput
            self.manual_input = TextInput(
                hint_text='Введите QR код или скопируйте из буфера обмена',
                multiline=False,
                size_hint_y=0.4
            )
            main_layout.add_widget(self.manual_input)
            self.camera_available = False

        # Кнопки внизу
        btn_layout = BoxLayout(size_hint_y=0.15, spacing=dp(10))

        if not self.camera_available:
            scan_btn = Button(text='Распознать')
            scan_btn.bind(on_press=self.on_manual_scan)
            btn_layout.add_widget(scan_btn)

        back_btn = Button(text='Назад')
        back_btn.bind(on_press=self.on_back)
        btn_layout.add_widget(back_btn)

        main_layout.add_widget(btn_layout)

        self.add_widget(main_layout)

        # Статус сканирования
        self.status_label = Label(
            text='',
            pos_hint={'x': 0, 'y': 0},
            size_hint=(1, 0.1)
        )

    def on_manual_scan(self, instance):
        """Обработка ручного ввода QR кода"""
        if not self.camera_available:
            qr_code = self.manual_input.text.strip()
            if qr_code:
                self._process_qr_code(qr_code)
            else:
                self._show_message("Введите QR код")

    def _process_qr_code(self, qr_code: str):
        """Обработать QR код"""
        try:
            mapping = self.qr_service.get_location_by_qr(qr_code)
            
            if mapping:
                # QR код найден! Переходим на карту с этим узлом
                message = f"✅ Найдено: {mapping.node_name} (Этаж {mapping.floor})"
                logger.info(f"QR code scanned: {mapping.node_name}")
                
                # Передаём информацию в MapScreen
                # TODO: Реализовать переход на MapScreen с автоматическим выбором узла
                self._show_message(message)
            else:
                self._show_message(f"❌ QR код не найден: {qr_code}")
                logger.warning(f"Unknown QR code: {qr_code}")
        except Exception as e:
            logger.error(f"Error processing QR code: {e}")
            self._show_message(f"Ошибка: {str(e)}")

    def _show_message(self, message: str):
        """Показать сообщение"""
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        label = Label(text=message, markup=True)
        popup_layout.add_widget(label)
        
        close_btn = Button(text='OK', size_hint_y=0.3)
        popup_layout.add_widget(close_btn)
        
        popup = Popup(
            title='Статус',
            content=popup_layout,
            size_hint=(0.8, 0.4)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def on_back(self, instance):
        """Вернуться назад"""
        self.manager.current = 'home'

    def on_enter(self):
        """Вызывается при входе на экран"""
        if hasattr(self, 'camera') and self.camera_available:
            try:
                self.camera.play = True
                logger.info("Camera started")
            except Exception as e:
                logger.error(f"Failed to start camera: {e}")

    def on_leave(self):
        """Вызывается при выходе со экрана"""
        if hasattr(self, 'camera') and self.camera_available:
            try:
                self.camera.play = False
                logger.info("Camera stopped")
            except Exception as e:
                logger.error(f"Failed to stop camera: {e}")
