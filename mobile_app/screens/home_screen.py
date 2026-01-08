"""
Главный экран приложения (выбор здания)
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from services.api_client import get_api_client, Building
from services.cache_service import get_cache_service
import logging
import threading

logger = logging.getLogger(__name__)
Window.size = (480, 800)


class HomeScreen(Screen):
    """Экран выбора здания"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.buildings: list[Building] = []
        self.api_client = get_api_client()
        self.cache_service = get_cache_service()

        # Основной лейаут
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Заголовок
        title_label = Label(
            text='[b]CampusCompass[/b]\nВыберите здание',
            markup=True,
            size_hint_y=0.15,
            font_size='24sp'
        )
        main_layout.add_widget(title_label)

        # ScrollView для списка зданий
        scroll_view = ScrollView(size_hint=(1, 0.7))
        self.buildings_grid = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(5)
        )
        self.buildings_grid.bind(minimum_height=self.buildings_grid.setter('height'))
        scroll_view.add_widget(self.buildings_grid)
        main_layout.add_widget(scroll_view)

        # Кнопки внизу
        button_layout = BoxLayout(size_hint_y=0.15, spacing=dp(5))

        refresh_btn = Button(
            text='Обновить',
            size_hint_x=0.25,
            background_color=(0.3, 0.6, 1.0, 1.0)
        )
        refresh_btn.bind(on_press=self.on_refresh)
        button_layout.add_widget(refresh_btn)

        qr_btn = Button(
            text='QR',
            size_hint_x=0.15,
            background_color=(0.0, 0.7, 0.3, 1.0)
        )
        qr_btn.bind(on_press=self.on_qr_scanner)
        button_layout.add_widget(qr_btn)

        history_btn = Button(
            text='История',
            size_hint_x=0.2,
            background_color=(0.5, 0.7, 0.5, 1.0)
        )
        history_btn.bind(on_press=self.on_history)
        button_layout.add_widget(history_btn)

        admin_btn = Button(
            text='Админ',
            size_hint_x=0.15,
            background_color=(0.7, 0.5, 0.5, 1.0)
        )
        admin_btn.bind(on_press=self.on_admin)
        button_layout.add_widget(admin_btn)

        settings_btn = Button(
            text='Выход',
            size_hint_x=0.15,
            background_color=(0.7, 0.7, 0.7, 1.0)
        )
        settings_btn.bind(on_press=self.on_settings)
        button_layout.add_widget(settings_btn)

        main_layout.add_widget(button_layout)
        self.add_widget(main_layout)

    def on_enter(self):
        """Вызывается при входе на экран"""
        self.load_buildings()

    def load_buildings(self):
        """Загрузить здания из API"""
        # Показываем лоадер
        loader_label = Label(text='Загрузка зданий...', size_hint_y=None, height=dp(50))
        self.buildings_grid.add_widget(loader_label)

        # Загружаем в отдельном потоке
        thread = threading.Thread(target=self._fetch_buildings)
        thread.daemon = True
        thread.start()

    def _fetch_buildings(self):
        """Получить здания с API (в отдельном потоке)"""
        try:
            logger.info("Fetching buildings from API")
            self.buildings = self.api_client.get_buildings()
            # Демо-данные уже закэшированы в api_client, не кэшируем их здесь

            # Обновляем UI в главном потоке через Clock
            Clock.schedule_once(lambda dt: self._update_buildings_display(), 0)

        except Exception as e:
            logger.error(f"Failed to load buildings: {e}")
            # Сохраняем сообщение об ошибке перед lambda
            error_message = f"Ошибка загрузки: {str(e)}"
            Clock.schedule_once(lambda dt, msg=error_message: self._show_error_popup(msg), 0)

    def _update_buildings_display(self):
        """Обновить отображение зданий"""
        self.buildings_grid.clear_widgets()

        if not self.buildings:
            error_label = Label(
                text='Нет доступных зданий',
                size_hint_y=None,
                height=dp(50)
            )
            self.buildings_grid.add_widget(error_label)
            return

        for building in self.buildings:
            btn = Button(
                text=f'[b]{building.name}[/b]\n{building.address}\nЭтажей: {building.floors}',
                markup=True,
                size_hint_y=None,
                height=dp(80),
                background_color=(0.3, 0.6, 1.0, 1.0)
            )
            btn.building = building
            btn.bind(on_press=self.on_building_selected)
            self.buildings_grid.add_widget(btn)

    def on_building_selected(self, instance):
        """Обработка выбора здания"""
        building = instance.building
        logger.info(f"Selected building: {building.name}")

        # Переходим на экран карты
        self.manager.get_screen('map').set_building(building)
        self.manager.current = 'map'

    def on_refresh(self, instance):
        """Обновить список зданий"""
        self.cache_service.delete('buildings')
        self.buildings_grid.clear_widgets()
        self.load_buildings()

    def on_history(self, instance):
        """Открыть историю посещений"""
        self.manager.current = 'history'

    def on_qr_scanner(self, instance):
        """Открыть QR сканер"""
        self.manager.current = 'qr_scanner'

    def on_admin(self, instance):
        """Открыть админ-панель"""
        self.manager.current = 'admin'

    def on_settings(self, instance):
        """Выход из приложения"""
        from kivy.app import App
        App.get_running_app().stop()

    def _save_settings(self, api_url: str):
        """Сохранить настройки"""
        if api_url.strip():
            self.api_client.set_base_url(api_url)
            self.cache_service.delete('buildings')
            logger.info(f"API URL changed to: {api_url}")
            self._show_info_popup("Настройки сохранены!")
            self.on_refresh(None)

    def _show_error_popup(self, message: str):
        """Показать ошибку"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        label = Label(text=message)
        content.add_widget(label)

        btn = Button(text='OK', size_hint_y=0.3)
        content.add_widget(btn)

        popup = Popup(
            title='Ошибка',
            content=content,
            size_hint=(0.8, 0.4)
        )
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def _show_info_popup(self, message: str):
        """Показать информационное сообщение"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        label = Label(text=message)
        content.add_widget(label)

        btn = Button(text='OK', size_hint_y=0.3)
        content.add_widget(btn)

        popup = Popup(
            title='Информация',
            content=content,
            size_hint=(0.8, 0.4)
        )
        btn.bind(on_press=popup.dismiss)
        popup.open()
