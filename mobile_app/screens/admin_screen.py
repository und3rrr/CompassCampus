"""
Экран администратора для управления маршрутами и ресурсами
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.clock import Clock
from services.auth_service import AuthenticationService, UserRole, UserPermission
from services.route_closure_service import RouteClosureService, ClosureType
from services.qr_service import QRCodeService
from services.api_client import get_api_client
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AdminScreen(Screen):
    """Экран администратора для управления системой"""

    def __init__(self, auth_service: AuthenticationService = None, 
                 qr_service = None, closure_service = None, **kwargs):
        # Извлекаем сервисы из kwargs (убираем их перед super())
        auth_service = auth_service or kwargs.pop('auth_service', None)
        qr_service = qr_service or kwargs.pop('qr_service', None)
        closure_service = closure_service or kwargs.pop('closure_service', None)
        
        super().__init__(**kwargs)
        self.auth_service = auth_service
        self.qr_service = qr_service
        self.closure_service = closure_service
        self.api_client = get_api_client()
        
        # Основной лейаут
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Заголовок
        title_label = Label(
            text='[b]Панель администратора[/b]',
            markup=True,
            size_hint_y=0.1,
            font_size='20sp'
        )
        main_layout.add_widget(title_label)

        # Кнопки для разных функций
        button_layout = GridLayout(cols=2, size_hint_y=0.3, spacing=dp(10))

        # Кнопка "Управление маршрутами"
        routes_btn = Button(
            text='🚧\nУправление\nмаршрутами',
            background_color=(1.0, 0.5, 0.0, 1.0)
        )
        routes_btn.bind(on_press=self.show_routes_management)
        button_layout.add_widget(routes_btn)

        # Кнопка "QR коды"
        qr_btn = Button(
            text='📱\nУправление\nQR кодами',
            background_color=(0.3, 0.6, 1.0, 1.0)
        )
        qr_btn.bind(on_press=self.show_qr_management)
        button_layout.add_widget(qr_btn)

        # Кнопка "Пользователи"
        users_btn = Button(
            text='👥\nПользователи',
            background_color=(0.3, 0.8, 0.3, 1.0)
        )
        users_btn.bind(on_press=self.show_users_management)
        button_layout.add_widget(users_btn)

        # Кнопка "Статистика"
        stats_btn = Button(
            text='📊\nСтатистика',
            background_color=(0.8, 0.3, 0.8, 1.0)
        )
        stats_btn.bind(on_press=self.show_statistics)
        button_layout.add_widget(stats_btn)

        main_layout.add_widget(button_layout)

        # Информационная панель
        self.info_label = Label(
            text='Выберите функцию для управления',
            size_hint_y=0.2,
            markup=True
        )
        main_layout.add_widget(self.info_label)

        # Кнопки внизу
        bottom_layout = BoxLayout(size_hint_y=0.1, spacing=dp(10))

        back_btn = Button(text='↩ Назад')
        back_btn.bind(on_press=self.on_back)
        bottom_layout.add_widget(back_btn)

        main_layout.add_widget(bottom_layout)
        self.add_widget(main_layout)

    def on_enter(self):
        """Проверить права администратора"""
        user = self.auth_service.get_current_user()
        if not user or user.role != UserRole.ADMIN:
            logger.warning("Non-admin user tried to access admin screen")
            self.manager.current = 'home'

    def show_routes_management(self, instance):
        """Показать управление маршрутами"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        title = Label(text='[b]Управление маршрутами[/b]', markup=True, size_hint_y=0.1)
        content.add_widget(title)

        # Form для закрытия маршрута
        form = GridLayout(cols=2, size_hint_y=0.5, spacing=dp(10))

        form.add_widget(Label(text='От узла:', size_hint_y=0.1))
        from_input = TextInput(hint_text='101', multiline=False, size_hint_y=0.1)
        form.add_widget(from_input)

        form.add_widget(Label(text='К узлу:', size_hint_y=0.1))
        to_input = TextInput(hint_text='102', multiline=False, size_hint_y=0.1)
        form.add_widget(to_input)

        form.add_widget(Label(text='Причина:', size_hint_y=0.1))
        reason_input = TextInput(hint_text='Ремонт', multiline=False, size_hint_y=0.1)
        form.add_widget(reason_input)

        form.add_widget(Label(text='Тип:', size_hint_y=0.1))
        type_spinner = Spinner(
            text='repair',
            values=('maintenance', 'repair', 'cleaning', 'emergency', 'other'),
            size_hint_y=0.1
        )
        form.add_widget(type_spinner)

        content.add_widget(form)

        # Кнопки
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=dp(10))

        def close_route():
            from_id = from_input.text.strip()
            to_id = to_input.text.strip()
            reason = reason_input.text.strip()
            closure_type = ClosureType(type_spinner.text)

            if from_id and to_id:
                closure_service = RouteClosureService()
                closure_service.close_route(
                    from_id=from_id,
                    to_id=to_id,
                    closure_type=closure_type,
                    reason=reason,
                    created_by=self.auth_service.get_current_user().user_id,
                    scheduled_until=datetime.now() + timedelta(hours=24)
                )
                self.info_label.text = f'✅ Маршрут {from_id}->{to_id} закрыт'
                popup.dismiss()
            else:
                self.info_label.text = '❌ Заполните поля'

        close_btn = Button(text='Закрыть маршрут')
        close_btn.bind(on_press=lambda x: close_route())
        btn_layout.add_widget(close_btn)

        cancel_btn = Button(text='Отмена')
        btn_layout.add_widget(cancel_btn)

        content.add_widget(btn_layout)

        popup = Popup(
            title='Закрыть маршрут',
            content=content,
            size_hint=(0.9, 0.8)
        )
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_qr_management(self, instance):
        """Показать управление QR кодами"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        title = Label(text='[b]Управление QR кодами[/b]', markup=True, size_hint_y=0.1)
        content.add_widget(title)

        # Form для создания QR кода
        form = GridLayout(cols=2, size_hint_y=0.5, spacing=dp(10))

        form.add_widget(Label(text='ID узла:', size_hint_y=0.1))
        node_input = TextInput(hint_text='101', multiline=False, size_hint_y=0.1)
        form.add_widget(node_input)

        form.add_widget(Label(text='Название:', size_hint_y=0.1))
        name_input = TextInput(hint_text='Аудитория 101', multiline=False, size_hint_y=0.1)
        form.add_widget(name_input)

        form.add_widget(Label(text='Этаж:', size_hint_y=0.1))
        floor_input = TextInput(hint_text='1', multiline=False, size_hint_y=0.1)
        form.add_widget(floor_input)

        content.add_widget(form)

        # Кнопки
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=dp(10))

        def create_qr():
            node_id = node_input.text.strip()
            name = name_input.text.strip()
            floor = floor_input.text.strip()

            if node_id and name and floor:
                qr_service = QRCodeService()
                qr_code = qr_service.create_qr_mapping(
                    node_id=node_id,
                    node_name=name,
                    floor=int(floor),
                    created_by=self.auth_service.get_current_user().user_id
                )
                self.info_label.text = f'✅ QR код создан: {qr_code}'
                popup.dismiss()
            else:
                self.info_label.text = '❌ Заполните все поля'

        create_btn = Button(text='Создать QR код')
        create_btn.bind(on_press=lambda x: create_qr())
        btn_layout.add_widget(create_btn)

        cancel_btn = Button(text='Отмена')
        btn_layout.add_widget(cancel_btn)

        content.add_widget(btn_layout)

        popup = Popup(
            title='Создать QR код',
            content=content,
            size_hint=(0.9, 0.8)
        )
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_users_management(self, instance):
        """Показать управление пользователями"""
        self.info_label.text = '👥 Управление пользователями\n(будет доступно в следующей версии)'

    def show_statistics(self, instance):
        """Показать статистику"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        title = Label(text='[b]Статистика системы[/b]', markup=True, size_hint_y=0.1)
        content.add_widget(title)

        # Получить информацию о закрытиях
        closure_service = RouteClosureService()
        active_closures = closure_service.get_active_closures()

        # Получить информацию о QR кодах
        qr_service = QRCodeService()
        all_qr = qr_service.get_all_qr_codes(active_only=True)

        stats_text = f"""
[b]Активные закрытия маршрутов:[/b] {len(active_closures)}

[b]QR коды:[/b] {len(all_qr)}

[b]Последние действия:[/b]
"""
        if active_closures:
            for closure in active_closures[:3]:
                stats_text += f"\n• {closure.from_id} -> {closure.to_id}: {closure.reason}"

        stats_label = Label(
            text=stats_text,
            markup=True,
            size_hint_y=0.8
        )
        content.add_widget(stats_label)

        close_btn = Button(text='Закрыть', size_hint_y=0.1)
        content.add_widget(close_btn)

        popup = Popup(
            title='Статистика',
            content=content,
            size_hint=(0.9, 0.8)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def on_back(self, instance):
        """Вернуться на домашний экран"""
        self.manager.current = 'home'
