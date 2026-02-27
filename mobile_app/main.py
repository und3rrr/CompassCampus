"""
CampusCompass Mobile - Главное приложение Kivy
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.clock import Clock
from screens.login_screen import LoginScreen
from screens.home_screen import HomeScreen
from screens.map_screen import MapScreen
from screens.qr_scanner_screen import QRScannerScreen
from screens.admin_screen import AdminScreen
from screens.history_screen import HistoryScreen
from screens.graph_editor_screen import GraphEditorScreen
from services.api_client import init_api_client
from services.cache_service import init_cache_service
from services.auth_service import AuthenticationService
from services.qr_service import QRCodeService
from services.route_closure_service import RouteClosureService
import logging
import os

# Настройка размера окна для Android
Window.size = (480, 800)

# Настройка логирования (временно ставим DEBUG для детальной диагностики старта)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CampusCompassApp(App):
    """Главное приложение CampusCompass"""

    def build(self):
        """Построить основной UI приложения"""
        logger.info("Starting CampusCompass Mobile Application")

        import time
        start_time = time.time()

        # Инициализируем сервисы (защищённо)
        api_url = os.getenv('API_URL', 'http://localhost:8000/api/v1')
        cache_dir = os.path.join(self.user_data_dir, '.cache')
        try:
            init_api_client(base_url=api_url)
            init_cache_service(cache_dir=cache_dir)
        except Exception as e:
            logger.exception(f"Error initializing services: {e}")

        # Инициализируем сервисы аутентификации и QR кодов
        auth_service = AuthenticationService(
            profile_dir=os.path.join(self.user_data_dir, '.profiles')
        )
        qr_service = QRCodeService(
            qr_dir=os.path.join(self.user_data_dir, '.qr_codes')
        )
        closure_service = RouteClosureService(
            closure_dir=os.path.join(self.user_data_dir, '.closures')
        )

        logger.info(f"API URL: {api_url}")
        logger.info(f"Cache dir: {cache_dir}")

        # Сохраняем сервисы в App для доступа из других скринов
        self.auth_service = auth_service
        self.qr_service = qr_service
        self.closure_service = closure_service

        # Создаём ScreenManager
        screen_manager = ScreenManager(transition=FadeTransition())

        # Добавляем скрины
        logger.info("[build] Adding LoginScreen...")
        login_screen = LoginScreen(auth_service, name='login')
        screen_manager.add_widget(login_screen)
        
        logger.info("[build] Adding HomeScreen...")
        home_screen = HomeScreen(name='home')
        screen_manager.add_widget(home_screen)
        
        logger.info("[build] Adding MapScreen...")
        map_screen = MapScreen(name='map')
        map_screen.closure_service = closure_service  # Устанавливаем сервис закрытий
        screen_manager.add_widget(map_screen)
        
        logger.info("[build] Adding QRScannerScreen...")
        qr_scanner_screen = QRScannerScreen(qr_service=qr_service, name='qr_scanner')
        screen_manager.add_widget(qr_scanner_screen)
        
        logger.info("[build] Adding AdminScreen...")
        admin_screen = AdminScreen(auth_service=auth_service, qr_service=qr_service, 
                                   closure_service=closure_service, name='admin')
        screen_manager.add_widget(admin_screen)
        
        logger.info("[build] Adding HistoryScreen...")
        history_screen = HistoryScreen(auth_service=auth_service, name='history')
        screen_manager.add_widget(history_screen)
        
        logger.info("[build] Adding GraphEditorScreen...")
        graph_editor_screen = GraphEditorScreen(name='graph_editor')
        screen_manager.add_widget(graph_editor_screen)
        
        logger.info("[build] All screens added")

        # Устанавливаем начальный скрин - сразу открываем карту
        screen_manager.current = 'map'

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Application initialized successfully in {elapsed:.0f}ms")

        # Heartbeat logger helps detect UI thread freezes (prints every second)
        self._heartbeat_count = 0
        def _heartbeat(dt):
            try:
                self._heartbeat_count += 1
                # Выключаем heartbeat в production логировании
                # logger.debug(f"[HEARTBEAT] UI alive #{self._heartbeat_count} current_screen={screen_manager.current}")
            except Exception:
                logger.exception("Heartbeat failed")
        Clock.schedule_interval(_heartbeat, 1.0)

        return screen_manager

    def on_pause(self):
        """Обработка паузы приложения (на Android)"""
        logger.info("Application paused")
        return True

    def on_resume(self):
        """Обработка возобновления приложения (на Android)"""
        logger.info("Application resumed")

    def on_stop(self):
        """Обработка остановки приложения"""
        logger.info("Application stopped")
        # Сохраняем текущего пользователя
        if self.auth_service.current_user:
            self.auth_service._save_last_user()


def main():
    """Точка входа приложения"""
    app = CampusCompassApp()
    app.run()


if __name__ == '__main__':
    main()

